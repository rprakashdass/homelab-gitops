
# Complete Deployment Walkthrough: Hello-World

How a single `git push` becomes a running automation.

## LAYER 1: GIT REPOSITORY (Your Machine)

### Files Before Push

```
homelab-gitops/
├── platform/applications-chart/
│   ├── Chart.yaml
│   ├── values.yaml                 ← Lists hello-world as enabled: true
│   └── templates/applications.yaml ← Will generate hello-world Application
│
├── charts/hello-world/
│   ├── Chart.yaml
│   ├── values.yaml                 ← hello-world specific config
│   └── (inherits templates from base-chart)
│
└── infrastructure/argocd/applications/
    └── platform-applications.yaml  ← Bootstrap Application
```

### User Action
```bash
$ git push origin main
```

**What's sent to GitHub:**
- All files above
- Git history
- Your commits

---

## STEP 1-2: GITHUB → ARGOCD (Webhook or Polling)

### Option A: Webhook (Fast)
```
GitHub: "Hey ArgoCD, homelab-gitops repo changed!"
  └─ POST https://your-argocd/api/webhook
```

### Option B: Polling (Safe)
```
ArgoCD every 3 minutes:
  "Is there anything new in https://github.com/YOUR_USERNAME/homelab-gitops.git?"
```

---

## LAYER 2: ARGOCD CONTROLLER (In Your Cluster)

### Step 3: ArgoCD Detects Change

ArgoCD is watching the `platform-applications` Application:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: platform-applications
  namespace: argocd
spec:
  source:
    repoURL: https://github.com/YOUR_USERNAME/homelab-gitops.git
    path: platform/applications-chart
  destination:
    namespace: argocd
```

**ArgoCD thinks:**
1. I need to sync `platform-applications`
2. Fetch repo from GitHub
3. Go to path: `platform/applications-chart`
4. This is a Helm chart
5. Render it with Helm
6. Compare with cluster state
7. Apply differences

### Step 4: ArgoCD Fetches & Renders Helm Chart

```bash
$ helm template platform-applications platform/applications-chart
```

**What's in values.yaml:**

```yaml
applications:
  hello-world:
    enabled: true                    # ✅ Will be rendered
    description: "Daily hello-world logger"
    path: charts/hello-world
    syncWave: "1"
  
  k8s-health-report:
    enabled: true                    # ✅ Will be rendered
    ...
  
  github-summary:
    enabled: false                   # ❌ Will be SKIPPED
    ...
```

**Helm template renders this:**

```yaml
{{- range $name, $app := .Values.applications }}
{{- if $app.enabled }}               # ← Check: is it enabled?
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: home-{{ $name }}
spec:
  source:
    path: {{ $app.path }}
  ...
{{- end }}
{{- end }}
```

**Output: 3 Application manifests generated**

```
✅ Application: home-hello-world
✅ Application: home-k8s-health-report
❌ Application: home-github-summary (skipped)
✅ Application: home-notion-monthly
```

### Step 5: ArgoCD Applies Generated Applications

```bash
$ kubectl apply -f - <<EOF
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: home-hello-world
  namespace: argocd
spec:
  project: home
  source:
    repoURL: https://github.com/YOUR_USERNAME/homelab-gitops.git
    targetRevision: main
    path: charts/hello-world
  destination:
    server: https://kubernetes.default.svc
    namespace: home
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
EOF
```

**Kubernetes API Server:**
```
✅ Application created: home-hello-world
```

---

## STEP 6: ARGOCD SYNCS THE HELLO-WORLD APPLICATION

ArgoCD sees the new `home-hello-world` Application and syncs it.

**Reads Application spec:**
```yaml
source:
  repoURL: https://github.com/YOUR_USERNAME/homelab-gitops.git
  path: charts/hello-world
destination:
  namespace: home
```

**ArgoCD does:**
1. Fetch repo (already has it)
2. Go to: `charts/hello-world`
3. Read `Chart.yaml` (finds dependency: base-chart)
4. Resolve dependency: `platform/base-chart`
5. This is a Helm chart
6. Render with Helm

### Step 7: Resolve Helm Dependency

**In charts/hello-world/Chart.yaml:**
```yaml
dependencies:
  - name: base-chart
    version: "0.1.0"
    repository: "file://../../../platform/base-chart"
