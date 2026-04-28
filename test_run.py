import os
import sys
import time
import json
import urllib.request
import urllib.error

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_URL = os.environ.get("GENERATOR_BASE_URL", "http://localhost:8000")
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", 5))

REQUIRED_FILES = {
    "src/index.html",
    "tests/test_functional.py",
    "docs/functional-req.md",
}

TERMINAL_STATUSES = {"done", "failed"}


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


def _group_files(files: set[str]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {"docs": [], "src": [], "tests": [], "other": []}
    for f in sorted(files):
        if f.startswith("docs/"):
            groups["docs"].append(f)
        elif f.startswith("src/"):
            groups["src"].append(f)
        elif f.startswith("tests/"):
            groups["tests"].append(f)
        elif not f.startswith("."):
            groups["other"].append(f)
    return groups


def main():
    input_dir = sys.argv[1] if len(sys.argv) > 1 else "test_input"

    bt_path = os.path.join(input_dir, "bt.md")
    bp_path = os.path.join(input_dir, "bp.md")
    features_path = os.path.join(input_dir, "features.md")

    print(f"=== Generator smoke-test | input: '{input_dir}' ===\n")

    print("Reading input files...")
    bt = read_file(bt_path)
    bp = read_file(bp_path)
    features = read_file(features_path) if os.path.isfile(features_path) else ""
    print(f"  bt.md        {len(bt)} chars")
    print(f"  bp.md        {len(bp)} chars")
    if features:
        print(f"  features.md  {len(features)} chars")
    else:
        print("  features.md  — not found, running without features")

    print("\nSending POST /generate...")
    try:
        result = post_json(f"{BASE_URL}/generate", {"bt": bt, "bp": bp, "features": features})
    except urllib.error.URLError as e:
        print(f"\nERROR: Cannot connect to server at {BASE_URL}")
        print(f"  {e}")
        print("\nMake sure the server is running:\n  uvicorn main:app --reload")
        sys.exit(1)

    run_id = result["run_id"]
    print(f"  run_id: {run_id}")
    print(f"  status: {result['status']}")
    print(f"\nPolling every {POLL_INTERVAL}s... (Ctrl+C to stop)\n")

    elapsed = 0
    files: set[str] = set()
    last_step = ""
    final_status = "unknown"

    try:
        while True:
            time.sleep(POLL_INTERVAL)
            elapsed += POLL_INTERVAL

            try:
                status_data = get_json(f"{BASE_URL}/status/{run_id}")
            except urllib.error.URLError as e:
                print(f"[{elapsed:4d}s] WARNING: status request failed ({e}), retrying...")
                continue

            files = set(f for f in status_data.get("files", []) if not f.startswith("."))
            current_status = status_data.get("status", "")
            current_step = status_data.get("step", "")
            error = status_data.get("error", "")

            step_display = f"  step: {current_step}" if current_step and current_step != last_step else ""
            last_step = current_step

            missing = REQUIRED_FILES - files
            missing_str = ", ".join(sorted(missing)) if missing else "none"
            print(f"[{elapsed:4d}s] status={current_status:<10} files={len(files):2d}  missing={missing_str}{step_display}")

            if current_status in TERMINAL_STATUSES:
                final_status = current_status
                if current_status == "failed" and error:
                    print(f"\n  ERROR: {error}")
                break

    except KeyboardInterrupt:
        final_status = "interrupted"
        print("\n\nStopped by user.")

    print("\n" + "=" * 52)
    if final_status == "done":
        print("RESULT: OK — pipeline completed successfully")
    elif final_status == "failed":
        print("RESULT: FAILED — pipeline ended with error")
    elif final_status == "interrupted":
        print(f"RESULT: INTERRUPTED by user after {elapsed}s")

    missing = REQUIRED_FILES - files
    if missing:
        print(f"\nMissing required files:")
        for f in sorted(missing):
            print(f"  ✗ {f}")

    if files:
        print(f"\nGenerated artifacts ({len(files)} files):")
        groups = _group_files(files)
        for group, items in groups.items():
            if items:
                print(f"  [{group}]")
                for f in items:
                    marker = "✓" if f in REQUIRED_FILES else " "
                    print(f"    {marker} {f}")

        print(f"\nDownload zip: {BASE_URL}/download/{run_id}")

    print("=" * 52)

    sys.exit(0 if final_status == "done" and not missing else 1)


if __name__ == "__main__":
    main()
