import sys
import os
import subprocess
import traceback
from collections import defaultdict
from datetime import datetime

# --- Global Configuration ---
USE_REQUEST_RESPONSE_FILES = True
OUTPUT_FOLDER_NAME = "zkvm_testing_with_rsa"
USE_JWT_FLAG = True
USE_RSA_VERIFY = False
# ----------------------------


base_dir = "policy_test_set"
main_path = "main.py"
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = f"logs\\log_{timestamp}.txt"
failed_log_file = f"logs\\failed_{timestamp}.txt"


lock_file = None
if lock_file is not None:
    import json
    with open(lock_file, 'r') as f:
        locked = json.load(f)
else:
    locked = None

# Tracking
total = 0
successes = 0
failures = 0
skips = 0

error_types = defaultdict(list)

os.makedirs(os.path.dirname(log_file), exist_ok=True)

# Logging setup
def log(message):
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(message + "\n")
    print(message)

def log_failure(message):
    with open(failed_log_file, "a", encoding="utf-8") as f:
        f.write(message + "\n")

if locked is not None:
    print("[INFO] Filter in use, skip wrong policy")

# Start log
log(f"\n=== Run started at {datetime.now()} ===")

import time

timings = {}

for folder in os.listdir(base_dir):
    if folder.startswith("III"):
        print(f"Ignoring {folder}")
        continue

    folder_path = os.path.join(base_dir, folder)

    if not os.path.isdir(folder_path):
        skips += 1
        error_types["Skipped"].append(folder)
        message = f"[SKIP] {folder}: Not a directory."
        log(message)
        log_failure(message)
        continue

    policy_file = os.path.join(folder_path, f"Policy_{folder}.xml")
    request_file = os.path.join(folder_path, f"Request_{folder}.xml")
    response_file = os.path.join(folder_path, f"Response_{folder}.xml")

    if not os.path.exists(policy_file) or not os.path.exists(request_file) or not os.path.exists(response_file):
        skips += 1
        error_types["Skipped"].append(folder)
        message = f"[SKIP] {folder}: Policy/Request/Response file missing."
        log(message)
        log_failure(message)
        continue

    total += 1

    if locked is not None:
        output_name = f"Policy_{folder}.xml.rs"
        if output_name in locked and locked[output_name][0] == 'Passed':
            log(f"[INFO] Processing {policy_file}")
        else:
            skips += 1
            log(f"[SKIP] {policy_file} not in lock file or marked as failed, skip")
            continue

    try:
        start_time = time.perf_counter()

        base_command = [sys.executable, main_path, policy_file]

        if USE_REQUEST_RESPONSE_FILES:
            command = base_command + [
                "-r", request_file,
                "-s", response_file
            ]
        else:
            command = base_command

        command.extend(["-o", OUTPUT_FOLDER_NAME])

        if USE_JWT_FLAG:
            command.append("-j")
            if USE_RSA_VERIFY:
                command.append("-R")

        # log(f"[INFO] Running command: {' '.join(str(c) for c in command)}")

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=20
        )

        end_time = time.perf_counter()
        elapsed_time = end_time - start_time

        if result.returncode == 0:
            successes += 1
            timings[folder] = elapsed_time
            log(f"[SUCCESS] {folder} - Time: {elapsed_time:.2f}s")
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

if timings:
    avg_time = sum(timings.values()) / len(timings)
    print(f"\nAverage execution time for successful runs: {avg_time:.2f}s")

    with open("execution_timings.txt", "w") as f:
        for folder, t in timings.items():
            f.write(f"{folder}: {t:.2f}s\n")
        f.write(f"\nAverage: {avg_time:.2f}s\n")

# Summary
log("\n=== SUMMARY ===")
log(f"Total attempted runs:            {total}")
log(f"Successful:                      {successes}")
log(f"Failed:                          {failures}")
log(f"Skipped (not attempted):         {skips}")

log("\n--- Error Types ---")
for err_type, folders in error_types.items():
    log(f"{err_type} ({len(folders)}): {', '.join(folders)}")



