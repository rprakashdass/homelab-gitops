# Cheatsheet

Quick reference for common commands and patterns.

## Setup (First Time)

```bash
# Update GitHub username in all files
sed -i '' 's/rprakashdass/rprakashdass/g' $(find . -type f -name "*.yaml" -o -name "*.md")

# Create namespace
kubectl create namespace home

# Apply ArgoCD project
kubectl apply -f infrastructure/argocd/project.yaml

# Apply all automations
kubectl apply -f infrastructure/argocd/applications/

# Verify
kubectl get applications -n argocd
kubectl get cronjob -n home
```

## Checking Status

```bash
# View all applications
kubectl get applications -n argocd
kubectl get applications -n argocd -o wide

# View application details
kubectl describe application home-hello-world -n argocd

# Watch sync status
kubectl get applications -n argocd -w

# View all resources
kubectl get all -n home

# View CronJobs
kubectl get cronjob -n home
kubectl describe cronjob home-hello-world -n home

# View recent jobs
kubectl get jobs -n home --sort-by=.metadata.creationTimestamp

# View pods
kubectl get pods -n home
kubectl get pods -n home -o wide

# View RBAC
kubectl get serviceaccount -n home
kubectl get role -n home
kubectl get rolebinding -n home
```

## Viewing Logs

```bash
# Logs from latest run of hello-world
kubectl logs -n home -l app.kubernetes.io/name=hello-world --tail=50

# Logs from specific pod
kubectl logs -n home POD_NAME

# Follow logs
kubectl logs -n home POD_NAME -f

# From recent pods only
kubectl logs -n home -l app.kubernetes.io/name=hello-world --since=30m
```

## Manual Testing

```bash
# Trigger a job immediately
kubectl create job --from=cronjob/home-hello-world manual-test-1 -n home

# Check if it ran
kubectl get pods -n home -l job-name=manual-test-1

# View its logs
kubectl logs -n home -l job-name=manual-test-1

# Delete test job
kubectl delete job manual-test-1 -n home
```

## Creating a New Automation

### 1. Copy template

```bash
cp -r charts/hello-world charts/my-automation
```

### 2. Edit Chart.yaml

```bash
vim charts/my-automation/Chart.yaml
# Update:
# - name: my-automation
# - description: "My new automation"
```

### 3. Edit values.yaml

```bash
vim charts/my-automation/values.yaml
# Update:
# - base-chart.kind: (cronjob/deployment/job)
# - base-chart.schedule: (cron if cronjob)
# - base-chart.image.repository: (your image)
# - base-chart.command/args: (what to run)
```

### 4. Create ArgoCD Application

```bash
cat > infrastructure/argocd/applications/my-automation.yaml <<EOF
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: home-my-automation
  namespace: argocd
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: home
  source:
    repoURL: https://github.com/rprakashdass/homelab-gitops.git
    targetRevision: main
    path: charts/my-automation
  destination:
    server: https://kubernetes.default.svc
    namespace: home
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
EOF
```

### 5. Deploy

```bash
git add charts/my-automation infrastructure/argocd/applications/my-automation.yaml
git commit -m "feat: add my-automation"
git push

# Watch it sync
kubectl get applications -n argocd -w
```

## Working with Secrets (SOPS)

```bash
# Setup (first time)
age-keygen -o ~/.config/sops/age/keys.txt
age-keygen -y ~/.config/sops/age/keys.txt  # copy public key to .sops.yaml

# Create plaintext secret (never commit!)
cat > charts/my-automation/secrets.yaml <<EOF
notion_api_key: "secret_value_here"
EOF

# Encrypt
sops -e charts/my-automation/secrets.yaml > charts/my-automation/secrets.enc.yaml

# Delete plaintext
rm charts/my-automation/secrets.yaml

# Commit encrypted
git add charts/my-automation/secrets.enc.yaml
git commit -m "feat: add encrypted secrets"
git push

# Edit encrypted secret
sops charts/my-automation/secrets.enc.yaml

# Verify it's actually encrypted
cat charts/my-automation/secrets.enc.yaml  # should show encrypted data
```

## Helm Chart Operations

```bash
# Lint chart
helm lint charts/my-automation

# Render templates (see what will be deployed)
helm template test charts/my-automation

# Render with base-chart values
helm template test charts/my-automation \
  -f platform/base-chart/values.yaml

# Get all values
helm values charts/my-automation

# Update dependencies
cd charts/my-automation
helm dependency update
cd ../..
```

## Debugging Issues

```bash
# Check namespace exists
kubectl get namespace home

# Check ArgoCD project
kubectl get appproject -n argocd

# Check application
kubectl describe application home-hello-world -n argocd

# View application sync status
kubectl get application home-hello-world -n argocd -o yaml

# Check pod events
kubectl describe pod POD_NAME -n home

# Check RBAC permissions
kubectl auth can-i list pods \
  --as=system:serviceaccount:home:home-hello-world \
  --namespace=home

# Check service account
kubectl get serviceaccount -n home
kubectl get role -n home
kubectl get rolebinding -n home

# Check resource limits
kubectl describe deployment my-automation -n home
kubectl describe cronjob my-automation -n home

# View cluster events
kubectl get events -n home --sort-by='.lastTimestamp'

# Check resource usage
kubectl top nodes
kubectl top pods -n home
```

