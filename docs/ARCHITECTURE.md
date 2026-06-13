# Architecture

Complete visual guide to the personal platform structure.

## Directory Tree

```
homelab-gitops/
├── README.md                           ← Start here: full documentation
├── QUICKSTART.md                       ← 5-minute setup guide
├── BOOTSTRAP_SUMMARY.md                ← What was built, why, next steps
├── ARCHITECTURE.md                     ← This file
├── .sops.yaml                          ← SOPS encryption config
│
├── infrastructure/                     ← Cluster bootstrap & setup
│   ├── README.md                       ← Infrastructure guide
│   ├── argocd/
│   │   ├── project.yaml                ← ArgoCD Project definition
│   │   └── applications/               ← One Application per automation
│   │       ├── hello-world.yaml
│   │       ├── k8s-health-report.yaml
│   │       └── notion-monthly.yaml
│   ├── ingress/                        ← Traefik config (future)
│   ├── storage-class/                  ← Storage provisioning (future)
│   ├── monitoring-bootstrap/           ← Prometheus/Grafana (future)
│   └── cert-manager/                   ← TLS certificates (future)
│
├── platform/                           ← Reusable capabilities
│   ├── README.md                       ← Platform guide
│   ├── base-chart/                     ← Universal Helm chart (foundation)
│   │   ├── Chart.yaml
│   │   ├── values.yaml                 ← All configuration options
│   │   ├── README.md                   ← How to use base-chart
│   │   └── templates/                  ← Kubernetes manifest templates
│   │       ├── _helpers.tpl            ← Helm template helpers
│   │       ├── workload.yaml           ← Deployment, StatefulSet, CronJob, Job
│   │       ├── service.yaml            ← Kubernetes Service
│   │       ├── ingress.yaml            ← Ingress for external access
│   │       ├── configmap.yaml          ← Configuration
│   │       ├── secret.yaml             ← Secrets
│   │       ├── pvc.yaml                ← Persistent storage
│   │       ├── hpa.yaml                ← Horizontal Pod Autoscaler
│   │       ├── serviceaccount.yaml     ← Service account for RBAC
│   │       ├── role.yaml               ← RBAC Role
│   │       └── rolebinding.yaml        ← RBAC RoleBinding
│   │
│   ├── libraries/                      ← Reusable code (Python, Go, Shell)
│   │   ├── python/                     ← Python packages
│   │   │   ├── homelab/                ← Main package
│   │   │   │   ├── k8s.py              ← Kubernetes helpers
│   │   │   │   ├── telegram.py         ← Telegram bot abstraction
│   │   │   │   ├── github.py           ← GitHub API helpers
│   │   │   │   └── logging.py          ← Structured logging
│   │   │   └── requirements.txt
│   │   ├── go/                         ← Go packages
│   │   │   ├── k8s/                    ← Kubernetes client wrappers
│   │   │   ├── telegram/               ← Telegram bot package
│   │   │   └── go.mod
│   │   └── shell/                      ← Shell utilities
│   │       ├── common.sh               ← Common functions
│   │       └── k8s-helpers.sh
│   │
│   ├── templates/                      ← Reusable k8s templates
│   ├── notifications/                  ← Notification abstractions
│   │   ├── telegram.yaml               ← Telegram notification template
│   │   ├── email.yaml                  ← Email template
│   │   └── webhook.yaml                ← Webhook template
│   │
│   ├── common/                         ← Common utilities
│   │   ├── logging.yaml                ← Logging patterns
│   │   ├── metrics.yaml                ← Prometheus metrics
│   │   └── config.yaml                 ← Configuration patterns
│   │
│   ├── rbac/                           ← RBAC policy templates
│   │   ├── read-pods.yaml              ← Read pods in namespace
│   │   ├── read-events.yaml            ← Read events/logs
│   │   └── full-admin.yaml
│   │
│   ├── policies/                       ← Security policies
│   │   ├── network-policies/           ← NetworkPolicy definitions
│   │   ├── pod-security/               ← PodSecurityPolicy
│   │   └── resource-quotas/            ← ResourceQuota templates
│   │
│   ├── secrets/                        ← Secret management setup
│   │   ├── setup.md                    ← SOPS + age setup guide
│   │   ├── examples/                   ← Example encrypted files
│   │   └── rotation.md                 ← Secret rotation patterns
│   │
│   └── workflowtemplates/              ← Argo Workflow templates (future)
│
├── services/                           ← Service abstractions
│   ├── README.md                       ← Services guide
│   ├── automation/                     ← CronJobs, workflows, schedules
│   │   ├── README.md
│   │   ├── cron-templates/             ← CronJob examples
│   │   └── workflow-templates/         ← Argo Workflow templates
│   │
│   ├── ai/                             ← AI agents, RAG, summarization
│   │   ├── README.md
│   │   ├── prompts/                    ← Prompt templates
│   │   ├── models/                     ← Model configurations
│   │   └── rag/                        ← RAG setup
│   │
│   ├── storage/                        ← MinIO, backups, archives
│   │   ├── README.md
│   │   ├── minio-config.yaml
│   │   ├── backup-policies/
│   │   └── lifecycle-policies/
│   │
│   ├── observability/                  ← Prometheus, Grafana, Loki
│   │   ├── README.md
│   │   ├── prometheus/                 ← Prometheus config
│   │   ├── grafana/                    ← Grafana dashboards
│   │   ├── loki/                       ← Log aggregation
│   │   └── alerts/                     ← Alert rules
│   │
│   ├── messaging/                      ← Telegram, email, webhooks
│   │   ├── README.md
│   │   ├── telegram/                   ← Telegram bot config
│   │   ├── email/                      ← Email config
│   │   ├── webhooks/                   ← Webhook routing
│   │   └── router/                     ← Notification router
│   │
│   └── security/                       ← SOPS, Vault, secrets
│       ├── README.md
│       ├── sops-setup/                 ← SOPS config
│       ├── vault/                      ← Vault setup (future)
│       └── external-secrets/           ← External Secrets Operator (future)
│
├── charts/                             ← Helm charts (monorepo)
│   ├── README.md                       ← How to create charts
│   ├── hello-world/                    ← Bootstrap example: daily logger
│   │   ├── Chart.yaml
│   │   ├── values.yaml
│   │   └── README.md
│   │
│   ├── k8s-health-report/              ← Bootstrap example: cluster health
│   │   ├── Chart.yaml
│   │   ├── values.yaml
│   │   └── README.md
│   │
│   └── notion-monthly/                 ← Bootstrap example: Notion placeholder
│       ├── Chart.yaml
│       ├── values.yaml
│       └── README.md
│
└── apps/                               ← Third-party applications
    └── README.md                       ← External apps (empty for now)
```

