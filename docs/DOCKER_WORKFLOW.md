# Docker Workflow

Build and manage Docker images for personal platform automations.

## Quick Start

### 1. Build Hello-World Image

```bash
cd scripts/hello-world-heartbeat

docker build -t rprakashdash/homelab/scripts:hello-world-heartbeat-v0.1.0 .
docker build -t rprakashdash/homelab/scripts:hello-world-heartbeat .  # latest tag
```

### 2. Test Locally

```bash
# Text output
docker run rprakashdash/homelab/scripts:hello-world-heartbeat-v0.1.0

# JSON output
docker run rprakashdash/homelab/scripts:hello-world-heartbeat-v0.1.0 --format json

# Compact output
docker run rprakashdash/homelab/scripts:hello-world-heartbeat-v0.1.0 --format compact
```

### 3. Push to Docker Hub

```bash
# Login (first time)
docker login

# Push versioned tag
docker push rprakashdash/homelab/scripts:hello-world-heartbeat-v0.1.0

# Push latest tag
docker push rprakashdash/homelab/scripts:hello-world-heartbeat
```

### 4. Use in Kubernetes

The Helm chart already points to this image:

```bash
git push origin main
# ArgoCD auto-syncs
kubectl get cronjob -n home
```

## Directory Structure

```
scripts/
├── README.md                           ← How to build and manage images
├── hello-world-heartbeat/              ← First automation
│   ├── Dockerfile
│   ├── app.py                          ← Python heartbeat script
│   ├── requirements.txt
│   ├── .dockerignore
│   └── README.md
├── k8s-health-report/                  ← Future automation
│   └── (same structure)
└── (more automations)
```

## Image Naming Convention

```
rprakashdash/homelab/scripts:AUTOMATION-vVERSION

Examples:
  rprakashdash/homelab/scripts:hello-world-heartbeat-v0.1.0
  rprakashdash/homelab/scripts:k8s-health-report-v0.2.0
  rprakashdash/homelab/scripts:github-summary-v1.0.0
```

**Tags to maintain:**
- `hello-world-heartbeat-v0.1.0` — Specific version (production use this)
- `hello-world-heartbeat` — Latest version
- `latest` — Latest of everything (avoid in production)

## Building Images

### Manual Build

```bash
# Build versioned image
cd scripts/hello-world-heartbeat
docker build -t rprakashdash/homelab/scripts:hello-world-heartbeat-v0.1.0 .

# Build latest tag
docker build -t rprakashdash/homelab/scripts:hello-world-heartbeat .
```

### Build Script (Future)

Create `scripts/build.sh`:

```bash
#!/bin/bash

SCRIPT_DIR="scripts/hello-world-heartbeat"
VERSION="v0.1.0"
REPO="rprakashdash/homelab/scripts"
NAME="hello-world-heartbeat"

echo "Building $NAME..."
docker build -t "$REPO:$NAME-$VERSION" "$SCRIPT_DIR"
docker build -t "$REPO:$NAME" "$SCRIPT_DIR"

echo "Images built:"
docker images | grep "$REPO" | grep "$NAME"
```

### CI/CD Build (Future)

GitHub Actions workflow: `.github/workflows/build-images.yml`

```yaml
name: Build Docker Images

on:
  push:
    paths:
      - 'scripts/**'
      - '.github/workflows/build-images.yml'
    branches:
      - main

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Login to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Build and push hello-world-heartbeat
        uses: docker/build-push-action@v4
        with:
          context: scripts/hello-world-heartbeat
          push: true
          tags: |
            rprakashdash/homelab/scripts:hello-world-heartbeat-v0.1.0
            rprakashdash/homelab/scripts:hello-world-heartbeat
            rprakashdash/homelab/scripts:hello-world-heartbeat-latest
```

## Testing Images

### Local Testing

```bash
# Run with default output
docker run rprakashdash/homelab/scripts:hello-world-heartbeat-v0.1.0

# Run with environment variables (simulate K8s)
docker run \
  -e HOSTNAME=test-pod-12345 \
  -e POD_NAMESPACE=home \
  -e NODE_NAME=my-node-1 \
  rprakashdash/homelab/scripts:hello-world-heartbeat-v0.1.0

# Run interactively
docker run -it --entrypoint /bin/bash rprakashdash/homelab/scripts:hello-world-heartbeat-v0.1.0

# Mount working directory
docker run -v $(pwd):/work rprakashdash/homelab/scripts:hello-world-heartbeat-v0.1.0
```

### Verify Image Details

```bash
# See image size
docker images rprakashdash/homelab/scripts

# See layers
docker history rprakashdash/homelab/scripts:hello-world-heartbeat-v0.1.0

# Inspect metadata
docker inspect rprakashdash/homelab/scripts:hello-world-heartbeat-v0.1.0

# View Dockerfile
docker inspect rprakashdash/homelab/scripts:hello-world-heartbeat-v0.1.0 \
  --format='{{json .Config}}' | jq
```

