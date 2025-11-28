import os
import re
import csv
import gzip
import argparse
from datetime import datetime
from collections import Counter

LOG_PATH = "/var/log/nginx"

# Regex para extraer método y endpoint
request_regex = re.compile(r'"(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS) ([^ ]+)')


def read_log_file(file_path):
    """Lee logs normales y .gz"""
    if file_path.endswith(".gz"):
        with gzip.open(file_path, "rt", errors="ignore") as f:
            for line in f:
                yield line
    else:
        with open(file_path, "r", errors="ignore") as f:
            for line in f:
                yield line


def extract_endpoint(line):
    """Extrae el endpoint y quita query params"""
    match = request_regex.search(line)
    if not match:
        return None

    method, path = match.groups()
    return path.split("?")[0]  # quitar parámetros


def load_prefixes(routes_file):
    """Carga prefijos desde un archivo de rutas"""
    prefixes = []
    if not os.path.exists(routes_file):
        print(f"ERROR: No se encontró el archivo {routes_file}")
        exit(1)

    with open(routes_file, "r", encoding="utf-8") as f:
        for line in f:
            clean = line.strip()
            if clean:
                prefixes.append(clean)

    return prefixes


def matches_prefix(endpoint, prefixes):
    """Devuelve True si el endpoint empieza con alguno de los prefijos"""
    return any(endpoint.startswith(pref) for pref in prefixes)


def main():
    parser = argparse.ArgumentParser(
        description="Analiza logs de Nginx y cuenta hits a endpoints específicos."
    )
    parser.add_argument(
        "--routes-file",
        default="./routes/main.txt",
        help="Archivo con la lista de prefijos de rutas a auditar.",
    )
    args = parser.parse_args()

    prefixes = load_prefixes(args.routes_file)
    counter = Counter()

    for filename in sorted(os.listdir(LOG_PATH)):
        if filename.startswith("access.log"):
            full_path = os.path.join(LOG_PATH, filename)

            for line in read_log_file(full_path):
                endpoint = extract_endpoint(line)
                if endpoint and matches_prefix(endpoint, prefixes):
                    counter[endpoint] += 1

    # Crear archivo con fecha
    today = datetime.now().strftime("%Y-%m-%d")
    output_filename = os.path.join("audits", f"auditoria_{today}.csv")  # Modified line

    # Ensure the 'audits' directory exists
    os.makedirs("audits", exist_ok=True)  # Added line

    with open(output_filename, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["endpoint", "count"])

        for endpoint, count in counter.most_common():
            writer.writerow([endpoint, count])

    print(f"\nReporte generado: {output_filename}\n")


if __name__ == "__main__":
    main()
