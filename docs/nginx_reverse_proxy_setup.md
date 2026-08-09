# Server Architecture Update: Nginx Reverse Proxy

As of August 5, 2026, the server architecture on `powersrv-small` has been updated to include Nginx as a reverse proxy. This change was necessary because multiple projects on the server require access to standard web ports (80/443).

## Key Changes

1. **Nginx Installation**: 
   - Nginx is now running as the primary web server facing the public internet, listening on ports **80** (HTTP) and **443** (HTTPS).

2. **`ntfy` Service Relocation**:
   - The self-hosted `ntfy` server was moved from listening directly on port 80 to a local-only port: **`127.0.0.1:8002`**.
   - Nginx is configured with a `default_server` block on port 80. Any HTTP request that does not match a specific domain is automatically reverse-proxied to `ntfy` on port 8002. This ensures backward compatibility for all existing scripts (like our scrapers) that send notifications to the server's IP address on port 80.

3. **Other Domain Handlers**:
   - Nginx also routes traffic for specific domains to their respective backend services. For example, traffic for `gerichte.bonngiesst.de` is secured with SSL via Certbot (port 443) and reverse-proxied to the local `bonn-gerichte` application running on port **`8001`**.

## Impact on Monitoring Scripts

- **No changes required**. Because Nginx forwards all default traffic on port 80 directly to `ntfy`, the python scrapers and any API calls hitting `http://5.252.227.183` continue to work exactly as they did before without needing port adjustments or configuration updates.

## WebSocket Support (Added Aug 9, 2026)

To resolve `SocketTimeoutException` errors in the Android ntfy app (caused by Nginx terminating idle JSON streams), the Nginx `default_server` configuration (`ntfy_default.conf`) was updated to fully support WebSockets. The following directives were added to the `location /` block:
- `proxy_http_version 1.1;`
- `proxy_set_header Upgrade $http_upgrade;`
- `proxy_set_header Connection "upgrade";`
- `proxy_read_timeout 86400s;` and `proxy_send_timeout 86400s;` (to keep connections alive for 24h).

Client applications and agents should prefer using WebSockets when subscribing to topics.