```

**Helm resolves:**
```
Need: base-chart v0.1.0
From: file://../../../platform/base-chart

Result: Uses platform/base-chart templates
```

### Step 8: Helm Renders the Chart

**Merges values (child overrides parent):**

From `platform/base-chart/values.yaml` (defaults):
```yaml
resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 100m
    memory: 128Mi
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  ...
```

From `charts/hello-world/values.yaml` (overrides):
```yaml
base-chart:
  kind: cronjob
  schedule: "0 7 * * *"
  image:
    repository: busybox
    tag: "latest"
  command: ["/bin/sh"]
  args:
    - -c
    - |
      echo "Hello from the personal platform!"
      echo "Current timestamp: $(date -u +'%Y-%m-%d %H:%M:%S UTC')"
      echo "Pod: $(hostname)"
  resources:
    limits:
      memory: "64Mi"    # Override base-chart default
    ...
```

**Helm renders templates:**

```yaml
# From templates/serviceaccount.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: home-hello-world
  namespace: home
---

# From templates/role.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: home-hello-world
  namespace: home
rules: []  # No RBAC needed
---

# From templates/rolebinding.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: home-hello-world
  namespace: home
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: home-hello-world
subjects:
- kind: ServiceAccount
  name: home-hello-world
  namespace: home
---

# From templates/workload.yaml (cronjob)
apiVersion: batch/v1
kind: CronJob
metadata:
  name: home-hello-world
  namespace: home
  labels:
    app.kubernetes.io/name: hello-world
    app.kubernetes.io/instance: home
spec:
  schedule: "0 7 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: home-hello-world
          securityContext:
            runAsNonRoot: true
            runAsUser: 1000
            fsGroup: 3000
          containers:
          - name: hello-world
            image: busybox:latest
            securityContext:
              allowPrivilegeEscalation: false
              readOnlyRootFilesystem: true
            command: ["/bin/sh"]
            args:
            - -c
            - |
              echo "Hello from the personal platform!"
              echo "Current timestamp: $(date -u +'%Y-%m-%d %H:%M:%S UTC')"
              echo "Pod: $(hostname)"
            resources:
              limits:
                cpu: 100m
                memory: 64Mi
              requests:
                cpu: 50m
                memory: 32Mi
          restartPolicy: OnFailure
```

### Step 9: ArgoCD Applies Manifests

```bash
$ kubectl apply -f - <<EOF
(all the manifests above)
EOF
```

**Kubernetes API processes:**
```
✅ ServiceAccount created: home-hello-world
✅ Role created: home-hello-world
✅ RoleBinding created: home-hello-world
✅ CronJob created: home-hello-world
```

---

## LAYER 3: KUBERNETES CLUSTER

Resources now exist in namespace `home`:

```bash
$ kubectl get all -n home

NAME                      READY   STATUS    RESTARTS   AGE
(no pods yet, will run at 7am)

$ kubectl get cronjob -n home

NAME               SCHEDULE    TIMEZONE   SUSPEND   ACTIVE   AGE
home-hello-world   0 7 * * *   UTC        False     0        5m

$ kubectl get serviceaccount -n home

NAME                 SECRETS   AGE
home-hello-world     0         5m
```

**kube-scheduler watches:**
```
"New CronJob: home-hello-world"
"Schedule: 0 7 * * * (every day at 7am UTC)"

Registered for execution at next scheduled time
```

---

## LAYER 4: SCHEDULED EXECUTION

### Time: 2024-06-13T07:00:00Z (7am UTC)

**kube-scheduler:**
```
"CronJob home-hello-world should run now!"
```

Creates a Job:
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: home-hello-world-1718264400-abc12
  namespace: home
spec:
  (based on CronJob template)
```

**Kubernetes API:**
```
✅ Job created: home-hello-world-1718264400-abc12
```

**Job controller:**
```
"Job exists, need to run it"
```

Creates a Pod:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: home-hello-world-1718264400-abc12
  namespace: home
  labels:
    job-name: home-hello-world-1718264400-abc12
spec:
  (based on Job template)
```

**Kubernetes API:**
```
✅ Pod created: home-hello-world-1718264400-abc12
```

---

## LAYER 5: CONTAINER EXECUTION

### kubelet (on your node)

```
1. Detects new Pod
2. PullImage: busybox:latest
3. CreateContainer
4. SetupSecurityContext:
     - runAsUser: 1000 (non-root)
     - runAsGroup: 3000
     - readOnlyRootFilesystem: true
