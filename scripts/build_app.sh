#!/bin/bash
# Builds AirpodsPosture.app in the project root.
#
# Core Motion on macOS requires NSMotionUsageDescription, and TCC associates
# that permission with the *running binary's* code signature. So we can't just
# exec an external python (its own signature wins and TCC SIGABRTs us). Instead
# we embed a COPY of the interpreter that has pyobjc/CoreMotion and ad-hoc
# re-sign it, so TCC reads THIS bundle's Info.plist.

set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP="$ROOT/AirpodsPosture.app"

# --- Pick an interpreter that actually has pyobjc + CoreMotion ---
pick_py() {
    for c in "$(command -v python3 2>/dev/null)" /opt/anaconda3/bin/python3 "$(command -v python 2>/dev/null)"; do
        [ -n "$c" ] && [ -x "$c" ] || continue
        if "$c" -c 'import CoreMotion' >/dev/null 2>&1; then
            "$c" -c 'import os, sys; print(os.path.realpath(sys.executable))'
            return 0
        fi
    done
    echo "ERROR: no python with pyobjc CoreMotion found (pip install pyobjc-framework-CoreMotion)" >&2
    exit 1
}

PYBIN="$(pick_py)"
PYHOME="$("$PYBIN" -c 'import sys; print(sys.prefix)')"

rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS"

cp "$ROOT/packaging/Info.plist" "$APP/Contents/Info.plist"

# Launcher, with PYTHONHOME baked in so the embedded interpreter finds its stdlib.
sed "s|@PYHOME@|$PYHOME|g" "$ROOT/packaging/launch" > "$APP/Contents/MacOS/launch"
chmod +x "$APP/Contents/MacOS/launch"

# Embed the interpreter as the bundle's MAIN executable (CFBundleExecutable =
# python3 in Info.plist). TCC only maps a process to a bundle's Info.plist when
# that process IS the main executable, so python3 must be it (not the launch
# wrapper). Repoint rpath at the real lib dir BEFORE signing.
cp "$PYBIN" "$APP/Contents/MacOS/python3"
chmod u+w "$APP/Contents/MacOS/python3"
install_name_tool -add_rpath "$PYHOME/lib" "$APP/Contents/MacOS/python3" 2>/dev/null || true

# Ad-hoc sign the WHOLE bundle so the signature seals Info.plist (incl.
# NSMotionUsageDescription); signing python3 alone does not bind it.
codesign --force --deep --sign - "$APP"

echo "Built $APP"
echo "  embedded interpreter: $PYBIN"
echo "  PYTHONHOME:           $PYHOME"
echo
echo "Run motion scripts via the bundle, not bare python3:"
echo "  AirpodsPosture.app/Contents/MacOS/launch calibrate.py   # first time only"
echo "  AirpodsPosture.app/Contents/MacOS/launch record_mac.py --label good"