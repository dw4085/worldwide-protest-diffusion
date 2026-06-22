#!/usr/bin/env python3
"""Run the full docx -> CSV -> HTML protest diffusion network pipeline."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build protest diffusion network from docx tables.")
    parser.add_argument("--docx", type=Path, default=Path("ppml categories.docx"))
    parser.add_argument("--csv", type=Path, default=Path("model2_coefficients.csv"))
    parser.add_argument("--html", type=Path, default=Path("protest_diffusion_network.html"))
    parser.add_argument("--summary", type=Path, default=Path("protest_influence_summary.html"))
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    commands = [
        [sys.executable, str(root / "extract_coefficients.py"), "--input", str(args.docx), "--output", str(args.csv)],
        [sys.executable, str(root / "build_network_viz.py"), "--input", str(args.csv), "--output", str(args.html)],
        [sys.executable, str(root / "build_influence_summary.py"), "--input", str(args.csv), "--output", str(args.summary)],
    ]

    for command in commands:
        result = subprocess.run(command, check=False)
        if result.returncode != 0:
            return result.returncode

    print(f"Pipeline complete. Open {args.html} or {args.summary} in a browser.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
