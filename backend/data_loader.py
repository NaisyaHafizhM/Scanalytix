"""Robust data loader for Auto EDA Insight.

Handles CSV/TSV, TXT (delimited, ragged rows, or whitespace), Excel, and
JSON (single object/array, JSON Lines, concatenated objects, wrapped,
columnar, dict-of-dicts, nested) and always returns a clean, properly
tabular DataFrame so downstream EDA pages don't break.
"""
import json
import csv
import io
import re
from collections import Counter
import pandas as pd


def _reset(f):
    try:
        f.seek(0)
    except Exception:
        pass


def _decode(uploaded_file):
    _reset(uploaded_file)
    raw = uploaded_file.read()
    if isinstance(raw, bytes):
        for enc in ("utf-8-sig", "utf-8", "latin-1"):
            try:
                return raw.decode(enc)
            except Exception:
                continue
        return raw.decode("utf-8", errors="replace")
    return str(raw)


def _detect_delimiter(lines):
    """Pick the delimiter whose per-line occurrence count is most consistent
    across the sampled lines (robust even with quoted fields / ragged rows)."""
    candidates = [",", ";", "\t", "|", ":"]
    sample = [ln for ln in lines if ln.strip()][:30]
    if not sample:
        return None
    best_delim, best_score = None, 0
    for d in candidates:
        counts = [ln.count(d) for ln in sample]
        nonzero = [c for c in counts if c > 0]
        if not nonzero:
            continue
        mode_count, mode_freq = Counter(counts).most_common(1)[0]
        if mode_count == 0:
            continue
        score = mode_freq
        if score > best_score:
            best_score, best_delim = score, d
    return best_delim


def _rows_from_delimited_text(text, delim):
    """Parse with csv.reader (handles quoted fields correctly), then pad
    short rows / merge overflow fields on ragged rows so every row lines
    up with the header instead of producing a single garbled column."""
    reader = csv.reader(io.StringIO(text), delimiter=delim)
    rows = [r for r in reader if any(cell.strip() for cell in r)]
    if not rows:
        return None
    header = [c.strip() for c in rows[0]]
    ncols = len(header)
    if ncols < 2:
        return None
    clean_rows = []
    for r in rows[1:]:
        if len(r) < ncols:
            r = r + [None] * (ncols - len(r))
        elif len(r) > ncols:
            r = r[:ncols - 1] + [delim.join(r[ncols - 1:])]
        clean_rows.append(r)
    return pd.DataFrame(clean_rows, columns=header)


def _clean_dataframe(df):
    """Common post-processing so every loaded file is genuinely tabular:
    - flatten/stringify any leftover list/dict cell values
    - strip whitespace from string cells / normalize blank-like values to NaN
    - auto-convert numeric-looking text columns to real numeric dtype
    - dedupe/clean column names
    """
    if df is None:
        return df

    df = df.reset_index(drop=True)

    for col in df.columns:
        if df[col].dtype == object:
            if df[col].map(lambda v: isinstance(v, (list, dict))).any():
                df[col] = df[col].apply(
                    lambda v: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v
                )

    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].apply(lambda v: v.strip() if isinstance(v, str) else v)
            df[col] = df[col].replace({"": None, "nan": None, "NaN": None, "null": None, "None": None, "NULL": None})

    for col in df.columns:
        if df[col].dtype == object:
            coerced = pd.to_numeric(df[col], errors="coerce")
            non_null = df[col].notna()
            if non_null.sum() > 0 and coerced[non_null].notna().mean() >= 0.9:
                df[col] = coerced

    seen = {}
    new_cols = []
    for i, c in enumerate(df.columns):
        name = str(c).strip() or f"column_{i+1}"
        if name in seen:
            seen[name] += 1
            name = f"{name}_{seen[name]}"
        else:
            seen[name] = 0
        new_cols.append(name)
    df.columns = new_cols

    return df


