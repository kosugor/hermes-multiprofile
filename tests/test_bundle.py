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
    "web-scraper": {"web", "browser", "file", "terminal"},
    "web-monitor": {"web", "browser", "file"},
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

    def test_lcm_is_enabled_only_for_coder(self):
        for name in PROFILE_NAMES:
            config = read(f"profiles/{name}/config.yaml")
            if name == "coder":
                self.assertIn("plugins:\n  enabled:\n    - hermes-lcm", config)
                self.assertIn("context:\n  engine: lcm", config)
            else:
                self.assertNotIn("hermes-lcm", config, name)
                self.assertNotIn("engine: lcm", config, name)

    def test_qmd_is_read_only_and_limited_to_wiki_maintainer(self):
        wiki = read("profiles/wiki-maintainer/config.yaml")
        self.assertIn("mcp_servers:\n  qmd:", wiki)
        self.assertIn('command: "${userHome}/.hermes/qmd-runtime/node_modules/.bin/qmd"', wiki)
        self.assertIn("include: [query, get, multi_get, status]", wiki)
        self.assertIn("trust: untrusted", wiki)
        self.assertIn("resources: false", wiki)
        self.assertIn("prompts: false", wiki)
        for name in PROFILE_NAMES - {"wiki-maintainer"}:
            self.assertNotIn("mcp_servers:", read(f"profiles/{name}/config.yaml"), name)

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

    def test_browser_is_hardened_and_limited_to_approved_profiles(self):
        browser_profiles = {"researcher", "web-scraper", "web-monitor"}
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
        for name in browser_profiles:
            config = read(f"profiles/{name}/config.yaml")
            for setting in required:
                self.assertIn(setting, config, name)
            disabled = re.search(r"disabled_toolsets: \[([^]]*)\]", config)
            self.assertIsNotNone(disabled, name)
            self.assertNotIn("browser", set(re.findall(r"[a-z_]+", disabled.group(1))), name)

        for name in PROFILE_NAMES - browser_profiles:
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

    def test_qmd_indexer_is_local_and_resource_limited(self):
        service = read("systemd/hermes-qmd-index.service.in")
        timer = read("systemd/hermes-qmd-index.timer.in")
        gateway = read("systemd/hermes-gateway.service.in")
        bootstrap = read("scripts/bootstrap-user.sh")
        self.assertIn("QMD_CONFIG_DIR=%h/.hermes/profiles/wiki-maintainer/qmd", service)
        self.assertIn("QMD_FORCE_CPU=1", service)
        self.assertIn("TimeoutStartSec=65min", service)
        self.assertIn("CPUQuota=100%", service)
        self.assertIn("MemoryMax=3G", service)
        self.assertIn("ReadOnlyPaths=/srv/hermes/wiki", service)
        self.assertIn("OnUnitInactiveSec=15min", timer)
        self.assertIn("%h/.cache/qmd", gateway)
        self.assertIn("hermes-qmd-index.timer", bootstrap)

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
            "install-lcm.sh",
            "install-qmd.sh",
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
            "verify-lcm-pin.sh",
            "verify-qmd-pin.sh",
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

        lcm = read("scripts/install-lcm.sh")
        self.assertIn("v1.0.0-rc.1", lcm)
        self.assertIn("8d1b1e6d3d63f5fc7b209e8d7ec1dc9b814f2e54", lcm)
        self.assertIn('"$repo_root/scripts/verify-lcm-pin.sh"', lcm)
        self.assertIn('"$repo_root/scripts/install-lcm.sh"', read("scripts/bootstrap-user.sh"))
        self.assertIn('"$repo_root/scripts/verify-lcm-pin.sh"', read("scripts/validate.sh"))
        self.assertIn('"$repo_root/scripts/verify-lcm-pin.sh"', read("scripts/gateway-preflight.sh"))

        qmd_install = read("scripts/install-qmd.sh")
        self.assertIn("qmd_version=2.8.3", qmd_install)
        self.assertIn('"$managed_node/npm" ci --omit=dev', qmd_install)
        self.assertIn('"$qmd_bin" pull', qmd_install)
        self.assertIn('"$qmd_bin" embed --timeout 60', qmd_install)
        self.assertIn('"$repo_root/scripts/install-qmd.sh"', read("scripts/bootstrap-user.sh"))
        self.assertIn('"$repo_root/scripts/verify-qmd-pin.sh"', read("scripts/validate.sh"))
        self.assertIn('"$repo_root/scripts/verify-qmd-pin.sh"', read("scripts/gateway-preflight.sh"))
        qmd_verify = read("scripts/verify-qmd-pin.sh")
        for model_sha256 in (
            "b5ce9d77a3fc4b3b39ccb5643c36777911cc4eb46a66962eadfa3f5f60490d63",
            "22c9979ce4fbcdc5acdc310c6641c32797eff1aa980b8f7a2db8a8ea23429a48",
            "000dfb1c06efa6a049e9f64ba921c3740e2454f62abab6fa10e77bd30bb2bcc0",
        ):
            self.assertIn(model_sha256, qmd_verify)

        qmd_package = __import__("json").loads(read("qmd/package.json"))
        qmd_lock = __import__("json").loads(read("qmd/package-lock.json"))
        self.assertEqual("2.8.3", qmd_package["dependencies"]["@tobilu/qmd"])
        locked_qmd = qmd_lock["packages"]["node_modules/@tobilu/qmd"]
        self.assertEqual("2.8.3", locked_qmd["version"])
        self.assertEqual(
            "sha512-zjfVwrObPB618B6x8SdhlGv/tX9OxRHsbQnr5DUtBvqPK6HGQ27lM+9/BAY5okpjrHVnW56hLyDkqoTcsrVLzA==",
            locked_qmd["integrity"],
        )
        for path, package in qmd_lock["packages"].items():
            if path and package.get("resolved"):
                self.assertIn("integrity", package, path)

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
            if name in {"researcher", "web-scraper", "web-monitor"}:
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

        lcm_tools = {
            "lcm_compile_evidence", "lcm_compute", "lcm_describe", "lcm_doctor",
            "lcm_evidence_pack", "lcm_expand", "lcm_expand_query", "lcm_grep",
            "lcm_inspect", "lcm_load_session", "lcm_query_state", "lcm_recall",
            "lcm_recent", "lcm_retrieve", "lcm_status",
        }
        self.assertTrue(lcm_tools <= set(inventory["coder"]))
        audit = read("scripts/audit-tools.py")
        for tool in lcm_tools:
            self.assertIn(f'"{tool}"', audit)
        for name in PROFILE_NAMES - {"coder"}:
            self.assertFalse(lcm_tools & set(inventory[name]), name)

        qmd_tools = {
            "mcp__qmd__query", "mcp__qmd__get",
            "mcp__qmd__multi_get", "mcp__qmd__status",
        }
        self.assertTrue(qmd_tools <= set(inventory["wiki-maintainer"]))
        for name in PROFILE_NAMES - {"wiki-maintainer"}:
            self.assertFalse(qmd_tools & set(inventory[name]), name)

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
