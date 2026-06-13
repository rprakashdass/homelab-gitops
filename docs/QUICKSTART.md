# Quick Start Guide

Get your personal platform up and running in 5 minutes.

## Prerequisites

- k3s cluster running (or any Kubernetes cluster)
- ArgoCD installed in the cluster
- `kubectl` configured for your cluster
- `git` and `helm` installed locally

## Steps

### 1. Clone the repository

```bash
git clone https://github.com/rprakashdass/homelab-gitops.git
cd homelab-gitops
```

### 2. Update placeholders

Search for `rprakashdass` and replace with your GitHub username:

```bash
# On macOS
find . -type f \( -name "*.yaml" -o -name "*.md" \) \
  -exec sed -i '' 's/REPLACE_ME_USERNAME/YOUR_USERNAME/g' {} \;

# On Linux
find . -type f \( -name "*.yaml" -o -name "*.md" \) \
  -exec sed -i 's/REPLACE_ME_USERNAME/YOUR_USERNAME/g' {} \;
```

Also update email addresses if needed.

### 3. Create namespace

```bash
kubectl create namespace home
```

### 4. Apply ArgoCD Project

This defines what your platform can do:

```bash
kubectl apply -f infrastructure/argocd/project.yaml
```

Verify:

```bash
kubectl get appproject -n argocd
# Should show: home
```

### 5. Apply ArgoCD Applications

Deploy the bootstrap automations:

```bash
kubectl apply -f infrastructure/argocd/applications/
```

Verify:

```bash
kubectl get applications -n argocd
# Should show:
# home-hello-world
# home-k8s-health-report
# home-notion-monthly
```

### 6. Wait for sync

ArgoCD syncs automatically. Check status:

```bash
kubectl get applications -n argocd -w
```

Wait until all show `Synced` status (usually < 30 seconds).

### 7. Verify CronJobs

```bash
kubectl get cronjob -n home
```

You should see:
- `home-hello-world` (daily at 7:00 AM UTC)
- `home-k8s-health-report` (weekly at 6:00 AM UTC)
- `home-notion-monthly` (monthly on 1st at 12:00 AM UTC)

### 8. Test manually

Trigger hello-world immediately:

```bash
kubectl create job --from=cronjob/home-hello-world test-1 -n home
```

Watch the job:

```bash
kubectl get pods -n home -w
kubectl logs -n home -l app.kubernetes.io/name=hello-world --tail=20
```

You should see output like:

```
Hello from the personal platform!
Current timestamp: 2024-06-13 14:32:45 UTC
Pod: test-1-xxxxx
```

Done! ✅

## Next Steps

1. **Review the architecture** → Read [README.md](README.md)
2. **Understand base-chart** → Read [platform/base-chart/README.md](platform/base-chart/README.md)
3. **Create your first automation** → See [charts/README.md](charts/README.md)
4. **Set up secrets** → Read [SOPS setup](platform/base-chart/README.md)

## Troubleshooting

### ArgoCD Applications not syncing

```bash
# Check ArgoCD logs
kubectl logs -n argocd -l app.argoproj.io=argocd-server

# Check application details
kubectl describe application home-hello-world -n argocd
```

### CronJobs not running

```bash
# Check cronjob status
kubectl describe cronjob home-hello-world -n home

# Check if namespace exists
kubectl get namespace home

# Check RBAC
kubectl get serviceaccount -n home
kubectl get role -n home
kubectl get rolebinding -n home
```

### Pods in error state

```bash
# See pod status
kubectl get pods -n home

# Get pod events
kubectl describe pod PODNAME -n home

# View logs
kubectl logs -n home PODNAME
```

## Common Commands

```bash
# View all resources
kubectl get all -n home

# View CronJob schedules
kubectl get cronjob -n home -o wide

# View recent job executions
kubectl get jobs -n home --sort-by=.metadata.creationTimestamp

# Trigger a job manually
kubectl create job --from=cronjob/CRONJOB_NAME manual-TIMESTAMP -n home

# View logs from last run
kubectl logs -n home -l app.kubernetes.io/name=AUTOMATION_NAME --tail=50

# Watch live syncing
kubectl get applications -n argocd -w

# Restart ArgoCD (if needed)
kubectl rollout restart deployment/argocd-server -n argocd
```

## Repository Structure Overview

```
homelab-gitops/
├── infrastructure/            ← Cluster setup (ArgoCD, etc)
│   └── argocd/               ← ArgoCD Project + Applications
├── platform/                  ← Reusable capabilities
│   └── base-chart/           ← Universal Helm chart foundation
├── services/                  ← Service configurations
├── charts/                    ← Individual automation charts
│   ├── hello-world/          ← Daily hello-world logger
│   ├── k8s-health-report/    ← Weekly cluster health
│   └── notion-monthly/       ← Monthly Notion (placeholder)
├── apps/                      ← Third-party apps (empty for now)
├── README.md                  ← Full documentation
├── QUICKSTART.md              ← This file
└── .sops.yaml                 ← Secret encryption config
```

## Architecture Diagram

```
┌──────────────────────────────────────┐
│         Git Repository               │
│  (homelab-gitops)                    │
│                                      │
│  ├── charts/hello-world/             │
│  ├── charts/k8s-health-report/       │
│  ├── platform/base-chart/            │
│  └── infrastructure/argocd/          │
└─────────────────┬────────────────────┘
                  │ (git push)
                  ▼
┌──────────────────────────────────────┐
│      GitHub (Your Repository)        │
└─────────────────┬────────────────────┘
                  │ (webhook)
                  ▼
┌──────────────────────────────────────┐
│    ArgoCD Controller (in cluster)    │
│                                      │
│  Monitors repository for changes     │
│  Syncs Kubernetes manifests          │
│  Auto-heals drift                    │
└─────────────────┬────────────────────┘
                  │ (deploys)
                  ▼
┌──────────────────────────────────────┐
│     Kubernetes Cluster (k3s)         │
│                                      │
│  namespace: home                     │
│  ├── CronJob: hello-world            │
│  ├── CronJob: k8s-health-report      │
│  ├── CronJob: notion-monthly         │
│  ├── ServiceAccount, RBAC, Secrets   │
│  └── ...                             │
└──────────────────────────────────────┘
```

## What Just Happened

1. **ArgoCD watches** your GitHub repository
2. **When you push changes**, ArgoCD detects them
3. **ArgoCD renders Helm charts** with values from the repo
4. **ArgoCD deploys** manifests to the cluster
5. **Kubernetes runs CronJobs** on their schedules
6. **You get automated workflows** that run reliably

This is **GitOps** — your Git repository is the source of truth for what runs in your cluster.

## Support

- Full docs: [README.md](README.md)
- Helm guide: [platform/base-chart/README.md](platform/base-chart/README.md)
- Automation examples: [charts/README.md](charts/README.md)
- Architecture: [infrastructure/README.md](infrastructure/README.md)

---

**Welcome to your personal Platform Engineering journey!** 🚀
