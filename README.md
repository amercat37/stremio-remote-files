# Stremio Remote Files Addon

Self-hosted Stremio addon that indexes a **remote movie and series library** and serves streams over:

- Internal trusted networks (LAN/VPN)
- External untrusted networks with token-based protection for catalogs, streams, and media delivery (via reverse proxy)

Stremio includes a “Local Files” addon for playing files stored on a PC.  
However, platforms like **Fire TV sticks, Android TV, and other embedded devices** have no local storage and no way to access local files.

This project runs a small server that:
- Scans and catalogs remote media
- Exposes it to Stremio as a normal addon
- Streams the actual media files back to Stremio over the network

---

## Requirements

Before you begin, you will need:

- **Docker** and **Docker Compose**
- A **TMDB API key** (free)
  - Create one at: https://www.themoviedb.org/settings/api
  - Used to retrieve movie and series metadata (IMDb ID, posters, genres)
- A TLS certificate (Stremio addons require valid, non-self-signed, certificates)

No Python installation is required on the host system.

---

## Architecture

There are **two services**:

### 1) `stremio-remote-files-api` (FastAPI)

- Scans `/media` and writes metadata to `/data/library.db`
- Exposes **Stremio addon endpoints**:
  - manifests
  - catalogs
  - stream resolvers
- Exposes **admin endpoints and UI**:
  - `/admin` (human-facing rescans)
  - `/internal/configure`, `/external/configure` (human-facing install / configuration page)
  - scan endpoints (manual rescans)

### 2) `stremio-remote-files-proxy` (Caddy)

- Reverse proxies API and admin routes to the API container
- Serves the **actual media bytes** directly from disk
- Enforces token validation for **external media requests** at the proxy layer
- Trusted internal networks (LAN/VPN) bypass token checks
- Token validation is delegated to the FastAPI `/auth` endpoint

---

## Media naming

### Movies (`/media/movies`)

Filename format:
```
Title (YEAR).ext
Title (YEAR) [1080p].ext
```

Examples:
```
Night of the Living Dead (1968).mp4
Night of the Living Dead (1968) [1080p].mp4
```

Rules:
- Year in parentheses is required
- Resolution tag is optional
- Any video extension is accepted

---

### Series (`/media/series`)

Folder / filename format:
```
Series Name/
  Season 01/
    S01E01 - Episode Title.ext
    S01E02 - Episode Title [1080p].ext
```

Examples:
```
Flash Gordon/Season 01/S01E01 - The Planet of Peril.mp4
Flash Gordon/Season 02/S02E03 - A Lesson in Courage [1080p].mp4
```

Rules:
- Season folders must be named `Season <number>`
- Episode files must start with `SxxExx`
- Episode title and resolution tag are optional

---

## Environment file setup (`.env`)

Create `.env` from `.env.sample`.

```env
STREAM_TOKENS=change-me
ADMIN_SCAN_TOKEN=change-me
TMDB_API_KEY=change-me
MEDIA_BASE_URL_INTERNAL=https://internal.host.name:11443
MEDIA_BASE_URL_EXTERNAL=https://external.host.name:11443
TRUSTED_NETWORKS=192.168.0.0/16 10.0.0.0/8 172.16.0.0/12
```

⚠️ MEDIA_BASE_URL_INTERNAL and MEDIA_BASE_URL_EXTERNAL must exactly match the scheme (http/https), host, and port exposed by the proxy.
A mismatch will cause Stremio to hide streams or fail playback silently.

### Variable reference

| Variable | Required | Description |
|---|---:|---|
| `STREAM_TOKENS` | Yes | **Comma-separated** list of tokens used by external Stremio stream resolvers |
| `ADMIN_SCAN_TOKEN` | Yes | Token required for admin scan and rebuild endpoints |
| `TMDB_API_KEY` | Yes | Used for metadata lookups (IMDb ID, posters, genres) |
| `MEDIA_BASE_URL_INTERNAL` | Yes | Base IP/URL used for Internal (LAN/VPN) streams |
| `MEDIA_BASE_URL_EXTERNAL` | Yes | Base IP/URL used for external streams over the internet (enforces token protection)|
| `TRUSTED_NETWORKS` | Yes | **Space-separated** CIDR ranges treated as trusted internal networks (LAN/VPN)|

### Tokens

Two separate token types are used:

