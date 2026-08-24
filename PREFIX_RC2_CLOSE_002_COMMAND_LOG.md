# PREFIX RC2 Close 002 Command Log

All commands were executed through `powershell.exe -NoProfile -ExecutionPolicy Bypass`. Network use was bounded to `python.org`, `pypi.org`, and `registry.npmjs.org` for the requested patch runtimes and registry audits.

## Source Authority

```powershell
git -C C:\FastIndustries status --short
git -C C:\FastIndustries remote get-url origin
git -C C:\FastIndustries rev-parse HEAD
git -C C:\FastIndustries rev-parse 'HEAD^{tree}'
git -C C:\FastIndustries rev-parse 'HEAD:ConstrainedPython'
git -C C:\FastIndustries log -1 --format='%H%x09%T%x09%s' -- ConstrainedPython
git -C C:\FastIndustries ls-files -- ConstrainedPython
git -C C:\FastIndustries status --short -- ConstrainedPython
```

Each tracked Git blob was streamed through SHA-256 and compared with the corresponding standalone file. The complete results are in `SOURCE_AUTHORITY_MANIFEST.json`.

## CPython Boundary Probes

```powershell
Invoke-WebRequest https://www.python.org/ftp/python/3.12.0/python-3.12.0-embed-amd64.zip -OutFile D:\PREFIX_RC2_CLOSE_002_TEMP\cpython-patches\python-3.12.0-embed-amd64.zip
Invoke-WebRequest https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip -OutFile D:\PREFIX_RC2_CLOSE_002_TEMP\cpython-patches\python-3.12.10-embed-amd64.zip
D:\PREFIX_RC2_CLOSE_002_TEMP\cpython-patches\python-3.12.0\python.exe C:\PREFIX_PYTHON\qualification\_hardening_artifacts\prefix_rc2_close_002\cpython_patch_probe.py
& 'C:\Program Files\Python312\python.exe' C:\PREFIX_PYTHON\qualification\_hardening_artifacts\prefix_rc2_close_002\cpython_patch_probe.py
D:\PREFIX_RC2_CLOSE_002_TEMP\cpython-patches\python-3.12.10\python.exe C:\PREFIX_PYTHON\qualification\_hardening_artifacts\prefix_rc2_close_002\cpython_patch_probe.py
```

## Registry Audits

```powershell
D:\PREFIX_RC2_CLOSE_002_TEMP\audit-venv\Scripts\python.exe -m pip_audit --path D:\PREFIX_RC2_CLOSE_002_TEMP\wheel-venv\Lib\site-packages --format json
D:\PREFIX_RC2_CLOSE_002_TEMP\wheel-venv\Scripts\python.exe -m pip install --index-url https://pypi.org/simple --upgrade pip
D:\PREFIX_RC2_CLOSE_002_TEMP\audit-venv\Scripts\python.exe -m pip_audit --path D:\PREFIX_RC2_CLOSE_002_TEMP\wheel-venv\Lib\site-packages --format json
npm audit --package-lock-only --registry https://registry.npmjs.org/ --json
npm audit --package-lock-only --registry https://registry.npmjs.org/
```

## Isolated VS Code

```powershell
$env:ELECTRON_RUN_AS_NODE='1'
& 'C:\Users\steve\AppData\Local\Programs\Microsoft VS Code\Code.exe' 'C:\Users\steve\AppData\Local\Programs\Microsoft VS Code\resources\app\out\cli.js' --version
& 'C:\Users\steve\AppData\Local\Programs\Microsoft VS Code\Code.exe' 'C:\Users\steve\AppData\Local\Programs\Microsoft VS Code\resources\app\out\cli.js' --user-data-dir D:\PREFIX_RC2_CLOSE_002_TEMP\user-data --extensions-dir D:\PREFIX_RC2_CLOSE_002_TEMP\extensions --install-extension C:\PREFIX_PYTHON\release\prefix-python-0.1.0.vsix --force
& 'C:\Users\steve\AppData\Local\Programs\Microsoft VS Code\Code.exe' 'C:\Users\steve\AppData\Local\Programs\Microsoft VS Code\resources\app\out\cli.js' --user-data-dir D:\PREFIX_RC2_CLOSE_002_TEMP\user-data --extensions-dir D:\PREFIX_RC2_CLOSE_002_TEMP\extensions --list-extensions --show-versions
Remove-Item Env:ELECTRON_RUN_AS_NODE
& 'C:\Users\steve\AppData\Local\Programs\Microsoft VS Code\Code.exe' --user-data-dir D:\PREFIX_RC2_CLOSE_002_TEMP\user-data --extensions-dir D:\PREFIX_RC2_CLOSE_002_TEMP\extensions --new-window D:\PREFIX_RC2_CLOSE_002_TEMP\workspace\apply_case.py
```

The final GUI command was attempted twice. VS Code itself refused startup while its updater was active; the copied `main.log` files are the authoritative result.

## Installed Wheel Runtime

```powershell
D:\PREFIX_RC2_CLOSE_002_TEMP\wheel-venv\Scripts\python.exe -c "import json,platform,prefix_python,sys; print(json.dumps({'executable':sys.executable,'version':platform.python_version(),'implementation':platform.python_implementation(),'prefix_package':prefix_python.__file__},sort_keys=True))"
D:\PREFIX_RC2_CLOSE_002_TEMP\wheel-venv\Scripts\prefix-python.exe --version
'if ready' | D:\PREFIX_RC2_CLOSE_002_TEMP\wheel-venv\Scripts\python.exe -m prefix_python --stdin --json
```

## Artifact Integrity

```powershell
Get-FileHash -Algorithm SHA256 C:\PREFIX_PYTHON\release\prefix-python-0.1.0-rc2.zip
Get-FileHash -Algorithm SHA256 C:\PREFIX_PYTHON\release\prefix_python-0.1.0-py3-none-any.whl
Get-FileHash -Algorithm SHA256 C:\PREFIX_PYTHON\release\prefix-python-0.1.0.vsix
Get-FileHash -Algorithm SHA256 C:\PREFIX_PYTHON\release\SHA256SUMS.txt
Get-FileHash -Algorithm SHA256 C:\PREFIX_PYTHON\release\prefix-python-0.1.0-rc2\SHA256SUMS.txt
```
