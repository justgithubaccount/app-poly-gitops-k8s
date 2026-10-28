## [1.4.1](https://github.com/justgithubaccount/app-poly-gitops-k8s/compare/v1.4.0...v1.4.1) (2026-10-28)

### 🐛 Bug Fixes

* route dev traces through Vector ([729da1d](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/729da1ddced4abbb02f6e8067e7d93d752d28289))

## [1.4.0](https://github.com/justgithubaccount/app-poly-gitops-k8s/compare/v1.3.1...v1.4.0) (2026-10-28)

### 🚀 Features

* make dev the complete application cluster ([#19](https://github.com/justgithubaccount/app-poly-gitops-k8s/issues/19)) ([4c82dbc](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/4c82dbccc0213cf1390175a7f835ef735ee72e87))

## [1.3.1](https://github.com/justgithubaccount/app-poly-gitops-k8s/compare/v1.3.0...v1.3.1) (2026-10-28)

### 🐛 Bug Fixes

* keep smoke LLM config in GitOps ([#18](https://github.com/justgithubaccount/app-poly-gitops-k8s/issues/18)) ([ef77ada](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/ef77ada33febe0643df0663666fe7621e801e3e5))

## [1.3.0](https://github.com/justgithubaccount/app-poly-gitops-k8s/compare/v1.2.2...v1.3.0) (2026-10-28)

### 🚀 Features

* add smoke trace pipeline ([#17](https://github.com/justgithubaccount/app-poly-gitops-k8s/issues/17)) ([968344e](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/968344e085ddb066f8204b117f01153ceb6e401b))

## [1.2.2](https://github.com/justgithubaccount/app-poly-gitops-k8s/compare/v1.2.1...v1.2.2) (2026-10-28)

### 🐛 Bug Fixes

* align CrewAI application revision ([#16](https://github.com/justgithubaccount/app-poly-gitops-k8s/issues/16)) ([15ab2a2](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/15ab2a21cd91610543c07b3e8f316eead2ace94e))

## [1.2.1](https://github.com/justgithubaccount/app-poly-gitops-k8s/compare/v1.2.0...v1.2.1) (2026-10-28)

### 🐛 Bug Fixes

* deploy grounded CrewAI health reports ([#15](https://github.com/justgithubaccount/app-poly-gitops-k8s/issues/15)) ([bbdefb8](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/bbdefb8d03b95fbc00bd8afa5f12e7f0965b09e6))

## [1.2.0](https://github.com/justgithubaccount/app-poly-gitops-k8s/compare/v1.1.0...v1.2.0) (2026-10-28)

### 🚀 Features

* wire CrewAI LLM runtime secret ([#14](https://github.com/justgithubaccount/app-poly-gitops-k8s/issues/14)) ([3d6c0ba](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/3d6c0ba8726d8c9ea21f7ba52479b029d75056de))

## [1.1.0](https://github.com/justgithubaccount/app-poly-gitops-k8s/compare/v1.0.0...v1.1.0) (2026-10-28)

### 🚀 Features

* add CrewAI smoke workload ([#13](https://github.com/justgithubaccount/app-poly-gitops-k8s/issues/13)) ([138fafb](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/138fafba32f8d688d5304b403e386b98a147cc06))

## 1.0.0 (2026-10-28)

### 🚀 Features

* **clusters:** activate prd environment ([b51c605](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/b51c6055feb7dcc59ffaa041be6bb339e95ec30b))
* add CloudNativePG operator and migrate chat-api to CNPG ([545cc24](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/545cc2407102f3f4deff085389aea2de0438fbfb))
* add Crunchy Data PostgreSQL Operator for chat-api ([#9](https://github.com/justgithubaccount/app-poly-gitops-k8s/issues/9)) ([b977342](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/b9773428b46e9567564a5d1dd9af5c049ce5e9e2))
* **tenants:** add data-team tenant ([4256026](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/4256026929773cacdada62f4487585be35141538))
* **tenants:** add helm values for all chat environments ([ba7cd0d](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/ba7cd0de77fcf38b807d69d687bbef2d1cf01b92))
* **tenants:** add ml-team tenant ([a55e29a](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/a55e29a7dcca7c72b7791fe8779148235fd6d6e3))
* **rbac:** add multi-cluster support for tenants ([f8def29](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/f8def295acd4f63214477af5d0b923489e6d4d58))
* **tenants:** add namespace isolation and resource quotas ([51aec0e](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/51aec0e2230f69f352fa9083eb9d22d39fe52921))
* add namespace manifests for automatic sync ([#3](https://github.com/justgithubaccount/app-poly-gitops-k8s/issues/3)) ([326ebe6](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/326ebe6d87cfe70a2dcad5553659b16f01995ff9))
* **clusters:** add stg environment ([3e69a00](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/3e69a008c1c14d0be2c635e6ed7a8ce32404dd3e))
* **clusters:** add tst environment ([57e1309](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/57e1309348c66feaec5bf41ff5e80317cd3f82d9))
* **chat:** configure chat-api Application for 4 environments ([#5](https://github.com/justgithubaccount/app-poly-gitops-k8s/issues/5)) ([6b66a6c](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/6b66a6c81af8f1a19c882cbb4ba45b5128376b31))
* unified Cloudflare secret with Reflector replication ([#8](https://github.com/justgithubaccount/app-poly-gitops-k8s/issues/8)) ([e084269](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/e084269a33ff29b62f0aac712e0ee3ef5856d17d))

### 🐛 Bug Fixes

* add high sync-wave values for CRD-dependent resources ([712dd01](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/712dd01a917bf779f5f2621fc155322155a078d9))
* add reflector annotations for cloudflare secret replication to cert-manager ([52ccfbc](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/52ccfbc01298339dd33cf5aa86d4e660bff0014e))
* add SkipDryRunOnMissingResource for CRD bootstrap ordering ([fcb411e](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/fcb411e1c75d7803ad97b0d9f955eb4f715b6913))
* add sync-wave to cloudflare secret and fix secret key name ([45a9aa2](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/45a9aa28429dcf8e8066f8d112625bfd8d831816))
* align conventional changelog writer versions ([#12](https://github.com/justgithubaccount/app-poly-gitops-k8s/issues/12)) ([00f76bb](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/00f76bb3f2f9b28c7f38f55ec78bd85189255b71))
* align GitOps app with current chart and image ([#10](https://github.com/justgithubaccount/app-poly-gitops-k8s/issues/10)) ([309cc63](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/309cc63cf1d19fd02eceb044e19f4928d96a880f))
* correct syncPolicy indentation and add sync-wave to PostgresCluster ([2dbcfbd](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/2dbcfbd76f7365961d3e67ae2afea543dad4e1d8))
* disable backend-protocol HTTPS for ArgoCD ingress ([63953c4](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/63953c4a37c8ceb6ac30d33269733eec53880d12))
* make semantic release dependencies reproducible ([#11](https://github.com/justgithubaccount/app-poly-gitops-k8s/issues/11)) ([655acf5](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/655acf5c5e4a3476c3fa967bed301a217c0849f0))
* move debug sink inside sinks block in vector-gateway config ([1f1ad13](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/1f1ad1304b16d8263121dcb3b25b80eae90fcf26))
* **nginx:** move ingress resources to base directory ([324dcef](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/324dcef6b62bbb93c174571bb2a11afdce1f3409))
* **secrets:** regenerate SealedSecrets with current controller key ([#7](https://github.com/justgithubaccount/app-poly-gitops-k8s/issues/7)) ([e67b7f5](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/e67b7f515d3618b33a6c9147a0178e04b29e305e))
* simplify PostgresCluster config to fix CrashLoopBackOff ([cb438cf](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/cb438cf9ef696152801aebac89ed7d31108ea509))
* **ci:** skip CRD types in kubeconform validation ([54d11bf](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/54d11bfca0661042b626ee5a29abe3ef782cd956))
* **gitops:** split ApplicationSet for dev Image Updater support ([dd37270](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/dd372706fdf15c8f93277069142cc951d03d944f))
* **clusters:** update dev bootstrap to correct repository ([5153c4b](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/5153c4ba763347c457c738e30573d071d66b0f54))
* use PGO secret for DATABASE_URL instead of SealedSecret ([25fc7ed](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/25fc7edabe056b0b521ee239e0ef91d5c0e0f038))

### 📚 Documentation

* add architecture and golden install documentation ([c8b9b68](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/c8b9b68cb5b800b247c0ee8b1cc1e7770c9b57d1))
* add argocd-demo reference context ([999885c](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/999885c5611ad6eae1823467465ed01eaa1e680d))
* update CLAUDE.md with golden install fixes ([3495738](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/3495738d0ec121270268acab803cd8d9f4a25296))

### ♻️ Code Refactoring

* **gitops:** implement matrix generator for tenant apps ([a9942da](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/a9942da965daf6f6e1a26cb4a1e3463b5f7b7605))

### ✅ Tests

* use in-cluster for all environments (single cluster testing) ([4a71b13](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/4a71b130cd0adee310f84f21b10e7d565bd93503))

### 🔧 CI/CD

* **workflows:** add release workflow and update validate matrix ([7c939da](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/7c939daa1ba3110ef79eed94b3490a2d7214d7a9))
* improve validation workflow with better OPA error reporting ([030686e](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/030686eb4f924add6b5acdf6765ce140b69ba961))

### 🏗️ Chores

* **ai-platform:** add Dify placeholder ([145426e](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/145426ea91fa61916756c05dbbebaafc24af89ec))
* add semantic-release configuration ([37c3ccd](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/37c3ccd672951e65d70c987e98d67632eefd618e))
* regenerate sealed secrets for new cluster ([a5bca5a](https://github.com/justgithubaccount/app-poly-gitops-k8s/commit/a5bca5a8b2861d69946f921f553eac983322ffe6))
