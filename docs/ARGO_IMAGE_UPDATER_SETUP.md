# Argo Image Updater Setup Guide

This guide walks you through setting up Argo Image Updater to automatically update container image tags when new images are pushed to GHCR.

## Quick Overview

Your GitOps flow:

```
Git Push (service code)
    ↓
GitHub Actions
    ├─ Detects changed services
    ├─ Builds Docker images
    └─ Pushes to ghcr.io
         ↓
    Argo Image Updater (polls GHCR every 2 minutes)
         ├─ Detects new image
         ├─ Updates values.yaml with new tag
         └─ Commits to Git
         ↓
    Argo CD (detects git change)
         ├─ Syncs updated Application
         └─ Deploys new image to cluster
```

Nobody commits `values.yaml` manually. It's fully automated.

## Prerequisites

- Argo CD installed and running
- GitHub repository with this GitOps project
- GHCR container registry with images pushed
- kubectl access to your cluster

## Step 1: Create GHCR Credentials Secret

If your GHCR repository is **private**, create a secret in the `argocd` namespace:

```bash
# Create a GitHub Personal Access Token with `read:packages` scope
# https://github.com/settings/tokens/new

export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"
export GITHUB_USERNAME="your-github-username"

# Create the secret
kubectl create secret docker-registry ghcr-creds \
  --docker-server=ghcr.io \
  --docker-username=$GITHUB_USERNAME \
  --docker-password=$GITHUB_TOKEN \
  -n argocd

# Verify
kubectl get secret ghcr-creds -n argocd -o yaml
```

If your GHCR repository is **public**, you can skip this step.

## Step 2: Install Argo Image Updater

### Option A: Using Helm Directly

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update

helm install argocd-image-updater argo/argocd-image-updater \
  -n argocd-image-updater \
  --create-namespace \
  -f infrastructure/argocd/image-updater/values.yaml
```

### Option B: Using Argo CD (Recommended)

Deploy Argo Image Updater as an ArgoCD Application:

```bash
kubectl apply -f infrastructure/argocd/image-updater/application.yaml
```

This allows Argo CD to manage the Image Updater deployment.

## Step 3: Verify Installation

```bash
# Check pods are running
kubectl get pods -n argocd-image-updater

# Check logs
kubectl logs -n argocd-image-updater deployment/argocd-image-updater -f
```

You should see logs like:
```
Starting Argo Image Updater
Registering registry credentials
Watching ArgoCD Applications for image updates
```

## Step 4: Annotate Your Applications

For each service you want to auto-update, add Image Updater annotations to its Application resource.

### Example: hello-world service

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: hello-world
  namespace: argocd
  annotations:
    # Image to track
    argocd-image-updater.argoproj.io/image-list: hello-world=ghcr.io/rprakashdass/hello-world

    # Helm parameters to update
    argocd-image-updater.argoproj.io/hello-world.helm.image-name: image.repository
    argocd-image-updater.argoproj.io/hello-world.helm.image-tag: image.tag

    # Update strategy
    argocd-image-updater.argoproj.io/hello-world.update-strategy: newest-build

    # Write back to git
    argocd-image-updater.argoproj.io/write-back-method: git
    argocd-image-updater.argoproj.io/git-branch: main

spec:
  # ... rest of Application spec ...
  source:
    # ... values must include image section ...
    helm:
      values: |
        image:
          repository: ghcr.io/rprakashdass/hello-world
          tag: latest
```

See: `services/automation/hello-world/application.yaml` for a complete example.

## Step 5: Generate GitHub Personal Access Token for Git Write-Back

Image Updater needs permission to commit changes to your repository. Create a token:

1. Go to https://github.com/settings/tokens/new
2. Name: `argocd-image-updater`
3. Scopes: `repo` (full control of private repositories)
4. Copy the token

Store it securely. You'll only see it once.

## Step 6: Create Git Credentials Secret (Optional)

If Image Updater should write back using a specific token instead of ArgoCD's credentials:

```bash
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"
export GITHUB_USERNAME="your-github-username"

kubectl create secret generic github-creds \
  --from-literal=username=$GITHUB_USERNAME \
  --from-literal=password=$GITHUB_TOKEN \
  -n argocd-image-updater
```

