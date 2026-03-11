# API Audit - Agent Guidelines

## Project Overview

Nginx log auditing tool for analyzing API endpoint performance. Processes access logs to generate daily performance reports and consolidates data across multiple dates.

**Main Scripts:**
- `audit.py` - Analyzes Nginx logs and generates daily endpoint performance reports
- `group.py` - Consolidates audit files by normalizing endpoints and aggregating metrics

**Tech Stack:** Python 3.14.3 (standard library only)

## Commands

### Running the Audit
```bash
# Analyze logs with default routes file (./routes/main.txt)
python3 audit.py

# Analyze logs with custom routes file
python3 audit.py --routes-file ./routes/hana.txt
```

### Consolidating Results
```bash
# Consolidate audit files from a directory
python3 group.py --input-dir audits/auditoria_main_2025-12-02
```

### Testing
No test suite is currently configured. When adding tests, place them in the project root with naming pattern `test_*.py` or `*_test.py`.

## Code Style Guidelines

### Imports
Standard library only. Group imports logically:
```python
import os
import re
import csv
import gzip
import argparse
import locale
from datetime import datetime
from collections import defaultdict
```

**Order:** Built-in modules first, then from-imports alphabetically.

### Type Hints
Optional but encouraged for function signatures:
```python
def normalize_endpoint(endpoint: str) -> str:
def extract_date_from_filename(filename: str):
```

Use type hints when they clarify complex data structures or return types.

### Naming Conventions
- **Functions/Variables:** `snake_case` (e.g., `extract_log_data`, `file_path`)
- **Constants:** `UPPER_SNAKE_CASE` (e.g., `LOG_PATH`, `log_data_regex`)
- **Private functions:** Prefix with underscore if intended as internal
- **Boolean variables:** Use `is_`, `has_`, `matches_` prefixes when appropriate

### Documentation
All functions must have docstrings:
```python
def read_log_file(file_path):
    """Reads log files, gzipped or plain text, line by line."""
    
def normalize_endpoint(endpoint: str) -> str:
    """
    Returns the base endpoint without the last variable segment.
    Example: /api/items_stock/06-98419 -> /api/items_stock/
    """
```

Use single-line docstrings for simple functions, multi-line for complex ones with examples.

### Error Handling
- Use try/except blocks for operations that may fail
- Provide clear error messages
- Graceful degradation when possible
```python
try:
    locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')
except locale.Error:
    print("Warning: Locale 'en_US.UTF-8' not available, date parsing may fail.")
```

- Exit with error code for critical failures: `exit(1)`
- Continue processing on non-critical errors with warning messages

### File I/O
Always use `with` statements for file operations:
```python
# Reading files
with open(file_path, "r", encoding="utf-8") as f:
    # process file

# Writing CSV
with open(output_filename, "w", encoding="utf-8", newline="") as file:
    writer = csv.writer(file)
    writer.writerow([...])
```

Always specify encoding explicitly (`encoding="utf-8"`). Use `errors="ignore"` for reading potentially corrupted log files.

### String Formatting
Use f-strings for string interpolation:
```python
print(f"ERROR: Routes file not found at {routes_file}")
print(f"  -> Processing file: {filename} for date {file_date}")
```

### Functions
- Keep functions small and focused (single responsibility)
- Use descriptive parameter names
- Return early for error conditions
- Use generator functions (`yield`) for large datasets:
```python
def read_log_file(file_path):
    """Reads log files, gzipped or plain text, line by line."""
    if file_path.endswith(".gz"):
        with gzip.open(file_path, "rt", errors="ignore") as f:
            yield from f
    else:
        with open(file_path, "r", errors="ignore") as f:
            yield from f
```

### Command-Line Interfaces
Use `argparse` for all CLI scripts:
```python
parser = argparse.ArgumentParser(
    description="Analyzes Nginx logs for daily endpoint performance."
)
parser.add_argument(
    "--routes-file",
    default="./routes/main.txt",
    help="File with endpoint prefixes to audit.",
)
args = parser.parse_args()
```

Always provide:
- Description in the parser
- Default values when appropriate
- Help text for all arguments

### User Feedback
Use emoji for visual feedback in console output:
- 🔍 Processing/scanning
- 📁 Directory/file creation
- 📂 Directory scanning
- ✅ Success
- ❌ Error (or use "ERROR:" prefix)

```python
print("🔍 Processing log files...")
print(f"📁 Report directory created: {output_dir}")
print(f"✅ Consolidated performance file generated: {output_filename}")
```

## Project-Specific Patterns

