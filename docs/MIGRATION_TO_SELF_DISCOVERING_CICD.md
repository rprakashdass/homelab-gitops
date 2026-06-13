# Migration to Self-Discovering CI/CD

Complete migration guide from manual CI/CD to the self-discovering platform.

## What Changed

### Before: Manual Everything
- 3 services in `charts/` directory (Helm charts only)
- Manual Docker Hub registry references
- Manual CI/CD pipeline (per-service build logic)
- Manual `infrastructure/argocd/applications/*.yaml` files
- Growing complexity as services scaled

### After: Self-Discovering
- 3 services in `services/` directory (source + Dockerfile + Helm + metadata)
- All images in `ghcr.io` (GitHub Container Registry)
- Universal CI/CD pipeline (`.github/workflows/build-and-deploy.yml`)
- Single source of truth: `platform/applications-chart/values.yaml`
- Scales to 50+ services without pipeline changes

## What Was Migrated

### Services Moved to services/

```
services/
├── hello-world/             ← Buildable service
│   ├── service.yaml         ← Self-describing metadata (NEW)
│   ├── Dockerfile           ← Docker image (MOVED from scripts/)
│   ├── Chart.yaml           ← Helm chart (UPDATED)
│   ├── values.yaml          ← Helm values (UPDATED)
│   ├── src/app.py           ← Source code (MOVED from scripts/)
│   └── requirements.txt      ← Dependencies (MOVED from scripts/)
│
├── k8s-health-report/       ← External image (bitnami/kubectl)
│   ├── service.yaml         ← Self-describing metadata (NEW)
│   ├── Chart.yaml           ← Helm chart (UPDATED)
│   └── values.yaml          ← Helm values (UPDATED)
│
├── notion-monthly/          ← External image (busybox)
│   ├── service.yaml         ← Self-describing metadata (NEW)
│   ├── Chart.yaml           ← Helm chart (UPDATED)
│   └── values.yaml          ← Helm values (UPDATED)
│
└── example-service/         ← Reference implementation
    ├── service.yaml         ← Copy and customize
    ├── Dockerfile
    ├── Chart.yaml
    ├── values.yaml
    ├── src/main.py
    ├── requirements.txt
    └── README.md
```

### Registry Migration: Docker Hub → ghcr.io

**Before:**
```yaml
# charts/hello-world/values.yaml
image:
  repository: rprakashdash/homelab/scripts
  tag: hello-world-heartbeat-v0.1.0
```

**After:**
```yaml
# services/hello-world/values.yaml
image:
  repository: ghcr.io/rprakashdass/hello-world
  tag: abc1234def5678  # ← Auto-updated by CI with git-sha
```

**Benefits:**
- `ghcr.io` is GitHub's native registry (no Docker Hub account needed)
- Image tags are immutable git-sha (always reproducible)
- CI/CD automatically updates tags (no manual image updates)
- Full audit trail in Git commit history

### Application Discovery

**Before:**
```yaml
# platform/applications-chart/values.yaml
applications:
  hello-world:
    path: charts/hello-world      # Old path
```

**After:**
```yaml
# platform/applications-chart/values.yaml
applications:
  hello-world:
    path: services/hello-world    # New path
```

## CI/CD Pipeline Implementation

### New Universal Pipeline

**File:** `.github/workflows/build-and-deploy.yml`

**Capabilities:**
- ✅ Discovers services from `services/*/service.yaml`
- ✅ Detects changes via Git diff
- ✅ Builds only changed services
- ✅ Runs builds in parallel (matrix strategy)
- ✅ Pushes to ghcr.io with git-sha tags
- ✅ Auto-updates `values.yaml` with new image tags
- ✅ Commits back to Git for ArgoCD
- ✅ Works for 3 services or 50 services (no changes needed)

**Jobs:**
1. `discover` — Find changed services
2. `build` — Build and push images (parallel)
3. `update-values` — Update Helm values with new tags
4. `summary` — Report status

### Service Metadata: service.yaml

Each service declares how to build/deploy:

```yaml
name: hello-world
build:
  enabled: true
  dockerfile: ./Dockerfile
image:
  registry: ghcr.io/rprakashdass
  name: hello-world
versioning:
  strategy: git-sha
  autoUpdate: true
```

**The CI reads this and:**
- Knows whether to build the service
- Knows where to push the image
- Knows how to version the image tag
- Knows whether to auto-update Helm values

## Step-by-Step: First Build

### 1. Verify Services Structure

```bash
ls -la services/hello-world/
# Should show:
#   service.yaml
#   Dockerfile
#   Chart.yaml
#   values.yaml
#   src/app.py
#   requirements.txt
```

### 2. Push to Main

