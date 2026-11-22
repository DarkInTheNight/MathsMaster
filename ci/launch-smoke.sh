#!/bin/bash
# Launch smoke test: builds the app the way Swift Playgrounds does (Debug), runs it in an
# iPad simulator twice (first run with no library, then with a fixture library so the main
# split view, Today and the card store load), and fails if the app crashes or exits.
# Usage: ci/launch-smoke.sh <output dir>
set -uo pipefail
OUT=${1:?output dir}
mkdir -p "$OUT"
ROOT=$(cd "$(dirname "$0")/.." && pwd)
BUNDLE=com.darkinthenight.mathsmaster

RUNTIME=$(xcrun simctl list runtimes -j | python3 -c '
import json,sys
rs=[r for r in json.load(sys.stdin)["runtimes"] if r["platform"]=="iOS" and r["isAvailable"]]
rs.sort(key=lambda r:[int(x) for x in r["version"].split(".")])
print(rs[-1]["identifier"] if rs else "")')
DEVTYPE=$(xcrun simctl list devicetypes -j | python3 -c '
import json,sys
ds=[d for d in json.load(sys.stdin)["devicetypes"] if d.get("productFamily")=="iPad" and "iPad Air" in d["name"]]
ds.sort(key=lambda d:d.get("minRuntimeVersion",0))
print(ds[-1]["identifier"] if ds else "")')
echo "Runtime: $RUNTIME  Device type: $DEVTYPE"
[ -n "$RUNTIME" ] && [ -n "$DEVTYPE" ] || { echo "::error::No iOS simulator runtime or iPad Air device type"; exit 1; }
UDID=$(xcrun simctl create mm-smoke "$DEVTYPE" "$RUNTIME") || UDID=""
if [ -z "$UDID" ]; then  # fall back to any existing iPad on that runtime
  UDID=$(xcrun simctl list devices available -j | python3 -c '
import json,sys
ds=json.load(sys.stdin)["devices"].get(sys.argv[1],[])
ip=[d["udid"] for d in ds if "iPad" in d["name"]]
print(ip[0] if ip else "")' "$RUNTIME")
fi
[ -n "$UDID" ] || { echo "::error::No iPad simulator"; xcrun simctl list devices available; exit 1; }
echo "Simulator: $UDID"
xcrun simctl boot "$UDID"
xcrun simctl bootstatus "$UDID" -b >/dev/null

echo "::group::Debug build for the simulator"
(cd "$ROOT/MathsMaster.swiftpm" && xcodebuild build -scheme MathsMaster -configuration Debug \
  -destination "id=$UDID" -derivedDataPath "$RUNNER_TEMP/dd-smoke" -quiet) || { echo "::error::Debug simulator build failed"; exit 1; }
echo "::endgroup::"
APP=$(find "$RUNNER_TEMP/dd-smoke/Build/Products" -maxdepth 2 -name "*.app" -path "*iphonesimulator*" | head -1)
echo "App: $APP"
xcrun simctl install "$UDID" "$APP"

# A small fixture library (one course in the current term), like a real first-week library.
LIB="$RUNNER_TEMP/smoke-library"
rm -rf "$LIB"; mkdir -p "$LIB/Courses/Test Course/Lecture notes" "$LIB/Courses/Test Course/Example sheets" \
  "$LIB/Courses/Test Course/Notebooks" "$LIB/Reviews" "$LIB/Logs" "$LIB/Inbox/jobs" "$LIB/AI" "$LIB/Exports"
Y=$(date +%Y)
cat > "$LIB/library.json" <<JSON
{ "courses": [ { "archived": false, "colour": "indigo", "folder": "Courses/Test Course",
    "id": "11111111-1111-1111-1111-111111111111", "lectures": 16, "name": "Test Course", "order": 0,
    "term": "michaelmas", "yearID": "22222222-2222-2222-2222-222222222222" } ],
  "createdAt": "${Y}-01-01T00:00:00Z", "libraryID": "33333333-3333-3333-3333-333333333333",
  "name": "MathsMaster", "schemaVersion": 1,
  "years": [ { "id": "22222222-2222-2222-2222-222222222222", "name": "Part IB",
    "terms": [ { "name": "michaelmas", "start": "$((Y-1))-10-01", "end": "$((Y+1))-12-31" },
               { "name": "lent", "start": "$((Y+2))-01-19", "end": "$((Y+2))-03-19" },
               { "name": "easter", "start": "$((Y+2))-04-27", "end": "$((Y+2))-06-18" } ] } ] }
JSON
echo '{ "id": "11111111-1111-1111-1111-111111111111", "name": "Test Course", "schemaVersion": 1 }' > "$LIB/Courses/Test Course/course.json"

CRASHDIR="$HOME/Library/Logs/DiagnosticReports"
FAIL=0
run() { # name, extra env
  local name=$1 lib=$2
  local before; before=$(ls "$CRASHDIR" 2>/dev/null | sort)
  echo "::group::Launch: $name"
  SIMCTL_CHILD_MM_SMOKE_LIBRARY="$lib" xcrun simctl launch --terminate-running-process "$UDID" "$BUNDLE" > "$OUT/launch-$name.txt" 2>&1
  cat "$OUT/launch-$name.txt"
  sleep 20
  xcrun simctl io "$UDID" screenshot "$OUT/$name.png" >/dev/null 2>&1
  local alive; alive=$(xcrun simctl spawn "$UDID" launchctl list | grep "UIKitApplication:$BUNDLE" | awk '{print $1}')
  echo "launchctl pid: ${alive:-none}"
  local new; new=$(comm -13 <(echo "$before") <(ls "$CRASHDIR" 2>/dev/null | sort) | grep -i "MathsMaster" || true)
  for f in $new; do
    echo "::error::Crash report $f"; cp "$CRASHDIR/$f" "$OUT/"
    python3 "$ROOT/ci/ips-summary.py" "$CRASHDIR/$f" || head -c 20000 "$CRASHDIR/$f"
  done
  if [ -n "$new" ] || [ -z "$alive" ] || [ "$alive" = "-" ]; then echo "::error::$name: the app is not running 20 s after launch"; FAIL=1; fi
  echo "::endgroup::"
}
run first-launch ""
run with-library "$LIB"
xcrun simctl spawn "$UDID" log show --last 3m --style compact --predicate 'process == "MathsMaster"' > "$OUT/app-log.txt" 2>/dev/null
tail -80 "$OUT/app-log.txt"
xcrun simctl shutdown "$UDID"; xcrun simctl delete "$UDID"
exit $FAIL
