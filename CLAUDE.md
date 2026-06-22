# Worldwide Protest Diffusion

Interactive visualization of cross-category protest diffusion from Model 2 PPML regressions. A Python pipeline extracts lag coefficients from Word regression tables, writes a CSV, and generates two standalone HTML pages: a force-directed network and an influence ranking summary.

## Quick start

```bash
python3 run_pipeline.py
open protest_diffusion_network.html
```

Requires Python 3.10+ and no third-party packages (`requirements.txt` is stdlib-only).

## Repository layout

| File | Role |
|------|------|
| `ppml categories.docx` | Source regression tables (15 focal categories × Model 2 cross-category lags) |
| `movement_categories.py` | Shared 15-category titles, Stata variable bases, and lag-variable mappings |
| `extract_coefficients.py` | Parses the docx → `model2_coefficients.csv` (210 directed ties) |
| `build_network_viz.py` | CSV → `protest_diffusion_network.html` (D3 force-directed network) |
| `build_influence_summary.py` | CSV → `protest_influence_summary.html` (influence ranking table) |
| `run_pipeline.py` | Runs extractor, network viz, and influence summary in sequence |
| `model2_coefficients.csv` | Generated edge list (committed for static deploy) |
| `protest_diffusion_network.html` | Generated interactive network (site entry point on Vercel) |
| `protest_influence_summary.html` | Generated influence ranking page |
| `vercel.json` | Rewrites `/` → network page for deployment |

## Data model

### Movement categories (15)

Each category has a display title and a Stata base used in variable names (`{base}_cnt` for the focal count, `{base}_cnt_l1` for the lagged cross-category predictor):

| Title | Base |
|-------|------|
| Governance & Politics | `gov_pol` |
| Education | `edu` |
| Labor | `labor` |
| Human Rights & Identity | `human_rights` |
| Justice & Accountability | `justice` |
| Security & Conflict | `security` |
| Health & Social Welfare | `health` |
| Religion & Belief | `religion` |
| Prices & Economy | `economy` |
| Public Services & Infrastructure | `pub_serv` |
| International Solidarity & Foreign Policy | `intl_solidarity` |
| Environment | `enviro` |
| Agriculture & Rural | `agri` |
| Land, Property & Housing | `land` |
| Other | `other` |

### CSV columns

Each row is one directed tie: lagged source category → focal (target) category in Model 2.

- `source_category`, `target_category` — human-readable labels
- `source_var`, `target_var` — Stata names (e.g. `edu_cnt_l1`, `gov_pol_cnt`)
- `coefficient`, `t_stat`, `stars` — Model 2 estimate and significance stars
- `sig_05`, `sig_01`, `sig_001` — booleans from star count (≥1, ≥2, ≥3)
- `model` — always `2` (cross-category lag model)

Expected shape: **15 tables × 14 cross-category lags = 210 rows**. Own-category lags and `same_ctry_distw_*` interaction terms are excluded.

### Extraction rules (`extract_coefficients.py`)

1. Unzip `word/document.xml` from the docx and concatenate text nodes.
2. Split on table header regex matching the 15 category titles (handles `Security Conflict` alias → `Security & Conflict`).
3. For each table, locate the regression body between `avg_built_up_height` and `_cons`, stopping before `c.vdem_libdem#c` interactions.
4. Match cross-category `*_cnt_l1` variables (excluding own lag and `same_ctry_distw_*`).
5. Parse Model 2 coefficient from the first coef block when two models appear, or the second when four models appear (Models 1–4 layout in doc tables).

**Known doc quirks:** duplicate Religion table with a stray `same_ctry_distw_gov_pol_cnt_l1`; header inconsistency `Security Conflict` vs `Security & Conflict`.

## Pipeline

```bash
python3 run_pipeline.py \
  --docx "ppml categories.docx" \
  --csv model2_coefficients.csv \
  --html protest_diffusion_network.html \
  --summary protest_influence_summary.html
```

Individual steps:

```bash
python3 extract_coefficients.py --input "ppml categories.docx" --output model2_coefficients.csv
python3 build_network_viz.py --input model2_coefficients.csv --output protest_diffusion_network.html
python3 build_influence_summary.py --input model2_coefficients.csv --output protest_influence_summary.html
```

After changing the docx or Python generators, rerun the pipeline and commit updated CSV/HTML if deploying.

## Network visualization (`protest_diffusion_network.html`)

Built by `build_network_viz.py` as a self-contained HTML file (D3 v7 from jsDelivr CDN).

**Interpretation:** directed edges run **source → target**. A positive coefficient means a lagged increase in the source category’s protest count is associated with a higher count in the target category (Model 2, controlling for other lags and covariates in the original tables).

**Layout:** D3 force simulation with link distances scaled by sign/magnitude, radial pull toward center for categories with stronger positive **outgoing** ties, node clamping, and fit-to-view on simulation end.

**Controls:**
- Significance filter: p < 0.05 / 0.01 / 0.001
- Sign filter: all / positive / negative ties
- Reset layout (clears manual drags)
- Zoom +/−, Fit, pan, scroll zoom
- Hover tooltips and sidebar detail
- Click node to highlight neighborhood; click background to clear
- Drag nodes manually

**Styling:** green positive ties, red negative ties; stroke width and arrow markers bucketed by |coefficient| within the active filter. Layout forces use rescaled magnitudes; hovers show actual coefficient values.

**Navigation:** link at top to influence summary page.

## Influence summary (`protest_influence_summary.html`)

Built by `build_influence_summary.py`. Ranks all 15 categories on a spectrum from **most influenced** to **most influential**, using significant **positive** ties only (toggle p thresholds match the network page).

Per category:
- **Incoming + weight** — count and sum of positive coefficients pointing in (other movements leading to this one)
- **Outgoing + weight** — count and sum pointing out (this movement leading to others)
- **Balance (in − out)** — higher = more influenced; lower = more influential

Sorted by balance descending. At default p < 0.05, extremes are typically **Security & Conflict** (most influenced) and **Land, Property & Housing** (most influential); rerun after data updates.

## Deployment (Vercel)

Static deploy: prebuilt HTML files are served from the repo root. `vercel.json` rewrites `/` to `/protest_diffusion_network.html` so the production URL opens the network view.

```bash
vercel --prod
```

No build command required unless you add a CI step to regenerate HTML from the docx. Python is not needed at runtime on Vercel.

## Development notes

- **No external Python deps** — keep generators stdlib-only unless there is a strong reason otherwise.
- **HTML is generated** — edit `build_network_viz.py` or `build_influence_summary.py`, not the `.html` files directly.
- **Category mappings** — any new category or rename must update `movement_categories.py` and the docx header regex in `extract_coefficients.py`.
- **Validation** — extractor raises if any table does not yield exactly 14 cross-category rows or total ≠ 210.

## GitHub

Repository: [dw4085/worldwide-protest-diffusion](https://github.com/dw4085/worldwide-protest-diffusion) (public). Push updates to `main`; Vercel redeploys from the connected project.

## Live site

- **Production:** https://worldwide-protest-diffusion.vercel.app/ (root URL opens the network visualization)
- **Influence summary:** https://worldwide-protest-diffusion.vercel.app/protest_influence_summary.html