- **Stream tokens**
  - Used by external Stremio stream resolver endpoints and direct external media requests
  - Invalid tokens return an empty stream list (no errors)

- **Admin token**
  - Used for administrative actions such as media scans and rebuilds
  - Passed as a `Bearer` token in the `Authorization` header
  - Invalid or missing tokens return explicit `401 / 403` errors

Stream tokens **cannot** be used for admin actions, and admin tokens are never accepted for stream resolution.

Tokens are **not required**, including for external access, for:
- Manifests

Tokens **are required** for external access to:
- Catalog endpoints
- Stream resolver endpoints
- Media Requests

---

## Generating a token

### Python
```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(32))'
```

### OpenSSL
```bash
openssl rand -base64 32 | tr -d '='
```

32-byte tokens are sufficient for both stream and admin use; you may generate longer tokens if desired.

---

## Setup / Quickstart

### 1) Configure shared media location

Both containers must mount the same media directory.  
The API container catalogs the media and the proxy serves the media to Stremio.

```yaml
./volumes/stremio-remote-files-shared/media:/media:ro
```

Place media in:
- `./volumes/stremio-remote-files-shared/media/movies`
- `./volumes/stremio-remote-files-shared/media/series`

### 2) Create `.env`

```bash
cp .env.sample .env
# edit values
```

### 3) Add TLS certificates

A TLS certificate (required for HTTPS and all external access; optional for internal HTTP-only LAN setups)

```
./volumes/stremio-remote-files-proxy/certs/fullchain.pem
./volumes/stremio-remote-files-proxy/certs/privkey.pem
```

### 4) Ports, DNS, firewall

Change the base URLs for internal and external access in the ```.env``` file:
- Update `MEDIA_BASE_URL_INTERNAL` and `MEDIA_BASE_URL_EXTERNAL`  

If you do expose this plugin externally:
- Update your routers firewall rules
- Update your DNS if using a hostname

### 5) Start containers

```bash
docker compose up -d --build
```

### Optional: Internal HTTP access (no internal DNS required)

In some environments (for example **Fire TV sticks**, ISP-managed DNS, or routers that do not allow custom DNS records), internal hostnames may not resolve, and HTTPS certificates tied to public hostnames may fail when accessing a private IP.

To support these cases, the proxy **can optionally expose internal access over plain HTTP** for trusted networks:

- When using internal HTTP access, token authentication is not enforced, as access is restricted by trusted network CIDRs.
- External access **must still use HTTPS** and token protection
- This allows devices to connect using a raw IP address (e.g. `http://192.168.1.48`)

Example use cases:
- Fire TV / Android TV devices without internal DNS
- Routers that cannot define local DNS overrides
- Simple LAN-only deployments

This mode is **optional** and intended only for trusted LAN/VPN environments.  
If you have working internal DNS and valid certificates, HTTPS-only internal access is still recommended.


### 6) Configure addon for Stremio

Open in a browser:
- Internal: https://<internal.host.name>:11443/internal/configure — Configure the addon for internal (LAN/VPN) access
- External: https://<external.host.name>:11443/external/configure — Configure the addon for external access with token authentication

A configuration web page will be displayed.  

![Configure page](img/configure.png)

Fill in the required fields:
- **Addon Base URL**  
Defaults to the URL used to access the configure page.
- **Stream Token**  
Only visible when accessing the "external" configuration page.
Use any token defined in `STREAM_TOKENS` in the `.env` file.

Click **Install Addon**:
- You will be prompted to open Stremio to install the addon
- The manifest URL is displayed in case automatic installation fails

In Stremio:
- Discover → Movies → **Remote Files** → `Movie Name` → Remote Files (Internal) - Play
- Discover → Series → **Remote Files** → `Series Name` → `Season` → `Episode` → Remote Files (Internal) - Play

or

Search for any movie or series and look at the list of streams on the right hand side.  Click the down arrow next to "All" at the top of the streams list.  Choose "Remote Files (Internal)" or "Remote Files (External)".

### Note on duplicate catalogs

When **both internal (HTTP)** and **external (HTTPS)** access are enabled, Stremio
will display duplicate “Remote Files” catalogs.

Duplicate catalogs are a **known Stremio client limitation**, not a server bug.

If you prefer to see only a single catalog, you can safely disable one manifest.

