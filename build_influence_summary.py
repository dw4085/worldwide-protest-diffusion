#!/usr/bin/env python3
"""Build an HTML summary ranking movement categories by influenced vs influential."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from movement_categories import CATEGORIES

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Protest Movement Influence Summary</title>
  <style>
    :root {
      --bg: #f6f4ef;
      --panel: #ffffff;
      --ink: #1f2933;
      --muted: #5d6b78;
      --positive: #1f7a4d;
      --negative: #b42318;
      --node: #2f4a68;
      --border: #d8dde3;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      font-family: "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(47, 74, 104, 0.08), transparent 28rem),
        var(--bg);
    }

    .page {
      max-width: 1100px;
      margin: 0 auto;
      padding: 24px;
    }

    .nav {
      margin-bottom: 18px;
      font-size: 0.95rem;
    }

    .nav a {
      color: var(--node);
    }

    h1 {
      margin: 0 0 8px;
      font-size: 1.9rem;
      letter-spacing: -0.02em;
    }

    .subtitle, .note {
      color: var(--muted);
      line-height: 1.55;
      max-width: 920px;
    }

    .controls {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      align-items: center;
      margin: 20px 0 16px;
    }

    .controls label {
      font-size: 0.95rem;
      color: var(--muted);
    }

    .btn-group {
      display: inline-flex;
      border: 1px solid var(--border);
      border-radius: 999px;
      overflow: hidden;
      background: var(--panel);
    }

    .btn-group button {
      border: 0;
      background: transparent;
      padding: 10px 16px;
      cursor: pointer;
      font: inherit;
      color: var(--ink);
    }

    .btn-group button.active {
      background: var(--node);
      color: white;
    }

    .panel {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 18px;
      box-shadow: 0 10px 30px rgba(31, 41, 51, 0.06);
      overflow: hidden;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.95rem;
    }

    thead th {
      text-align: left;
      padding: 14px 16px;
      background: #f8f9fb;
      border-bottom: 1px solid var(--border);
      font-weight: 600;
      color: var(--ink);
    }

    tbody td {
      padding: 14px 16px;
      border-bottom: 1px solid rgba(216, 221, 227, 0.8);
      vertical-align: middle;
    }

    tbody tr:last-child td {
      border-bottom: 0;
    }

    tbody tr.influenced td:first-child {
      color: var(--positive);
      font-weight: 600;
    }

    tbody tr.influential td:first-child {
      color: var(--negative);
      font-weight: 600;
    }

    .metric {
      font-variant-numeric: tabular-nums;
    }

    .bar-wrap {
      min-width: 180px;
    }

    .bar-track {
      display: flex;
      height: 10px;
      border-radius: 999px;
      overflow: hidden;
      background: #eef1f4;
    }

    .bar-in {
      background: var(--positive);
    }

    .bar-out {
      background: #6b8cae;
    }

    .bar-labels {
      display: flex;
      justify-content: space-between;
      font-size: 0.78rem;
      color: var(--muted);
      margin-top: 4px;
    }

    .rank-note {
      padding: 12px 16px 16px;
      color: var(--muted);
      font-size: 0.92rem;
      line-height: 1.45;
      border-top: 1px solid var(--border);
    }
  </style>
</head>
<body>
  <div class="page">
    <p class="nav"><a href="protest_diffusion_network.html">← Back to network visualization</a></p>
    <h1>Movement Influence Summary</h1>
    <p class="subtitle">
      Categories ranked from <strong>most influenced</strong> (other movement types most strongly
      lead to this type through significant positive lagged ties) to
      <strong>most influential</strong> (this type most strongly leads to other movement types).
    </p>
    <p class="note">
      Rankings use statistically significant <em>positive</em> Model 2 coefficients only.
      Incoming weight is the sum of positive coefficients on ties pointing <em>into</em> a category;
      outgoing weight is the sum on ties pointing <em>out</em>. Categories with high incoming and
      low outgoing mass appear first; categories with high outgoing and low incoming mass appear last.
    </p>

    <div class="controls">
      <label for="sig-buttons">Include ties significant at:</label>
      <div class="btn-group" id="sig-buttons">
        <button data-level="sig_05" class="active" type="button">p &lt; 0.05</button>
        <button data-level="sig_01" type="button">p &lt; 0.01</button>
        <button data-level="sig_001" type="button">p &lt; 0.001</button>
      </div>
    </div>

    <div class="panel">
      <table>
        <thead>
          <tr>
            <th>Rank</th>
            <th>Movement category</th>
            <th>Incoming + weight</th>
            <th>Outgoing + weight</th>
            <th>Balance (in − out)</th>
            <th>In vs out</th>
          </tr>
        </thead>
        <tbody id="summary-body"></tbody>
      </table>
      <div class="rank-note" id="rank-note"></div>
    </div>
  </div>

  <script>
    const DATA = __DATA_JSON__;
    const CATEGORIES = __CATEGORIES_JSON__;
    let currentLevel = "sig_05";

    function formatCoef(value) {
      return value.toExponential(3);
    }

    function computeRows(level) {
      const stats = new Map(
        CATEGORIES.map((cat) => [
          cat.label,
          {
            label: cat.label,
            inWeight: 0,
            outWeight: 0,
            inCount: 0,
            outCount: 0,
          },
        ])
      );

      DATA.forEach((row) => {
        if (!row[level] || row.coefficient <= 0) return;
        const incoming = stats.get(row.target_label);
        const outgoing = stats.get(row.source_label);
        incoming.inWeight += row.coefficient;
        incoming.inCount += 1;
        outgoing.outWeight += row.coefficient;
        outgoing.outCount += 1;
      });

      return Array.from(stats.values())
        .map((row) => ({
          ...row,
          balance: row.inWeight - row.outWeight,
        }))
        .sort((a, b) => b.balance - a.balance);
    }

    function rowClass(index, total) {
      if (index === 0) return "influenced";
      if (index === total - 1) return "influential";
      return "";
    }

    function render() {
      const rows = computeRows(currentLevel);
      const maxTotal = Math.max(
        ...rows.map((row) => Math.max(row.inWeight, row.outWeight)),
        1e-9
      );

      const body = d3SelectBody(rows, maxTotal);
      document.getElementById("summary-body").innerHTML = body;

      const mostInfluenced = rows[0];
      const mostInfluential = rows[rows.length - 1];
      document.getElementById("rank-note").textContent =
        `At ${currentLevel === "sig_05" ? "p < 0.05" : currentLevel === "sig_01" ? "p < 0.01" : "p < 0.001"}, ` +
        `${mostInfluenced.label} is the most influenced category (balance ${formatCoef(mostInfluenced.balance)}), ` +
        `and ${mostInfluential.label} is the most influential (balance ${formatCoef(mostInfluential.balance)}).`;
    }

    function d3SelectBody(rows, maxTotal) {
      return rows.map((row, index) => {
        const inShare = row.inWeight / (row.inWeight + row.outWeight || 1);
        const outShare = 1 - inShare;
        const cls = rowClass(index, rows.length);
        return `
          <tr class="${cls}">
            <td>${index + 1}</td>
            <td>${row.label}</td>
            <td class="metric">${row.inCount} / ${formatCoef(row.inWeight)}</td>
            <td class="metric">${row.outCount} / ${formatCoef(row.outWeight)}</td>
            <td class="metric">${formatCoef(row.balance)}</td>
            <td class="bar-wrap">
              <div class="bar-track">
                <div class="bar-in" style="width:${(inShare * 100).toFixed(1)}%"></div>
                <div class="bar-out" style="width:${(outShare * 100).toFixed(1)}%"></div>
              </div>
              <div class="bar-labels">
                <span>in</span>
                <span>out</span>
              </div>
            </td>
          </tr>
        `;
      }).join("");
    }

    document.querySelectorAll("#sig-buttons button").forEach((button) => {
      button.addEventListener("click", () => {
        document.querySelectorAll("#sig-buttons button").forEach((b) => b.classList.remove("active"));
        button.classList.add("active");
        currentLevel = button.dataset.level;
        render();
      });
    });

    render();
  </script>
</body>
</html>
"""


