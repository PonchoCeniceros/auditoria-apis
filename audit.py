import os
import re
import csv
import gzip
from datetime import datetime
from collections import Counter

LOG_PATH = "/var/log/nginx"
ROUTES_FILE = "./routes/main.txt"  # Archivo externo con prefijos

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


def load_prefixes():
    """Carga prefijos desde el archivo routes_list.txt"""
    prefixes = []
    if not os.path.exists(ROUTES_FILE):
        print(f"ERROR: No se encontró el archivo {ROUTES_FILE}")
        exit(1)

    with open(ROUTES_FILE, "r", encoding="utf-8") as f:
        for line in f:
            clean = line.strip()
            if clean:
                prefixes.append(clean)

    return prefixes


def matches_prefix(endpoint, prefixes):
    """Devuelve True si el endpoint empieza con alguno de los prefijos"""
    return any(endpoint.startswith(pref) for pref in prefixes)


def main():
    prefixes = load_prefixes()
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
    output_filename = f"auditoria_{today}.csv"

    total_hits = sum(counter.values())

    with open(output_filename, "w", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["endpoint", "count"])

        for endpoint, count in counter.most_common():
            writer.writerow([endpoint, count])

    """
    with open(output_filename, "w", encoding="utf-8") as file:
        file.write("===== Frecuencia de endpoints seleccionados =====\n\n")
        file.write(f"Total de hits filtrados: {total_hits}\n\n")

        for endpoint, count in counter.most_common():
            file.write(f"{endpoint:50} {count}\n")
    """

    print(f"\nReporte generado: {output_filename}\n")


if __name__ == "__main__":
    main()