## Pushing to Docker Hub

### Login

```bash
docker login

# Or with personal access token:
cat ~/docker-token.txt | docker login -u rprakashdash --password-stdin
```

### Push Tags

```bash
# Push versioned image
docker push rprakashdash/homelab/scripts:hello-world-heartbeat-v0.1.0

# Push latest tag
docker push rprakashdash/homelab/scripts:hello-world-heartbeat

# Push all tags for an automation
docker push rprakashdash/homelab/scripts --all-tags
```

### Verify Push

```bash
# List images on Docker Hub
docker image ls | grep rprakashdash/homelab/scripts

# Pull from Docker Hub (on different machine)
docker pull rprakashdash/homelab/scripts:hello-world-heartbeat-v0.1.0
```

## Production Best Practices

### 1. Always Use Specific Versions

❌ **Don't do this:**
```yaml
image: rprakashdash/homelab/scripts:hello-world-heartbeat  # vague
```

✅ **Do this:**
```yaml
image: rprakashdash/homelab/scripts:hello-world-heartbeat-v0.1.0  # exact
```

### 2. Minimal Base Images

❌ **Don't do this:**
```dockerfile
FROM python:3.11  # 900MB
```

✅ **Do this:**
```dockerfile
FROM python:3.11-slim  # 150MB
```

### 3. Non-Root User

❌ **Don't do this:**
```dockerfile
# Runs as root
CMD ["python", "app.py"]
```

✅ **Do this:**
```dockerfile
RUN useradd -m appuser
USER appuser
CMD ["python", "app.py"]
```

### 4. Security Context in Kubernetes

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop:
      - ALL
```

### 5. Health Checks

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD python -c "import sys; sys.exit(0)"
```

### 6. Resource Limits

```yaml
resources:
  limits:
    cpu: 100m
    memory: 64Mi
  requests:
    cpu: 50m
    memory: 32Mi
```

## Troubleshooting

### Image pull fails in Kubernetes

```bash
# Check image exists locally
docker images | grep hello-world-heartbeat

# Verify Docker Hub
docker pull rprakashdash/homelab/scripts:hello-world-heartbeat-v0.1.0

# Check imagePullPolicy
kubectl get pod -o yaml | grep imagePullPolicy

# View pull events
kubectl describe pod <POD_NAME>
```

### Image size is too large

```bash
# Check layers
docker history rprakashdash/homelab/scripts:hello-world-heartbeat-v0.1.0

# Use smaller base image
FROM python:3.11-slim  # instead of python:3.11

# Use multi-stage build
FROM python:3.11-slim as builder
# ... build dependencies ...

FROM python:3.11-slim
COPY --from=builder /app /app
```

### Permission denied running container

```bash
# Check user in image
docker inspect rprakashdash/homelab/scripts:hello-world-heartbeat-v0.1.0 \
  --format='{{.Config.User}}'

# Ensure user exists
RUN useradd -m -u 1000 appuser
USER appuser
```

## Workflow Summary

```
1. Create/modify script in scripts/hello-world-heartbeat/

2. Build image locally:
   docker build -t rprakashdash/homelab/scripts:hello-world-heartbeat-v0.1.0 .

3. Test image:
   docker run rprakashdash/homelab/scripts:hello-world-heartbeat-v0.1.0

4. Push to Docker Hub:
   docker push rprakashdash/homelab/scripts:hello-world-heartbeat-v0.1.0

5. Update Helm chart:
   charts/hello-world/values.yaml → point to new image version

6. Commit and push:
   git add scripts/ charts/ && git commit && git push

7. ArgoCD syncs automatically:
   CronJob updated → uses new image
```

## Versioning Strategy

**Semantic Versioning: v{MAJOR}.{MINOR}.{PATCH}**

- **v0.1.0** — Initial beta release
- **v0.2.0** — Bug fix or new feature (still beta)
- **v1.0.0** — First stable release
- **v1.1.0** — New feature (stable)
- **v1.1.1** — Bug fix (stable)

### When to Bump Version

| Change | Version |
|--------|---------|
| Bug fix | Patch (0.0.X) |
| New feature | Minor (0.X.0) |
| Breaking change | Major (X.0.0) |
| Beta → Stable | Minor (0.0.0 → 1.0.0) |

## Future Enhancements

- [ ] Automated CI/CD builds (GitHub Actions)
- [ ] Image scanning (Trivy, Snyk)
- [ ] Multi-architecture builds (amd64, arm64)
- [ ] Signed images (cosign)
- [ ] SBOM generation
- [ ] Registry mirroring

---

See [scripts/README.md](scripts/README.md) for more details.
See [charts/hello-world/](charts/hello-world/) for Helm integration.
