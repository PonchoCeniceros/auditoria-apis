import csv
import argparse
import re
from collections import Counter
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
        description="Consolidates endpoint counts from all audit files in a directory."
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
                with open(full_path, "r", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    next(reader, None)  # Skip header
                    
                    # Group within the file first
                    file_counter = Counter()
                    for row in reader:
                        if len(row) != 2:
                            continue
                        endpoint, count_str = row
                        try:
                            count = int(count_str)
                            base_endpoint = normalize_endpoint(endpoint)
                            file_counter[base_endpoint] += count
                        except ValueError:
                            continue
                    
                    # Add file's grouped data to the main list
                    for endpoint, total in file_counter.items():
                        all_rows.append([endpoint, total, file_date])

            except Exception as e:
                print(f"    -> ERROR: Failed to process file: {e}. Skipping.")

    if not all_rows:
        print("No data was processed. No output file will be generated.")
        return

    # Determine output file path
    # Saves the consolidated file in the *same* directory as the input directory
    # e.g., if input is audits/run1/, output is audits/consolidado_run1.csv
    input_dir_name = os.path.basename(os.path.normpath(args.input_dir))
    parent_dir = os.path.dirname(os.path.normpath(args.input_dir))
    output_filename = os.path.join(parent_dir, f"consolidado_{input_dir_name}.csv")

    # Save consolidated result
    with open(output_filename, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["endpoint_base", "total", "date"])
        writer.writerows(sorted(all_rows, key=lambda x: (x[2], x[0]))) # Sort by date, then endpoint

    print(f"\n✅ Consolidated file generated: {output_filename}")


if __name__ == "__main__":
    main()
