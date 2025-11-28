import csv
from collections import Counter
from pathlib import Path

INPUT_FILE = "auditoria_2025-11-26.csv"
OUTPUT_FILE = "agrupado.csv"


def normalize_endpoint(endpoint: str) -> str:
    """
    Devuelve el endpoint base sin el último segmento variable.
    Ejemplo: /api/items_stock/06-98419 → /api/items_stock/
    """
    parts = endpoint.strip().split("/")
    if len(parts) <= 3:
        # No tiene un resource variable → se queda igual
        return endpoint if endpoint.endswith("/") else endpoint + "/"

    # Quitar el último segmento variable
    base = "/".join(parts[:-1]) + "/"
    return base


def main():
    counter = Counter()

    print(f"🔍 Procesando archivo: {INPUT_FILE}")

    # Leer CSV
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) != 2:
                continue

            endpoint, count = row
            try:
                count = int(count)
            except ValueError:
                continue  # ignorar filas inválidas

            base_endpoint = normalize_endpoint(endpoint)
            counter[base_endpoint] += count

    # Guardar resultado
    with open(OUTPUT_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["endpoint_base", "total"])

        for endpoint, total in counter.most_common():
            writer.writerow([endpoint, total])

    print(f"📁 Archivo generado: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
