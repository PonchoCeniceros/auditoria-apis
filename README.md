# API Audit

Nginx log auditing tool for analyzing API endpoint performance.

## Requirements

- Python 3.14+
- Access to Nginx logs (`/var/log/nginx`)

## Usage

### Analyze Logs

```bash
# Using default routes (./routes/main.txt)
python3 audit.py

# Using custom routes file
python3 audit.py --routes-file ./routes/hana.txt
python3 audit.py --routes-file ./routes/shopify.txt
python3 audit.py --routes-file ./routes/shopify_hana.txt
python3 audit.py --routes-file ./routes/ftapi.txt
python3 audit.py --routes-file ./routes/ftapi_hana.txt
```

### Consolidate Results

```bash
python3 group.py --input-dir audits/auditoria_main_2025-12-02
```

## Route Files

| File | Description |
|------|-------------|
| `routes/main.txt` | Main API endpoints |
| `routes/hana.txt` | HANA-specific endpoints |
| `routes/shopify.txt` | Shopify API endpoints |
| `routes/shopify_hana.txt` | Shopify HANA endpoints |
| `routes/ftapi.txt` | FT-API Node.js endpoints |
| `routes/ftapi_hana.txt` | FT-API HANA endpoints |

## Output

- Daily reports: `audits/auditoria_<route>_<date>/auditoria_<date>.csv`
- Consolidated: `audits/consolidado_auditoria_<route>_<date>.csv`
