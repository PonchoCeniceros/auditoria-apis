import os
import re
import csv
import gzip
import argparse
import locale
from datetime import datetime
from collections import defaultdict

# Set locale for parsing month names
try:
    locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')
except locale.Error:
    print("Warning: Locale 'en_US.UTF-8' not available, date parsing may fail.")

LOG_PATH = "/var/log/nginx"

# Regex to extract date, method, path, total duration, and backend time
log_data_regex = re.compile(
    r'.*?\[(?P<date>\d{2}/\w{3}/\d{4}):[^\s]+ .*?\] '
    r'"(?P<method>\w+) (?P<path>[^ ]+).*?" \d+ \d+ '
    r'(?P<duration>[\d.]+) (?P<backend_time>[\d.]+)'
)


def read_log_file(file_path):
    """Reads log files, gzipped or plain text, line by line."""
    if file_path.endswith(".gz"):
        with gzip.open(file_path, "rt", errors="ignore") as f:
            yield from f
    else:
        with open(file_path, "r", errors="ignore") as f:
            yield from f


def extract_log_data(line):
    """Extracts date, endpoint, and performance metrics from a log line."""
    match = log_data_regex.match(line)
    if not match:
        return None

    data = match.groupdict()
    try:
        date_obj = datetime.strptime(data['date'], "%d/%b/%Y").date()
        endpoint = data['path'].split("?")[0]
        duration = float(data['duration'])
        backend_time = float(data['backend_time'])
        return date_obj, endpoint, duration, backend_time
    except (ValueError, KeyError):
        return None


def load_prefixes(routes_file):
    """Loads endpoint prefixes from the specified file."""
    if not os.path.exists(routes_file):
        print(f"ERROR: Routes file not found at {routes_file}")
        exit(1)
    with open(routes_file, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def matches_prefix(endpoint, prefixes):
    """Checks if an endpoint starts with any of the loaded prefixes."""
    return any(endpoint.startswith(pref) for pref in prefixes)


def get_unique_dir(base_name, parent_dir="."):
    """Creates a unique directory name, appending a suffix if necessary."""
    full_base_path = os.path.join(parent_dir, base_name)
    dir_name = full_base_path
    counter = 1
    while os.path.exists(dir_name):
        dir_name = f"{full_base_path}_{counter}"
        counter += 1
    return dir_name


def main():
    parser = argparse.ArgumentParser(
        description="Analyzes Nginx logs for daily endpoint performance."
    )
    parser.add_argument(
        "--routes-file",
        default="./routes/main.txt",
        help="File with endpoint prefixes to audit.",
    )
    args = parser.parse_args()

    prefixes = load_prefixes(args.routes_file)
    # New data structure to hold count and summed times
    daily_data = defaultdict(lambda: defaultdict(lambda: {'count': 0, 'total_duration': 0.0, 'backend_time': 0.0}))

    print("🔍 Processing log files...")
    for filename in sorted(os.listdir(LOG_PATH)):
        if filename.startswith("access.log"):
            full_path = os.path.join(LOG_PATH, filename)
            for line in read_log_file(full_path):
                result = extract_log_data(line)
                if result:
                    log_date, endpoint, duration, backend_time = result
                    if endpoint and matches_prefix(endpoint, prefixes):
                        stats = daily_data[log_date][endpoint]
                        stats['count'] += 1
                        stats['total_duration'] += duration
                        stats['backend_time'] += backend_time

    if not daily_data:
        print("No matching log entries found.")
        return

    today_str = datetime.now().strftime("%Y-%m-%d")
    routes_file_base = os.path.splitext(os.path.basename(args.routes_file))[0]
    dir_base_name = f"auditoria_{routes_file_base}_{today_str}"
    
    output_dir = get_unique_dir(dir_base_name, parent_dir="audits")
    os.makedirs(output_dir)
    print(f"📁 Report directory created: {output_dir}")

    for log_date, endpoints in sorted(daily_data.items()):
        date_str = log_date.strftime('%Y-%m-%d')
        output_filename = os.path.join(output_dir, f"auditoria_{date_str}.csv")
        
        # Prepare data for sorting and writing
        output_rows = []
        for endpoint, stats in endpoints.items():
            count = stats['count']
            avg_duration = stats['total_duration'] / count if count > 0 else 0
            avg_backend_time = stats['backend_time'] / count if count > 0 else 0
            output_rows.append([endpoint, count, avg_duration, avg_backend_time])
        
        # Sort by count descending
        output_rows.sort(key=lambda x: x[1], reverse=True)

        with open(output_filename, "w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["endpoint", "count", "avg_total_duration", "avg_backend_time"])
            writer.writerows(output_rows)

        print(f"  -> Daily performance report generated: {output_filename}")

    print("\n✅ Process completed successfully.")


if __name__ == "__main__":
    main()