5. StartContainer
6. Run command: /bin/sh -c '...'
```

### Container Output

```
Hello from the personal platform!
Current timestamp: 2024-06-13 07:00:15 UTC
Pod: home-hello-world-1718264400-abc12
```

### Container Lifecycle

```
Status: Running
  └─ Executing command
  └─ Writing to stdout
  └─ Exit code: 0 (success)

kubelet detects exit
  └─ Status changes: Succeeded
  └─ kubelet captures logs
  └─ Pod remains for history (ttlSecondsAfterFinished: 86400 = 24 hours)
```

---

## LAYER 6: LOGS & OBSERVABILITY

### View the Pod
```bash
$ kubectl get pods -n home -l app.kubernetes.io/name=hello-world

NAME                                    READY   STATUS      RESTARTS   AGE
home-hello-world-1718264400-abc12      0/1     Completed   0          2m
```

### View the Logs
```bash
$ kubectl logs -n home home-hello-world-1718264400-abc12

Hello from the personal platform!
Current timestamp: 2024-06-13 07:00:15 UTC
Pod: home-hello-world-1718264400-abc12
```

Or:
```bash
$ kubectl logs -n home -l app.kubernetes.io/name=hello-world --tail=20

(same output)
```

### View the CronJob
```bash
$ kubectl get cronjob -n home

NAME               SCHEDULE    TIMEZONE   SUSPEND   ACTIVE   LAST SCHEDULE   AGE
home-hello-world   0 7 * * *   UTC        False     0        2m ago          1h
```

### View the Job
```bash
$ kubectl get jobs -n home

NAME                              COMPLETIONS   DURATION   AGE
home-hello-world-1718264400      1/1           2s         2m
```

### View ArgoCD Applications
```bash
$ kubectl get applications -n argocd

NAME                       SYNC STATUS   HEALTH STATUS   AGE
platform-applications      Synced        Healthy         1h
home-hello-world           Synced        Healthy         1h
home-k8s-health-report     Synced        Healthy         1h
home-notion-monthly        Synced        Healthy         1h
```

---

## COMPLETE FLOW DIAGRAM

```
┌──────────────────────────┐
│  GitHub Repository       │
│  (homelab-gitops)        │
└────────────┬─────────────┘
             │ git push
             ▼
┌──────────────────────────┐
│  GitHub API              │
│  Webhook notification    │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────────────────────┐
│  ArgoCD Webhook Handler                  │
│  "platform-applications needs sync"      │
└────────────┬─────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────┐
│  ArgoCD Application Controller           │
│  Syncing: platform-applications          │
│                                          │
│  1. Fetch repo                           │
│  2. Go to: platform/applications-chart   │
│  3. Render Helm                          │
│  4. Generate Applications                │
└────────────┬─────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────┐
│  Helm Template Rendering                 │
│  Input: values.yaml (enabled: true)      │
│  Template: applications.yaml             │
│  Output: Application manifests           │
│    - home-hello-world                    │
│    - home-k8s-health-report              │
│    - home-notion-monthly                 │
│    - (NOT home-github-summary: disabled) │
└────────────┬─────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────┐
│  Kubernetes API Server                   │
│  Apply generated Applications            │
└────────────┬─────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────┐
│  ArgoCD Application Controller           │
│  New Application detected: home-hello... │
│  Syncing: home-hello-world               │
│                                          │
│  1. Fetch repo                           │
│  2. Go to: charts/hello-world            │
│  3. Resolve dependencies: base-chart     │
│  4. Render Helm                          │
│  5. Generate Kubernetes manifests        │
└────────────┬─────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────┐
│  Helm Template Rendering                 │
│  Input: hello-world values.yaml          │
│  Parent: base-chart/templates/           │
│  Output: Kubernetes manifests            │
│    - ServiceAccount                      │
│    - Role                                │
│    - RoleBinding                         │
│    - CronJob                             │
└────────────┬─────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────┐
│  Kubernetes API Server                   │
│  Apply generated manifests               │
└────────────┬─────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────┐
│  kubelet (your node)                     │
│  Watches CronJob schedule                │
│  "Next run: 7am UTC"                     │
└────────────┬─────────────────────────────┘
             │ (time passes until 7am UTC)
             ▼
