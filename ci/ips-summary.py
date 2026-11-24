"""Prints the useful part of an Apple .ips crash report: exception, termination reason, crashed thread frames."""
import json, sys

text = open(sys.argv[1]).read()
header, _, body = text.partition("\n")
report = json.loads(body)
print("Exception:", json.dumps(report.get("exception")))
print("Termination:", json.dumps(report.get("termination")))
asi = report.get("asi")
if asi:
    print("ASI:", json.dumps(asi))
images = report.get("usedImages", [])
for t in report.get("threads", []):
    if not t.get("triggered"):
        continue
    print("Crashed thread:", t.get("name") or t.get("queue") or "")
    for f in t.get("frames", [])[:40]:
        img = images[f["imageIndex"]]["name"] if f.get("imageIndex") is not None and f["imageIndex"] < len(images) else "?"
        print(f"  {img:28} {f.get('symbol', '?')} +{f.get('symbolLocation', 0)} {f.get('sourceFile', '')}:{f.get('sourceLine', '')}")