## Data Flow

### From Git to Cluster

```
┌─────────────────────────────────────┐
│     You push to GitHub              │
│  (charts/, infrastructure/, etc)    │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│   GitHub Webhook (optional)         │
│   Notifies ArgoCD of changes        │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│    ArgoCD (in cluster)              │
│                                     │
│  1. Polls repo every 3 minutes      │
│  2. Detects changes                 │
│  3. Runs: helm template             │
│  4. Compares with cluster state     │
│  5. Applies changes (if different)  │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│   Kubernetes API Server             │
│   Updates cluster resources         │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│   Kubernetes Controller              │
│   (kubelet, kube-scheduler, etc)    │
│                                     │
│   1. Creates pods                   │
│   2. Runs CronJobs on schedule      │
│   3. Manages lifecycle              │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│   Your Automations Run!             │
│                                     │
│   - hello-world (daily)             │
│   - k8s-health-report (weekly)      │
│   - notion-monthly (monthly)        │
│   - (your custom automations)       │
└─────────────────────────────────────┘
```

## Chart Architecture

Each chart extends base-chart:

```
┌──────────────────────────────────────┐
│   platform/base-chart/               │
│   (universal, reusable foundation)   │
│                                      │
│   Templates:                         │
│   - workload.yaml (all types)        │
│   - service.yaml                     │
│   - ingress.yaml                     │
│   - configmap.yaml                   │
│   - secret.yaml                      │
│   - pvc.yaml, hpa.yaml               │
│   - rbac (role, rolebinding)         │
│                                      │
│   Values: 100+ configurable options  │
└────────────┬─────────────────────────┘
             │
    ┌────────┼────────┬────────────────┐
    │        │        │                │
    ▼        ▼        ▼                ▼
┌──────┐┌─────┐┌──────┐    ┌───────────┐
│hello │││k8s- ││notion│    │ (future)  │
│world ││health││monthly   │ automations│
└──────┘└─────┘└──────┘    └───────────┘
    │        │        │                │
    └────────┼────────┴────────────────┘
             │
    Extend base-chart with values.yaml:
    - image: (container image)
    - schedule: (cron)
    - resources: (limits)
    - command: (what to run)
    - secret: (encrypted data)
    - rbac: (permissions)
    - etc
```

