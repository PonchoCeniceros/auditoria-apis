import csv
import argparse
from collections import Counter
from pathlib import Path

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
    parser = argparse.ArgumentParser(
        description="Agrupa y cuenta los endpoints de un archivo de auditoría."
    )
    parser.add_argument(
        "--input-file",
        required=True,
        help="Ruta al archivo de auditoría CSV (ej: audits/auditoria_2025-11-28.csv)",
    )
    args = parser.parse_args()

    counter = Counter()

    print(f"🔍 Procesando archivo: {args.input_file}")

    # Leer CSV
    with open(args.input_file, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)  # Saltar la cabecera
        for row in reader:
            if len(row) != 2:
                continue

            endpoint, count_str = row
            try:
                count = int(count_str)
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