## Common Cron Schedules

```
0 7 * * *       # Daily at 7:00 AM
0 6 * * 0       # Weekly on Sunday at 6:00 AM
0 0 1 * *       # Monthly on 1st at midnight
0 0 1 1 *       # Yearly on Jan 1st at midnight
*/5 * * * *     # Every 5 minutes
0 9,15 * * *    # 9 AM and 3 PM daily
0 0 * * 1       # Monday at midnight
```

Use [crontab.guru](https://crontab.guru) for verification.

## Git Workflow

```bash
# Check status
git status

# See changes
git diff

# See history
git log --oneline -10

# Create commit
git add .
git commit -m "feat: add my-automation"

# Push (ArgoCD syncs automatically)
git push

# View remote
git remote -v

# Pull latest
git pull
```

## Useful kubectl Aliases

Add to your shell profile (~/.bashrc or ~/.zshrc):

```bash
alias k=kubectl
alias kn='kubectl -n'
alias kgh='kubectl -n home'
alias kga='kubectl -n argocd'

alias kgapp='kubectl get applications -n argocd'
alias kgcj='kubectl get cronjob -n home'
alias kgp='kubectl get pods -n home'
alias kgl='kubectl logs -n home'
alias kdel='kubectl delete'
alias kdes='kubectl describe'
```

Then use:

```bash
kgapp          # get applications -n argocd
kgcj           # get cronjob -n home
kgh get pods   # kubectl -n home get pods
kgl -l app... --tail=50
```

## Useful jq Commands

Filter and format JSON output:

```bash
# Get application sync status
kubectl get applications -n argocd -o json | \
  jq '.items[] | {name: .metadata.name, status: .status.sync.status}'

# Get failed pods
kubectl get pods -n home -o json | \
  jq '.items[] | select(.status.phase != "Running")'

# Get resource usage
kubectl top pods -n home -o json | \
  jq '.items[] | {name: .metadata.name, cpu: .usage.cpu, memory: .usage.memory}'
```

## Troubleshooting Template

When something breaks:

1. **Check git**
   ```bash
   git log --oneline -5
   git status
   ```

2. **Check applications**
   ```bash
   kubectl describe application NAME -n argocd
   kubectl get application -n argocd -o yaml
   ```

3. **Check resources**
   ```bash
   kubectl get all -n home
   kubectl get events -n home
   ```

4. **Check specific pod**
   ```bash
   kubectl describe pod POD_NAME -n home
   kubectl logs -n home POD_NAME
   ```

5. **Check RBAC**
   ```bash
   kubectl auth can-i get pods \
     --as=system:serviceaccount:home:NAME
   ```

6. **Force resync**
   ```bash
   kubectl patch application home-AUTOMATION \
     -n argocd \
     -p '{"metadata":{"finalizers":null}}'
   kubectl apply -f infrastructure/argocd/applications/AUTOMATION.yaml
   ```

## Performance

```bash
# View resource usage
kubectl top nodes
kubectl top pods -n home

# See resource requests
kubectl describe nodes
kubectl describe pod POD_NAME -n home

# Check HPA status
kubectl get hpa -n home
kubectl describe hpa HPA_NAME -n home
```

## Backup & Restore

```bash
# Backup all manifests
kubectl get all -n home -o yaml > backup-home.yaml

# Backup ArgoCD applications
kubectl get applications -n argocd -o yaml > backup-apps.yaml

# Restore from backup
kubectl apply -f backup-home.yaml
kubectl apply -f backup-apps.yaml
```

## Cleanup

```bash
# Delete specific automation
kubectl delete application home-AUTOMATION -n argocd

# Delete all automations
kubectl delete applications -n argocd --all

# Delete namespace (everything in it)
kubectl delete namespace home

# Delete finished jobs
kubectl delete job --field-selector status.successful=1 -n home

# Delete failed pods
kubectl delete pod --field-selector=status.phase=Failed -n home
```

## Quick Test

```bash
# Everything in one command
kubectl create job --from=cronjob/home-hello-world test-$(date +%s) -n home && \
sleep 3 && \
kubectl get pods -n home -l job-name=$(kubectl get pods -n home -o jsonpath='{.items[0].metadata.labels.job-name}' --sort-by=.metadata.creationTimestamp) && \
kubectl logs -n home -l job-name=$(kubectl get pods -n home -o jsonpath='{.items[0].metadata.labels.job-name}' --sort-by=.metadata.creationTimestamp) --tail=20
```

---

**Save this file for quick reference!**

For detailed info, see:
- [QUICKSTART.md](QUICKSTART.md) — Setup and first deployment
- [README.md](README.md) — Complete documentation
- [ARCHITECTURE.md](ARCHITECTURE.md) — Visual guide
- [charts/README.md](charts/README.md) — Creating automations
