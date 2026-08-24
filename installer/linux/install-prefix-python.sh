#!/usr/bin/env sh
set -eu

PRODUCT_VERSION="0.1.0"
EXTENSION_ID="fastindustries.prefix-python"
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PAYLOAD_DIR="$SCRIPT_DIR/payload"
MANIFEST="$PAYLOAD_DIR/payload-manifest.json"

fail() {
    printf '%s\n' "PREFIX for Python installation blocked: $*" >&2
    exit 1
}

find_python() {
    if [ -n "${PREFIX_PYTHON_RUNTIME:-}" ]; then
        printf '%s\n' "$PREFIX_PYTHON_RUNTIME"
        return
    fi
    for candidate in python3.12 python3 python; do
        if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import platform,sys; raise SystemExit(0 if platform.python_implementation()=="CPython" and sys.version_info[:2]==(3,12) else 1)' >/dev/null 2>&1; then
            command -v "$candidate"
            return
        fi
    done
    return 1
}

[ "$(uname -s)" = "Linux" ] || fail "Linux is required."
[ "$(uname -m)" = "x86_64" ] || [ "$(uname -m)" = "amd64" ] || fail "Linux amd64 is required."
[ -f "$MANIFEST" ] || fail "the payload manifest is missing; re-download the complete Linux amd64 package."
PYTHON=$(find_python) || fail "CPython 3.12 was not found. Install the python3.12 package for your distribution, then run this installer again."

"$PYTHON" - "$PAYLOAD_DIR" "$MANIFEST" <<'PY'
import hashlib, json, pathlib, sys
payload = pathlib.Path(sys.argv[1])
manifest = json.loads(pathlib.Path(sys.argv[2]).read_text(encoding="utf-8"))
if manifest.get("product") != "PREFIX for Python" or manifest.get("version") != "0.1.0" or manifest.get("platform") != "linux-amd64":
    raise SystemExit("invalid package manifest identity")
for artifact in manifest.get("artifacts", []):
    path = payload / artifact["name"]
    if not path.is_file():
        raise SystemExit(f"missing payload: {artifact['name']}")
    if hashlib.sha256(path.read_bytes()).hexdigest() != artifact["sha256"]:
        raise SystemExit(f"payload hash mismatch: {artifact['name']}")
PY

DATA_ROOT=${XDG_DATA_HOME:-"$HOME/.local/share"}
INSTALL_ROOT=${PREFIX_INSTALL_ROOT:-"$DATA_ROOT/fastindustries/prefix-python"}
BIN_ROOT=${PREFIX_BIN_ROOT:-"$HOME/.local/bin"}
PARENT=$(dirname -- "$INSTALL_ROOT")
STAGE="$PARENT/prefix-python.installing.$$"
BACKUP="$PARENT/prefix-python.previous.$$"

cleanup() {
    [ ! -e "$STAGE" ] || rm -rf -- "$STAGE"
}
trap cleanup EXIT HUP INT TERM

mkdir -p "$PARENT" "$STAGE/lib" "$STAGE/runtime" "$STAGE/assets" "$STAGE/bin" "$BIN_ROOT"
WHEEL=$("$PYTHON" -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["wheel"])' "$MANIFEST")
VSIX=$("$PYTHON" -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["vsix"])' "$MANIFEST")
"$PYTHON" -m zipfile -e "$PAYLOAD_DIR/$WHEEL" "$STAGE/lib"
cp "$PAYLOAD_DIR/$VSIX" "$STAGE/assets/prefix-python-0.1.0.vsix"
cp "$PAYLOAD_DIR/broken_missing_colon.txt" "$STAGE/assets/broken_missing_colon.txt"
cp "$PAYLOAD_DIR/broken_return_outside_function.txt" "$STAGE/assets/broken_return_outside_function.txt"

cat > "$STAGE/runtime/prefix-python-python" <<EOF
#!/usr/bin/env sh
export PYTHONPATH="$INSTALL_ROOT/lib"
exec "$PYTHON" "\$@"
EOF
chmod 0755 "$STAGE/runtime/prefix-python-python"

