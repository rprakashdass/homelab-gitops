# Telegram Bot Integration Guide

Centralized Telegram bot for messaging, notifications, and commands across all platform services.

## Architecture

```
┌──────────────────────────────────────┐
│   Services (hello-world, etc)        │
│                                      │
│   - Send notifications via HTTP      │
│   - Receive commands via Telegram    │
└────────────────┬─────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────┐
│   Telegram Bot Service               │
│   (services/messaging/telegram-bot)  │
│                                      │
│   Port: 9999                         │
│   /api/notify - receive messages     │
│   /health - health check             │
│   Telegram polling - receive commands│
└────────────────┬─────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────┐
│   Telegram Bot API                   │
│   (Telegram servers)                 │
└──────────────────────────────────────┘
```

## Setup

### 1. Create Telegram Bot

```bash
# Message @BotFather on Telegram
/start
/newbot
# Follow prompts, you'll get a token

# Save the token
export TELEGRAM_TOKEN="YOUR_BOT_TOKEN_HERE"
export TELEGRAM_CHAT_ID="YOUR_CHAT_ID_HERE"
```

### 2. Create Kubernetes Secret

```bash
kubectl create secret generic telegram-bot-secrets \
  --from-literal=TELEGRAM_TOKEN="$TELEGRAM_TOKEN" \
  --from-literal=TELEGRAM_CHAT_ID="$TELEGRAM_CHAT_ID" \
  -n home
```

### 3. Create ConfigMap

The centralized configuration is in `platform/common/telegram-configmap.yaml`. Apply it:

```bash
kubectl apply -f platform/common/telegram-configmap.yaml
```

### 4. Deploy Telegram Bot

The bot is enabled in `platform/applications-chart/values.yaml`:

```yaml
applications:
  telegram-bot:
    enabled: true
    path: services/messaging/telegram-bot
    syncWave: "0"  # Deploy before other services
```

Push to Git and ArgoCD will deploy it:

```bash
git add platform/
git commit -m "feat: enable telegram-bot service"
git push origin main

# Watch deployment
kubectl get deployment -n home -w
kubectl logs -n home -l app=telegram-bot -f
```

## Receiving Commands

The bot supports these commands:

### Implemented Commands

#### /help
Show list of available commands

**Usage:** `/help`

**Response:**
```
🤖 HomeLab Bot Commands

Navigation:
/help - Show this help message
/status - Show system status
/health - Show health checks

Automation:
/resume - Show latest resume (AI-generated)
...
```

#### /resume
Show latest AI-generated resume

**Usage:** `/resume`

**Response:**
```
📄 Latest Resume (AI-Generated)

Status: ✅ Generated today
Profile:
- Experience: Software Engineer, Platform Engineering
...
```

#### /status
Show system status

**Usage:** `/status`

#### /health
Show health checks

**Usage:** `/health`

### Planned Commands

- `/github` - GitHub activity summary
- `/deploy` - Deploy service
- `/backup` - Trigger backup
- `/expenses` - Show expenses
- `/notion` - Notion workspace
- `/budget` - Show budget status
- `/restart` - Restart services
- `/logs` - View recent logs

## Sending Notifications

### From Services: HTTP API

Any service can send notifications by POSTing to the telegram-bot HTTP API:

```bash
curl -X POST http://telegram-bot:9999/api/notify \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Backup Complete",
    "message": "Daily backup finished successfully",
    "service": "backup-job"
  }'
```

### Hello-World Example

**hello-world** sends daily heartbeat notifications to Telegram:

**Configuration** (`services/automation/hello-world/values.yaml`):
```yaml
envFrom:
  - configMapRef:
      name: telegram-configmap

command: ["python", "app.py"]
args:
  - --format
  - text
  - --telegram  # ← Enable telegram notifications
```

**Code** (`services/automation/hello-world/src/app.py`):
```python
def send_to_telegram(self) -> bool:
    """Send heartbeat via Telegram bot."""
    host = os.getenv("TELEGRAM_BOT_HOST", "telegram-bot")
    port = os.getenv("TELEGRAM_BOT_PORT", "9999")
    endpoint = f"http://{host}:{port}/api/notify"

    payload = {
        "title": "❤️ Platform Heartbeat",
        "message": f"*Timestamp:* {self.timestamp}\n*Status:* Healthy ✅",
        "service": "hello-world",
    }

    response = requests.post(endpoint, json=payload, timeout=5)
    return response.status_code in (200, 201, 204)
```

### Using the Notify Helper

Telegram bot includes a reusable `notify.py` helper:

```python
from notify import notify_user, notify_success, notify_error

# Send info notification
notify_user(
    title="Backup Complete",
    message="Daily backup finished successfully",
    service="backup-job"
)

# Convenience functions
notify_success(message="Deployment complete", service="deploy")
notify_error(message="Backup failed!", service="backup")
notify_warning(message="Disk space low", service="monitoring")
```

**Configuration:**
```bash
# Environment variables (set in service values)
TELEGRAM_BOT_HOST=telegram-bot
TELEGRAM_BOT_PORT=9999
```

## API Endpoints