### Log File Processing
Support both compressed and plain text logs:
```python
def read_log_file(file_path):
    if file_path.endswith(".gz"):
        with gzip.open(file_path, "rt", errors="ignore") as f:
            yield from f
    else:
        with open(file_path, "r", errors="ignore") as f:
            yield from f
```

Always handle encoding errors gracefully with `errors="ignore"`.

### Regex Patterns
Pre-compile regex for performance:
```python
log_data_regex = re.compile(
    r'.*?\[(?P<date>\d{2}/\w{3}/\d{4}):[^\s]+ .*?\] '
    r'"(?P<method>\w+) (?P<path>[^ ]+).*?" \d+ \d+ '
    r'(?P<duration>[\d.]+) (?P<backend_time>[\d.]+)'
)
```

Use named groups (`?P<name>`) for clarity.

### Data Aggregation
Use `defaultdict` with lambda factories for nested data structures:
```python
daily_data = defaultdict(
    lambda: defaultdict(
        lambda: {'count': 0, 'total_duration': 0.0, 'backend_time': 0.0}
    )
)
```

This avoids key existence checks and provides clean default values.

### Date Handling
Parse dates with `strptime`, format with `strftime`:
```python
# Parsing
date_obj = datetime.strptime(data['date'], "%d/%b/%Y").date()

# Formatting
date_str = log_date.strftime('%Y-%m-%d')
today_str = datetime.now().strftime("%Y-%m-%d")
```

### CSV Operations
Use `csv` module with proper encoding:
```python
# Reading
with open(full_path, "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    header = next(reader, None)
    for row in reader:
        # process row

# Writing
with open(output_filename, "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["endpoint", "count", "avg_total_duration", "avg_backend_time"])
    writer.writerows(output_rows)
```

Always use `newline=""` when writing CSV to prevent blank lines on Windows.

### File Naming Conventions
- **Audit reports:** `auditoria_YYYY-MM-DD.csv`
- **Consolidated reports:** `consolidado_auditoria_<route>_<date>.csv`
- **Audit directories:** `auditoria_<route>_<date>` (with suffix `_1`, `_2` if exists)

```python
dir_base_name = f"auditoria_{routes_file_base}_{today_str}"
output_dir = get_unique_dir(dir_base_name, parent_dir="audits")
```

### Route Files
Load endpoint prefixes from text files in `routes/`:
```python
def load_prefixes(routes_file):
    if not os.path.exists(routes_file):
        print(f"ERROR: Routes file not found at {routes_file}")
        exit(1)
    with open(routes_file, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]
```

Check file existence before reading. Filter empty lines and strip whitespace.

### Endpoint Normalization
Remove variable segments from endpoints to group similar paths:
```python
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
```

### Sorting Data
Sort output by meaningful metrics:
```python
# Sort by count descending
output_rows.sort(key=lambda x: x[1], reverse=True)

# Sort by date, then by total hits descending
writer.writerows(sorted(all_rows, key=lambda x: (x[4], -x[1])))
```

## File Organization

```
api_audit/
├── audit.py              # Main audit script
├── group.py              # Consolidation script
├── routes/               # Route prefix configuration
│   ├── main.txt          # Main API routes
│   └── hana.txt          # HANA-specific routes
└── audits/               # Generated reports (gitignored)
    ├── auditoria_main_YYYY-MM-DD/
    │   └── auditoria_YYYY-MM-DD.csv
    └── consolidado_auditoria_main_YYYY-MM-DD.csv
```

## Best Practices

1. **Check file/directory existence** before reading or processing
2. **Handle encoding explicitly** - always use `encoding="utf-8"`
3. **Provide clear error messages** - explain what went wrong and where
4. **Use descriptive variable names** - avoid single letters except for simple loops
5. **Comment complex logic only** - prefer self-documenting code
6. **Follow PEP 8 basics** - 4 spaces indentation, max line length ~100
7. **Process data in streams** - use generators for large files
8. **Validate input data** - check row lengths, parse errors, missing values
9. **Round floating point results** - use `round(value, 3)` for display
10. **Protect against division by zero** - always check `if count > 0`

## Common Tasks

### Adding a New Route File
1. Create text file in `routes/` directory
2. Add one endpoint prefix per line
3. Run audit with `--routes-file` argument

### Modifying Log Regex
Update `log_data_regex` in `audit.py` if log format changes. Maintain named groups for clarity.

### Processing Different Date Ranges
The script processes all files matching `access.log*` in `/var/log/nginx`. Control date range by managing which log files are present.

## Environment Notes

- **Python Version:** 3.14.3
- **Log Path:** `/var/log/nginx` (hardcoded in `audit.py`)
- **Dependencies:** Standard library only (no pip install required)
- **Platform:** Cross-platform (tested on macOS, Linux)
