"""Install the final VSIX and exact candidate wheel in a disposable real Code host.
No publisher login, Marketplace upload, live purchase or live license activation occurs.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, io, json, os, platform, re, shutil, subprocess, sys, tarfile, urllib.request, venv, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RUNTIME_URL="https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip"
RUNTIME_SHA="4acbed6dd1c744b0376e3b1cf57ce906f9dc9e95e68824584c8099a63025a3c3"
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def execute(command,env,cwd,timeout=240):
    rendered=[str(x) for x in command]
    try:
        done=subprocess.run(rendered,env=env,cwd=cwd,text=True,encoding="utf-8",errors="replace",stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
        return {"command":rendered,"exit_code":done.returncode,"stdout":done.stdout,"stderr":done.stderr,"timed_out":False}
    except subprocess.TimeoutExpired as error:
        def decode(value): return value.decode("utf-8",errors="replace") if isinstance(value,bytes) else value or ""
        return {"command":rendered,"exit_code":124,"stdout":decode(error.stdout),"stderr":decode(error.stderr),"timed_out":True,"timeout_seconds":timeout}
def acquire(url,target):
    target.parent.mkdir(parents=True,exist_ok=True)
    request=urllib.request.Request(url,headers={"User-Agent":"PREFIX-Distribution-Qualification/1.0"})
    with urllib.request.urlopen(request,timeout=60) as response: target.write_bytes(response.read())
    return target
def unpack_zip(path,target):
    with zipfile.ZipFile(path) as archive:
        for member in archive.namelist():
            destination=(target/member).resolve()
            if not destination.is_relative_to(target.resolve()): raise RuntimeError("archive escaped its target")
        archive.extractall(target)
def get_code(out):
    destination=out/"code"
    target="win32-x64-archive" if os.name=="nt" else "linux-x64"
    archive=acquire(f"https://update.code.visualstudio.com/1.85.2/{target}/stable",out/("code.zip" if os.name=="nt" else "code.tar.gz"))
    destination.mkdir(parents=True,exist_ok=True)
    if os.name=="nt":
        unpack_zip(archive,destination)
        return destination/"Code.exe"
    with tarfile.open(archive) as tar: tar.extractall(destination,filter="data")
    return destination/"VSCode-linux-x64"/"code"
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",type=Path,default=ROOT)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--vsix",type=Path,required=True)
    parser.add_argument("--wheel",type=Path)
    parser.add_argument("--code",type=Path)
    parser.add_argument("--windows-runtime",type=Path)
    args=parser.parse_args()
    out=args.output.resolve(); out.mkdir(parents=True,exist_ok=True)
    source=args.source.resolve(); env=os.environ.copy(); env.pop("ELECTRON_RUN_AS_NODE",None)
    env["PREFIX_ENTITLEMENT_ROOT"]=str(out/"synthetic-entitlement")
    wheel=args.wheel.resolve() if args.wheel else None
    report={"schema":"prefix-distribution-vscode.v1","platform":platform.system().lower(),"machine":platform.machine().lower(),"synthetic_entitlement_only":True,"live_activation_verified":False,"interactive_password_input_verified":False,"publication_performed":False,"steps":[]}
    try:
        if wheel is None:
            wheel_dir=out/"wheel"; wheel_dir.mkdir(exist_ok=True)
            build_space=out/"wheel-build"; build_space.mkdir()
            builder_path=source/"qualification"/"build_final_release.py"
            specification=importlib.util.spec_from_file_location("prefix_qualified_builder",builder_path)
            builder=importlib.util.module_from_spec(specification); specification.loader.exec_module(builder)
            raw_wheel=builder._build_wheel(build_space)
            wheel=wheel_dir/raw_wheel.name
            builder._canonicalize_zip(raw_wheel,wheel)
            report["steps"].append({"command":["shared qualified _build_wheel","shared _canonicalize_zip"],"builder":str(builder_path),"builder_sha256":digest(builder_path),"exit_code":0})
        report["wheel"]={"path":str(wheel),"sha256":digest(wheel)}
        report["vsix"]={"path":str(args.vsix.resolve()),"sha256":digest(args.vsix.resolve())}
        if os.name=="nt":
            env["LOCALAPPDATA"]=str(out/"appdata")
            runtime=out/"appdata"/"FastIndustries"/"PREFIX for Python"/"runtime"
            runtime.mkdir(parents=True,exist_ok=True)
            archive=args.windows_runtime.resolve() if args.windows_runtime else acquire(RUNTIME_URL,out/"python-3.12.10-embed-amd64.zip")
            if digest(archive)!=RUNTIME_SHA: raise RuntimeError("embedded CPython custody failed")
            unpack_zip(archive,runtime)
            (runtime/"python312._pth").write_text("python312.zip\n.\nLib/site-packages\nimport site\n",encoding="ascii")
            packages=runtime/"Lib"/"site-packages"; packages.mkdir(parents=True,exist_ok=True)
            unpack_zip(wheel,packages)
            engine=runtime/"python.exe"
            report["runtime_archive"]={"sha256":digest(archive),"source":RUNTIME_URL}
        else:
            env["XDG_DATA_HOME"]=str(out/"data")
            install=out/"data"/"fastindustries"/"prefix-python"
            runtime=install/"runtime"; runtime.mkdir(parents=True,exist_ok=True)
            venv.create(install/"venv",with_pip=False)
            python=install/"venv"/"bin"/"python"
            packages=install/"venv"/"lib"/"python3.12"/"site-packages"
            packages.mkdir(parents=True,exist_ok=True)
            unpack_zip(wheel,packages)
            engine=runtime/"prefix-python-python"
            engine.write_text('#!/bin/sh\nexec "'+str(python)+'" -I "$@"\n',encoding="utf-8"); engine.chmod(0o755)
        code=args.code.resolve() if args.code else get_code(out)
        report["code"]={"path":str(code),"sha256":digest(code)}
        profile=out/"vscode-user"; extensions=out/"vscode-extensions"
        profile.mkdir(exist_ok=True); extensions.mkdir(exist_ok=True)
        install_args=["--user-data-dir",profile,"--extensions-dir",extensions,"--install-extension",args.vsix.resolve(),"--force"]
        if os.name=="nt":
            cli_candidates=[code.parent/"resources"/"app"/"out"/"cli.js"]
            launcher=code.parent/"bin"/"code.cmd"
            if launcher.is_file():
                match=re.search(r'"%~dp0\.\.\\([^"\r\n]*cli\.js)"',launcher.read_text(encoding="utf-8"))
                if match: cli_candidates.insert(0,code.parent/Path(match.group(1)))
            cli=next((candidate for candidate in cli_candidates if candidate.is_file()),None)
            if cli is None: raise RuntimeError("installed Code CLI entry point is missing")
            cli_env=dict(env); cli_env["ELECTRON_RUN_AS_NODE"]="1"
            step=execute([code,cli,*install_args],cli_env,out)
        else:
            cli=code.parent/"resources"/"app"/"out"/"cli.js"
            if not cli.is_file(): raise RuntimeError("Linux Code CLI entry point is missing")
            cli_env=dict(env); cli_env["ELECTRON_RUN_AS_NODE"]="1"; cli_env.pop("VSCODE_DEV",None)
            step=execute([code,cli,"--ms-enable-electron-run-as-node",*install_args],cli_env,out)
        report["steps"].append(step)
        if step["exit_code"]!=0: raise RuntimeError("VSIX install failed")
        env["PREFIX_HOST_CASE_REPORT"]=str(out/"host-case-report.json")
        wrong_engine=shutil.which("node") or shutil.which("false")
        if not wrong_engine: raise RuntimeError("wrong-interpreter fixture executable is unavailable")
        host_command=[sys.executable,source/"qualification"/"run_vscode_host_proof.py","--code",code,"--user-data-dir",profile,"--extensions-dir",extensions,"--timeout-engine",sys.executable,"--wrong-engine",wrong_engine,"--output",out/"vscode-host.json"]
        if os.name!="nt":
            host_command+=["--xvfb-run",shutil.which("xvfb-run")]
            if shutil.which("dbus-run-session"): host_command+=["--dbus-run-session",shutil.which("dbus-run-session")]
        step=execute(host_command,env,out,timeout=520)
        report["steps"].append(step)
        proof=json.loads((out/"vscode-host.json").read_text(encoding="utf-8"))
        report["host_proof"]=proof
        report["passed"]=proof["passed"]
        cases=[]
        for run in proof["runs"]:
            marker=next((line.split("PREFIX_VSCODE_HOST_PROOF_OK ",1)[1] for line in run["stdout_tail"].splitlines() if "PREFIX_VSCODE_HOST_PROOF_OK " in line),None)
            if marker:
                metadata=json.loads(marker); cases.extend(metadata.get("cases",[]))
        report["test_counts"]={"pass":sum(case["passed"] for case in cases),"fail":0 if report["passed"] else None,"error":0 if report["passed"] else None,"skip":0,"expected_host_runs":2,"completed_host_runs":len(proof["runs"]),"expected_cases_per_run":16}
        if not proof["passed"]: raise RuntimeError("actual extension-host qualification failed")
    except Exception as error:
        report["passed"]=False; report["error"]=str(error)
    (out/"distribution-vscode-result.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"passed":report.get("passed",False),"output":str(out/"distribution-vscode-result.json"),"test_counts":report.get("test_counts")},sort_keys=True))
    return 0 if report.get("passed") else 1
if __name__=="__main__": raise SystemExit(main())
