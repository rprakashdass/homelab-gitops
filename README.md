# homelab-gitops (PRIVATE)

Production-quality personal Kubernetes platform — GitOps, Helm, ArgoCD.

Not a homelab. A personal Internal Developer Platform (IDP) for automation.

## Vision

Build a Kubernetes-native platform that automates daily/personal life while teaching Platform Engineering fundamentals.

**Core Principles:**
- GitOps first
- Kubernetes native
- Helm first
- Modular and reusable
- Production quality
- Simple before clever

## Architecture

Monorepo structure organized by capability, not technology:

```
homelab-gitops/
├── infrastructure/           ← Cluster components
│   └── argocd/              ← ArgoCD config
│       ├── project.yaml     ← ArgoCD Project definition
│       └── applications/    ← ArgoCD Application manifests
├── platform/                ← Reusable platform capabilities
│   ├── base-chart/          ← Universal Helm chart (foundation)
│   ├── templates/           ← Reusable k8s templates
│   ├── libraries/           ← Shared code libraries
│   ├── notifications/       ← Notification abstractions
│   ├── common/              ← Common utilities
│   ├── rbac/                ← RBAC templates
│   ├── policies/            ← Security policies
│   └── secrets/             ← Secret management setup
├── platform/common/         ← Shared services
│   └── telegram-bot/        ← Centralized Telegram bot
├── services/                ← Domain-specific services
│   ├── automation/          ← Cronjobs, workflows, schedules
│   │   ├── hello-world/     ← Daily heartbeat (bootstrap)
│   │   ├── k8s-health-report/  ← Weekly cluster health
│   │   └── notion-automations/ ← Monthly Notion generation
│   ├── ai/                  ← AI agents, RAG, summarization
│   ├── storage/             ← MinIO, backups, archives
│   ├── observability/       ← Prometheus, Grafana, Loki
│   └── security/            ← SOPS, Vault, secrets
├── apps/                    ← Third-party applications
└── .sops.yaml               ← Secret encryption config
```

## Key Files

| Path | Purpose |
|------|---------|
| `infrastructure/argocd/project.yaml` | ArgoCD Project — defines what this project can do |
| `infrastructure/argocd/applications/` | ArgoCD Applications — one per service/automation |
| `platform/base-chart/` | Universal reusable Helm chart (all services extend this) |
| `services/<category>/<service>/` | Individual service Helm charts (extend base-chart) |
| `platform/common/<service>/` | Shared services (extend base-chart) |
| `.sops.yaml` | SOPS encryption config for secrets |

## Getting Started

### 1. Replace Template Values

Search for `rprakashdass` and update with your GitHub username:

```bash
grep -r "rprakashdass" .
```

Also update the email in `maintainers` sections.

### 2. Create ArgoCD Project

This defines your ArgoCD project and what it's allowed to do:

```bash
kubectl create namespace argocd  # if not already created
kubectl apply -f infrastructure/argocd/project.yaml
```

### 3. Create ArgoCD Applications

Each service is managed by an ArgoCD Application:

```bash
kubectl apply -f infrastructure/argocd/applications/
```

ArgoCD will:
1. Pull the chart from `charts/*/`
2. Render it with Helm
3. Deploy to the `home` namespace
4. Continuously sync (auto-heal, prune)

### 4. Verify

```bash
# Check applications
kubectl get applications -n argocd

# Check synced resources
kubectl get all -n home

# Check cronjob schedules
kubectl get cronjob -n home

# View logs
kubectl logs -n home -l app.kubernetes.io/name=hello-world
```

## Adding a New Automation

Every new automation follows this pattern:

### 1. Create Chart

Choose a category (`automation`, `ai`, `storage`, `observability`, `security`) and create:

```bash
mkdir -p services/<category>/my-new-automation
```

Create `services/<category>/my-new-automation/Chart.yaml`:

```yaml
apiVersion: v2
name: my-new-automation
description: "My new automation"
type: application
version: 1.0.0
appVersion: "1.0"
keywords:
  - automation

home: https://github.com/rprakashdass/homelab-gitops
sources:
  - https://github.com/rprakashdass/homelab-gitops

maintainers:
  - name: rprakashdass
    email: rprakashdass@gmail.com

dependencies:
  - name: base-chart
    version: "1.0.0"
    repository: "file://../../platform/base-chart"
```

