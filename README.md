# BC Road Safety Explorer

An interactive road safety analytics project built with public British Columbia data.

The project turns annual road safety tables into a small decision-support dashboard with KPI definitions, trend analysis, vulnerable road user summaries, regional comparisons, simple forecasting, and an animated map experience.

## Why I built it

Road safety reporting is more useful when the metric definition, data limitation, trend, and geographic context are visible together. This project keeps those pieces connected instead of showing charts without context.

## Data sources

The build downloads current public datasets from the Government of British Columbia / RoadSafetyBC data catalogue:

- Motor Vehicle Fatalities by Road User Type
- Motor Vehicle Fatalities by Region
- Motor Vehicle Serious Injuries by Region
- Motor Vehicle Fatalities with Speeding Involvement

The project also attempts to retrieve City of Vancouver intersection traffic movement count locations for the map. If that optional source is unavailable, the road safety dashboard still builds from the provincial sources.

See `docs/data-sources.md` for source URLs, definitions, caveats, and refresh notes.

## What the project does

- Downloads public road safety data at build time
- Normalizes both wide and long government CSV layouts
- Validates years, categories, counts, duplicate rows, and missing values
- Builds KPI definitions with numerator, denominator, source, refresh cadence, caveats, and intended use
- Calculates annual and five-year trends
- Summarizes vulnerable road users
- Compares police traffic regions
- Produces a simple three-year linear trend forecast with an explicit limitation note
- Publishes an animated, responsive GitHub Pages dashboard
- Includes count-up KPI cards, animated chart drawing, a playable year timeline, pulsing map markers, hover interactions, and reduced-motion support
- Includes automated tests and GitHub Actions

## Tech

Python, Pandas, NumPy, scikit-learn, JavaScript, HTML, CSS, Chart.js, Leaflet, GitHub Actions

## Local run

```bash
python -m pip install -r requirements.txt
python src/download_data.py
python src/build_dashboard.py
pytest -q
```

Then serve `site/` locally with any static HTTP server.

## Important limitations

The project combines several public aggregate datasets. It does not contain individual crash records, personal information, or exact crash coordinates. Regional map markers are approximate visual anchors for aggregate police traffic regions and are not crash locations.

The forecasting component is a baseline trend projection, not an official ICBC forecast and not a causal road safety model.
