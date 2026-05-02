---
service: backend
summary: Open-Meteo integration with caching, resampling, and PDF weather rendering.
paths:
  - backend/app/services/weather/service.py
  - backend/app/services/weather/provider.py
  - backend/app/services/weather/open_meteo.py
  - backend/app/services/weather/cache.py
  - backend/app/services/weather/resampler.py
  - backend/app/services/weather/weather_factory.py
  - backend/app/services/weather/wmo_codes.py
  - backend/app/services/weather/icon_paths.py
  - backend/app/services/weather/pdf_renderer.py
flows: []
touches:
  - PostgreSQL
  - In-memory cache
external:
  - Open-Meteo API
last_verified_commit: 9b0d86029a07dc6995ab5dc9f883ef48d6346f9b
---

## Purpose
Orchestrates weather data retrieval from Open-Meteo, caches responses, stitches timelines, and renders weather visualisations for PDF reports.

## Interface
- `service.py::WeatherService`
  - `resolve_site_location`
  - `get_current_weather`
  - `get_forecast`
  - `get_history`
  - `get_timeline`
- `provider.py::WeatherProvider` (ABC)
  - `get_current`
  - `get_forecast`
  - `get_fine_precipitation`
  - `get_historical`
- `open_meteo.py::OpenMeteoProvider`
- `cache.py::WeatherCache`
  - `get`, `put`, `invalidate`, `invalidate_site`
- `weather_factory.py::get_weather_service`
- `weather_factory.py::get_cache`
- `weather_factory.py::get_provider`
- `weather_factory.py::reset_weather_singletons`
- `resampler.py::resample_to_interval`
- `resampler.py::deduplicate_to_interval`
- `resampler.py::snap_to_interval`
- `resampler.py::angular_interpolate`
- `wmo_codes.py::wmo_code_to_condition`
- `wmo_codes.py::wind_speed_to_beaufort`
- `wmo_codes.py::classify_precipitation_type`
- `wmo_codes.py::is_drizzle_code`
- `icon_paths.py::draw_svg_icon`
- `icon_paths.py::parse_svg_path`
- `icon_paths.py::get_weather_icon`
- `pdf_renderer.py::WeatherPageRenderer`
  - `render`
  - `render_inline`
- `pdf_renderer.py::render_weather_to_png`

## State
- `WeatherCache` stores in-process TTL entries keyed by `(site_id, data_type)`; default TTL is 900 seconds.
- `weather_factory.py` holds module-level singletons `_weather_cache` and `_weather_provider`.
  - Invariant: singletons are shared across requests; tests must call `reset_weather_singletons` for isolation.

## Internals
- `WeatherService.resolve_site_location` derives lat/lon from the most recent calibrated `SiteMap` centroid.
- `get_timeline` stitches DB observations (past), archive backfill (gaps), and forecast (future), all resampled to a configurable slot interval (default 15 min).
- Fine precipitation (15-min resolution) overlays forecast slots when available.
- `OpenMeteoProvider` fetches deterministic and ensemble forecasts; ensemble p10/p90 is computed via linear interpolation over flattened member arrays.
- `resampler` handles passthrough, interpolation (coarser→finer), and downsampling (finer→coarser), using angular interpolation for wind direction.
- `wmo_codes` maps WMO 4677 codes to `WeatherCondition` and Beaufort scale.
- `icon_paths` contains QWeather SVG path data and a parser that renders to ReportLab `Canvas`.
- `pdf_renderer` draws temperature labels, precipitation bars, wind arrows, condition icons, and a time axis; `render_weather_to_png` rasterises via pypdfium2.

## Touches
| resource | how | why |
| PostgreSQL | `WeatherObservation` table | persist current weather readings |
| In-memory cache | `WeatherCache` | reduce API call volume |
| Open-Meteo API | HTTPS GET forecast, archive, ensemble endpoints | weather data source |

## Gotchas
- Timeline normalises datetimes to naive for slot comparison; aware datetimes from DB are stripped of tzinfo.
- `OpenMeteoProvider` returns empty lists on HTTP errors rather than raising.
- Cache singletons are shared across requests; `reset_weather_singletons` is provided for test isolation.
- PDF renderer assumes a square SVG viewBox (default 16); non-square icons may distort.
