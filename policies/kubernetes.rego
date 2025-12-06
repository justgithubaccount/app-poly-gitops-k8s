package kubernetes

import rego.v1

# ═══════════════════════════════════════════════════════════════════════════════
# Cluster-scoped resources (не требуют namespace)
# ═══════════════════════════════════════════════════════════════════════════════
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

# ArgoCD resources (управляются ArgoCD, имеют свой namespace в spec)
argocd_kinds := {
  "Application",
  "ApplicationSet",
  "AppProject",
}

# ═══════════════════════════════════════════════════════════════════════════════
# 📛 1. Namespace должен быть указан (для namespaced ресурсов)
# ═══════════════════════════════════════════════════════════════════════════════
deny contains msg if {
  not cluster_scoped_kinds[input.kind]
  not argocd_kinds[input.kind]
  not input.metadata.namespace
  msg := sprintf("[%s/%s] Resource is missing namespace", [input.kind, input.metadata.name])
}

# ═══════════════════════════════════════════════════════════════════════════════
# 🛡️ 2. Контейнеры должны иметь ресурсы
# ═══════════════════════════════════════════════════════════════════════════════
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

# ═══════════════════════════════════════════════════════════════════════════════
# 🔬 3. Должны быть probes (только для production workloads)
# ═══════════════════════════════════════════════════════════════════════════════
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

# Определяем production workloads по labels
is_production_workload if {
  input.metadata.labels.env == "prd"
}

is_production_workload if {
  input.metadata.labels.environment == "production"
}

# ═══════════════════════════════════════════════════════════════════════════════
# 🔐 4. Security context (рекомендации, не обязательно)
# ═══════════════════════════════════════════════════════════════════════════════
# Примечание: многие сторонние чарты не имеют runAsNonRoot
# warn contains msg if {
#   input.kind == "Deployment"
#   not input.spec.template.spec.securityContext.runAsNonRoot
#   msg := sprintf("[Deployment/%s] Recommendation: set runAsNonRoot: true", [input.metadata.name])
# }

# ═══════════════════════════════════════════════════════════════════════════════
# 📦 5. Chat-API специфичные проверки
# ═══════════════════════════════════════════════════════════════════════════════
# Примечание: отключено, т.к. annotation задается через Helm values
# deny contains msg if {
#   input.kind == "Deployment"
#   input.metadata.labels["app.kubernetes.io/name"] == "chat-api"
#   not input.spec.template.metadata.annotations["openrouter.model"]
#   msg := "[Deployment/chat-api] Missing openrouter.model annotation"
# }

# ═══════════════════════════════════════════════════════════════════════════════
# 🔭 6. OTEL (только для production)
# ═══════════════════════════════════════════════════════════════════════════════
# Примечание: отключено, т.к. OTEL injector добавляет автоматически
# deny contains msg if {
#   input.kind == "Deployment"
#   is_production_workload
#   container := input.spec.template.spec.containers[_]
#   not has_otel_endpoint(container)
#   msg := sprintf("[Deployment/%s] Container '%s' missing OTEL_EXPORTER_OTLP_ENDPOINT", [input.metadata.name, container.name])
# }

# has_otel_endpoint(container) if {
#   some env in container.env
#   env.name == "OTEL_EXPORTER_OTLP_ENDPOINT"
# }

# ═══════════════════════════════════════════════════════════════════════════════
# 🏷️ 7. Labels обязательны для workloads
# ═══════════════════════════════════════════════════════════════════════════════
deny contains msg if {
  input.kind == "Deployment"
  not input.metadata.labels["app.kubernetes.io/name"]
  msg := sprintf("[Deployment/%s] Missing required label: app.kubernetes.io/name", [input.metadata.name])
}

# ═══════════════════════════════════════════════════════════════════════════════
# 🔒 8. SealedSecrets должны иметь namespace
# ═══════════════════════════════════════════════════════════════════════════════
deny contains msg if {
  input.kind == "SealedSecret"
  not input.metadata.namespace
  msg := sprintf("[SealedSecret/%s] Must have namespace specified", [input.metadata.name])
}

# ═══════════════════════════════════════════════════════════════════════════════
# 🌐 9. Ingress должен иметь TLS для production
# ═══════════════════════════════════════════════════════════════════════════════
deny contains msg if {
  input.kind == "Ingress"
  input.metadata.labels.env == "prd"
  not input.spec.tls
  msg := sprintf("[Ingress/%s] Production ingress must have TLS configured", [input.metadata.name])
}

# ═══════════════════════════════════════════════════════════════════════════════
# 📊 10. HPA должен иметь разумные лимиты
# ═══════════════════════════════════════════════════════════════════════════════
deny contains msg if {
  input.kind == "HorizontalPodAutoscaler"
  input.spec.maxReplicas > 100
  msg := sprintf("[HPA/%s] maxReplicas > 100 is likely a mistake", [input.metadata.name])
}