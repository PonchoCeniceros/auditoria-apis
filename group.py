import csv
import argparse
import re
from collections import defaultdict
import os


def normalize_endpoint(endpoint: str) -> str:
    """
    Returns the base endpoint without the last variable segment.
    Example: /api/items_stock/06-98419 -> /api/items_stock/
    """
    parts = endpoint.strip().split("/")
    if len(parts) <= 3:
        return endpoint if endpoint.endswith("/") else endpoint + "/"
    base = "/".join(parts[:-1]) + "/"
    return base


def extract_date_from_filename(filename: str):
    """Extracts YYYY-MM-DD date from a filename like 'auditoria_2025-11-28.csv'."""
    match = re.search(r"(\d{4}-\d{2}-\d{2})", filename)
    return match.group(1) if match else None


def main():
    parser = argparse.ArgumentParser(
        description="Consolidates endpoint performance data from all audit files in a directory."
    )
    parser.add_argument(
        "--input-dir",
        required=True,
        help="Path to the directory containing audit CSV files (e.g., audits/auditoria_main_2025-11-28).",
    )
    args = parser.parse_args()

    if not os.path.isdir(args.input_dir):
        print(f"Error: Provided path '{args.input_dir}' is not a valid directory.")
        return

    all_rows = []
    print(f"📂 Scanning directory: {args.input_dir}")

    for filename in sorted(os.listdir(args.input_dir)):
        # Process only raw audit CSV files
        if filename.startswith("auditoria_") and filename.endswith(".csv"):
            file_date = extract_date_from_filename(filename)
            if not file_date:
                print(f"  -> Warning: Could not extract date from '{filename}'. Skipping.")
                continue

            print(f"  -> Processing file: {filename} for date {file_date}")
            full_path = os.path.join(args.input_dir, filename)
            
            try:
                # Data structure for the current file's aggregation
                file_aggregator = defaultdict(lambda: {'total_hits': 0, 'sum_duration': 0.0, 'sum_backend': 0.0})

                with open(full_path, "r", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    header = next(reader, None)
                    # Expecting header: endpoint, count, avg_total_duration, avg_backend_time
                    if not header or len(header) != 4:
                         print(f"    -> Warning: Unexpected header '{header}'. Skipping.")
                         continue

                    for row in reader:
                        if len(row) != 4:
                            continue
                        
                        endpoint, count_str, avg_duration_str, avg_backend_str = row
                        try:
                            count = int(count_str)
                            avg_duration = float(avg_duration_str)
                            avg_backend = float(avg_backend_str)
                            
                            base_endpoint = normalize_endpoint(endpoint)
                            
                            # Update stats for the base_endpoint
                            stats = file_aggregator[base_endpoint]
                            stats['total_hits'] += count
                            # Calculate total times by multiplying average by count
                            stats['sum_duration'] += avg_duration * count
                            stats['sum_backend'] += avg_backend * count

                        except ValueError:
                            continue
                
                # After processing the file, calculate averages and add to the main list
                for base_endpoint, stats in file_aggregator.items():
                    total_hits = stats['total_hits']
                    avg_total_duration = round(stats['sum_duration'] / total_hits, 3) if total_hits > 0 else 0
                    avg_backend_time = round(stats['sum_backend'] / total_hits, 3) if total_hits > 0 else 0
                    all_rows.append([base_endpoint, total_hits, avg_total_duration, avg_backend_time, file_date])

            except Exception as e:
                print(f"    -> ERROR: Failed to process file: {e}. Skipping.")

    if not all_rows:
        print("No data was processed. No output file will be generated.")
        return

    # Determine output file path
    input_dir_name = os.path.basename(os.path.normpath(args.input_dir))
    parent_dir = os.path.dirname(os.path.normpath(args.input_dir))
    output_filename = os.path.join(parent_dir, f"consolidado_{input_dir_name}.csv")

    # Save consolidated result
    with open(output_filename, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["endpoint_base", "total_hits", "avg_total_duration", "avg_backend_time", "date"])
        # Sort by date, then by total hits descending
        writer.writerows(sorted(all_rows, key=lambda x: (x[4], -x[1])))

    print(f"\n✅ Consolidated performance file generated: {output_filename}")


if __name__ == "__main__":
    main()