```bash
git add services/
git add .github/workflows/build-and-deploy.yml
git add platform/applications-chart/values.yaml
git commit -m "feat: migrate to self-discovering CI/CD

- Move services from charts/ to services/
- Add service.yaml metadata to all services
- Replace Docker Hub with ghcr.io
- Implement universal CI/CD pipeline
- All image tags now git-sha based with auto-update"

git push origin main
```

### 3. GitHub Actions Runs

Navigate to: https://github.com/rprakashdass/homelab-gitops/actions

**Watch the workflow:**
1. `discover` — Detects `hello-world`, `k8s-health-report`, `notion-monthly` changed
2. `build` — Builds all three (only `hello-world` has Dockerfile, others skip build)
3. `update-values` — Updates `services/hello-world/values.yaml` with new tag
4. `summary` — Reports success

### 4. Verify Git Commit

```bash
git log --oneline -5
# Should show:
# abc1234 ci: auto-update image tags
# def5678 feat: migrate to self-discovering CI/CD
```

### 5. Verify Image in Registry

```bash
# Login to ghcr.io
gh auth token | docker login ghcr.io -u USERNAME --password-stdin

# Check image exists
docker pull ghcr.io/rprakashdass/hello-world:abc1234
```

### 6. Verify ArgoCD Syncs

```bash
kubectl get applications -n argocd
# Should show all three with "Synced" status

kubectl describe application home-hello-world -n argocd
# Check image: ghcr.io/rprakashdass/hello-world:abc1234
```

### 7. Verify Pod Runs

```bash
# Wait for next scheduled time or manually trigger
kubectl create job --from=cronjob/home-hello-world test-manual -n home

kubectl logs -n home -l job-name=test-manual --tail=20
# Should show heartbeat output
```

## Adding a New Service

### 1. Copy Example Service

```bash
cp -r services/example-service services/my-new-service
cd services/my-new-service
```

### 2. Update Metadata

```yaml
# service.yaml
name: my-new-service
image:
  registry: ghcr.io/rprakashdass
  name: my-new-service
```

### 3. Update Helm Chart

```yaml
# Chart.yaml
name: my-new-service
description: "What this service does"
```

### 4. Write Code

```bash
rm -rf src/*
# Add your source code
```

### 5. Commit and Push

```bash
git add services/my-new-service/
git commit -m "feat: add my-new-service"
git push origin main
```

**CI/CD automatically:**
- Detects the change
- Builds the Docker image
- Pushes to ghcr.io
- Updates values.yaml
- ArgoCD deploys it

**No pipeline changes needed!**

## What to Remove

### Delete Old references

The old `charts/` directory is deprecated but kept for reference:

```bash
# ✅ KEEP (reference only)
charts/README.md

# ✅ ALREADY DELETED
charts/hello-world/           ← Moved to services/hello-world/
charts/k8s-health-report/     ← Moved to services/k8s-health-report/
charts/notion-monthly/        ← Moved to services/notion-monthly/
```

### Delete Old Dockerfiles (already handled)

```bash
# ✅ ALREADY DELETED/MOVED
scripts/hello-world-heartbeat/  ← Moved to services/hello-world/
```

## Verification Checklist

- [ ] All three services in `services/` directory
- [ ] Each service has `service.yaml`
- [ ] `service.yaml` points to `ghcr.io` registry
- [ ] `.github/workflows/build-and-deploy.yml` exists
- [ ] `platform/applications-chart/values.yaml` updated to point to `services/`
- [ ] CI/CD workflow triggered on first push
- [ ] hello-world image built and pushed to ghcr.io
- [ ] values.yaml auto-updated with git-sha tag
- [ ] ArgoCD applications synced
- [ ] Pods running with new images

## Benefits Summary

| Aspect | Before | After |
|--------|--------|-------|
| **Adding service** | Create chart + Dockerfile + CI logic | Create `services/service/` + push |
| **Building** | Manual Docker Hub build | Automatic ghcr.io build |
| **Image tags** | Mutable `latest` tags | Immutable git-sha tags |
| **Scaling** | CI complexity grows | CI stays same |
| **Deployment** | Manual updates | Auto-updates via Git |
| **Audit trail** | Limited | Full Git history |

## Next Steps

1. **Review the implementation**
   - Read [docs/SELF_DISCOVERING_CICD.md](./SELF_DISCOVERING_CICD.md)
   - Review [services/hello-world/](../services/hello-world/)

2. **Test the pipeline**
   - Make a small change to `services/hello-world/src/app.py`
   - Push to main
   - Watch GitHub Actions run
   - Verify image builds and deploys

3. **Add your first new service**
   - Use [services/example-service/](../services/example-service/) as template
   - Create something useful (automation, worker, etc.)
   - Push and watch it auto-build/deploy

4. **Monitor and iterate**
   - Check `kubectl logs -n home` for service logs
   - Review [platform/applications-chart/values.yaml](../platform/applications-chart/values.yaml) for enabled services

---

**Your platform is now self-discovering and scales infinitely!** 🚀