def _try_read_fixed_width(text):
    """Handle 'pretty-printed' / aligned plain-text tables: decorative title
    lines, dashed separator rules, and columns lined up with runs of spaces
    instead of a real delimiter. Strips anything that isn't part of the
    actual table, then tokenizes each remaining line on whitespace."""
    lines = text.splitlines()
    decorative = re.compile(r"^[\s\-=_*~]+$")
    candidates = [ln for ln in lines if ln.strip() and not decorative.match(ln)]
    if len(candidates) < 2:
        return None

    tokenized = [re.split(r"\s+", ln.strip()) for ln in candidates]
    counts = [len(t) for t in tokenized]
    mode_count, freq = Counter(counts).most_common(1)[0]
    # require a real table shape (>=2 cols) backed by most of the lines,
    # so a stray title/caption line doesn't get treated as the header
    if mode_count < 2 or freq < max(2, len(candidates) * 0.5):
        return None

    matching = [t for t, c in zip(tokenized, counts) if c == mode_count]
    if len(matching) < 2:
        return None
    header, rows = matching[0], matching[1:]
    return pd.DataFrame(rows, columns=header)


def _try_read_csv(uploaded_file):
    """Multi-strategy delimited-text reader: detect a consistent delimiter
    and parse manually (handles quotes + ragged rows safely), falling back
    to a whitespace-aligned table reader, then pandas' own engines, and
    finally whitespace-delimited as a last resort."""
    text = _decode(uploaded_file)
    lines = text.splitlines()

    delim = _detect_delimiter(lines)
    if delim:
        try:
            df = _rows_from_delimited_text(text, delim)
            if df is not None and df.shape[1] > 1:
                return df
        except Exception:
            pass

    # Aligned/decorated text table (titles + dashed rules + space-padded cols)
    try:
        fw_df = _try_read_fixed_width(text)
        if fw_df is not None and fw_df.shape[1] > 1:
            return fw_df
    except Exception:
        pass

    # Fall back to pandas' own parsers
    last_err = None
    for kwargs in ({"sep": None, "engine": "python", "on_bad_lines": "skip"},
                    {"sep": ","}, {"sep": ";"}, {"sep": "\t"}, {"sep": "|"}):
        try:
            df = pd.read_csv(io.StringIO(text), **kwargs)
            if df is not None and df.shape[1] > 1:
                return df
        except Exception as e:
            last_err = e

    # Whitespace-delimited fallback (e.g. log-like / space separated data)
    try:
        df_ws = pd.read_csv(io.StringIO(text), sep=r"\s+", engine="python")
        if df_ws is not None and df_ws.shape[1] > 1:
            return df_ws
    except Exception as e:
        last_err = e

    raise last_err or ValueError("File tidak dapat dibaca sebagai data tabular.")


def _parse_json_text(text):
    """Parse JSON text, gracefully handling JSON Lines (one object per line)
    and concatenated JSON objects without a wrapping array/commas."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # JSON Lines: one JSON value per non-empty line
    records, ok = [], True
    for line in text.splitlines():
        line = line.strip().rstrip(",")
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            ok = False
            break
    if ok and records:
        return records

    # Concatenated JSON objects with no separators/newlines between them
    decoder = json.JSONDecoder()
    idx, n, records2 = 0, len(text), []
    while idx < n:
        while idx < n and text[idx] in " \t\r\n,":
            idx += 1
        if idx >= n:
            break
        try:
            obj, end = decoder.raw_decode(text, idx)
        except json.JSONDecodeError:
            break
        records2.append(obj)
        idx = end
    if records2:
        return records2

    raise ValueError("File JSON tidak valid / formatnya tidak dikenali.")


def _find_records_list(obj, depth=3):
    """Recursively search a parsed JSON value for the list-of-dicts that
    represents the 'real' tabular data, even when it's wrapped in metadata
    keys (e.g. {"meta": {...}, "data": [...]}) or nested a level or two
    deeper (e.g. {"response": {"results": [...]}}). Picks the largest such
    list found, so small metadata lists don't get mistaken for the table."""
    candidates = []

    def _walk(o, d):
        if d < 0:
            return
        if isinstance(o, list):
            if o and all(isinstance(item, dict) for item in o):
                candidates.append(o)
            return
        if isinstance(o, dict):
            for v in o.values():
                _walk(v, d - 1)

    _walk(obj, depth)
    if not candidates:
        return None
    return max(candidates, key=len)