Create `services/<category>/my-new-automation/values.yaml`:

```yaml
base-chart:
  kind: cronjob
  schedule: "0 9 * * *"  # 9am UTC daily
  image:
    repository: my-org/my-image
    tag: "1.0"
  resources:
    limits:
      memory: "256Mi"
```

### 2. Create ArgoCD Application

Create `infrastructure/argocd/applications/my-new-automation.yaml`:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: home-my-new-automation
  namespace: argocd
  labels:
    app.kubernetes.io/name: home-my-new-automation
    app.kubernetes.io/component: argocd-application
    app.kubernetes.io/part-of: home-automation-platform
  annotations:
    app.kubernetes.io/description: "My new automation"
    argocd.argoproj.io/sync-wave: "1"
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: home
  source:
    repoURL: https://github.com/rprakashdass/homelab-gitops.git
    targetRevision: main
    path: services/<category>/my-new-automation
  destination:
    server: https://kubernetes.default.svc
    namespace: home
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - ServerSideApply=true
    retry:
      limit: 3
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
```

### 3. Deploy

```bash
git add services/<category>/my-new-automation infrastructure/argocd/applications/my-new-automation.yaml
git commit -m "feat: add my-new-automation"
git push
# ArgoCD syncs automatically
```

## Base Chart

The **base-chart** is the foundation for all services. It's a universal, reusable Helm chart that supports:

- **Workloads**: Deployment, StatefulSet, CronJob, Job
- **Networking**: Service, Ingress
- **Storage**: PersistentVolumeClaim, ConfigMap, Secret
- **Scaling**: HorizontalPodAutoscaler
- **Security**: ServiceAccount, Role, RoleBinding, securityContext
- **Health**: Liveness, Readiness, Startup probes

See [platform/base-chart/README.md](platform/base-chart/README.md) for detailed docs.

### Example: CronJob

```yaml
# charts/my-cronjob/values.yaml
base-chart:
  kind: cronjob
  schedule: "0 7 * * *"
  image:
    repository: busybox
    tag: "latest"
  command: ["/bin/sh"]
  args:
    - -c
    - echo "Hello from $(date)"
  resources:
    limits:
      memory: "128Mi"
```

### Example: Deployment with Service

```yaml
# charts/my-api/values.yaml
base-chart:
  kind: deployment
  replicaCount: 2
  image:
    repository: my-api
    tag: "1.0"
  service:
    enabled: true
    port: 8080
    targetPort: 8080
  ingress:
    enabled: true
    hosts:
      - host: my-api.home
        paths:
          - path: /
            pathType: Prefix
  resources:
    limits:
      memory: "512Mi"
      cpu: "500m"
```

## Secret Management

Secrets are encrypted with SOPS + age before committing.

### Setup (first time only)

```bash
# Generate age key (if not exists)
age-keygen -o ~/.config/sops/age/keys.txt

# Get your public key
age-keygen -y ~/.config/sops/age/keys.txt

# Add public key to .sops.yaml in this repo
```

### Create a Secret

```bash
# Create plaintext (never commit)
cat > services/<category>/my-automation/secrets.yaml <<EOF
notion:
  apiKey: "secret_your_token_here"
EOF

# Encrypt with SOPS
sops -e services/<category>/my-automation/secrets.yaml \
  > services/<category>/my-automation/secrets.enc.yaml

# Delete plaintext
rm services/<category>/my-automation/secrets.yaml

# Commit encrypted only
git add services/<category>/my-automation/secrets.enc.yaml
git commit -m "feat: add encrypted secrets for my-automation"
```

### Use Secret in Chart

In your `services/<category>/my-automation/Chart.yaml`, reference the secret:

```yaml
base-chart:
  secret:
    enabled: true
    data:
      API_KEY: ENC[AES256_GCM,data:...,type:str]
      # ... other encrypted values
```

Or in `values.yaml`:

```yaml
base-chart:
  secret:
    enabled: true
    # Will be merged with values from values-secrets.enc.yaml