cat > "$STAGE/bin/prefix-python" <<EOF
#!/usr/bin/env sh
exec "$INSTALL_ROOT/runtime/prefix-python-python" -m prefix_python "\$@"
EOF
cat > "$STAGE/bin/prefix-python-ops" <<EOF
#!/usr/bin/env sh
exec "$INSTALL_ROOT/runtime/prefix-python-python" -m prefix_python.operator_console "\$@"
EOF
cat > "$STAGE/bin/prefix-python-demo" <<EOF
#!/usr/bin/env sh
exec "$INSTALL_ROOT/runtime/prefix-python-python" -m prefix_python "$INSTALL_ROOT/assets/broken_missing_colon.txt" --json
EOF
chmod 0755 "$STAGE/bin/prefix-python" "$STAGE/bin/prefix-python-ops" "$STAGE/bin/prefix-python-demo"

PYTHONPATH="$STAGE/lib" "$PYTHON" -m prefix_python --version | grep '0.1.0' >/dev/null || fail "the bundled engine version smoke check failed."
SMOKE=$(printf 'if ready\nprint("launch")\n' | PYTHONPATH="$STAGE/lib" "$PYTHON" -m prefix_python --stdin --json)
printf '%s' "$SMOKE" | "$PYTHON" -c 'import json,sys; p=json.load(sys.stdin); raise SystemExit(0 if p.get("status")=="ACCEPT_FIXED" and "if ready:" in p.get("source", "") else 1)' || fail "the correction smoke check failed."

"$PYTHON" - "$STAGE/install-manifest.json" "$PYTHON" "$WHEEL" "$VSIX" <<'PY'
import json, pathlib, platform, sys
pathlib.Path(sys.argv[1]).write_text(json.dumps({
    "product": "PREFIX for Python",
    "version": "0.1.0",
    "platform": "linux-amd64",
    "runtime": f"CPython {platform.python_version()}",
    "runtime_path": sys.argv[2],
    "wheel": sys.argv[3],
    "vsix": sys.argv[4],
    "smoke_status": "ACCEPT_FIXED",
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

if [ -e "$INSTALL_ROOT" ]; then mv "$INSTALL_ROOT" "$BACKUP"; fi
mv "$STAGE" "$INSTALL_ROOT"
if command -v code >/dev/null 2>&1; then
    set -- --install-extension "$INSTALL_ROOT/assets/prefix-python-0.1.0.vsix" --force
    if [ -n "${PREFIX_VSCODE_EXTENSIONS_DIR:-}" ]; then set -- "$@" --extensions-dir "$PREFIX_VSCODE_EXTENSIONS_DIR"; fi
    if [ -n "${PREFIX_VSCODE_USER_DATA_DIR:-}" ]; then set -- "$@" --user-data-dir "$PREFIX_VSCODE_USER_DATA_DIR"; fi
    code "$@" || {
        rm -rf -- "$INSTALL_ROOT"
        [ ! -e "$BACKUP" ] || mv "$BACKUP" "$INSTALL_ROOT"
        fail "VS Code extension installation failed."
    }
    set -- --list-extensions
    if [ -n "${PREFIX_VSCODE_EXTENSIONS_DIR:-}" ]; then set -- "$@" --extensions-dir "$PREFIX_VSCODE_EXTENSIONS_DIR"; fi
    if [ -n "${PREFIX_VSCODE_USER_DATA_DIR:-}" ]; then set -- "$@" --user-data-dir "$PREFIX_VSCODE_USER_DATA_DIR"; fi
    code "$@" | grep -Fx "$EXTENSION_ID" >/dev/null || {
        rm -rf -- "$INSTALL_ROOT"
        [ ! -e "$BACKUP" ] || mv "$BACKUP" "$INSTALL_ROOT"
        fail "VS Code did not report the PREFIX extension after setup."
    }
else
    printf '%s\n' "VS Code was not found. The engine is installed; install VS Code from https://code.visualstudio.com/ and rerun this installer to add the extension." >&2
fi

ln -sfn "$INSTALL_ROOT/bin/prefix-python" "$BIN_ROOT/prefix-python"
ln -sfn "$INSTALL_ROOT/bin/prefix-python-ops" "$BIN_ROOT/prefix-python-ops"
ln -sfn "$INSTALL_ROOT/bin/prefix-python-demo" "$BIN_ROOT/prefix-python-demo"
[ ! -e "$BACKUP" ] || rm -rf -- "$BACKUP"
trap - EXIT HUP INT TERM

printf '%s\n' "PREFIX for Python $PRODUCT_VERSION is installed."
printf '%s\n' "Engine: $INSTALL_ROOT/runtime/prefix-python-python"
printf '%s\n' "Demo: $BIN_ROOT/prefix-python-demo"
printf '%s\n' "Open a Python file in VS Code and run 'PREFIX: Govern Active Python Transition'."
