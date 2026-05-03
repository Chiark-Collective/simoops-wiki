---
service: backend
summary: "S3-compatible storage abstraction wrapping boto3 for MinIO"
paths: [backend/app/services/storage.py]
flows: []
touches: [infra/data-stores]
external: []
last_verified_commit: f9606469ce367229c5c91e03c3ba917779015030
---

## Purpose
Wrap boto3 to provide upload, download, presigned URLs, and health checks
against the configured MinIO S3-compatible endpoint. This is the only module
allowed to import boto3.

## Interface
- `services/storage.py::StorageError` — tuple of `(BotoCoreError, ClientError)` for catch-all storage failure handling
- `services/storage.py::S3Object` — dataclass of `content: bytes` and `content_type: str`
- `services/storage.py::get_client()` — cached boto3 S3 client
- `services/storage.py::upload_file(local_path, key, content_type)` → `str` — s3:// URI
- `services/storage.py::upload_bytes(data, key, content_type)` → `str` — s3:// URI
- `services/storage.py::download_file(key, local_path)` → `None`
- `services/storage.py::get_file_bytes(key)` → `bytes`
- `services/storage.py::get_object(key)` → `S3Object`
- `services/storage.py::object_exists(key)` → `bool`
- `services/storage.py::ensure_bucket()` → `None` — idempotent bucket creation
- `services/storage.py::generate_presigned_url(key, expires_in)` → `str`
- `services/storage.py::delete_file(key)` → `None`
- `services/storage.py::delete_file_no_error(key, *, site_id=None, session=None)` → `None` — async; on `StorageError` inserts `PendingStorageDelete` into caller's session
- `services/storage.py::check_health()` → `Literal["ok", "unreachable", "misconfigured"]`
- `services/storage.py::parse_s3_uri(uri)` → `tuple[str, str]` — bucket and key

## State
Cached boto3 S3 client via `get_client()`.

| symbol | type | semantics |
|---|---|---|
| `get_client` | `lru_cache` wrapper | One boto3 client per process |

Invariants:
- Client is configured with `us-east-1` region and MinIO endpoint credentials
- All operations target the single configured bucket (`minio_bucket`)

## Internals
- `upload_file` uses `client.upload_file`; `upload_bytes` uses `client.upload_fileobj` with `BytesIO`
- `get_object` returns both body and `ContentType`; `get_file_bytes` returns only body
- `object_exists` uses `head_object` and catches `ClientError` to return `False`
- `check_health` uses `head_bucket`; misconfiguration codes (NoSuchBucket, AccessDenied, …) return `"misconfigured"`, all other failures return `"unreachable"`
- `delete_file_no_error` runs S3 delete in thread via `asyncio.to_thread`; on failure adds `PendingStorageDelete` row to the supplied `session`
- `parse_s3_uri` validates `s3://` prefix and non-empty key; raises `ValueError` on malformed input

## Touches
| resource | how | why |
|---|---|---|
| infra/data-stores | boto3 S3 client to MinIO endpoint | Object storage for files, images, exports |

## Gotchas
- `generate_presigned_url` defaults to 1 hour expiry; callers needing longer must override `expires_in`
- All operations assume the bucket already exists; call `ensure_bucket()` at startup if running in fresh environments
