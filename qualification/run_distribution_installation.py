"""Test exact wheel entry points and retained installers in disposable locations."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import venv
import zipfile
from pathlib import Path

from run_distribution_vscode import get_code

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'if ready\nprint("launch")\n'


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    artifacts, out = args.artifacts.resolve(), args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    report = {"schema": "prefix-distribution-installation.v1", "platform": sys.platform,
              "synthetic_entitlement_only": True, "production_activation_verified": False,
              "purchase_performed": False, "checks": [], "steps": []}
    env = os.environ.copy()
    for name in ["PYTHONPATH", "PYTHONHOME", "ELECTRON_RUN_AS_NODE"]:
        env.pop(name, None)
    env["PREFIX_ENTITLEMENT_ROOT"] = str(out / "wheel-entitlement")

    def check(name, condition):
        report["checks"].append({"name": name, "passed": bool(condition)})
        if not condition:
            raise AssertionError(name)

    def run(command, *, input_text=None, expected=0, environment=env):
        result = subprocess.run([str(x) for x in command], cwd=out, env=environment,
                                input=input_text, text=True, encoding="utf-8", errors="replace",
                                capture_output=True, timeout=240)
        report["steps"].append({"command": [str(x) for x in command], "exit_code": result.returncode,
                                "stdout": result.stdout, "stderr": result.stderr})
        if result.returncode != expected:
            raise AssertionError(f"unexpected exit {result.returncode}, expected {expected}")
        return result.stdout

    def evaluate(command, *, expected, environment=env):
        return json.loads(run([*command, "--stdin", "--json"], input_text=SOURCE,
                              expected=expected, environment=environment))

    def fixture(python, environment=env):
        run([python, ROOT / "qualification/vscode_harness/entitlement_fixture.py", "active"],
            environment=environment)

    try:
        manifest = json.loads((artifacts / "DISTRIBUTION_MANIFEST.json").read_text())
        report["source"] = manifest["source"]
        report["artifacts"] = manifest["artifacts"]
        for item in manifest["artifacts"]:
            actual = hashlib.sha256((artifacts / item["name"]).read_bytes()).hexdigest()
            check("artifact custody: " + item["name"], actual == item["sha256"])
        wheel = artifacts / "prefix_python-0.1.0-py3-none-any.whl"
        virtual = out / "wheel-install"
        venv.create(virtual, with_pip=True)
        scripts = virtual / ("Scripts" if os.name == "nt" else "bin")
        python = scripts / ("python.exe" if os.name == "nt" else "python")
        cli = scripts / ("prefix-python.exe" if os.name == "nt" else "prefix-python")
        ops = scripts / ("prefix-python-ops.exe" if os.name == "nt" else "prefix-python-ops")
        run([python, "-m", "pip", "install", "--no-index", "--no-deps", wheel])
        check("installed console version", "0.1.0" in run([cli, "--version"]))
        denied = evaluate([cli], expected=3)
        check("installed console unactivated refusal", denied.get("refusal_code") == "entitlement_required"
              and denied.get("mutation_performed") is False and denied.get("source") == SOURCE)
        check("denied source binding", denied.get("input_sha256") == hashlib.sha256(SOURCE.encode()).hexdigest()
              and denied.get("output_sha256") == denied.get("input_sha256"))
        check("installed operator entry point gate", "entitlement_required" in run([ops, "--json"], expected=3))
        fixture(python)
        accepted = evaluate([cli], expected=0)
        check("installed console synthetic entitlement correction", accepted.get("status") == "ACCEPT_FIXED"
              and "if ready:" in accepted.get("source", ""))
        code = get_code(out / "host")
        report["code"] = {"path": str(code), "sha256": hashlib.sha256(code.read_bytes()).hexdigest(),
                          "source": "https://update.code.visualstudio.com/1.85.2/"}
        installer_env = env.copy()
        installer_env["PREFIX_ENTITLEMENT_ROOT"] = str(out / "installer-entitlement")
        install_root = out / "installed-product"
        installer_env["PREFIX_INSTALL_ROOT"] = str(install_root)
        installer_env["PREFIX_VSCODE_USER_DATA_DIR"] = str(out / "installer-code-user")
        installer_env["PREFIX_VSCODE_EXTENSIONS_DIR"] = str(out / "installer-code-extensions")
        # Only the freshly created child of this proof root can be uninstalled.
        check("disposable install custody", install_root.is_relative_to(out) and not install_root.exists())
        unpack = out / "package"
        unpack.mkdir()
        if os.name == "nt":
            installer_env["LOCALAPPDATA"] = str(out / "installer-localappdata")
            installer_env["APPDATA"] = str(out / "installer-appdata")
            with zipfile.ZipFile(artifacts / "prefix-python-0.1.0-windows-x64.zip") as archive:
                for name in archive.namelist():
                    if not (unpack / name).resolve().is_relative_to(unpack):
                        raise RuntimeError("package path escaped proof root")
                archive.extractall(unpack)
            package = unpack / "prefix-python-0.1.0-windows-x64"
            code_cli = code.parent / "bin/code.cmd"
            pwsh = shutil.which("pwsh") or "powershell.exe"
            run([pwsh, "-NoProfile", "-File", package / "Install-PREFIX-for-Python.ps1",
                 "-InstallRoot", install_root, "-CodeCli", code_cli], environment=installer_env)
            installed_python = install_root / "runtime/python.exe"
            installed_command = [installed_python, "-m", "prefix_python"]
            uninstall = [pwsh, "-NoProfile", "-File", package / "Uninstall-PREFIX-for-Python.ps1",
                         "-InstallRoot", install_root, "-CodeCli", code_cli]
        else:
            installer_env["HOME"] = str(out / "installer-home")
            installer_env["XDG_DATA_HOME"] = str(out / "installer-data")
            installer_env["PREFIX_BIN_ROOT"] = str(out / "installer-bin")
            installer_env["PREFIX_PYTHON_RUNTIME"] = sys.executable
            installer_env["PATH"] = str(code.parent / "bin") + os.pathsep + installer_env["PATH"]
            with tarfile.open(artifacts / "prefix-python-0.1.0-linux-amd64.tar.gz") as archive:
                archive.extractall(unpack, filter="data")
            package = unpack / "prefix-python-0.1.0-linux-amd64"
            run([package / "install-prefix-python.sh"], environment=installer_env)
            installed_python = install_root / "runtime/prefix-python-python"
            installed_command = [out / "installer-bin/prefix-python"]
            uninstall = [package / "uninstall-prefix-python.sh"]
        install_manifest = json.loads((install_root / "install-manifest.json").read_text(encoding="utf-8-sig"))
        report["install_manifest"] = install_manifest
        check("unactivated installer records expected refusal", install_manifest["smoke_status"] == "REFUSE_INVALID")
        check("installed product version", "0.1.0" in run([*installed_command, "--version"], environment=installer_env))
        denied = evaluate(installed_command, expected=3, environment=installer_env)
        check("installed product blocks before activation", denied.get("refusal_code") == "entitlement_required"
              and denied.get("source") == SOURCE and denied.get("mutation_performed") is False)
        fixture(installed_python, installer_env)
        corrected = evaluate(installed_command, expected=0, environment=installer_env)
        check("installed product synthetic entitlement correction", corrected.get("status") == "ACCEPT_FIXED")
        run(uninstall, environment=installer_env)
        check("uninstall removed disposable product", not install_root.exists())
        report["passed"] = True
    except Exception as error:
        report["passed"] = False
        report["error"] = f"{type(error).__name__}: {error}"
    report["counts"] = {"checks": len(report["checks"]),
                        "passed": sum(item["passed"] for item in report["checks"]),
                        "failed": sum(not item["passed"] for item in report["checks"])}
    (out / "installation-result.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": report["passed"], "counts": report["counts"], "error": report.get("error")}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
