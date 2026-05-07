---
service: backend
summary: "Pure-function module normalising uploaded logos to uniform map-renderable shapes"
paths: [backend/app/services/logo_normalisation.py]
flows: []
touches: []
external: []
last_verified_commit: c56ee3d5e04d0143a312d17b22ca262eaa150bd2
---

## Purpose
Normalise uploaded contractor and site logos to a uniform shape suitable for MapLibre
`loadImage` rendering: 512×512 RGBA PNG for rasters, verbatim passthrough for SVG.

## Interface
- `logo_normalisation.py::normalise_logo(data, content_type)` → `(bytes, str, str)` — returns `(normalised_bytes, final_content_type, file_extension)`
- `logo_normalisation.py::ALLOWED_LOGO_TYPES` — `frozenset` of accepted MIME types
- `logo_normalisation.py::MAX_LOGO_SIZE` — 2 MB upload limit
- `logo_normalisation.py::LogoNormalisationError` — `ValueError` subclass for bad MIME, corrupt raster, unsafe SVG

## Internals
- Raster path (PNG/JPEG/WebP): convert to RGBA, `thumbnail()` with `LANCZOS` resampling down to fit 512×512 preserving aspect, paste centred onto transparent 512×512 canvas, re-encode as PNG
- Short-circuit: already-512×512 RGBA PNG bytes returned untouched
- SVG path: parse with `ElementTree`, reject any `<script>` tag (namespaced or not), pass through verbatim — frontend rasterises at draw time
- No upscaling — smaller images sit centred with transparent letterbox padding
- All errors raise `LogoNormalisationError`; route layer maps to 400 Bad Request

## Gotchas
- SVG safety check is structural only (`<script>` rejection); no XSS sanitisation beyond that
- `MAX_LOGO_SIZE` is enforced by the route layer, not inside `normalise_logo` itself
- Site logo route (`sites.py`) imports `ALLOWED_LOGO_TYPES` and `MAX_LOGO_SIZE` from this module for validation but uploads **raw unnormalised bytes** — no resize, no RGBA conversion, no SVG script check