# services/

Domain-specific service abstractions and configurations.

## Contents

| Service | Purpose |
|---------|---------|
| `automation/` | CronJobs, workflows, schedules, reminders |
| `ai/` | Agents, RAG, summarization, embeddings, LLM integration |
| `storage/` | MinIO, backups, snapshots, object storage, archives |
| `observability/` | Prometheus, Grafana, Loki, dashboards, alerts |
| `messaging/` | Telegram, email, webhooks, notification routing |
| `security/` | SOPS, External Secrets, Vault, policies |

## What Belongs Here

Each service is a **capability** that multiple automations use.

Services are **configuration and setup** for a shared capability:
- YAML configurations
- Default values
- Policy definitions
- Integration examples

Services are **NOT**:
- Individual automations (those go in `charts/`)
- Reusable code (that goes in `platform/`)
- Cluster infrastructure (that goes in `infrastructure/`)

## Automation Service

Handles all time-based automations.

```
services/automation/
├── README.md               ← Automation service docs
├── values.yaml             ← Default settings
├── cron-templates/         ← CronJob templates
├── workflow-templates/     ← Argo Workflow templates
└── examples/
    ├── daily-task/
    ├── weekly-task/
    └── event-driven-task/
```

### Adding an Automation

All automations are Helm charts in `charts/`.

Examples:
- `charts/hello-world/` — daily logger
- `charts/k8s-health-report/` — weekly report
- `charts/github-summary/` — weekly activity
- `charts/backup-job/` — daily backup

### Scheduling

Every automation specifies its schedule in Helm values:

```yaml
# charts/my-automation/values.yaml
base-chart:
  kind: cronjob
  schedule: "0 7 * * *"  # daily at 7am UTC
```

See cron schedule syntax: [crontab.guru](https://crontab.guru)

## AI Service

Handles agent logic, summarization, embeddings, and LLM integration.

```
services/ai/
├── README.md
├── prompts/                ← Prompt templates
│   ├── summarization.txt
│   ├── extraction.txt
│   └── agent-instructions.txt
├── models/                 ← Model configurations
│   ├── gpt-4.yaml
│   ├── claude.yaml
│   └── local-llm.yaml
├── rag/                    ← RAG setup
│   ├── embedding-models.yaml
│   └── vector-db-config.yaml
└── examples/
    ├── document-summarizer/
    ├── meeting-notes-parser/
    └── resume-generator/
```

### Using AI Capabilities

Example automation that uses AI to summarize:

```yaml
# charts/meeting-summarizer/values.yaml
base-chart:
  kind: cronjob
  image:
    repository: my-org/meeting-summarizer
  env:
    OPENAI_API_KEY: "${OPENAI_API_KEY}"
    AI_MODEL: "gpt-4"
    # Uses prompts from services/ai/prompts/
```

## Storage Service

Manages MinIO, backups, and persistent data.

```
services/storage/
├── README.md
├── minio-config.yaml       ← MinIO setup
├── backup-policies/        ← Backup schedules and retention
│   ├── daily-backup.yaml
│   ├── weekly-backup.yaml
│   └── retention.yaml
├── lifecycle-policies/     ← Object expiration
└── examples/
    ├── database-backup/
    ├── document-archive/
    └── media-storage/
```

### Backup Automation

Example automation that backs up to MinIO:

```yaml
# charts/database-backup/values.yaml
base-chart:
  kind: cronjob
  schedule: "0 2 * * *"  # daily at 2am UTC
  image:
    repository: my-org/database-backup
  env:
    MINIO_ENDPOINT: "minio.home"
    MINIO_BUCKET: "backups"
```

## Observability Service

Handles monitoring, logging, and alerting.

```
services/observability/
├── README.md
├── prometheus/             ← Prometheus configuration
│   ├── scrape-configs/
│   └── alert-rules/
├── grafana/                ← Grafana dashboards
│   ├── home-automation-overview/
│   ├── cronjob-success-rate/
│   └── resource-usage/
├── loki/                   ← Log aggregation
│   └── pipeline-config.yaml
└── alerts/
    ├── failed-jobs.yaml
    ├── high-memory.yaml
    └── pod-crashes.yaml
```

### Metrics from Automations

Every automation can export metrics:

```yaml
# charts/my-automation/values.yaml
base-chart:
  podAnnotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8000"
    prometheus.io/path: "/metrics"
```

Then Prometheus scrapes them and Grafana visualizes.

## Messaging Service

Handles notifications across channels.

```
services/messaging/
├── README.md
├── telegram/               ← Telegram bot config
│   ├── token.enc.yaml
│   └── chat-ids.yaml
├── email/                  ← Email config
│   ├── smtp-config.yaml
│   └── templates/
├── webhooks/               ← Webhook routing
│   ├── slack-webhook.yaml
│   └── custom-webhooks.yaml
└── router/                 ← Multi-channel routing
    └── notification-router.yaml
```

### Sending Notifications

From any automation:

```python
# In your automation code
from homelab.notifications import NotificationRouter

router = NotificationRouter(
    telegram_token=os.environ["TELEGRAM_BOT_TOKEN"],
    telegram_chat_id=os.environ["TELEGRAM_CHAT_ID"],
)

# Send to all configured channels
router.notify(
    title="Backup Complete",
    message="Database backup succeeded",
    severity="success"
)
```

## Security Service

Manages secrets, encryption, and access control.

```
services/security/
├── README.md
├── sops-setup/             ← SOPS + age configuration
│   ├── keys.txt
│   └── .sops.yaml
├── vault/                  ← Vault configuration (future)
│   └── policies/
├── external-secrets/       ← External Secrets Operator
│   └── secret-stores.yaml
└── rbac-templates/         ← RBAC best practices
    ├── read-only.yaml
    ├── admin.yaml
    └── ci-cd.yaml
```

### Managing Secrets

All secrets are encrypted with SOPS before committing:

```bash
# Create plaintext
cat > secrets.yaml <<EOF
NOTION_API_KEY: "secret_value"
EOF

# Encrypt
sops -e secrets.yaml > secrets.enc.yaml

# Delete plaintext
rm secrets.yaml

# Commit encrypted
git add secrets.enc.yaml
```

## Philosophy

**Services organize the platform, automations use the services.**

A service is a concern (observability, messaging, storage) that:
- Is shared across multiple automations
- Has configuration and setup
- Should be updated independently
- Can evolve without breaking automations

An automation is a use of a service:
- "Run a backup job" → uses `storage` service
- "Send a notification" → uses `messaging` service
- "Scrape metrics" → uses `observability` service

## Best Practices

1. **One service per concern** — easy to understand
2. **Shared configuration** — DRY principle
3. **Clear interfaces** — documented how automations use it
4. **Backward compatibility** — updates don't break automations
5. **Sensible defaults** — minimal override needed

## Adding a New Service

1. Create directory: `services/my-service/`
2. Add README explaining the service
3. Add configuration files and templates
4. Add examples showing how automations use it
5. Document environment variables and secrets
6. Link from this README

## Future Services

As the platform grows:

- **Database** — PostgreSQL, MySQL connections, migrations
- **Cache** — Redis, Memcached configuration
- **Search** — Elasticsearch, OpenSearch integration
- **Files** — Document processing, OCR
- **Analytics** — BigQuery, data warehouse integration
- **Payments** — Stripe, payment processing
- **Scheduling** — Complex workflows, dependencies
- **Secrets** — Vault, credential management

---

See also: [../platform/README.md](../platform/README.md), [../charts/README.md](../charts/README.md)
