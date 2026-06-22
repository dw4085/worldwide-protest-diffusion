# Worldwide Protest Diffusion

Interactive visualization of cross-category protest diffusion from Model 2 PPML regressions. This repo turns regression tables in a Word document into a directed network of movement categories and a ranked influence summary.

**Live site:** https://worldwide-protest-diffusion.vercel.app/

- [Network visualization](https://worldwide-protest-diffusion.vercel.app/) — force-directed graph of lagged cross-category ties
- [Influence summary](https://worldwide-protest-diffusion.vercel.app/protest_influence_summary.html) — categories ranked from most influenced to most influential

## What it shows

The analysis covers **15 protest movement categories** (Governance & Politics, Education, Labor, Human Rights & Identity, and others). Each directed tie represents a Model 2 cross-category lag: a lagged count in one category predicting the focal category’s protest count.

- **Positive ties (green):** a lagged increase in the source category is associated with more protests in the target category.
- **Negative ties (red):** the opposite association.

The network page supports filtering by significance (p < 0.05 / 0.01 / 0.001), positive/negative direction, zoom/pan, click-to-highlight neighborhoods, and draggable nodes. The influence summary ranks categories by the weighted sum of significant positive incoming vs. outgoing ties.

## Quick start

Requires Python 3.10+. No third-party packages.

```bash
python3 run_pipeline.py
open protest_diffusion_network.html
```

This reads `ppml categories.docx`, writes `model2_coefficients.csv`, and regenerates both HTML pages.

## Repository structure

| File | Description |
|------|-------------|
| `ppml categories.docx` | Source regression tables |
| `extract_coefficients.py` | Docx → CSV (210 directed ties) |
| `build_network_viz.py` | CSV → interactive network HTML |
| `build_influence_summary.py` | CSV → influence ranking HTML |
| `run_pipeline.py` | Runs all three steps |
| `movement_categories.py` | Shared category ↔ variable mappings |
| `vercel.json` | Serves the network page at `/` on Vercel |

Generated outputs (`model2_coefficients.csv`, `protest_diffusion_network.html`, `protest_influence_summary.html`) are committed so the site can deploy as static files without a build step.

## Pipeline options

```bash
python3 run_pipeline.py \
  --docx "ppml categories.docx" \
  --csv model2_coefficients.csv \
  --html protest_diffusion_network.html \
  --summary protest_influence_summary.html
```

Run individual steps:

```bash
python3 extract_coefficients.py --input "ppml categories.docx" --output model2_coefficients.csv
python3 build_network_viz.py --input model2_coefficients.csv --output protest_diffusion_network.html
python3 build_influence_summary.py --input model2_coefficients.csv --output protest_influence_summary.html
```

After updating the docx or Python generators, rerun the pipeline and commit the updated CSV/HTML before pushing to redeploy.

## Deployment

The site is hosted on Vercel as a static deployment. Pushes to `main` redeploy automatically.

To deploy manually:

```bash
vercel --prod
```

## Further documentation

See [CLAUDE.md](CLAUDE.md) for detailed extraction rules, the full category mapping, CSV schema, and development notes.
