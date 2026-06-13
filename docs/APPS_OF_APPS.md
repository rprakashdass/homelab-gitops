# Apps of Apps Architecture

Complete guide to the "Apps of Apps" pattern for managing platform applications.

## What Changed?

### Before (Individual Applications)

```
infrastructure/argocd/applications/
├── hello-world.yaml
├── k8s-health-report.yaml
├── notion-monthly.yaml
└── ... (one file per app)
```

**Problem:** To enable/disable an app or add a new one, you manually edit YAML files.

### After (Apps of Apps)

```
platform/applications-chart/
├── Chart.yaml
├── values.yaml         ← Single source of truth
└── templates/
    └── applications.yaml  ← Generates all Applications
```

**Solution:** Edit one `values.yaml` file. Helm generates the Applications. ArgoCD deploys them.

## How It Works

### Step 1: You Edit values.yaml

```yaml
applications:
  hello-world:
    enabled: true    # ✅ Deployed
  
  github-summary:
    enabled: false   # ⏸ Not deployed
```

### Step 2: Helm Generates Applications

The template `applications.yaml` loops through values and creates:

```yaml
kind: Application
metadata:
  name: home-hello-world
spec:
  source:
    path: charts/hello-world
  ...
---
# github-summary is NOT generated (enabled: false)
```

### Step 3: ArgoCD Deploys Applications

The bootstrap Application (`platform-applications`) syncs the Helm chart:

```bash
ArgoCD: "Render Helm chart → Get generated Applications → Deploy to cluster"
```

### Step 4: Generated Applications Deploy Services

Each generated Application pulls from its chart:

```bash
home-hello-world Application: "Get charts/hello-world → Deploy to home namespace"
```

## Quick Start

### 1. Deploy the Bootstrap Application

This Application generates all others:

```bash
kubectl apply -f infrastructure/argocd/applications/platform-applications.yaml
```

### 2. Wait for Sync

```bash
kubectl get applications -n argocd -w
# Wait for platform-applications to show as Synced
```

### 3. Verify All Applications Created

```bash
kubectl get applications -n argocd

# Expected output:
# NAME                       SYNC STATUS   HEALTH STATUS
# platform-applications      Synced        Healthy
# home-hello-world           Synced        Healthy
# home-k8s-health-report     Synced        Healthy
# home-notion-monthly        Synced        Healthy
```

### 4. Enable/Disable Apps

Edit `platform/applications-chart/values.yaml`:

```yaml
applications:
  hello-world:
    enabled: true    # Keep enabled

  github-summary:
    enabled: true    # ← Enable this
```

Commit and push:

```bash
git add platform/applications-chart/values.yaml
git commit -m "feat: enable github-summary automation"
git push

# ArgoCD automatically syncs (watch it):
kubectl get applications -n argocd -w
```

## Architecture Diagram

```
┌─────────────────────────────────────────────┐
│ Git Repository (homelab-gitops)             │
│                                             │
│ platform/applications-chart/values.yaml     │
│   applications:                             │
│     hello-world: enabled: true              │
│     github-summary: enabled: false          │
│     ...                                     │
└────────────────┬────────────────────────────┘
                 │ (you push changes)
                 ▼
┌─────────────────────────────────────────────┐
│ GitHub Repository                           │
└────────────────┬────────────────────────────┘
                 │ (webhook)
                 ▼
┌─────────────────────────────────────────────┐
│ ArgoCD (in cluster)                         │
│                                             │
│ Watches: platform-applications Application  │
│ Action: Render Helm chart (platform/...)    │
│ Result: Generates Application manifests     │
└────────────────┬────────────────────────────┘
                 │ (applies generated Applications)
                 ▼
┌─────────────────────────────────────────────┐
│ ArgoCD Applications (generated)              │
│                                             │
│ ├── home-hello-world Application            │
│ ├── home-k8s-health-report Application      │
│ ├── home-notion-monthly Application         │
│ └── (more as enabled in values)             │
└────────────────┬────────────────────────────┘
                 │ (deploys)
                 ▼
┌─────────────────────────────────────────────┐
│ Kubernetes Cluster                          │
│                                             │
│ namespace: home                             │
│ ├── CronJob: hello-world                    │
│ ├── CronJob: k8s-health-report              │
│ └── ...                                     │
│                                             │
│ namespace: argocd                           │
│ ├── Application: platform-applications      │
│ ├── Application: home-hello-world           │
│ └── ...                                     │
└─────────────────────────────────────────────┘
```