Then update the Application annotation:
```yaml
argocd-image-updater.argoproj.io/write-back-method: git:secret:argocd-image-updater/github-creds
```

## Step 7: Deploy an Application

Create or update an Application with Image Updater annotations:

```bash
kubectl apply -f services/automation/hello-world/application.yaml
```

## Step 8: Test It

### Trigger a Build

Push a change to a service and let GitHub Actions build a new image:

```bash
# Make a change to hello-world service
echo "test" >> services/automation/hello-world/src/main.py
git add -A
git commit -m "test: trigger hello-world build"
git push
```

GitHub Actions will:
1. Build the image
2. Push to `ghcr.io/rprakashdass/hello-world:<git-sha>`

### Watch Argo Image Updater

```bash
kubectl logs -n argocd-image-updater deployment/argocd-image-updater -f
```

Wait ~2 minutes. You should see:
```
Checking image ghcr.io/rprakashdass/hello-world for updates
Found new image tag: abc1234
Updating hello-world in git repository
```

### Verify Git Update

```bash
git log --oneline infrastructure/argocd/applications/ | head -5
```

You should see a commit from Image Updater with the new tag.

### Verify Argo CD Sync

Check the Argo CD UI or:

```bash
kubectl get application hello-world -n argocd -o jsonpath='{.status.operationState.message}'
```

The Application should sync to the new image.

## Debugging

### Image Updater Logs

```bash
kubectl logs -n argocd-image-updater deployment/argocd-image-updater -f
```

### Check Annotations

```bash
kubectl get application hello-world -n argocd -o yaml | grep image-updater
```

### Test Registry Access

```bash
kubectl exec -it -n argocd-image-updater deployment/argocd-image-updater -- sh

# Inside the pod:
docker pull ghcr.io/rprakashdass/hello-world:latest
```

### Check RBAC Permissions

```bash
kubectl auth can-i get applications \
  --as=system:serviceaccount:argocd-image-updater:argocd-image-updater \
  -n argocd
```

Should return `yes`.

### Verify Git Credentials

```bash
kubectl get secret ghcr-creds -n argocd -o yaml
```

Should show credentials are base64-encoded.

## Update Strategies

When configuring Image Updater, choose an update strategy:

- **newest-build** (default): Picks the newest image by timestamp. Good for Git SHA tags.
- **semver**: Matches semantic versioning (v1.2.3). Good for tagged releases.
- **latest**: Always picks the `latest` tag.
- **name**: Lexicographic sorting (A-Z). Good for named tags.
- **digest**: Tracks by SHA digest. Good for immutable tags.

For this setup with Git SHA tags, use `newest-build`.

## Common Issues

### "Image not found"

- Verify image exists: `docker pull ghcr.io/rprakashdass/hello-world:abc1234`
- Check GHCR credentials are correct
- Ensure Image Updater pod has registry credentials

### "Failed to update git"

- Verify ArgoCD has git credentials configured
- Check git token has `repo` scope
- Ensure the target branch exists

### "Updates not triggering"

- Check Image Updater pod is running
- Verify Application annotations are correct
- Check Image Updater logs for errors
- Wait ~2 minutes (polling interval)

### "No permissions to update Application"

- Verify Image Updater ServiceAccount RBAC
- Check Image Updater is in same namespace or has cross-namespace permissions

## Next Steps

1. Install Argo Image Updater (Step 2)
2. Annotate your Applications (Step 4)
3. Test with a manual push (Step 8)
4. Monitor and iterate

Once working, the entire flow is automatic: push code → GitHub Actions builds → Image Updater updates Git → Argo CD deploys.

## References

- [Argo Image Updater Docs](https://argocd-image-updater.readthedocs.io/)
- [Installation Guide](https://argocd-image-updater.readthedocs.io/en/stable/install/)
- [Configuration Guide](https://argocd-image-updater.readthedocs.io/en/stable/configuration/applications/)
- [ArtifactHub Helm Chart](https://artifacthub.io/packages/helm/argo/argocd-image-updater)