## Deployment Pipeline

```
┌──────────────────────────────────────────────────────┐
│  You create/modify chart                             │
│  - charts/my-automation/Chart.yaml                   │
│  - charts/my-automation/values.yaml                  │
└────────────────┬─────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────┐
│  Create ArgoCD Application                           │
│  - infrastructure/argocd/applications/my-automation  │
│  (Points to charts/my-automation/)                   │
└────────────────┬─────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────┐
│  Commit and push to GitHub                           │
│  git add charts/my-automation/                       │
│  git add infrastructure/argocd/applications/         │
│  git push                                            │
└────────────────┬─────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────┐
│  ArgoCD detects change and syncs                     │
│  1. Reads charts/my-automation/Chart.yaml            │
│  2. Resolves dependency: base-chart                  │
│  3. Merges values (base + my-automation)             │
│  4. Renders Helm templates                          │
│  5. Deploys to cluster                              │
└────────────────┬─────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────┐
│  Your automation is live!                            │
│  - Runs on schedule (CronJob)                        │
│  - Observable (logs, metrics, events)               │
│  - Reliable (RBAC, security, limits)                │
│  - Maintainable (clear code, documented)            │
└──────────────────────────────────────────────────────┘
```

## Component Relationships

```
┌─────────────────────────────────────────────────────────┐
│              infrastructure/                             │
│  Cluster bootstrap, ArgoCD, networking, storage         │
├─────────────────────────────────────────────────────────┤
│              platform/                                   │
│  Reusable libraries, base-chart, abstractions           │
│  (shared by all services and charts)                    │
├─────────────────────────────────────────────────────────┤
│              services/                                   │
│  Service configurations: automation, ai, storage, etc   │
│  (define capabilities that automations use)            │
├─────────────────────────────────────────────────────────┤
│              charts/                                     │
│  Individual automation Helm charts                      │
│  (extend base-chart, use services)                     │
├─────────────────────────────────────────────────────────┤
│              apps/                                       │
│  Third-party applications (low priority)               │
└─────────────────────────────────────────────────────────┘

Dependency flow:
  charts/ ──depends on──> base-chart (platform/)
                          └──> libraries (platform/)
                          └──> services/ configurations

  base-chart ──depends on──> No other components
  services/  ──depends on──> Nothing (just config)
  platform/  ──depends on──> Nothing (foundation)
```

## Security Model

```
┌──────────────────────────────────────────────────────┐
│  Secrets (SOPS + age encrypted)                      │
│  - Never stored in plaintext in git                  │
│  - Encrypted with SOPS before committing             │
│  - age key stored locally (~/.config/sops/age/)      │
│  - ArgoCD decrypts automatically at sync time        │
├──────────────────────────────────────────────────────┤
│  RBAC (Least Privilege)                              │
│  - Each automation has its own ServiceAccount        │
│  - Role defines minimal required permissions         │
│  - RoleBinding connects ServiceAccount to Role       │
├──────────────────────────────────────────────────────┤
│  Security Context (Non-root, read-only)              │
│  - Containers run as user 1000 (not root)            │
│  - Filesystem is read-only (except /tmp)             │
│  - Capabilities dropped (CAP_ALL)                    │
├──────────────────────────────────────────────────────┤
│  Resource Limits (Prevent DoS)                       │
│  - CPU limits prevent runaway processes              │
│  - Memory limits prevent OOMKills                    │
│  - Based on expected workload size                   │
└──────────────────────────────────────────────────────┘
```

