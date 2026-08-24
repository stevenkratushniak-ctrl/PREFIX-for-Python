from __future__ import annotations

import argparse
import json
import os
import platform
import signal
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "qualification" / "vscode_harness"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run PREFIX in a real VS Code extension host twice.")
    parser.add_argument("--code", required=True, type=Path, help="Code.exe on Windows or the code launcher on Linux.")
    parser.add_argument("--user-data-dir", required=True, type=Path)
    parser.add_argument("--extensions-dir", required=True, type=Path)
    parser.add_argument("--timeout-engine", required=True, type=Path, help="External CPython executable used with the timeout fixture.")
    parser.add_argument("--wrong-engine", required=True, type=Path, help="Executable that cannot speak the PREFIX engine protocol.")
    parser.add_argument("--xvfb-run", type=Path, help="Linux xvfb-run path for headless qualification.")
    parser.add_argument("--dbus-run-session", type=Path, help="Linux dbus-run-session path for an isolated desktop bus.")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    args.user_data_dir.mkdir(parents=True, exist_ok=True)
    args.extensions_dir.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment["PREFIX_TIMEOUT_ENGINE"] = str(args.timeout_engine.resolve())
    environment["PREFIX_WRONG_ENGINE"] = str(args.wrong_engine.resolve())
    environment["PYTHONPATH"] = str(HARNESS / "timeout_module")
    environment["VSCODE_DISABLE_UPDATE"] = "1"
    host_workdir = args.user_data_dir / "host-workdir"
    host_workdir.mkdir(parents=True, exist_ok=True)
    if args.xvfb_run:
        environment["GDK_BACKEND"] = "x11"
        environment["GTK_USE_PORTAL"] = "0"
        environment["NO_AT_BRIDGE"] = "1"
        environment["XDG_SESSION_TYPE"] = "x11"
        environment.pop("WAYLAND_DISPLAY", None)
        if args.dbus_run_session:
            environment.pop("DBUS_SESSION_BUS_ADDRESS", None)
        else:
            environment["DBUS_SESSION_BUS_ADDRESS"] = "unix:path=/dev/null"

    base = [
        str(args.code.resolve()),
        f"--extensionDevelopmentPath={HARNESS}",
        f"--extensionTestsPath={HARNESS / 'suite' / 'index.js'}",
        f"--user-data-dir={args.user_data_dir.resolve()}",
        f"--extensions-dir={args.extensions_dir.resolve()}",
        "--disable-updates",
        "--skip-welcome",
        "--skip-release-notes",
        "--disable-workspace-trust",
        "--disable-extension=github.copilot",
        "--disable-extension=github.copilot-chat",
        "--no-sandbox",
    ]
    if args.xvfb_run:
        base.extend([
            "--verbose",
            "--disable-dev-shm-usage",
            "--ozone-platform=x11",
            "--disable-features=GlobalShortcutsPortal",
            "--password-store=basic",
            "--use-gl=swiftshader",
        ])
    prefix = [str(args.xvfb_run.resolve()), "-a"] if args.xvfb_run else []
    if args.dbus_run_session:
        prefix.extend([str(args.dbus_run_session.resolve()), "--"])
    command = prefix + base
    runs = []
    for run_number in (1, 2):
        completed = _run_host(command, environment, host_workdir)
        combined = completed["stdout"] + completed["stderr"]
        passed = completed["exit_code"] == 0 and not completed["timed_out"] and "PREFIX_VSCODE_HOST_PROOF_OK" in combined
        runs.append({
            "run": run_number,
            "exit_code": completed["exit_code"],
            "timed_out": completed["timed_out"],
            "passed": passed,
            "stdout_tail": completed["stdout"][-6000:],
            "stderr_tail": completed["stderr"][-6000:],
        })
        if not passed:
            break

    report = {
        "schema": "prefix-vscode-host-proof.v1",
        "platform": platform.system().lower(),
        "machine": platform.machine().lower(),
        "code": str(args.code.resolve()),
        "runs": runs,
        "passed": len(runs) == 2 and all(run["passed"] for run in runs),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "passed": report["passed"], "runs": len(runs)}, sort_keys=True))
    return 0 if report["passed"] else 1


def _run_host(command: list[str], environment: dict[str, str], cwd: Path) -> dict[str, object]:
    process = subprocess.Popen(
        command,
        cwd=cwd,
        env=environment,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=os.name != "nt",
    )
    try:
        stdout, stderr = process.communicate(timeout=240)
        return {"exit_code": process.returncode, "stdout": stdout, "stderr": stderr, "timed_out": False}
    except subprocess.TimeoutExpired:
        if os.name == "nt":
            process.kill()
        else:
            os.killpg(process.pid, signal.SIGKILL)
        stdout, stderr = process.communicate()
        stderr += "\nPREFIX host qualification exceeded its 240-second deadline.\n"
        return {"exit_code": 124, "stdout": stdout, "stderr": stderr, "timed_out": True}


if __name__ == "__main__":
    raise SystemExit(main())
