# infrastructure/

Cluster-level components and bootstrap configuration.

## Contents

| Directory | Purpose |
|-----------|---------|
| `argocd/` | ArgoCD configuration (Project, Applications) |
| `ingress/` | Ingress controller (Traefik, cert-manager) |
| `storage-class/` | Storage provisioners (local-path, etc.) |
| `monitoring-bootstrap/` | Prometheus/Grafana bootstrap |
| `cert-manager/` | Certificate management (TLS) |

## What Belongs Here

Cluster-wide, infrastructure-level concerns that:
- Are installed once per cluster
- Cannot be scoped to a single namespace
- Manage cluster resources (ingress, storage, security)
- Bootstrap the automation platform

## What Does NOT Belong Here

- Service-specific Helm charts → go to `charts/`
- Reusable libraries and abstractions → go to `platform/`
- Domain-specific automations → go to `services/`
- Third-party applications → go to `apps/`

## ArgoCD Setup

### Directory Structure

```
argocd/
├── project.yaml              ← ArgoCD AppProject definition
└── applications/             ← One Application per service
    ├── hello-world.yaml
    ├── k8s-health-report.yaml
    ├── notion-monthly.yaml
    └── ... (add more as you build)
```

### The Flow

1. **project.yaml** defines the "home" project
   - What repositories can be accessed
   - What namespaces can be deployed to
   - What resources can be managed

2. **applications/** contain ArgoCD Application manifests
   - Each automation gets its own Application
   - Application points to a chart in `charts/`
   - ArgoCD auto-syncs when the repo changes

3. **Adding a new automation**
   ```bash
   # 1. Create chart in charts/my-automation
   mkdir -p charts/my-automation
   
   # 2. Create Application in infrastructure/argocd/applications/
   cat > infrastructure/argocd/applications/my-automation.yaml <<EOF
   apiVersion: argoproj.io/v1alpha1
   kind: Application
   metadata:
     name: home-my-automation
     namespace: argocd
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
   
   # 3. Deploy
   kubectl apply -f infrastructure/argocd/applications/my-automation.yaml
   ```

### Verify

```bash
# Check project
kubectl get appproject -n argocd

# Check applications
kubectl get applications -n argocd

# Check sync status
kubectl get applications -n argocd -o wide

# View detailed status
kubectl describe application home-hello-world -n argocd
```

## Philosophy

Infrastructure is **minimal and intentional**.

It exists to:
- ✅ Enable the platform (ArgoCD for GitOps)
- ✅ Provide foundational services (storage, networking, TLS)
- ✅ Enforce security policies (RBAC, network policies)

It does **NOT** exist to:
- ❌ Run application code
- ❌ Host third-party apps
- ❌ Be clever or over-engineered

## Future Components

As the platform grows, you'll add:
- `cert-manager/` — automated certificate renewal
- `ingress/` — Traefik configuration
- `storage-class/` — persistent storage provisioning
- `monitoring-bootstrap/` — Prometheus/Grafana setup
- `policies/` — NetworkPolicy, PodSecurityPolicy, etc.

But these are all *infrastructure concerns*, not *application concerns*.

---

See also: [../platform/README.md](../platform/README.md), [../charts/README.md](../charts/README.md)