def _json_to_dataframe(raw):
    """Smartly turn arbitrary parsed JSON into a clean tabular DataFrame."""
    if isinstance(raw, list):
        if len(raw) == 0:
            return pd.DataFrame()
        if all(isinstance(item, dict) for item in raw):
            return pd.json_normalize(raw, sep="_")
        return pd.DataFrame({"value": raw})

    if isinstance(raw, dict):
        # Wrapped/nested case first: {"meta": {...}, "data": [...]},
        # {"status": "ok", "response": {"results": [...]}}, etc.
        records = _find_records_list(raw)
        if records:
            return pd.json_normalize(records, sep="_")

        list_values = {k: v for k, v in raw.items() if isinstance(v, list)}

        # {"data": [...]}, {"results": [...]}, etc.
        if len(raw) == 1 and list_values:
            inner = next(iter(list_values.values()))
            if inner and all(isinstance(item, dict) for item in inner):
                return pd.json_normalize(inner, sep="_")
            return pd.DataFrame({next(iter(raw.keys())): inner})

        # Columnar dict-of-equal-length-lists: {"col1": [...], "col2": [...]}
        if list_values and len(list_values) == len(raw):
            lengths = {len(v) for v in list_values.values()}
            if len(lengths) == 1:
                return pd.DataFrame(raw)

        # Dict-of-dicts keyed by id: {"row1": {...}, "row2": {...}}
        dict_values = {k: v for k, v in raw.items() if isinstance(v, dict)}
        if len(dict_values) == len(raw) and len(raw) > 0:
            return pd.DataFrame.from_dict(raw, orient="index").reset_index().rename(columns={"index": "id"})

        # Single flat dict -> wrap as one-row table
        return pd.json_normalize([raw], sep="_")

    return pd.DataFrame({"value": [raw]})


def load_file(uploaded_file):
    """Returns (df, text_content, error_message). Tries hard not to crash for unknown tabular data."""
    name = getattr(uploaded_file, "name", "uploaded_file")
    ext = name.split(".")[-1].lower() if "." in name else "csv"
    df = None
    text_content = None
    error = None
    try:
        if ext in ("csv", "txt", "tsv"):
            try:
                df = _try_read_csv(uploaded_file)
            except Exception:
                text_content = _decode(uploaded_file)
                lines = [line for line in text_content.splitlines() if line.strip()]
                if lines:
                    split_rows = [re.split(r"\s+", line.strip()) for line in lines]
                    max_cols = max(len(r) for r in split_rows)
                    if max_cols > 1:
                        cols = [f"column_{i+1}" for i in range(max_cols)]
                        padded = [r + [None] * (max_cols - len(r)) for r in split_rows]
                        df = pd.DataFrame(padded, columns=cols)
                    else:
                        df = pd.DataFrame({"text": lines})
                else:
                    df = pd.DataFrame({"text": [text_content]})
        elif ext in ("xlsx", "xls"):
            _reset(uploaded_file)
            df = pd.read_excel(uploaded_file)
        elif ext == "json":
            text = _decode(uploaded_file)
            raw = _parse_json_text(text)
            df = _json_to_dataframe(raw)
        else:
            try:
                df = _try_read_csv(uploaded_file)
            except Exception as e:
                error = f"Format .{ext} belum didukung penuh dan gagal dibaca: {e}"

        if df is not None:
            df = _clean_dataframe(df)
    except Exception as e:
        error = str(e)
    return df, text_content, error
