#!/usr/bin/env python3
"""Extract Model 2 cross-category lag coefficients from ppml categories.docx to CSV."""

from __future__ import annotations

import argparse
import csv
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from movement_categories import (
    LAG_VAR_TO_TITLE,
    base_for_title,
    normalize_title,
)

W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

TABLE_HEADER_RE = re.compile(
    r"(Governance & Politics|Education|Labor|Human Rights & Identity|"
    r"Justice & Accountability|Security Conflict|Health & Social Welfare|"
    r"Religion & Belief|Prices & Economy|Public Services & Infrastructure|"
    r"International Solidarity & Foreign Policy|Environment|Agriculture & Rural|"
    r"Land, Property & Housing|Other)\(1\)\(2\)\(3\)\(4\)"
)

COEF_BLOCK_RE = re.compile(
    r"(-?\d+\.?\d*(?:e[+-]?\d+)?|\.\d+)(\*{0,3})?\((-?\d+\.?\d*)\)",
    re.IGNORECASE,
)

CROSS_LAG_RE = re.compile(r"(?<!same_ctry_distw_)([a-z_]+_cnt_l1)")


def extract_docx_text(docx_path: Path) -> str:
    with zipfile.ZipFile(docx_path) as archive:
        xml = archive.read("word/document.xml")
    root = ET.fromstring(xml)
    parts: list[str] = []
    for node in root.iter(f"{W_NS}t"):
        if node.text:
            parts.append(node.text)
        if node.tail:
            parts.append(node.tail)
    return "".join(parts)


def stars_to_flags(stars: str) -> tuple[bool, bool, bool]:
    count = len(stars)
    return count >= 1, count >= 2, count >= 3


def parse_model2_coef(var_segment: str) -> tuple[float, str, float, bool, bool, bool] | None:
    """Parse the Model 2 coefficient from a variable row segment."""
    match = re.match(r"^([a-z_]+_cnt_l1)(.*)$", var_segment)
    if not match:
        return None

    var_name, rest = match.group(1), match.group(2)
    if var_name not in LAG_VAR_TO_TITLE:
        return None

    blocks = COEF_BLOCK_RE.findall(rest)
    if not blocks:
        return None

    # Cross-category lags appear only in models 2 and 4; first block is model 2.
    if len(blocks) == 2:
        coef_s, stars, t_s = blocks[0]
    elif len(blocks) == 4:
        coef_s, stars, t_s = blocks[1]
    else:
        return None

    coef = float(coef_s)
    t_stat = float(t_s)
    sig_05, sig_01, sig_001 = stars_to_flags(stars)
    return coef, stars, t_stat, sig_05, sig_01, sig_001


def split_table_blocks(text: str) -> list[tuple[str, str]]:
    matches = list(TABLE_HEADER_RE.finditer(text))
    blocks: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        title = normalize_title(match.group(1))
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        blocks.append((title, text[start:end]))
    return blocks


def extract_rows_from_table(title: str, block: str) -> list[dict[str, object]]:
    focal_base = base_for_title(title)
    own_lag = f"{focal_base}_cnt_l1"

    body_start = block.find("avg_built_up_height")
    body_end = block.find("_cons")
    if body_start < 0 or body_end < 0:
        raise ValueError(f"Could not locate regression body for table: {title}")

    body = block[body_start:body_end]
    interaction_pos = body.find("c.vdem_libdem#c")
    if interaction_pos >= 0:
        body = body[:interaction_pos]

    rows: list[dict[str, object]] = []
    for var_name in dict.fromkeys(CROSS_LAG_RE.findall(body)):
        if var_name == own_lag or var_name.startswith("same_ctry_distw_"):
            continue

        source_title = LAG_VAR_TO_TITLE.get(var_name)
        if source_title is None:
            continue

        pattern = re.compile(
            rf"{re.escape(var_name)}"
            r"(-?\d+\.?\d*(?:e[+-]?\d+)?|\.\d+)(\*{0,3})?\((-?\d+\.?\d*)\)"
            r"(-?\d+\.?\d*(?:e[+-]?\d+)?|\.\d+)(\*{0,3})?\((-?\d+\.?\d*)\)"
        )
        match = pattern.search(body)
        if not match:
            continue

        coef = float(match.group(1))
        stars = match.group(2) or ""
        t_stat = float(match.group(3))
        sig_05, sig_01, sig_001 = stars_to_flags(stars)

        rows.append(
            {
                "source_category": source_title,
                "target_category": title,
                "source_var": var_name,
                "target_var": f"{focal_base}_cnt",
                "coefficient": coef,
                "t_stat": t_stat,
                "stars": stars,
                "sig_05": sig_05,
                "sig_01": sig_01,
                "sig_001": sig_001,
                "model": 2,
            }
        )

    if len(rows) != 14:
        raise ValueError(
            f"Expected 14 cross-category coefficients for {title}, found {len(rows)}"
        )

    return rows


def extract_coefficients(docx_path: Path) -> list[dict[str, object]]:
    text = extract_docx_text(docx_path)
    all_rows: list[dict[str, object]] = []

    for title, block in split_table_blocks(text):
        all_rows.extend(extract_rows_from_table(title, block))

    if len(all_rows) != 15 * 14:
        raise ValueError(f"Expected 210 rows, found {len(all_rows)}")

    return all_rows


def write_csv(rows: list[dict[str, object]], csv_path: Path) -> None:
    fieldnames = [
        "source_category",
        "target_category",
        "source_var",
        "target_var",
        "coefficient",
        "t_stat",
        "stars",
        "sig_05",
        "sig_01",
        "sig_001",
        "model",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract Model 2 protest diffusion coefficients from a Word document."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("ppml categories.docx"),
        help="Input .docx file with regression tables",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("model2_coefficients.csv"),
        help="Output CSV path",
    )
    args = parser.parse_args()

    if not args.input.exists():
        print(f"Input file not found: {args.input}", file=sys.stderr)
        return 1

    rows = extract_coefficients(args.input)
    write_csv(rows, args.output)
    print(f"Wrote {len(rows)} coefficients to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