## Management Operations

### View All Applications and Their Status

```bash
kubectl get applications -n argocd -o wide
```

### See Configuration

```bash
# What's in the current values?
helm values platform/applications-chart

# What will be generated?
helm template platform-applications platform/applications-chart
```

### Enable an Application

```yaml
# Edit platform/applications-chart/values.yaml
applications:
  github-summary:
    enabled: true    # ← Change from false
```

### Disable an Application

```yaml
# Edit platform/applications-chart/values.yaml
applications:
  hello-world:
    enabled: false   # ← Change from true
```

The Application and all its resources will be cleaned up by ArgoCD (because `prune: true`).

### Add a New Application

1. Create the Helm chart:
   ```bash
   mkdir -p charts/my-new-app
   # Create Chart.yaml and values.yaml
   ```

2. Add to values.yaml:
   ```yaml
   my-new-app:
     enabled: true
     description: "My new automation"
     path: charts/my-new-app
     syncWave: "2"
   ```

3. Commit and push
4. ArgoCD automatically creates the Application

### View Detailed Status

```bash
kubectl describe application home-hello-world -n argocd
```

### Force Sync

```bash
argocd app sync home-hello-world --grpc-web
# Or:
kubectl patch application home-hello-world -n argocd -p \
  '{"metadata":{"annotation":{"argocd.argoproj.io/refresh":"hard"}}}' \
  --type merge
```

## Migrating from Individual Applications

If you have existing individual Application files:

### Option 1: Keep Both (Safer)

Keep existing applications and add the new apps-of-apps alongside:

```bash
# Old approach still works
kubectl get applications -n argocd

# New approach is platform-applications
# It generates the same apps
```

Just make sure `values.yaml` in `platform-applications` matches what you had before.

### Option 2: Migrate Completely (Cleaner)

1. Ensure `platform-applications` values.yaml has all your applications
2. Deploy the bootstrap Application:
   ```bash
   kubectl apply -f infrastructure/argocd/applications/platform-applications.yaml
   ```
3. Verify all applications sync:
   ```bash
   kubectl get applications -n argocd
   ```
4. Delete old individual Application files (optional):
   ```bash
   kubectl delete -f infrastructure/argocd/applications/hello-world.yaml
   kubectl delete -f infrastructure/argocd/applications/k8s-health-report.yaml
   # etc...
   ```

The new platform-applications approach will already have created these as generated Applications.

## Understanding Sync Waves

Sync Waves control the order in which applications deploy:

```yaml
applications:
  prometheus:
    syncWave: "0"    # Deploy FIRST (infrastructure)
  
  hello-world:
    syncWave: "1"    # Deploy SECOND (core automations)
  
  github-summary:
    syncWave: "2"    # Deploy THIRD (optional automations)
```

**When you deploy:**
1. Wave 0 apps sync and become healthy
2. Wave 1 apps start
3. Wave 2 apps start
4. All healthy = Application is Synced

**Why use waves?**
- Prometheus deploys before apps that emit metrics
- Infrastructure ready before applications use it
- Proper dependency ordering
- Avoid race conditions

## Best Practices

### 1. Keep values.yaml Organized

```yaml
# Bootstrap automations (Phase 1)
applications:
  hello-world:
    enabled: true
    syncWave: "1"

  k8s-health-report:
    enabled: true
    syncWave: "1"

  # Real automations (Phase 3)
  github-summary:
    enabled: false
    syncWave: "2"

  backup-job:
    enabled: false
    syncWave: "2"

  # Observability (Phase 4)
  prometheus:
    enabled: false
    syncWave: "0"
```

### 2. Document Each Application