**This addon now defaults to exposing catalogs only from the internal manifest, even when both internal and external access are enabled, preventing duplicate catalogs in Stremio by default.**

See:  
👉 [Eliminating duplicate catalogs by disabling one manifest](#eliminating-duplicate-catalogs-by-disabling-one-manifest)

---

## Scanning media

### Automatic scan

On API startup:
- Database schema is initialized
- Movie library is scanned
- Series library is scanned

### Manual scan (Admin UI)

Admin page:
- `https://<internal.host.name>:11443/admin`
- `https://<external.host.name>:11443/admin`

Admin actions (token required):
- Scan Library - `POST /admin/scan`
- Full Rebuild - `POST /admin/scan/rebuild`

![Admin page](img/admin.png)

### Manual rescan via Docker (no HTTP, no curl)

You can trigger a media rescan directly inside the running API container
by importing and calling the scanner functions. This bypasses FastAPI,
authentication, and networking entirely.

This uses the same code paths as the startup scan.

#### Rescan movies and series

```bash
docker exec -i stremio-remote-files-api python - <<'PY'
from scanner.scan_movies import scan_movies
from scanner.scan_series import scan_series

scan_movies()
scan_series()

print("Scan complete")
PY
```

### Manual rescan via HTTP / HTTPS

You can trigger a rescan using the admin endpoints directly from the host
or any trusted LAN/VPN client.

#### Internal
```bash
curl -X POST https://internal.host.name:11443/admin/scan \
  -H "Authorization: Bearer ADMIN_SCAN_TOKEN"
```

#### External
```bash
curl -k -X POST https://external.host.name:11443/admin/scan \
  -H "Authorization: Bearer ADMIN_SCAN_TOKEN"
```

#### Full rebuild (Internal)
```bash
curl -X POST https://internal.host.name:11443/admin/scan/rebuild \
  -H "Authorization: Bearer ADMIN_SCAN_TOKEN"
```

#### Full rebuild (External)
```bash
curl -k -X POST https://external.host.name:11443/admin/scan/rebuild \
  -H "Authorization: Bearer ADMIN_SCAN_TOKEN"
```

#### Notes

- Intended for trusted internal (LAN/VPN) or secured HTTPS access over the internet
- Requires a valid admin token
- Uses the same code path as the Admin UI
- Does not require Docker access

---

## API endpoints

### Admin pages (public)

- `GET /admin`

### Admin actions (token required)

- `POST /admin/scan`
- `POST /admin/scan/rebuild`

---

### Stremio addon endpoints

**Important:**  
External manifests do **not** require tokens.  
External catalog and stream resolver endpoints **require token validation**.

#### Manifests
- `GET /internal/manifest.json`
- `GET /external/manifest.json`

#### Catalogs (token required for external only)
- `GET /internal/catalog/movie/remote-movies.json`
- `GET /external/catalog/movie/remote-movies.json`
- `GET /internal/catalog/series/remote-series.json`
- `GET /external/catalog/series/remote-series.json`

#### Streams (token required for external only)

Movies:
- `GET /internal/stream/movie/{imdb_id}.json`
- `GET /external/stream/movie/{imdb_id}.json?token=...`

Series (episode format: `ttXXXXXX:season:episode`)
- `GET /internal/stream/series/{episode_id}.json`
- `GET /external/stream/series/{episode_id}.json?token=...`

Unauthorized external stream requests return an **empty stream list**, matching Stremio addon expectations.

#### Configuration
- `GET /internal/configure`
- `GET /external/configure`

---

## Proxy behavior and tests

### Internal

- Proxies API and admin routes without token checks
- Terminates TLS
- Serves media bytes without token checks

Test:
```bash
curl -I https://internal.host.name:11443/movies/Night%20of%20the%20Living%20Dead%20(1968).mp4
```

### External

- Proxies API and admin routes with token checks
- Terminates TLS
- Catalog and stream discovery are protected at the API layer using token authentication
- Media byte delivery is protected by the reverse proxy for external access using token authentication
- External media requests are authenticated via FastAPI `/auth`
- This ensures reliable playback while preventing unauthenticated external access


Tests:
```bash
curl -k -I \
  -H "Authorization: Bearer DUMMY_TOKEN" \
  "https://external.host.name:11443/movies/Night%20of%20the%20Living%20Dead%20(1968).mp4"
```

---

## Troubleshooting

**Catalog is empty**
- Check media mount paths
- Verify naming rules:
  - Movies must be named `Title (YEAR).ext` (optional `[resolution]`)
  - Series must follow `Series Name/Season XX/SxxExx - Title.ext`
  - Incorrect filenames or season folder names are skipped during scanning
- Run `/admin/scan`


**External streams are empty**
- Confirm `?token=` is provided
- Confirm token exists in `STREAM_TOKENS`

**TMDB lookup failures**
- Verify `TMDB_API_KEY`
- Confirm outbound internet access

---

## Future enhancements

### Episode stored in the wrong season folder

If an episode file (e.g. `S02E01`) is placed in the wrong season directory (e.g. `Season 03`):

- The scanner trusts the folder structure
- The `Remote Files (Internal) - Play` link will appear under the folder’s season and the file's episode
- Playback still works, but metadata is incorrect

Possible future approaches:
- Derive season/episode from filename only
- Validate folder vs filename and warn or skip
- Add a strict validation mode


### Partial series population

If only one episode of a series exists on disk:

- The series still appears in catalogs
- All seasons/episodes may be browsable
- Only existing episodes are playable using `Remote Files (Internal) - Play` link

Possible future improvements:
- Hide empty seasons
- Only expose seasons with files
- Add scan summaries indicating partial availability

---

## Known limitations

### Duplicate catalogs in Stremio

When **both internal and external access are enabled**, Stremio **will** display
duplicate catalog entries (for example, two “Remote Files” rows under Movies or Series).

This is expected behavior.

It occurs because:

- The addon exposes **both** `/internal/manifest.json` and `/external/manifest.json`
- Stremio installs and caches **both manifests independently**
- Stremio does not reliably merge or deduplicate catalogs across manifests

This is a **Stremio client behavior**, not a server or database issue.

---

### Eliminating duplicate catalogs by disabling one manifest

If you **do need both internal and external access**, you can still eliminate
duplicate catalogs by **removing catalog definitions from one manifest**.

This preserves:
- dual access (internal + external)
- correct stream resolution
- token-based security

while avoiding duplicate UI entries.

#### Recommended approach

Expose catalogs from **only one manifest**:

- Keep catalogs in `/internal/manifest.json`
- Remove (or empty) `catalogs` in `/external/manifest.json`

The external manifest can still expose:
- stream resolvers
- configuration UI
- admin functionality

#### Example: disable catalogs in the external manifest

In `manifest_external()`:

```python
return {
    "id": "org.remote-files",
    "name": "Remote Files (External)",
    "version": "1.1.1",
    "description": "Browse and play your own media securely over HTTPS",
    "resources": [
        {
            "name": "stream",
            "types": ["movie", "series"],
            "idPrefixes": ["tt"],
        },
    ],
    "types": ["movie", "series"],
    "catalogs": []
}
```

#### Result

- Only **one** “Remote Files” catalog appears in Stremio
- Internal and external streaming both continue to work
- No loss of functionality
- No reliance on Stremio cache behavior

#### Notes

- This does **not** affect media scanning or database contents
- This does **not** affect stream URLs or token enforcement
- This is a UI-level limitation of the Stremio client
- This is the recommended solution when dual access is required


---

## Ruff linting (optional)

Ruff is used for development linting only.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install ruff
ruff check .
```

Optional `pyproject.toml`:
```toml
[tool.ruff]
line-length = 100
target-version = "py312"
```

---

## Security notes

- Admin and configure pages are intentionally public
- The configure page itself does not grant access to media
- Admin API actions (`/admin/scan`, `/admin/scan/rebuild`) require a Bearer token
- Manifests are intentionally unauthenticated
- External catalog and stream resolver endpoints enforce token checks
- All external access is served over HTTPS
- Token authentication at the API layer is enforced only for external catalog and stream resolver endpoints
- Stream tokens and admin tokens are intentionally separate to reduce blast radius
- Trusted internal networks bypass token checks
- External media requests are authenticated via the FastAPI `/auth` endpoint
- Stream discovery and resolution are still token-protected at the API layer
- External stream and catalog endpoints return empty results (not errors) when tokens are invalid, matching Stremio addon expectations.

This design follows the same security model used by common Stremio addons, which protect stream discovery and resolution rather than media byte delivery.

---

## License

**PolyForm Noncommercial 1.0.0**

See `LICENSE` for full terms.