## Scalability Model

```
┌───────────────────────────────────────────────────────┐
│ Bootstrap Phase (v0.1)                                │
│ - 3 example automations                               │
│ - 1 universal base-chart                              │
│ - ~50 lines of YAML (very DRY)                        │
├───────────────────────────────────────────────────────┤
│ Phase 2: Platform Libraries                          │
│ - Add Python/Go reusable libraries                    │
│ - No new infrastructure needed                        │
│ - Charts still use same base-chart                    │
├───────────────────────────────────────────────────────┤
│ Phase 3: Real Automations (5-20 more)                │
│ - Each still extends base-chart                       │
│ - Total YAML stays minimal (DRY)                      │
│ - No infrastructure changes needed                    │
├───────────────────────────────────────────────────────┤
│ Phase 4: Observability                               │
│ - Add Prometheus, Grafana, Loki                       │
│ - All automations emit metrics/logs                   │
│ - No chart changes needed                             │
├───────────────────────────────────────────────────────┤
│ Phase 5: Scale to 50+ automations                    │
│ - Still using same base-chart                         │
│ - Platform libraries fully mature                     │
│ - Observability comprehensive                        │
│ - GitOps managing everything                         │
└───────────────────────────────────────────────────────┘

Scaling is EASY because:
- Base-chart scales to any number of charts
- Platform libraries are reusable
- Services define capabilities once
- Git history tracks evolution
- ArgoCD handles deployment at any scale
```

## Example: How Hello-World Works

```
1. Chart Definition
   charts/hello-world/Chart.yaml
   - Declares dependency on base-chart

2. Values
   charts/hello-world/values.yaml
   - Sets base-chart:
     - kind: cronjob
     - schedule: "0 7 * * *"
     - image: busybox
     - command: echo "Hello from..."

3. ArgoCD Application
   infrastructure/argocd/applications/hello-world.yaml
   - Points to charts/hello-world/
   - Specifies namespace: home

4. Helm Rendering
   Helm template test charts/hello-world
   - Reads Chart.yaml (dependency: base-chart)
   - Reads values.yaml (hello-world config)
   - Renders templates/workload.yaml with values
   - Creates CronJob manifest

5. Deployment
   ArgoCD detects git change
   - Renders CronJob manifest
   - Applies to cluster
   - CronJob scheduled

6. Execution
   kubelet/kube-scheduler
   - Watches CronJob schedule
   - At 07:00 UTC daily, creates Job
   - Job creates Pod
   - Pod runs container
   - Pod logs output

7. Observation
   kubectl logs -n home -l app.kubernetes.io/name=hello-world
   - Shows: "Hello from the personal platform!"
   - Shows: timestamp
   - Shows: pod name
```

## Reading Guide

- **Quick start?** → [QUICKSTART.md](QUICKSTART.md)
- **Full vision?** → [README.md](README.md)
- **Create a chart?** → [charts/README.md](charts/README.md)
- **Understand base-chart?** → [platform/base-chart/README.md](platform/base-chart/README.md)
- **Set up secrets?** → [platform/README.md](platform/README.md) + `platform/secrets/`
- **Add a service?** → [services/README.md](services/README.md)
- **Deploy to cluster?** → [infrastructure/README.md](infrastructure/README.md)
- **Phase summary?** → [BOOTSTRAP_SUMMARY.md](BOOTSTRAP_SUMMARY.md)
- **This file?** → You're reading it!

---

**You now understand the complete architecture.** 🎯

Ready to: [Deploy](QUICKSTART.md) | [Create automation](charts/README.md) | [Read full guide](README.md)
