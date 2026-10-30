package kubernetes

import rego.v1

# Cluster-scoped resources do not require metadata.namespace.
cluster_scoped_kinds := {
  "Namespace",
  "ClusterRole",
  "ClusterRoleBinding",
  "ClusterIssuer",
  "CustomResourceDefinition",
  "StorageClass",
  "PersistentVolume",
  "IngressClass",
  "PriorityClass",
  "ValidatingWebhookConfiguration",
  "MutatingWebhookConfiguration",
}

# Argo CD resources follow their own destination namespace rules.
argocd_kinds := {
  "Application",
  "ApplicationSet",
  "AppProject",
}

# Namespaced resources must declare metadata.namespace.
deny contains msg if {
  not cluster_scoped_kinds[input.kind]
  not argocd_kinds[input.kind]
  not input.metadata.namespace
  msg := sprintf("[%s/%s] Resource is missing namespace", [input.kind, input.metadata.name])
}

# Deployment containers must set memory and CPU limits.
deny contains msg if {
  input.kind == "Deployment"
  container := input.spec.template.spec.containers[_]
  not container.resources.limits.memory
  msg := sprintf("[Deployment/%s] Container '%s' missing memory limit", [input.metadata.name, container.name])
}

deny contains msg if {
  input.kind == "Deployment"
  container := input.spec.template.spec.containers[_]
  not container.resources.limits.cpu
  msg := sprintf("[Deployment/%s] Container '%s' missing CPU limit", [input.metadata.name, container.name])
}

# Production Deployment containers must define liveness and readiness probes.
deny contains msg if {
  input.kind == "Deployment"
  is_production_workload
  container := input.spec.template.spec.containers[_]
  not container.livenessProbe
  msg := sprintf("[Deployment/%s] Container '%s' missing livenessProbe", [input.metadata.name, container.name])
}

deny contains msg if {
  input.kind == "Deployment"
  is_production_workload
  container := input.spec.template.spec.containers[_]
  not container.readinessProbe
  msg := sprintf("[Deployment/%s] Container '%s' missing readinessProbe", [input.metadata.name, container.name])
}

is_production_workload if {
  input.metadata.labels.env == "prd"
}

is_production_workload if {
  input.metadata.labels.environment == "production"
}

# Workload labels are required for selection and ownership.
deny contains msg if {
  input.kind == "Deployment"
  not input.metadata.labels["app.kubernetes.io/name"]
  msg := sprintf("[Deployment/%s] Missing required label: app.kubernetes.io/name", [input.metadata.name])
}

deny contains msg if {
  input.kind == "SealedSecret"
  not input.metadata.namespace
  msg := sprintf("[SealedSecret/%s] Must have namespace specified", [input.metadata.name])
}

# Production Ingress resources must terminate TLS.
deny contains msg if {
  input.kind == "Ingress"
  input.metadata.labels.env == "prd"
  not input.spec.tls
  msg := sprintf("[Ingress/%s] Production ingress must have TLS configured", [input.metadata.name])
}

# Reject likely accidental HPA limits.
deny contains msg if {
  input.kind == "HorizontalPodAutoscaler"
  input.spec.maxReplicas > 100
  msg := sprintf("[HPA/%s] maxReplicas > 100 is likely a mistake", [input.metadata.name])
}
