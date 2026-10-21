# Harness SMP under Argo CD (lab)

The `harness` Helm release in namespace `harness` (chart 0.46.0), managed by Argo CD.

| Path                       | What it is                                                                          |
| -------------------------- | ----------------------------------------------------------------------------------- |
| `override-demo.yaml`       | Sizing profile shipped inside the chart, loaded first. No sizing is set in this repo |
| `values/lab-values.yaml`   | Lab settings that differ from the chart defaults and the demo profile               |
| `values/lab-security.yaml` | Pod and container security contexts                                                 |
| `values/lab-secrets.yaml`  | Secret references only: which Secret and key each service reads. Names, no values   |
| `argocd/harness-smp.yaml`  | The Argo CD Application (chart from the Harness Helm repo, values from this branch) |

## Secrets that live outside Git

This repository is public. Create these in the cluster before the first sync:

```bash
# Harness license, referenced by global.license.secrets.kubernetesSecrets
kubectl create secret generic harness-license -n harness --from-file=NG_LICENSE=<license-file>

# harness-db-migrator SECRET, pinned so a re-created Secret keeps the current value
kubectl create secret generic harness-db-migrator-pinned -n harness --from-literal=SECRET=<current value>
```

The services' shared JWT secrets come from `harness-shared-secrets-046-r7`, which must also exist in the cluster.

## Apply

```bash
kubectl apply -f smp-argocd/argocd/harness-smp.yaml
argocd app diff harness-smp      # review before syncing
argocd app sync harness-smp
```

Sync is manual, with no prune and no self-heal.
