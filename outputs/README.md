# Data dictionary: `submission.csv` and `outputs/`

Every file here is written by code in `code/` from our forecasts. None holds observed 2019–2025 weather. All files are UTF-8, comma-separated (CSV) or RFC 7946 GeoJSON, with a header row and no index column.

**Conventions for all files**

- **Join key:** `city_id`, the city's current GHCN station ID, as in the `ID` column of the training dataset's `city_info` table (e.g., Pittsburgh = `USW00094823`).
- **Coordinates:** `lat` / `lon` in decimal degrees, WGS 84 (EPSG:4326), from `city_info`.
- **Units:** °F, inches and °F-days, as in the source data. No conversions.
- **Missing values:** none. Every city has a forecast for every year and metric, including the city-metrics the challenge does not score.
- **Baseline period:** "1989_2018" columns are the mean of the valid years in 1989–2018 under the challenge's validity rule (≤ 10 missing days), as recorded (no station-change correction).
- **Rounding:** values are rounded to 2 decimal places.

## Metrics

| Code | Meaning | Unit |
|---|---|---|
| `annual_avg_temp` | Mean over the year of the daily mean temperature, (Tmax + Tmin) / 2 | °F |
| `total_precip_in` | Total precipitation over the year | inches |
| `hottest_day_temp` | Highest daily maximum temperature of the year | °F |
| `cdd` | Cooling degree days: sum over days of max(0, (Tmax + Tmin)/2 − 65) | °F-days |

## `submission.csv` (long format, the scored file)

5,880 rows = 210 cities × 7 years × 4 metrics. Written by `code/forecast.py`.

| Column | Type | Unit | Description |
|---|---|---|---|
| `city_id` | string | – | Station ID (join key) |
| `year` | integer | – | Forecast year, 2019–2025 |
| `metric` | string | – | One of the four metric codes above |
| `predicted_value` | float | metric's unit | Forecast made with data up to 2018-12-31 only |

## `outputs/forecasts_wide.csv` (one row per city and year)

1,470 rows = 210 cities × 7 years. Written by `code/export.py`. Same values as `submission.csv`, pivoted, with name and coordinates added, for spreadsheets and plotting.

| Column | Type | Unit | Description |
|---|---|---|---|
| `city_id` | string | – | Station ID (join key) |
| `name` | string | – | City name as in `city_info` |
| `lat`, `lon` | float | degrees (WGS 84) | Station location |
| `year` | integer | – | Forecast year, 2019–2025 |
| `annual_avg_temp` | float | °F | Forecast |
| `total_precip_in` | float | inches | Forecast |
| `hottest_day_temp` | float | °F | Forecast |
| `cdd` | float | °F-days | Forecast |

## `outputs/forecasts.geojson` (one point per city)

A GeoJSON `FeatureCollection` of 210 `Point` features, coordinates `[lon, lat]` in WGS 84. Written by `code/export.py`. Opens in QGIS, ArcGIS, geojson.io and kepler.gl. Each feature has 38 properties:

| Property | Type | Unit | Description |
|---|---|---|---|
| `city_id` | string | – | Station ID (join key) |
| `name` | string | – | City name |
| `<metric>_1989_2018` | float | metric's unit | Mean of valid years 1989–2018 (baseline) |
| `<metric>_2019_2025_mean` | float | metric's unit | Mean of the seven yearly forecasts |
| `<metric>_<year>` | float | metric's unit | Forecast for each year 2019–2025 |

`<metric>` is each of the four metric codes, so there are 2 + 4 × (1 + 1 + 7) = 38 properties.

## `outputs/cdd_change_by_city.csv` (cooling demand change, Policy Idea)

210 rows, one per city, sorted by `cdd_change_pct` (largest first). Written by `code/policy_analysis.py`.

| Column | Type | Unit | Description |
|---|---|---|---|
| `city_id` | string | – | Station ID (join key) |
| `name` | string | – | City name |
| `lat`, `lon` | float | degrees (WGS 84) | Station location |
| `cdd_1989_2018` | float | °F-days | Mean yearly CDD, valid years 1989–2018 |
| `cdd_2019_2025_forecast` | float | °F-days | Mean of the 2019–2025 CDD forecasts |
| `temp_1989_2018` | float | °F | Mean annual average temperature, valid years 1989–2018 |
| `temp_2019_2025_forecast` | float | °F | Mean of the 2019–2025 temperature forecasts |
| `cdd_change` | float | °F-days | `cdd_2019_2025_forecast − cdd_1989_2018` |
| `cdd_change_pct` | float | % | `100 × cdd_change / cdd_1989_2018` |
| `temp_change` | float | °F | `temp_2019_2025_forecast − temp_1989_2018` |
| `cooling_gap_city` | boolean | – | `True` if `cdd_1989_2018 < 1000` **and** `cdd_change_pct ≥ 20` **and** `cdd_change ≥ 50` (the Policy Idea's trigger) |

**Read with care:** our forecasts ran cool in the pre-2018 backtest (−0.34 °F mean bias in temperature, −22 °F-days in CDD), so these increases are more likely under- than overestimates. They are point forecasts with no uncertainty range.
