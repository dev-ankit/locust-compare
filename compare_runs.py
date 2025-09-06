#!/usr/bin/env python3
import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re


NUMERIC_FIELDS = {
    "Request Count",
    "Failure Count",
    "Median Response Time",
    "Average Response Time",
    "Min Response Time",
    "Max Response Time",
    "Average Content Size",
    "Requests/s",
    "Failures/s",
    # Percentile columns (if present)
    "50%",
    "66%",
    "75%",
    "80%",
    "90%",
    "95%",
    "98%",
    "99%",
    "99.9%",
    "99.99%",
    "100%",
}


@dataclass(frozen=True)
class Row:
    name: str
    type: str
    data: Dict[str, float]


def _as_float(value: str) -> Optional[float]:
    if value is None:
        return None
    value = value.strip()
    if value == "":
        return None
    try:
        # Most values are numeric; ints are fine as floats too
        return float(value)
    except ValueError:
        return None


def load_report(path: Path) -> List[Row]:
    """Load a Locust report.csv and return parsed rows.

    If `path` is a directory, attempts to read `path / 'report.csv'`.
    If `path` is a file, uses it directly.
    """
    report_path = path
    if path.is_dir():
        candidate = path / "report.csv"
        if not candidate.exists():
            raise FileNotFoundError(f"report.csv not found in directory: {path}")
        report_path = candidate
    elif path.is_file():
        if path.name != "report.csv" and not path.name.endswith(".csv"):
            raise ValueError(f"Provided file does not look like a CSV report: {path}")
    else:
        raise FileNotFoundError(f"Path not found: {path}")

    rows: List[Row] = []
    with report_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            name = (raw.get("Name") or "").strip()
            rtype = (raw.get("Type") or "").strip()
            data: Dict[str, float] = {}
            for k, v in raw.items():
                if k in ("Name", "Type"):
                    continue
                if k in NUMERIC_FIELDS:
                    fv = _as_float(v)
                    if fv is not None:
                        data[k] = fv
            rows.append(Row(name=name, type=rtype, data=data))
    return rows


def index_rows(rows: List[Row]) -> Dict[str, Row]:
    """Index rows by their name, with a synthetic key '__Aggregated__' for the Aggregated row."""
    idx: Dict[str, Row] = {}
    for r in rows:
        key = "__Aggregated__" if r.name == "Aggregated" else r.name
        idx[key] = r
    return idx


def _extract_template_args(html_text: str) -> Optional[dict]:
    """Extract JSON assigned to window.templateArgs in a Locust HTML file.

    Uses a brace-matching approach to safely capture the JSON object.
    Returns a parsed dict or None if not found/invalid.
    """
    # Prefer the explicit assignment form
    m = re.search(r"window\.templateArgs\s*=\s*\{", html_text)
    if not m:
        return None
    brace_start = m.start() + m.group(0).rfind("{")
    if brace_start == -1:
        return None
    # Match braces to find the end of the JSON object
    depth = 0
    i = brace_start
    while i < len(html_text):
        ch = html_text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(html_text[brace_start : i + 1])
                except Exception:
                    return None
        i += 1
    return None


def load_html_feature_rows(dir_path: Path) -> Dict[str, Row]:
    """Parse per-feature Locust HTML pages for summary metrics.

    Returns a mapping from feature name (file stem) to Row containing fields:
    - Requests/s (from latest history.current_rps)
    - Average Response Time (from latest history.total_avg_response_time)
    - 50% (from latest history.response_time_percentile_0.5)
    - 95% (from latest history.response_time_percentile_0.95)
    """
    rows: Dict[str, Row] = {}
    if not dir_path.is_dir():
        return rows
    for html_path in dir_path.glob("*.html"):
        # Skip wrapper/aux pages that aren't feature dashboards
        if html_path.name in {"htmlpublisher-wrapper.html"}:
            continue
        try:
            text = html_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        tmpl = _extract_template_args(text)
        if not tmpl:
            continue
        history = tmpl.get("history") or []
        if not history:
            continue
        # Choose last sample with non-null metrics
        last = None
        for item in reversed(history):
            if (
                isinstance(item, dict)
                and item.get("current_rps") is not None
                and item.get("total_avg_response_time") is not None
            ):
                last = item
                break
        if not last:
            continue
        data: Dict[str, float] = {}
        def set_if_float(key_out: str, key_in: str):
            v = last.get(key_in)
            if isinstance(v, (int, float)):
                data[key_out] = float(v)

        set_if_float("Requests/s", "current_rps")
        set_if_float("Average Response Time", "total_avg_response_time")
        set_if_float("50%", "response_time_percentile_0.5")
        set_if_float("95%", "response_time_percentile_0.95")

        feature_name = html_path.stem
        rows[feature_name] = Row(name=feature_name, type="HTML", data=data)
    return rows


def pct_change(base: Optional[float], curr: Optional[float]) -> Optional[float]:
    if base is None or curr is None:
        return None
    if base == 0:
        return None
    return (curr - base) / base * 100.0


def diff(base: Optional[float], curr: Optional[float]) -> Optional[float]:
    if base is None or curr is None:
        return None
    return curr - base