┌──────────────────────────────────────────┐
│  kube-scheduler                          │
│  "CronJob should run now"                │
│  Creates: Job                            │
└────────────┬─────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────┐
│  Job Controller                          │
│  Creates: Pod                            │
└────────────┬─────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────┐
│  kubelet                                 │
│  1. Pull image: busybox                  │
│  2. Create container                     │
│  3. Set security context                 │
│  4. Run command                          │
└────────────┬─────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────┐
│  Container Execution                     │
│  /bin/sh -c                              │
│  echo "Hello from..."                    │
│  echo "Current timestamp: ..."           │
│  echo "Pod: ..."                         │
└────────────┬─────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────┐
│  Log Output                              │
│  kubelet captures stdout                 │
│  Stores in log stream                    │
└────────────┬─────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────┐
│  You View Logs                           │
│  $ kubectl logs -n home ...              │
│                                          │
│  Hello from the personal platform!       │
│  Current timestamp: 2024-06-13 07:00:15  │
│  Pod: home-hello-world-...               │
└──────────────────────────────────────────┘
```

---

## TIME BREAKDOWN

| Stage | Time |
|-------|------|
| git push | Instant |
| GitHub webhook → ArgoCD | < 1 second |
| ArgoCD renders platform-applications | 1-2 seconds |
| Kubernetes applies Application | < 1 second |
| ArgoCD renders hello-world | 2-3 seconds |
| Kubernetes applies manifests | < 1 second |
| **Total until "ready"** | **~10 seconds** |
| Kubernetes waits for schedule | Until 7am UTC |
| Pod creation + execution | < 1 second |
| **Total until "running"** | **~10 seconds OR until next 7am** |

---

## KEY TRANSFORMATIONS

```
Platform Files
  ↓
Helm Chart 1 (platform-applications)
  ↓
Application Manifests (home-hello-world)
  ↓
Kubernetes API (creates Application in argocd namespace)
  ↓
Helm Chart 2 (hello-world + base-chart)
  ↓
Kubernetes Manifests (ServiceAccount, Role, RoleBinding, CronJob)
  ↓
Kubernetes API (creates resources in home namespace)
  ↓
kube-scheduler + kubelet
  ↓
Container Runtime
  ↓
Container Execution
  ↓
Logs
```

---

## WHAT IF YOU CHANGE SOMETHING?

### Scenario 1: Change Schedule

**Edit: charts/hello-world/values.yaml**
```yaml
schedule: "0 9 * * *"  # ← Change from 7am to 9am
```

**git push**

**ArgoCD:**
1. Renders hello-world chart again
2. Detects change in CronJob schedule
3. Updates CronJob: "0 9 * * *"
4. Old CronJob deleted (prune: true)

**Result:** Next run is 9am UTC instead of 7am. Automatic. No manual steps.

### Scenario 2: Disable the App

**Edit: platform/applications-chart/values.yaml**
```yaml
hello-world:
  enabled: false  # ← Disable
```

**git push**

**ArgoCD (platform-applications):**
1. Renders chart again
2. hello-world NOT in generated manifests (if statement skips it)
3. Detects: Application exists in cluster, not in generated
4. Deletes: home-hello-world Application

**Kubernetes (cascading delete):**
1. Deletes Application
2. Deletes all related resources (CronJob, ServiceAccount, Role, RoleBinding)
3. No orphaned resources

**Result:** App completely removed. Automatic cleanup. No manual steps.

---

## SUMMARY

Everything starts with **one git push**:

```
git push
  ↓ (ArgoCD detects via webhook)
Helm renders platform-applications
  ↓ (generates home-hello-world Application)
Kubernetes applies Application
  ↓ (ArgoCD detects new Application)
Helm renders hello-world chart
  ↓ (with base-chart templates)
Kubernetes applies manifests
  ↓ (ServiceAccount, Role, RoleBinding, CronJob)
At scheduled time, kubelet runs Pod
  ↓ (7am UTC)
Container executes
  ↓
Logs available for viewing
```

**Everything is:**
- ✅ Automated
- ✅ Declarative (in git)
- ✅ Reproducible
- ✅ Observable (logs, status)
- ✅ Reversible (git revert)

This is GitOps.

---

See: [APPS_OF_APPS.md](APPS_OF_APPS.md), [README.md](README.md), [platform/applications-chart/README.md](platform/applications-chart/README.md)
