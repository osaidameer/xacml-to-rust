import os
import subprocess
import traceback
from collections import defaultdict
from datetime import datetime

# Configuration
base_dir = r".\policy_test_set"
main_path = r".\main.py"
log_file = "log.txt"
failed_log_file = "failed.txt"

# Tracking
total = 0
successes = 0
failures = 0
error_types = defaultdict(list)

# Logging setup
def log(message):
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(message + "\n")
    print(message)

def log_failure(message):
    with open(failed_log_file, "a", encoding="utf-8") as f:
        f.write(message + "\n")

# Start log
log(f"\n=== Run started at {datetime.now()} ===")

for folder in os.listdir(base_dir):
    if folder.startswith("III"):
        print(f"Ignoring {folder}")
        continue
    folder_path = os.path.join(base_dir, folder)

    if not os.path.isdir(folder_path):
        failures += 1
        error_types["Skipped"].append(folder)
        message = f"[SKIP] {folder}: Not a directory."
        log(message)
        log_failure(message)
        continue

    policy_file = os.path.join(folder_path, f"Policy_{folder}.xml")
    if not os.path.exists(policy_file):
        failures += 1
        error_types["Skipped"].append(folder)
        message = f"[SKIP] {folder}: Policy file not found."
        log(message)
        log_failure(message)
        continue

    total += 1
    log(f"[INFO] Processing {policy_file}")

    try:
        result = subprocess.run(
            ["python", main_path, policy_file],
            capture_output=True,
            text=True,
            timeout=20  # Adjust as needed
        )

        if result.returncode == 0:
            successes += 1
            log(f"[SUCCESS] {folder}")
        else:
            failures += 1
            error_type = f"RuntimeError_{result.returncode}"
            error_types[error_type].append(folder)
            error_message = f"[ERROR] {folder}: {error_type}\n{result.stderr.strip()}"
            log(error_message)
            log_failure(error_message)

    except subprocess.TimeoutExpired:
        failures += 1
        error_types["TimeoutExpired"].append(folder)
        message = f"[TIMEOUT] {folder}: Execution timed out."
        log(message)
        log_failure(message)

    except Exception as e:
        failures += 1
        exc_type = type(e).__name__
        error_types[exc_type].append(folder)
        message = f"[EXCEPTION] {folder}: {exc_type}\n{traceback.format_exc()}"
        log(message)
        log_failure(message)

# Summary
log("\n=== SUMMARY ===")
log(f"Total processed (attempted runs): {total}")
log(f"Successful:                      {successes}")
log(f"Failed (including skips):        {failures}")

log("\n--- Error Types ---")
for err_type, folders in error_types.items():
    log(f"{err_type} ({len(folders)}): {', '.join(folders)}")