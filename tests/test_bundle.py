import os
import re
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASH = shutil.which("bash")
if not BASH and os.name == "nt":
    git_bash = Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Git" / "bin" / "bash.exe"
    if git_bash.is_file():
        BASH = str(git_bash)
PROFILE_NAMES = {
    "default",
    "researcher",
    "coder",
    "reviewer",
    "wiki-maintainer",
    "web-scraper",
    "web-monitor",
}
WORKERS = PROFILE_NAMES - {"default"}
EXPECTED_TOOLSETS = {
    "default": {"kanban", "clarify", "todo", "memory", "session_search"},
    "researcher": {"web", "browser", "file", "terminal", "memory", "session_search"},
    "coder": {"file", "terminal", "memory"},
    "reviewer": {"file", "terminal", "web"},
    "wiki-maintainer": {"file", "terminal", "memory"},
    "web-scraper": {"web", "file", "terminal"},
    "web-monitor": {"web", "file"},
}


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def platform_toolsets(config: str, platform: str) -> set[str]:
    match = re.search(rf"(?m)^  {re.escape(platform)}: \[([^]]*)\]$", config)
    if not match:
        raise AssertionError(f"missing explicit platform_toolsets.{platform} allowlist")
    return {item.strip() for item in match.group(1).split(",") if item.strip()}


