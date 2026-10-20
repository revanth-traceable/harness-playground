# Harness SMP under Argo CD (lab)

The `harness` Helm release in namespace `harness` (chart 0.46.0), managed by Argo CD.

| Path                      | What it is                                                   |
| ------------------------- | ------------------------------------------------------------ |
| `values/lab-values.yaml`  | Values for the chart. Holds Secret **names** only, no secret values |
| `argocd/harness-smp.yaml` | The Argo CD Application (chart from the Harness Helm repo, values from this branch) |

## Secrets that live outside Git

This repository is public. Create these in the cluster before the first sync:

```bash
# Harness license, referenced by global.license.secrets.kubernetesSecrets
kubectl create secret generic harness-license -n harness --from-file=NG_LICENSE=<license-file>
```

## Apply

```bash
kubectl apply -f smp-argocd/argocd/harness-smp.yaml
argocd app diff harness-smp      # review before syncing
argocd app sync harness-smp
```

Sync is manual, with no prune and no self-heal.
