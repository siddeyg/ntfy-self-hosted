# ntfy Client Instructions (for Gemini Agents/Instances)

This document provides the necessary information for another Gemini instance or any other agent to use the self-hosted `ntfy` server on `powersrv-small`.

## Server Details

**CRITICAL RULE:** We ALWAYS use this self-hosted server for notifications. We NEVER use the public `ntfy.sh` server.

- **Base URL:** `http://5.252.227.183`
- **Port:** `80`
- **Authentication:** Required (Basic Auth)

## Credentials

- **Username:** `admin`
- **Password:** `goonline4M`

## Usage Examples

### 1. Publishing a Message (Sending)

To send a notification to a topic (e.g., `gemini_updates`), use a POST request with Basic Auth.

**Curl CLI:**
```bash
curl -u admin:goonline4M -d "Build completed successfully" http://5.252.227.183/gemini_updates
```

**Python (Requests):**
```python
import requests

url = "http://5.252.227.183/gemini_updates"
auth = ("admin", "goonline4M")
data = "Task processed by Gemini Instance A"

response = requests.post(url, data=data, auth=auth)
print(response.json())
```

### 2. Subscribing to a Topic (Listening)

To listen for incoming messages on a topic in real-time.

**Curl CLI (JSON Stream):**
```bash
curl -u admin:goonline4M -s http://5.252.227.183/gemini_updates/json
```

## Security Note

- Topic names can be anything you choose. For private communication between instances, use a unique or random topic name.
- Authentication is strictly enforced. Anonymous requests will receive a `403 Forbidden` error.