### POST /api/notify

Send a notification message.

**Request:**
```json
{
  "title": "Notification Title",
  "message": "Notification message body",
  "service": "service-name",
  "chat_id": 12345,  # optional
  "level": "info"    # info, warning, error
}
```

**Response:**
```json
{
  "success": true,
  "message": "Notification sent"
}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-06-13T10:30:00Z"
}
```

### GET /commands

List available commands.

**Response:**
```json
{
  "commands": [
    {
      "name": "help",
      "description": "Show help message",
      "status": "implemented"
    },
    {
      "name": "resume",
      "description": "Show latest resume",
      "status": "implemented"
    },
    ...
  ]
}
```

## Centralized Configuration

**File:** `platform/common/telegram-configmap.yaml`

All services reference this ConfigMap:

```yaml
envFrom:
  - configMapRef:
      name: telegram-configmap
```

This ensures:
- Single source of truth for bot connection
- Easy to change endpoints (one place)
- Consistent configuration across services

**Environment Variables from ConfigMap:**
```
TELEGRAM_BOT_HOST
TELEGRAM_BOT_PORT
TELEGRAM_BOT_URL
TELEGRAM_BOT_NOTIFY_ENDPOINT
TELEGRAM_BOT_HEALTH_ENDPOINT
```

## Adding Telegram to Your Service

### 1. Update values.yaml

```yaml
base-chart:
  # Reference the centralized telegram configuration
  envFrom:
    - configMapRef:
        name: telegram-configmap
```

### 2. Add requests to requirements.txt

```
requests>=2.31.0
```

### 3. Send notification in code

```python
import os
import requests

def send_notification(title, message):
    host = os.getenv("TELEGRAM_BOT_HOST", "telegram-bot")
    port = os.getenv("TELEGRAM_BOT_PORT", "9999")
    endpoint = f"http://{host}:{port}/api/notify"

    payload = {
        "title": title,
        "message": message,
        "service": "my-service",
    }

    try:
        response = requests.post(endpoint, json=payload, timeout=5)
        return response.status_code in (200, 201, 204)
    except Exception as e:
        print(f"Failed to send notification: {e}")
        return False

# Usage
send_notification(
    title="✅ Task Complete",
    message="My service finished successfully"
)
```

## Troubleshooting

### Bot not receiving commands

```bash
# Check if bot is running
kubectl get deployment -n home | grep telegram-bot

# Check logs
kubectl logs -n home -l app=telegram-bot -f

# Verify secret exists
kubectl get secret telegram-bot-secrets -n home

# Test health endpoint
kubectl port-forward -n home svc/telegram-bot 9999:9999
curl http://localhost:9999/health
```

### Notifications not being sent

```bash
# Check ConfigMap exists
kubectl get configmap -n home | grep telegram

# Check service can reach bot
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- \
  curl -X POST http://telegram-bot:9999/api/notify \
    -H "Content-Type: application/json" \
    -d '{"title":"test","message":"test","service":"test"}'

# Check bot logs for errors
kubectl logs -n home -l app=telegram-bot --tail=50
```

### Cannot reach telegram-bot from service

```bash
# Verify DNS resolution
kubectl run -it --rm debug --image=alpine --restart=Never -- \
  nslookup telegram-bot.home.svc.cluster.local

# Check service exists
kubectl get svc -n home | grep telegram-bot

# Check network policies (if any)
kubectl get networkpolicies -n home
```

## Testing

### Manual Test

```bash
# Port-forward to bot
kubectl port-forward -n home svc/telegram-bot 9999:9999

# Send test notification
curl -X POST http://localhost:9999/api/notify \
  -H "Content-Type: application/json" \
  -d '{
    "title": "🧪 Test Notification",
    "message": "This is a test from curl",
    "service": "test-service"
  }'

# Check health
curl http://localhost:9999/health

# List commands
curl http://localhost:9999/commands
```

### Test from Pod

```bash
# Run test pod
kubectl run -it --rm test --image=python:3.11-slim --restart=Never -- bash

# Inside pod
python3 << 'EOF'
import requests
import json

payload = {
    "title": "📊 Pod Test",
    "message": "Notification from inside Kubernetes pod",
    "service": "test-pod"
}

response = requests.post(
    "http://telegram-bot:9999/api/notify",
    json=payload,
    timeout=5
)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
EOF
```

## Security Considerations

1. **Secret Management:** Telegram token stored in Kubernetes Secret (not in Git)
2. **Network:** Bot only exposed internally (ClusterIP service)
3. **Authentication:** Future - add token-based auth to /api/notify
4. **Rate Limiting:** Future - implement rate limiting to prevent abuse

## Next Steps

1. **Implement more commands:**
   - `/github` - query GitHub API
   - `/deploy` - trigger deployments
   - `/backup` - manual backup trigger

2. **Add more notifications:**
   - Service health alerts
   - Deployment completion
   - Error notifications

3. **Integration with observability:**
   - Prometheus alerts → Telegram
   - Loki logs → Telegram

---

**The telegram-bot is your centralized messaging hub for the entire platform!** 🚀