```

Then use in the container as environment variables:

```yaml
env:
  - name: NOTION_API_KEY
    valueFrom:
      secretKeyRef:
        name: my-automation
        key: API_KEY
```

## Bootstrap Phase

Started with minimal complexity:

✅ Base Helm chart (universal, reusable)
✅ Three bootstrap automations:
  - hello-world (daily timestamp)
  - k8s-health-report (weekly cluster health)
  - notion-monthly (placeholder for future)
✅ ArgoCD setup
✅ SOPS encryption ready
✅ Production-quality manifests (RBAC, security contexts, resource limits)

## Next Phases

As the platform grows:

**Phase 2 — Platform Abstractions:**
- Notification library (Telegram, email)
- Configuration management (reload patterns)
- Database/storage utilities
- Caching strategies

**Phase 3 — Real Integrations:**
- Notion API client + monthly generation
- GitHub activity summarizer
- Resume generator
- AI-powered document summarization
- Personal expense tracker

**Phase 4 — Observability:**
- Prometheus metrics from all automations
- Grafana dashboards
- Loki log aggregation
- Alerting on failures

**Phase 5 — Scale:**
- 50+ automations
- Complex workflows (Argo Workflows)
- Multi-tenant abstractions (future)
- Community contributions (publish shared libraries)

## Development

### Lint Helm charts

```bash
helm lint platform/base-chart
helm lint charts/hello-world
```

### Test Helm rendering

```bash
helm template home charts/hello-world \
  -f platform/base-chart/values.yaml
```

### View what ArgoCD will deploy

```bash
kubectl diff -f infrastructure/argocd/applications/hello-world.yaml
```

## Documentation

Each directory has a README explaining:
- What belongs there
- Why it exists
- Best practices
- Future purpose

Start with:
- [platform/base-chart/README.md](platform/base-chart/README.md) — Helm foundation
- [infrastructure/argocd/README.md](infrastructure/argocd/README.md) — ArgoCD setup
- Service-specific READMEs (coming soon)

## Philosophy

### Why Monorepo?

- Everything in one place ✓
- Easier to evolve as you learn ✓
- Simple to manage (no cross-repo coordination) ✓
- Single git history ✓
- Charts, values, and scripts evolve together ✓

### DRY Principle

- Base chart eliminates boilerplate
- Reusable templates in `platform/`
- Common libraries in `platform/common/`
- No copy-paste between charts

### Production Quality

Even though this is a personal platform, every manifest includes:
- Labels and annotations
- Resource requests and limits
- Security contexts (non-root, read-only filesystem)
- RBAC (least privilege)
- Health checks (where applicable)
- Proper error handling
- Documented trade-offs

### Simple Before Clever

- Bash/Python/Go scripts before complex frameworks
- Direct kubectl before Argo Workflows (until needed)
- Local state before distributed systems
- Prefer maintainability over cleverness

## Status

```
┌──────────────────────────────────────────────────────┐
│  v0.1.0 — Bootstrap Phase Complete                   │
├──────────────────────────────────────────────────────┤
│ ✅ Monorepo structure                                │
│ ✅ Base Helm chart (universal reusable)              │
│ ✅ Hello-world CronJob (daily timestamp)             │
│ ✅ K8s health report CronJob (weekly)                │
│ ✅ Notion placeholder (ready for integration)        │
│ ✅ ArgoCD Applications (auto-sync)                   │
│ ✅ SOPS encryption ready                             │
│ ✅ Production manifests (RBAC, security, limits)     │
├──────────────────────────────────────────────────────┤
│ ⏳ Phase 2 — Platform libraries                      │
│ ⏳ Phase 3 — Real API integrations                   │
│ ⏳ Phase 4 — Observability & monitoring              │
│ ⏳ Phase 5 — Scale to 50+ automations                │
└──────────────────────────────────────────────────────┘
```

## Further Reading

- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)
- [Helm Documentation](https://helm.sh/docs/)
- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [SOPS - Secrets Operations](https://github.com/mozilla/sops)
- [age - A simple, modern encryption tool](https://github.com/FiloSottile/age)

---

**Repository**: PRIVATE
**Owner**: You
**Email**: rprakashdass@gmail.com
**Status**: Active development
