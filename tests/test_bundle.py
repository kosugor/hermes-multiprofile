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
    "orchestrator",
    "researcher",
    "coder",
    "reviewer",
    "wiki-maintainer",
    "web-scraper",
    "web-monitor",
}
WORKERS = PROFILE_NAMES - {"orchestrator"}
EXPECTED_TOOLSETS = {
    "orchestrator": {"kanban", "clarify", "todo", "memory", "session_search"},
    "researcher": {"web", "browser", "file", "terminal", "memory", "session_search"},
    "coder": {"file", "terminal", "memory"},
    "reviewer": {"file", "terminal", "web"},
    "wiki-maintainer": {"file", "terminal", "memory"},
    "web-scraper": {"web", "browser", "file", "terminal"},
    "web-monitor": {"web", "browser", "file", "terminal", "cronjob"},
}


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def platform_toolsets(config: str, platform: str) -> set[str]:
    match = re.search(rf"(?m)^  {re.escape(platform)}: \[([^]]*)\]$", config)
    if not match:
        raise AssertionError(f"missing explicit platform_toolsets.{platform} allowlist")
    return {item.strip() for item in match.group(1).split(",") if item.strip()}


class BundleTests(unittest.TestCase):

    def test_bootstrap_opts_every_profile_out_of_bundled_skills(self):
        bootstrap = read("scripts/bootstrap-user.sh")
        self.assertNotIn("hermes skills opt-out", bootstrap)
        self.assertIn('--no-alias --no-skills', bootstrap)
        self.assertIn('hermes -p "$profile" skills opt-out', bootstrap)


    def test_bootstrap_does_not_touch_builtin_default_profile(self):
        bootstrap = read("scripts/bootstrap-user.sh")
        self.assertNotIn('"$hermes_home/profiles/default"', bootstrap)
        self.assertNotIn('hermes -p default', bootstrap)
        self.assertIn('expected_profiles=(orchestrator ', bootstrap)
        self.assertIn('local destination="$hermes_home/profiles/$name"', bootstrap)
        self.assertNotIn('destination=$hermes_home', bootstrap)

        bootstrap = read("scripts/bootstrap-user.sh")
        gateway_dropin = read("systemd/hermes-gateway-orchestrator.service.d/override.conf.in")
        dashboard = read("systemd/hermes-dashboard.service.in")
        self.assertIn("gateway install --force --no-start-now", bootstrap)
        self.assertIn("gateway_service=hermes-gateway.service", bootstrap)
        self.assertIn("hermes-gateway-orchestrator.service", bootstrap)
        self.assertIn("gateway-preflight.sh", gateway_dropin)
        self.assertIn("Wants=hermes-dashboard.service", gateway_dropin)
        self.assertIn("ExecStart=@HERMES_BIN@ -p orchestrator dashboard", dashboard)

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
                self.assertIn("context:\n  engine: compressor", config, name)

    def test_langfuse_profile_activation_and_metadata_capture(self):
        for name in PROFILE_NAMES:
            config = read(f"profiles/{name}/config.yaml")
            env = read(f"profiles/{name}/.env.example")
            if name in {"wiki-maintainer", "web-scraper"}:
                self.assertNotIn("observability/langfuse", config, name)
                self.assertNotIn("HERMES_LANGFUSE_", env, name)
            else:
                self.assertIn("observability/langfuse", config, name)
                self.assertIn("HERMES_LANGFUSE_PUBLIC_KEY=", env, name)
                self.assertIn("HERMES_LANGFUSE_SECRET_KEY=", env, name)
                self.assertIn("HERMES_LANGFUSE_CAPTURE=metadata", env, name)
                self.assertIn("HERMES_LANGFUSE_RELEASE=v2026.9.11", env, name)
                self.assertIn(f"HERMES_LANGFUSE_ENV=production-{name}", env, name)

    def test_qmd_trust_is_profile_scoped_and_tool_limited(self):
        wiki = read("profiles/wiki-maintainer/config.yaml")
        self.assertIn("mcp_servers:\n  qmd:", wiki)
        self.assertIn('command: "${userHome}/.hermes/qmd-runtime/node_modules/.bin/qmd"', wiki)
        self.assertIn("include: [query, get, multi_get, status]", wiki)
        self.assertIn("trust: full", wiki)
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
        }
        for name in PROFILE_NAMES:
            config = read(f"profiles/{name}/config.yaml")
            disabled_match = re.search(r"disabled_toolsets:\s*(?:\[([^]]*)\]|\n((?:    - .+\n)+))", config)
            self.assertIsNotNone(disabled_match, name)
            disabled_text = " ".join(group or "" for group in disabled_match.groups())
            self.assertTrue(forbidden <= set(re.findall(r"[a-z_]+", disabled_text)), name)
            if name == "web-monitor":
                self.assertNotIn("cronjob", set(re.findall(r"[a-z_]+", disabled_text)))
                self.assertIn("allow_agent_scheduling: true", config)
            else:
                self.assertIn("cronjob", set(re.findall(r"[a-z_]+", disabled_text)), name)

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

    def test_worker_sandboxes_are_networkless_and_not_reused_across_processes(self):
        required = (
            "backend: docker",
            "lifetime_seconds: 600",
            "docker_mount_cwd_to_workspace: true",
            "docker_run_as_host_user: false",
            "docker_forward_env: []",
            "docker_network: false",
            'docker_extra_args: ["--pids-limit", "256"]',
            "container_cpu: 1",
            "container_memory: 1536",
            "docker_persist_across_processes: false",
        )
        for name in WORKERS:
            config = read(f"profiles/{name}/config.yaml")
            for line in required:
                self.assertIn(line, config, f"{name}: {line}")
            expected_persistence = "true" if name in {"coder", "reviewer", "web-scraper", "wiki-maintainer", "web-monitor"} else "false"
            self.assertIn(f"container_persistent: {expected_persistence}", config, name)
            if name in {"wiki-maintainer", "web-monitor"}:
                expected_cwd = "/srv/hermes/wiki" if name == "wiki-maintainer" else "/srv/hermes/monitor"
                self.assertIn(f"  cwd: {expected_cwd}", config, name)
            else:
                self.assertNotRegex(config, r"(?m)^\s+cwd:")
            self.assertNotIn("docker.sock", config)
            self.assertNotIn("docker_volumes:", config)

    def test_orchestrator_is_only_profile_with_telegram_secret(self):
        orchestrator_env = read("profiles/orchestrator/.env.example")
        self.assertIn("TELEGRAM_BOT_TOKEN=", orchestrator_env)
        self.assertIn("TELEGRAM_ALLOWED_CHATS=", orchestrator_env)
        self.assertIn("GATEWAY_ALLOW_ALL_USERS=false", orchestrator_env)
        for name in WORKERS:
            self.assertNotIn("TELEGRAM_", read(f"profiles/{name}/.env.example"), name)
        self.assertIn("AGENT_BROWSER_EXECUTABLE_PATH=", read("profiles/researcher/.env.example"))
        self.assertIn("AGENT_BROWSER_EXECUTABLE_PATH=", read("profiles/web-scraper/.env.example"))
        self.assertIn("AGENT_BROWSER_EXECUTABLE_PATH=", read("profiles/web-monitor/.env.example"))
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
                self.assertNotIn("fallback_model:", config)

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
        self.assertEqual(5, compose.count("profiles: [extraction]"))
        compose_script = read("scripts/compose.sh")
        self.assertIn("core-up)", compose_script)
        self.assertIn("extraction-up)", compose_script)
        self.assertIn("extraction-stop)", compose_script)

    def test_dashboard_uses_configurable_tailscale_host_and_web_ports_stay_loopback(self):
        dashboard = read("systemd/hermes-dashboard.service.in")
        self.assertIn("EnvironmentFile=-%h/.config/hermes/dashboard.env", dashboard)
        self.assertIn("--host ${HERMES_DASHBOARD_HOST} --port 9119", dashboard)
        compose = read("infra/compose.yaml")
        self.assertNotIn('"0.0.0.0:8888:', compose)
        self.assertNotIn('"0.0.0.0:3002:', compose)

    def test_qmd_indexer_is_local_and_resource_limited(self):
        service = read("systemd/hermes-qmd-index.service.in")
        timer = read("systemd/hermes-qmd-index.timer.in")
        bootstrap = read("scripts/bootstrap-user.sh")
        self.assertIn("QMD_CONFIG_DIR=%h/.hermes/profiles/wiki-maintainer/qmd", service)
        self.assertIn("QMD_FORCE_CPU=1", service)
        self.assertIn("TimeoutStartSec=15min", service)
        self.assertIn("CPUQuota=25%", service)
        self.assertIn("MemoryMax=1G", service)
        self.assertIn("ReadOnlyPaths=/srv/hermes/wiki", service)
        self.assertIn("OnUnitInactiveSec=15min", timer)
        embed_service = read("systemd/hermes-qmd-embed.service.in")
        embed_timer = read("systemd/hermes-qmd-embed.timer.in")
        self.assertIn('qmd embed --timeout 60', embed_service)
        self.assertIn("CPUQuota=50%", embed_service)
        self.assertIn("MemoryMax=3G", embed_service)
        self.assertIn("OnCalendar=*-*-* 02:30:00", embed_timer)
        self.assertIn("hermes-qmd-index.timer", bootstrap)
        self.assertIn("hermes-qmd-embed.timer", bootstrap)

    def test_monitor_installs_paused_with_orchestrator_delivery(self):
        script = read("scripts/install-monitor.sh")
        self.assertIn("--paused", script)
        self.assertIn("--deliver bot-chat:orchestrator", script)
        self.assertNotIn(" cron resume ", script)
        self.assertIn("MONITOR_SCHEMA", script)
        self.assertIn("Set MONITOR_SELECTOR, MONITOR_SCHEMA, or both.", script)
        self.assertIn('monitor_root=/srv/hermes/monitor', script)
        self.assertIn('--workdir "$monitor_root"', script)
        self.assertIn('/workspace/.hermes-monitor-workspace', script)
        self.assertNotIn('--continuity', script)
        self.assertIn('/srv/hermes/monitor', read("scripts/install-host.sh"))
        self.assertIn('/srv/hermes/monitor/monitoring', read("scripts/install-host.sh"))
        self.assertIn('/srv/hermes/monitor/.hermes-monitor-workspace', read("scripts/bootstrap-user.sh"))
        self.assertIn('/srv/hermes/monitor "$stage/srv/hermes/monitor"', read("scripts/backup.sh"))

    def test_wiki_triage_installer_is_paused_and_scoped(self):
        script = read("scripts/install-wiki-triage.sh")
        wiki_config = read("profiles/wiki-maintainer/config.yaml")
        self.assertIn("timezone: Europe/Belgrade", wiki_config)
        self.assertIn("  cwd: /srv/hermes/wiki", wiki_config)
        self.assertIn("    timeout: 300", wiki_config)
        self.assertIn("every day at 03:30", script)
        self.assertNotIn("every 1d at 03:30", script)
        self.assertIn("wiki-clipping-triage", script)
        self.assertIn("--skill scheduled-wiki-maintenance", script)
        self.assertIn("--workdir \"$wiki_root\"", script)
        self.assertIn("--deliver bot-chat:orchestrator", script)
        self.assertIn("--provider openai-codex", script)
        self.assertIn("--model gpt-5.6-terra", script)
        self.assertIn("--paused", script)
        self.assertIn("investments", script)
        self.assertIn("software-development", script)
        self.assertIn("WIKI_TRIAGE_TIMEZONE", script)
        self.assertIn('grep -Fxq "  cwd: $wiki_root"', script)
        self.assertIn("WIKI_TRIAGE_UPDATE_EXISTING", script)
        self.assertIn("Review legacy plain Markdown clippings", script)
        self.assertIn("Do not require a separate", script)


    def test_capture_validator_requires_provenance_hash_contract(self):
        validator = read("profiles/web-scraper/skills/web-clipper/scripts/validate-capture.py")
        for field in ("supplied_url", "canonical_url", "published_at", "retrieved_at", "capture_status", "capture_method", "provider", "model", "content_sha256"):
            self.assertIn(field, validator)
        self.assertIn("does not match the exact Markdown body bytes", validator)
        self.assertIn('"deferred"', validator)
        self.assertIn('"--root"', validator)

    def test_yaml_validator_dependency_is_pinned_and_smoke_checked(self):
        requirements = read("images/hermes-sandbox/dependencies/python-requirements.lock")
        self.assertIn("PyYAML==6.0.3", requirements)
        self.assertIn("--hash=sha256:", requirements)
        self.assertIn('import yaml; print(yaml.__version__)', read("scripts/rebuild-sandbox.sh"))


    def test_archive_audits_support_topic_wikis_and_inbox(self):
        audit = read("profiles/wiki-maintainer/skills/audit-vault-links/scripts/wiki-audit.py")
        for wiki in ("investments", "devops", "software-development", "ai"):
            self.assertIn(f'"{wiki}"', audit)
        self.assertIn("body_of", audit)
        validator = read("profiles/wiki-maintainer/skills/audit-vault-links/scripts/validate-vault.py")
        self.assertIn('"inbox/clippings/"', validator)

    def test_board_sync_uses_pinned_cli_and_accepts_list_json(self):
        script = read("scripts/sync-boards.sh")
        self.assertIn("hermes -p orchestrator kanban init", script)
        self.assertIn("hermes -p orchestrator kanban boards list --json", script)
        self.assertIn("hermes -p orchestrator kanban boards create", script)
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
            "install-wiki-triage.sh",
            "wiki-writer-lock.py",
            "backup.sh",
            "restore.sh",
            "upgrade.sh",
            "validate.sh",
            "rebuild-sandbox.sh",
            "sync-boards.sh",
            "gateway-preflight.sh",
            "verify-lcm-pin.sh",
            "verify-qmd-pin.sh",
            "verify-langfuse-pin.sh",
            "install-langfuse.sh",
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
        self.assertIn('expected_home=$(getent passwd "$(id -un)"', bootstrap)
        self.assertIn('XDG_RUNTIME_DIR="$user_runtime_dir"', bootstrap)
        self.assertIn('DBUS_SESSION_BUS_ADDRESS="unix:path=$user_runtime_dir/bus"', bootstrap)
        self.assertIn("systemctl --user show-environment", bootstrap)
        self.assertIn("Log in directly", bootstrap)
        self.assertIn("Hermes deployment: systemd user bus", bootstrap)
        self.assertIn('export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"', bootstrap)



    def test_hermes_upgrade_delegates_to_unpinned_installer(self):
        upgrade = read("scripts/upgrade-hermes.sh")
        self.assertIn('exec "$repo_root/scripts/install-hermes.sh"', upgrade)
        self.assertNotIn("--tag", upgrade)
        self.assertNotIn("APPROVED_HERMES", upgrade)


    def test_backup_quiesces_both_writers(self):
        backup = read("scripts/backup.sh")
        dashboard_stop = backup.index("systemctl --user stop hermes-dashboard.service")
        gateway_stop = backup.index('systemctl --user stop "$gateway_service"')
        self.assertLess(dashboard_stop, gateway_stop)
        self.assertIn("dashboard_was_active", backup)
        self.assertIn('/srv/hermes/artifacts "$stage/srv/hermes/artifacts"', backup)
        self.assertIn("required_kib=$((source_kib * 2))", backup)
        self.assertIn("excluded_rebuildable=hermes-agent,node,qmd-runtime,bin", backup)

    def test_wiki_writer_lock_is_shared_and_installed(self):
        helper = read("scripts/wiki-writer-lock.py")
        for operation in ("acquire", "inspect", "release", "compare_digest"):
            self.assertIn(operation, helper)
        for script in ("scripts/bootstrap-user.sh", "scripts/install-wiki-triage.sh"):
            contents = read(script)
            self.assertIn("wiki-writer-lock.py", contents)
            self.assertIn("Refusing to replace a non-directory wiki writer lock", contents)
            self.assertIn("/.hermes-maintenance/", contents)
        for profile_path in (
            "profiles/web-scraper/skills/web-clipper/SKILL.md",
            "profiles/wiki-maintainer/skills/maintain-obsidian-wiki/SKILL.md",
            "profiles/wiki-maintainer/skills/scheduled-wiki-maintenance/SKILL.md",
        ):
            self.assertIn("wiki-writer-lock.py", read(profile_path))


    def test_gateway_has_fail_closed_preflight(self):
        bootstrap = read("scripts/bootstrap-user.sh")
        dropin = read("systemd/hermes-gateway-orchestrator.service.d/override.conf.in")
        self.assertIn('gateway install --force --no-start-now', bootstrap)
        self.assertIn('hermes-gateway-orchestrator.service.d', bootstrap)
        self.assertIn("gateway-preflight.sh", dropin)
        preflight = read("scripts/gateway-preflight.sh")
        self.assertIn("TELEGRAM_ALLOWED_CHATS must equal the operator ID", preflight)
        self.assertIn("OPENAI_API_KEY is forbidden", preflight)
        self.assertIn("requires top-level toolsets: [kanban]", preflight)


    def test_sandbox_base_and_dependency_inputs_are_locked(self):
        dockerfile = read("images/hermes-sandbox/Dockerfile")
        self.assertIn("# check=skip=InvalidDefaultArgInFrom", dockerfile)
        self.assertIn("BASE_IMAGE is intentionally required", dockerfile)
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
        for script in scripts:
            result = subprocess.run([BASH, "-n", script], capture_output=True, text=True)
            self.assertEqual(0, result.returncode, f"{script}: {result.stderr}")

    def test_validation_audits_installed_profiles_and_core_web_mode(self):
        validate = read("scripts/validate.sh")
        self.assertIn('--profiles-root "$hermes_home/profiles"', validate)
        self.assertIn('hermes_checkout=${HERMES_CHECKOUT:-$hermes_home/hermes-agent}', validate)
        self.assertIn('"$hermes_checkout/venv/bin/python"', validate)
        self.assertIn('"$hermes_checkout/.venv/bin/python"', validate)
        self.assertIn("--core-web", validate)
        self.assertIn("QMD embed timer is active", validate)
        self.assertIn('"$repo_root/scripts/verify-langfuse-pin.sh"', validate)
        self.assertIn("HERMES_LANGFUSE_CAPTURE", validate)
        self.assertIn("production-$profile", validate)
        self.assertIn("firecrawl_denied_private_target", validate)
        self.assertIn(".data.metadata.statusCode == 403", validate)
        self.assertIn('test("blocked|private/internal|security rules"; "i")', validate)
        self.assertIn("Web Scraper workspace-mount compatibility settings", validate)
        self.assertIn("container_persistent: true", validate)
        self.assertIn("docker_persist_across_processes: false", validate)
        gateway = read("scripts/gateway-preflight.sh")
        self.assertIn('"$repo_root/scripts/verify-langfuse-pin.sh"', gateway)
        self.assertIn('hermes -p "$profile" config check', gateway)
        self.assertNotIn('--user "$(id -u):$(id -g)" --read-only', validate)

    def test_langfuse_lock_is_hash_pinned(self):
        lock = read("langfuse/requirements.txt")
        self.assertRegex(lock, r"(?m)^langfuse==4\.14\.1 \\\n")
        self.assertRegex(lock, r"(?m)^    --hash=sha256:[0-9a-f]{64}$")
        self.assertIn("langfuse==4.14.1", read("langfuse/requirements.in"))



if __name__ == "__main__":
    unittest.main(verbosity=2)
