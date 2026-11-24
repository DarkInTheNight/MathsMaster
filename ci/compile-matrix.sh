#!/bin/bash
# Compiles the app's Swift sources with every Xcode 26.x on the runner (Debug, like Swift Playgrounds),
# so code that needs a newer compiler than Swift Playground ships fails here, not on the iPad.
# Usage: ci/compile-matrix.sh [extra swiftc flags]
set -uo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
SOURCES=()
while IFS= read -r f; do SOURCES+=("$f"); done < <(find "$ROOT/MathsMaster2.swiftpm" -name '*.swift' ! -name Package.swift ! -path '*/.swiftpm/*' | sort)
echo "${#SOURCES[@]} source files"
FAIL=0
SEEN=""
for X in $(ls -d /Applications/Xcode_26*.app | sort -V); do
  export DEVELOPER_DIR="$X/Contents/Developer"
  SDK=$(xcrun --sdk iphoneos --show-sdk-path 2>/dev/null) || { echo "$X: no iOS SDK, skipped"; continue; }
  V=$(xcrun swiftc --version 2>&1 | grep -o "Apple Swift version [0-9.]*")
  case " $SEEN " in *" $V|$(basename "$SDK") "*) continue;; esac   # same compiler and SDK already checked
  SEEN="$SEEN $V|$(basename "$SDK")"
  echo "::group::$(basename "$X") · $(basename "$SDK") · $V"
  LOG="${RUNNER_TEMP:-/tmp}/compile.log"
  if xcrun swiftc -c -wmo -parse-as-library -module-name AppModule -Onone -DDEBUG \
       -target arm64-apple-ios26.0 -sdk "$SDK" -swift-version 5 "$@" \
       -o "${RUNNER_TEMP:-/tmp}/app.o" "${SOURCES[@]}" > "$LOG" 2>&1; then
    echo "OK"; grep -c "warning:" "$LOG" | sed 's/^/warnings: /'
  else
    grep -E "error:" -A3 "$LOG" | head -80
    echo "::error::$(basename "$X") ($V) failed to compile the app"; FAIL=1
  fi
  echo "::endgroup::"
done
exit $FAIL