def load_csv(csv_path: Path) -> list[dict[str, object]]:
    with csv_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["coefficient"] = float(row["coefficient"])
        row["t_stat"] = float(row["t_stat"])
        row["sig_05"] = row["sig_05"] == "True"
        row["sig_01"] = row["sig_01"] == "True"
        row["sig_001"] = row["sig_001"] == "True"
    return rows


def build_payload(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "source_label": row["source_category"],
            "target_label": row["target_category"],
            "coefficient": row["coefficient"],
            "stars": row["stars"],
            "sig_05": row["sig_05"],
            "sig_01": row["sig_01"],
            "sig_001": row["sig_001"],
        }
        for row in rows
    ]


def render_html(payload: list[dict[str, object]]) -> str:
    categories = [{"id": base, "label": title} for title, base in CATEGORIES]
    return (
        HTML_TEMPLATE.replace("__DATA_JSON__", json.dumps(payload, indent=2))
        .replace("__CATEGORIES_JSON__", json.dumps(categories, indent=2))
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build influence summary HTML from Model 2 coefficients CSV."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("model2_coefficients.csv"),
        help="Input CSV produced by extract_coefficients.py",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("protest_influence_summary.html"),
        help="Output HTML path",
    )
    args = parser.parse_args()

    if not args.input.exists():
        print(f"Input CSV not found: {args.input}", file=sys.stderr)
        return 1

    rows = load_csv(args.input)
    html = render_html(build_payload(rows))
    args.output.write_text(html, encoding="utf-8")
    print(f"Wrote influence summary to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
