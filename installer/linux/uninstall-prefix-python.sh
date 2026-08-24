#!/usr/bin/env sh
set -eu
DATA_ROOT=${XDG_DATA_HOME:-"$HOME/.local/share"}
INSTALL_ROOT=${PREFIX_INSTALL_ROOT:-"$DATA_ROOT/fastindustries/prefix-python"}
BIN_ROOT=${PREFIX_BIN_ROOT:-"$HOME/.local/bin"}
if command -v code >/dev/null 2>&1; then
    set -- --uninstall-extension fastindustries.prefix-python
    if [ -n "${PREFIX_VSCODE_EXTENSIONS_DIR:-}" ]; then set -- "$@" --extensions-dir "$PREFIX_VSCODE_EXTENSIONS_DIR"; fi
    if [ -n "${PREFIX_VSCODE_USER_DATA_DIR:-}" ]; then set -- "$@" --user-data-dir "$PREFIX_VSCODE_USER_DATA_DIR"; fi
    code "$@" || true
fi
rm -f -- "$BIN_ROOT/prefix-python" "$BIN_ROOT/prefix-python-ops" "$BIN_ROOT/prefix-python-demo"
rm -rf -- "$INSTALL_ROOT"
printf '%s\n' "PREFIX for Python was removed from $INSTALL_ROOT"