```yaml
hello-world:
  enabled: true
  description: "Daily hello-world logger — runs at 7am UTC"
  path: charts/hello-world
  syncWave: "1"
```

### 3. Use Consistent Naming

Chart names → Application names:

```
charts/hello-world/        → Application: home-hello-world
charts/github-summary/     → Application: home-github-summary
```

### 4. Review Before Enabling

Before enabling a new app:

```bash
# 1. Check the chart exists
ls -la charts/my-new-app/

# 2. Check values.yaml is valid
helm lint charts/my-new-app

# 3. Render locally to see what will deploy
helm template my-app charts/my-new-app

# 4. Enable in platform/applications-chart/values.yaml
# 5. Commit and push
```

### 5. Use Meaningful Sync Waves

```
Wave 0: Infrastructure (Prometheus, Grafana, storage)
Wave 1: Core automations (hello-world, k8s-health-report)
Wave 2: Secondary automations (github-summary, backups)
```

## Troubleshooting

### Generated Applications Not Appearing

```bash
# Check if platform-applications is synced
kubectl get application platform-applications -n argocd

# See what Helm generated
kubectl get application home-hello-world -n argocd
```

### Application Enabled But Not Deploying

```bash
# Check if the chart path exists
ls charts/hello-world/Chart.yaml

# Check if the Application was generated
kubectl describe application home-hello-world -n argocd

# Check Application sync status
kubectl patch application platform-applications -n argocd \
  -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}' \
  --type merge
```

### Too Many Apps Syncing at Once

Use sync waves to stagger:

```yaml
applications:
  prometheus:
    syncWave: "0"    # Waits for this first

  hello-world:
    syncWave: "1"    # Waits for wave 0
```

### Values Not Taking Effect

```bash
# Force ArgoCD to re-render
argocd app refresh platform-applications --hard

# Or:
kubectl patch application platform-applications -n argocd \
  -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}' \
  --type merge
```

## Comparison: Before vs After

### Adding a New Application

**Before (Individual Files):**
```bash
# Create chart
mkdir -p charts/github-summary
# Create Chart.yaml, values.yaml

# Create Application manifest
cat > infrastructure/argocd/applications/github-summary.yaml <<EOF
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: home-github-summary
...
EOF

# Apply manually
kubectl apply -f infrastructure/argocd/applications/github-summary.yaml

# Commit both files
git add charts/github-summary infrastructure/argocd/applications/github-summary.yaml
```

**After (Apps of Apps):**
```bash
# Create chart
mkdir -p charts/github-summary
# Create Chart.yaml, values.yaml

# Edit one values file
vim platform/applications-chart/values.yaml
# Add:
# github-summary:
#   enabled: true

# Commit one file
git add charts/github-summary platform/applications-chart/values.yaml

# ArgoCD handles the rest automatically!
```

### Enabling/Disabling an Application

**Before:**
```bash
# Delete the Application file
rm infrastructure/argocd/applications/hello-world.yaml
kubectl delete application home-hello-world -n argocd
git add infrastructure/argocd/applications/
git commit -m "remove hello-world"
```

**After:**
```bash
# Edit one line
vim platform/applications-chart/values.yaml
# Change: enabled: true → enabled: false

git add platform/applications-chart/values.yaml
git commit -m "disable hello-world temporarily"
# ArgoCD automatically cleans up!
```

## Summary

| Aspect | Before (Individual) | After (Apps of Apps) |
|--------|------------------|-------------------|
| **Adding app** | Create chart + create Application file | Create chart + edit values.yaml |
| **Enabling/disabling** | Delete/create Application file | Edit one line in values.yaml |
| **Source of truth** | Multiple Application files | One values.yaml |
| **Scalability** | Messy at 20+ apps | Clean at 50+ apps |
| **Deployment order** | Uncontrolled | Sync Waves |
| **View all apps** | List all files | View values.yaml |

---

**This is the enterprise-grade way to manage ArgoCD applications.**

As you scale from 3 to 50 automations, you'll be grateful for this pattern.

See also: [platform/applications-chart/README.md](platform/applications-chart/README.md)