class BundleTests(unittest.TestCase):
    def test_exact_profile_set(self):
        actual = {path.name for path in (ROOT / "profiles").iterdir() if path.is_dir()}
        self.assertEqual(PROFILE_NAMES, actual)
        for name in PROFILE_NAMES:
            for required in ("config.yaml", "SOUL.md", ".env.example"):
                self.assertTrue((ROOT / "profiles" / name / required).is_file())

    def test_exact_positive_toolset_allowlists(self):
        for name, expected in EXPECTED_TOOLSETS.items():
            config = read(f"profiles/{name}/config.yaml")
            for platform in ("cli", "telegram", "api_server", "cron"):
                self.assertEqual(expected, platform_toolsets(config, platform), f"{name}:{platform}")

    def test_bootstrap_opts_every_profile_out_of_bundled_skills(self):
        bootstrap = read("scripts/bootstrap-user.sh")
        self.assertIn("hermes skills opt-out", bootstrap)
        self.assertIn('--no-alias --no-skills', bootstrap)
        self.assertIn('hermes -p "$profile" skills opt-out', bootstrap)

    def test_openai_runtime_is_explicitly_auto(self):
        for name in PROFILE_NAMES:
            config = read(f"profiles/{name}/config.yaml")
            self.assertIn("  openai_runtime: auto", config, name)
            self.assertIn("updates:\n  check: false", config, name)

    def test_forbidden_toolsets_are_explicitly_disabled(self):
        forbidden = {
            "code_execution",
            "delegation",
            "computer_use",
            "messaging",
            "cronjob",
        }
        for name in PROFILE_NAMES:
            config = read(f"profiles/{name}/config.yaml")
            disabled_match = re.search(r"disabled_toolsets:\s*(?:\[([^]]*)\]|\n((?:    - .+\n)+))", config)
            self.assertIsNotNone(disabled_match, name)
            disabled_text = " ".join(group or "" for group in disabled_match.groups())
            self.assertTrue(forbidden <= set(re.findall(r"[a-z_]+", disabled_text)), name)

    def test_browser_is_hardened_and_limited_to_researcher(self):
        researcher = read("profiles/researcher/config.yaml")
        required = (
            '  backend: "off"',
            "  cloud_provider: local",
            "  engine: chrome",
            "  headed: false",
            "  inactivity_timeout: 60",
            "  command_timeout: 30",
            "  record_sessions: false",
            "  allow_private_urls: false",
            "  auto_local_for_private_urls: false",
            '  cdp_url: ""',
            "  restrict_evaluate: true",
            "  allow_unsafe_evaluate: false",
            "  use_real_profile: false",
            "  dialog_policy: auto_dismiss",
            "  dialog_timeout_s: 30",
        )
        for setting in required:
            self.assertIn(setting, researcher)
        disabled = re.search(r"disabled_toolsets: \[([^]]*)\]", researcher)
        self.assertIsNotNone(disabled)
        self.assertNotIn("browser", set(re.findall(r"[a-z_]+", disabled.group(1))))

        for name in PROFILE_NAMES - {"researcher"}:
            config = read(f"profiles/{name}/config.yaml")
            disabled_match = re.search(r"disabled_toolsets:\s*(?:\[([^]]*)\]|\n((?:    - .+\n)+))", config)
            self.assertIsNotNone(disabled_match, name)
            disabled_text = " ".join(group or "" for group in disabled_match.groups())
            self.assertIn("browser", set(re.findall(r"[a-z_]+", disabled_text)), name)
            self.assertNotRegex(config, r"(?m)^browser:$", name)

    def test_web_capability_is_limited_to_source_facing_profiles(self):
        web_profiles = {"researcher", "reviewer", "web-scraper", "web-monitor"}
        for name in PROFILE_NAMES - web_profiles:
            config = read(f"profiles/{name}/config.yaml")
            disabled_match = re.search(r"disabled_toolsets:\s*(?:\[([^]]*)\]|\n((?:    - .+\n)+))", config)
            self.assertIsNotNone(disabled_match, name)
            disabled_text = " ".join(group or "" for group in disabled_match.groups())
            self.assertIn("web", set(re.findall(r"[a-z_]+", disabled_text)), name)
            self.assertNotRegex(config, r"(?m)^web:$", name)

    def test_worker_sandboxes_are_networkless_and_ephemeral(self):
        required = (
            "backend: docker",
            "lifetime_seconds: 600",
            "docker_mount_cwd_to_workspace: true",
            "docker_run_as_host_user: true",
            "docker_forward_env: []",
            "docker_network: false",
            'docker_extra_args: ["--pids-limit", "256"]',
            "container_cpu: 1",
            "container_memory: 1536",
            "container_persistent: false",
            "docker_persist_across_processes: false",
        )
        for name in WORKERS:
            config = read(f"profiles/{name}/config.yaml")
            for line in required:
                self.assertIn(line, config, f"{name}: {line}")
            self.assertNotRegex(config, r"(?m)^\s+cwd:")
            self.assertNotIn("docker.sock", config)
            self.assertNotIn("docker_volumes:", config)

    def test_default_is_only_profile_with_telegram_secret(self):
        default_env = read("profiles/default/.env.example")
        self.assertIn("TELEGRAM_BOT_TOKEN=", default_env)
        self.assertIn("TELEGRAM_ALLOWED_CHATS=", default_env)
        self.assertIn("GATEWAY_ALLOW_ALL_USERS=false", default_env)
        for name in WORKERS:
            self.assertNotIn("TELEGRAM_", read(f"profiles/{name}/.env.example"), name)
        self.assertIn("AGENT_BROWSER_EXECUTABLE_PATH=", read("profiles/researcher/.env.example"))
        self.assertIn(
            "AGENT_BROWSER_EXECUTABLE_PATH=$hermes_home/bin/chromium",
            read("scripts/bootstrap-user.sh"),
        )

    def test_fallback_policy(self):
        fallback = {"researcher", "wiki-maintainer", "web-scraper", "web-monitor"}
        for name in PROFILE_NAMES:
            config = read(f"profiles/{name}/config.yaml")
            if name in fallback:
                self.assertIn("model: openrouter/free", config)
                self.assertIn("model: nous/welcome", config)
            else:
                self.assertNotIn("fallback_providers:", config)

    def test_compose_ports_limits_and_digest_variables(self):
        compose = read("infra/compose.yaml")
        published = re.findall(r'- "([^\"]+:[0-9]+)"', compose)
        self.assertEqual({"127.0.0.1:8888:8080", "127.0.0.1:3002:3002"}, set(published))
        for limit in ("128m", "256m", "384m", "512m", "2g"):
            self.assertIn(f"mem_limit: {limit}", compose)
        self.assertNotRegex(compose, r"(?m)^\s+image:\s+[^$]")
        self.assertIn('max-size: "10m"', compose)
        self.assertIn('max-file: "3"', compose)
        self.assertIn('NUM_WORKERS_PER_QUEUE: "1"', compose)
        self.assertIn('MAX_CONCURRENT_JOBS: "1"', compose)
        self.assertIn('BROWSER_POOL_SIZE: "1"', compose)

    def test_dashboard_and_web_ports_are_loopback_only(self):
        self.assertIn("dashboard --host 127.0.0.1 --port 9119", read("systemd/hermes-dashboard.service.in"))
        compose = read("infra/compose.yaml")
        self.assertNotIn('"0.0.0.0:8888:', compose)
        self.assertNotIn('"0.0.0.0:3002:', compose)

    def test_monitor_installs_paused_with_default_delivery(self):
        script = read("scripts/install-monitor.sh")
        self.assertIn("--paused", script)
        self.assertIn("--deliver bot-chat:default", script)
        self.assertNotIn(" cron resume ", script)
        self.assertIn("MONITOR_SCHEMA", script)
        self.assertIn("Set MONITOR_SELECTOR, MONITOR_SCHEMA, or both.", script)

    def test_board_sync_uses_pinned_cli_and_accepts_list_json(self):
        script = read("scripts/sync-boards.sh")
        self.assertIn("boards set-default-workdir", script)
        self.assertNotIn("boards set-workdir", script)
        self.assertIn('if type == "array"', script)

    def test_web_stack_requires_installed_egress_guard(self):
        unit = read("systemd/hermes-web.service.in")
        self.assertIn("ExecStartPre=/usr/bin/test -r /etc/nftables.d/hermes-egress.nft", unit)
        self.assertIn("ExecStartPre=/usr/bin/systemctl is-active --quiet nftables.service", unit)
        guard = read("scripts/install-egress-guard.sh")
        self.assertIn("ct state established,related accept", guard)
        self.assertIn("::ffff:169.254.0.0/112", guard)

    def test_operational_scripts_exist(self):
        for name in (
            "install-host.sh",
            "install-hermes.sh",
            "install-browser.sh",
            "bootstrap-user.sh",
            "lock-images.sh",
            "compose.sh",
            "install-egress-guard.sh",
            "install-monitor.sh",
            "backup.sh",
            "restore.sh",
            "upgrade.sh",
            "validate.sh",
            "rebuild-sandbox.sh",
            "sync-boards.sh",
            "gateway-preflight.sh",
            "verify-hermes-pin.sh",
            "verify-images.sh",
            "upgrade-hermes.sh",
        ):
            self.assertTrue((ROOT / "scripts" / name).is_file(), name)

    def test_host_preflight_is_narrow(self):
        install = read("scripts/install-host.sh")
        bootstrap = read("scripts/bootstrap-user.sh")
        for marker in ("Ubuntu versions are 22.04 and 24.04", "Supported Debian version is 12", "10 GiB RAM", "20 GiB free disk"):
            self.assertIn(marker, install)
        self.assertIn("ubuntu:22.04|ubuntu:24.04|debian:12", bootstrap)
        self.assertIn("CgroupVersion", bootstrap)
        self.assertIn('HERMES_HOME=$HOME/.hermes', bootstrap)

    def test_hermes_installer_is_release_and_checksum_pinned(self):
        installer = read("scripts/install-hermes.sh")
        self.assertIn("v2026.9.11", installer)
        self.assertIn("939e45c91d751fadd94dcd1b873ac3cb44846213", installer)
        self.assertRegex(installer, r"installer_sha256=[0-9a-f]{64}")
        self.assertIn("sha256sum --check --status", installer)
        self.assertIn("--force-commit", installer)
        self.assertIn("--no-skills", installer)
        self.assertIn("--non-interactive", installer)
        self.assertIn("--skip-browser", installer)
        self.assertIn('bash "$repo_root/scripts/install-browser.sh"', installer)

        browser = read("scripts/install-browser.sh")
        self.assertIn("agent_browser_version=0.26.0", browser)
        self.assertIn("playwright_version=1.62.1", browser)
        self.assertIn("--ignore-scripts", browser)
        self.assertIn('"$playwright_bin" install chromium', browser)
        self.assertIn('"$hermes_home/bin/chromium"', browser)
        self.assertNotIn("browser-use", browser)

    def test_hermes_upgrade_uses_locked_environment(self):
        upgrade = read("scripts/upgrade-hermes.sh")
        self.assertIn("uv sync --extra all --locked", upgrade)
        self.assertIn('bash "$repo_root/scripts/install-browser.sh"', upgrade)
        self.assertNotIn("uv pip install", upgrade)
        self.assertIn("merge-base --is-ancestor", upgrade)

    def test_backup_quiesces_both_writers(self):
        backup = read("scripts/backup.sh")
        dashboard_stop = backup.index("systemctl --user stop hermes-dashboard.service")
        gateway_stop = backup.index("systemctl --user stop hermes-gateway.service")
        self.assertLess(dashboard_stop, gateway_stop)
        self.assertIn("dashboard_was_active", backup)

    def test_gateway_has_fail_closed_preflight(self):
        unit = read("systemd/hermes-gateway.service.in")
        self.assertIn("ExecStartPre=@DEPLOY_DIR@/scripts/gateway-preflight.sh", unit)
        self.assertIn("ExecStart=@HERMES_BIN@ gateway run --replace", unit)
        preflight = read("scripts/gateway-preflight.sh")
        self.assertIn("TELEGRAM_ALLOWED_CHATS must equal the operator ID", preflight)
        self.assertIn("OPENAI_API_KEY is forbidden", preflight)

    def test_reviewed_tool_inventory_covers_profiles(self):
        inventory = __import__("json").loads(read("policy/tool-inventory.json"))
        self.assertEqual(PROFILE_NAMES, set(inventory))
        forbidden = {
            "execute_code",
            "delegate_task",
            "browser_exec",
            "computer_use",
            "send_message",
            "cronjob",
        }
        for name, tools in inventory.items():
            self.assertFalse(forbidden & set(tools), name)
            if name == "researcher":
                self.assertIn("browser_navigate", tools)
            else:
                self.assertFalse({tool for tool in tools if tool.startswith("browser_")}, name)
        self.assertIn("todo_list", inventory["default"])
        for name in WORKERS - {"web-monitor"}:
            self.assertIn("process_manage", inventory[name], name)
        self.assertNotIn("process", {tool for tools in inventory.values() for tool in tools})
        self.assertNotIn("todo", {tool for tools in inventory.values() for tool in tools})

        workers = __import__("json").loads(read("policy/kanban-worker-inventory.json"))
        self.assertEqual(WORKERS, set(workers))
        injected = {tool for tool in inventory["default"] if tool.startswith("kanban_")}
        for name in WORKERS:
            self.assertEqual(set(inventory[name]) | injected, set(workers[name]), name)

    def test_sandbox_base_and_dependency_inputs_are_locked(self):
        dockerfile = read("images/hermes-sandbox/Dockerfile")
        self.assertIn("ARG BASE_IMAGE", dockerfile)
        self.assertNotRegex(dockerfile, r"(?m)^ARG BASE_IMAGE=.+:")
        self.assertIn("ARG DEBIAN_SNAPSHOT=20260909T000000Z", dockerfile)
        self.assertIn("snapshot.debian.org", dockerfile)
        self.assertIn("--require-hashes", dockerfile)
        self.assertIn("npm ci --ignore-scripts", dockerfile)
        self.assertIn('git config --system user.name "Hermes Agent"', dockerfile)
        sources = read("infra/images.sources.env")
        self.assertIn("SANDBOX_BASE_IMAGE_SOURCE=", sources)
        self.assertIn("python3.11-nodejs22-bookworm", sources)

    def test_firecrawl_release_sources_are_explicit(self):
        sources = read("infra/images.sources.env")
        self.assertIn("FIRECRAWL_REQUIRED_RELEASE=v2.11.0", sources)
        self.assertIn("FIRECRAWL_REQUIRED_COMMIT=ef12eb36b2f3", sources)
        self.assertIn("FIRECRAWL_IMAGE_SOURCE=ghcr.io/firecrawl/firecrawl:sha-ef12eb36b2f3-linux-arm64", sources)

    def test_committed_image_lock_is_immutable(self):
        lock = read("infra/images.lock.env")
        assignments = [line for line in lock.splitlines() if line and not line.startswith("#")]
        self.assertEqual(8, len(assignments))
        for assignment in assignments:
            self.assertRegex(assignment, r"^[A-Z_]+=[^:@\s]+(?:/[^:@\s]+)+@sha256:[0-9a-f]{64}$")

    @unittest.skipUnless(BASH, "bash is not installed")
    def test_shell_syntax(self):
        scripts = sorted(str(path) for path in (ROOT / "scripts").glob("*.sh"))
        result = subprocess.run([BASH, "-n", *scripts], capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_no_committed_secret_values(self):
        secret_assignment = re.compile(
            r"(?mi)^(?:TELEGRAM_BOT_TOKEN|OPENROUTER_API_KEY|POSTGRES_PASSWORD|BULL_AUTH_KEY)=(.+)$"
        )
        for path in ROOT.rglob("*"):
            if not path.is_file() or ".git" in path.parts or path.name == "test_bundle.py":
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for match in secret_assignment.finditer(text):
                self.assertIn(match.group(1).strip().lower(), {"", "change-me", "change_me"}, str(path))


if __name__ == "__main__":
    unittest.main(verbosity=2)
