import os
import re
import csv
import gzip
import argparse
import locale
from datetime import datetime
from collections import Counter, defaultdict

# Set locale to parse month names in English, crucial for log date parsing
try:
    locale.setlocale(locale.LC_TIME, "en_US.UTF-8")
except locale.Error:
    print(
        "Warning: Locale 'en_US.UTF-8' not available. Date parsing might fail if log month names are in English."
    )

LOG_PATH = "/var/log/nginx"

# Regex to extract date, method, and endpoint from a standard Nginx log line
log_data_regex = re.compile(
    r'.*?\[(\d{2}/\w{3}/\d{4}):\d{2}:\d{2}:\d{2} .*?\] "'
    r"(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS) ([^ ]+)"
)


def read_log_file(file_path):
    """Reads log files, including gzipped ones, line by line."""
    if file_path.endswith(".gz"):
        with gzip.open(file_path, "rt", errors="ignore") as f:
            yield from f
    else:
        with open(file_path, "r", errors="ignore") as f:
            yield from f


def extract_log_data(line):
    """Extracts date and endpoint from a log line, returning a date object and a string."""
    match = log_data_regex.match(line)
    if not match:
        return None, None

    date_str, _, path = match.groups()
    try:
        date_obj = datetime.strptime(date_str, "%d/%b/%Y").date()
    except ValueError:
        return None, None  # Ignore lines with malformed dates

    endpoint = path.split("?")[0]
    return date_obj, endpoint


def load_prefixes(routes_file):
    """Loads endpoint prefixes from the specified file."""
    prefixes = []
    if not os.path.exists(routes_file):
        print(f"ERROR: Routes file not found at {routes_file}")
        exit(1)

    with open(routes_file, "r", encoding="utf-8") as f:
        for line in f:
            clean = line.strip()
            if clean:
                prefixes.append(clean)
    return prefixes


def matches_prefix(endpoint, prefixes):
    """Checks if an endpoint matches any of the loaded prefixes."""
    return any(endpoint.startswith(pref) for pref in prefixes)


def get_unique_dir(base_name, parent_dir="."):
    """Creates a unique directory name by appending a suffix if the base name exists."""
    counter = 1
    # Prepend parent_dir to the base_name to ensure uniqueness within that parent
    full_base_path = os.path.join(parent_dir, base_name)
    dir_name = full_base_path
    while os.path.exists(dir_name):
        dir_name = f"{full_base_path}_{counter}"
        counter += 1
    return dir_name


def main():
    parser = argparse.ArgumentParser(
        description="Analyzes Nginx logs and generates daily endpoint hit reports."
    )
    parser.add_argument(
        "--routes-file",
        default="./routes/main.txt",
        help="File containing the list of endpoint prefixes to audit.",
    )
    args = parser.parse_args()

    prefixes = load_prefixes(args.routes_file)
    daily_counters = defaultdict(Counter)

    print("🔍 Processing log files...")
    for filename in sorted(os.listdir(LOG_PATH)):
        if filename.startswith("access.log"):
            full_path = os.path.join(LOG_PATH, filename)
            for line in read_log_file(full_path):
                log_date, endpoint = extract_log_data(line)
                if log_date and endpoint and matches_prefix(endpoint, prefixes):
                    daily_counters[log_date][endpoint] += 1

    if not daily_counters:
        print("No log entries found matching the specified criteria.")
        return

    today_str = datetime.now().strftime("%Y-%m-%d")
    routes_file_base = os.path.splitext(os.path.basename(args.routes_file))[0]
    dir_base_name = f"auditoria_{routes_file_base}_{today_str}"

    output_dir = get_unique_dir(dir_base_name, parent_dir="audits")
    os.makedirs(output_dir)
    print(f"📁 Report directory created: {output_dir}")

    for log_date, counter in sorted(daily_counters.items()):
        date_str = log_date.strftime("%Y-%m-%d")
        output_filename = os.path.join(output_dir, f"auditoria_{date_str}.csv")

        with open(output_filename, "w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["endpoint", "count"])
            for endpoint, count in counter.most_common():
                writer.writerow([endpoint, count])

        print(f"  -> Daily report generated: {output_filename}")

    print("\n✅ Process completed successfully.")


if __name__ == "__main__":
    main()