def format_number(v: Optional[float]) -> str:
    if v is None:
        return "-"
    # Heuristic: show integers without decimals when close to int
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    # Else show with up to 3 decimals
    return f"{v:.3f}"


def print_section(title: str):
    print("")
    print(title)
    print("-" * len(title))


def render_comparison(
    base_row: Optional[Row], curr_row: Optional[Row], important_fields: List[str]
):
    headers = [
        "Metric",
        "Base",
        "Current",
        "Diff",
        "% Change",
    ]
    rows: List[List[str]] = []

    base_data = base_row.data if base_row else {}
    curr_data = curr_row.data if curr_row else {}

    fields = important_fields[:]
    # Also include any extra percentile columns present in data
    extra_fields = [k for k in curr_data.keys() | base_data.keys() if k.endswith("%") and k not in fields]
    fields.extend(sorted(extra_fields))

    for field in fields:
        b = base_data.get(field)
        c = curr_data.get(field)
        d = diff(b, c)
        p = pct_change(b, c)
        p_str = "-" if p is None else f"{p:+.1f}%"
        rows.append([
            field,
            format_number(b),
            format_number(c),
            ("-" if d is None else (f"{d:+.3f}" if abs(d - round(d)) > 1e-9 else f"{int(d):+d}")),
            p_str,
        ])

    # Determine column widths
    widths = [max(len(h), *(len(r[i]) for r in rows)) for i, h in enumerate(headers)]

    # Print header
    header_line = "  ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    sep_line = "  ".join("-" * widths[i] for i in range(len(headers)))
    print(header_line)
    print(sep_line)
    for r in rows:
        print("  ".join(r[i].ljust(widths[i]) for i in range(len(headers))))


def compare_reports(base_path: Path, curr_path: Path, as_json: bool = False) -> int:
    base_rows = load_report(base_path)
    curr_rows = load_report(curr_path)

    base_idx = index_rows(base_rows)
    curr_idx = index_rows(curr_rows)

    all_keys = sorted(set(base_idx.keys()) | set(curr_idx.keys()))

    important_fields = [
        "Requests/s",
        "Request Count",
        "Failure Count",
        "Average Response Time",
        "Median Response Time",
        "Min Response Time",
        "Max Response Time",
        "95%",
    ]

    # Also parse per-feature HTML pages if directories are given
    base_html_rows = load_html_feature_rows(base_path if base_path.is_dir() else base_path.parent)
    curr_html_rows = load_html_feature_rows(curr_path if curr_path.is_dir() else curr_path.parent)

    if as_json:
        # Produce a structured JSON dict
        out: Dict[str, Dict[str, Dict[str, Optional[float]]]] = {}
        for key in all_keys:
            b = base_idx.get(key)
            c = curr_idx.get(key)
            # Combine fields present
            fields = set(important_fields)
            if b:
                fields.update(b.data.keys())
            if c:
                fields.update(c.data.keys())
            entry: Dict[str, Dict[str, Optional[float]]] = {}
            for f in sorted(fields):
                bb = b.data.get(f) if b else None
                cc = c.data.get(f) if c else None
                entry[f] = {
                    "base": bb,
                    "current": cc,
                    "diff": diff(bb, cc),
                    "pct_change": pct_change(bb, cc),
                }
            out[key] = entry
        # Add HTML features
        html_keys = sorted(set(base_html_rows.keys()) | set(curr_html_rows.keys()))
        for key in html_keys:
            b = base_html_rows.get(key)
            c = curr_html_rows.get(key)
            fields = set(important_fields)
            if b:
                fields.update(b.data.keys())
            if c:
                fields.update(c.data.keys())
            entry: Dict[str, Dict[str, Optional[float]]] = {}
            for f in sorted(fields):
                bb = b.data.get(f) if b else None
                cc = c.data.get(f) if c else None
                entry[f] = {
                    "base": bb,
                    "current": cc,
                    "diff": diff(bb, cc),
                    "pct_change": pct_change(bb, cc),
                }
            out[f"HTML:{key}"] = entry
        print(json.dumps(out, indent=2))
        return 0

    # Human readable output
    print_section("Aggregated")
    render_comparison(base_idx.get("__Aggregated__"), curr_idx.get("__Aggregated__"), important_fields)

    endpoint_keys = [k for k in all_keys if k != "__Aggregated__"]
    for ek in endpoint_keys:
        title = f"Endpoint: {ek}"
        print_section(title)
        render_comparison(base_idx.get(ek), curr_idx.get(ek), important_fields)

    # Render HTML features
    feature_keys = sorted(set(base_html_rows.keys()) | set(curr_html_rows.keys()))
    if feature_keys:
        print_section("HTML Features")
        for fk in feature_keys:
            print_section(f"Feature: {fk}")
            render_comparison(base_html_rows.get(fk), curr_html_rows.get(fk), important_fields)

    return 0


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Compare Locust performance reports between a base and current run.\n"
            "Provide either directories containing report.csv or direct CSV file paths."
        )
    )
    parser.add_argument("base", type=Path, help="Base run directory or report.csv path")
    parser.add_argument("current", type=Path, help="Current run directory or report.csv path")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()
    try:
        return compare_reports(args.base, args.current, as_json=args.json)
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
