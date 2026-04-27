"""
Quick smoke-test for the Generator pipeline.

Usage:
    python test_run.py

The server must be running:
    uvicorn main:app --reload
"""

import time
import json
import urllib.request

BASE_URL = "http://localhost:8000"
POLL_INTERVAL = 5    # seconds between status checks
TIMEOUT = 180        # total seconds to wait

REQUIRED_FILES = {
    "src/index.html",
    "tests/test_functional.py",
    "docs/functional-req.md",
}


def read_file(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def post_json(url: str, data: dict) -> dict:
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read())


def main():
    print("Reading test_input files...")
    bt = read_file("test_input/bt.md")
    bp = read_file("test_input/bp.md")
    features = read_file("test_input/features.md")

    print("Sending POST /generate...")
    result = post_json(f"{BASE_URL}/generate", {"bt": bt, "bp": bp, "features": features})
    run_id = result["run_id"]
    print(f"run_id: {run_id}")
    print(f"status: {result['status']}")

    elapsed = 0
    files = []
    while elapsed < TIMEOUT:
        time.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL
        status_data = get_json(f"{BASE_URL}/status/{run_id}")
        files = set(status_data.get("files", []))
        missing = REQUIRED_FILES - files
        print(f"[{elapsed:3d}s] files={len(files)}  missing={sorted(missing) if missing else 'none'}")
        if not missing:
            print("All required files present — pipeline complete.")
            break
    else:
        missing = REQUIRED_FILES - files
        print(f"\nTIMEOUT after {TIMEOUT}s. Still missing: {sorted(missing)}")

    print("\n--- Generated artifacts ---")
    for f in sorted(files):
        print(f"  {f}")

    if files:
        print(f"\nDownload zip: {BASE_URL}/download/{run_id}")


if __name__ == "__main__":
    main()
