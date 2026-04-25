---
title: "TestQL Faza 6: Auto-Discovery dowolnego artefaktu IT i generowanie testów"
slug: testql-phase-6-artifact-discovery
date: 2026-04-25
project: testql
version_target: "1.1.0 → 1.5.0"
phases: 6
parent_plan: testql-multi-dsl-refactor-plan.md
status: proposed
audience: llm-executor, human-reviewer
markpact: "plan path=articles/testql-phase-6-artifact-discovery.md"
tags: [testql, refactoring, artifact-discovery, test-generation, semcod]
---

# TestQL Faza 6: Auto-Discovery + Auto-Generation dla dowolnego artefaktu IT

Rozszerzenie planu `testql-multi-dsl-refactor-plan.md` o szóstą fazę: automatyczne wykrywanie typu artefaktu (paczka, projekt, usługa, plik konfiguracyjny) przez skanowanie struktury — nawet gdy manifest jest niekompletny lub go nie ma — i generowanie testów w wybranym DSL.

## 1. Cel strategiczny

Dla dowolnego artefaktu IT wskazanego ścieżką, URL-em lub deskryptorem:

- Wykryj typ (lub kombinację typów) przez wieloźródłowe skanowanie.
- Znormalizuj manifest do wspólnej reprezentacji `ArtifactManifest`, nawet z fragmentarycznymi danymi.
- Dobierz przepisy testowe (recipes) odpowiednie dla tego typu i poziomu kompletności manifestu.
- Wygeneruj testy w wybranym DSL (TestTOON, NL, Pytest, ...) używając Unified IR z Fazy 0.
- Uruchom testy w pipeline executora i raportuj.

Wynik: TestQL przestaje być narzędziem "dla projektów które już mają OpenAPI/DOQL/SUMD" i staje się narzędziem "wskaż mi cokolwiek IT, dam ci testy".

Kluczowa zasada: brak manifestu nie blokuje generowania testów. Skan struktury zawsze daje minimum testów (smoke, dependency-audit, install). Pełny manifest tylko zwiększa pokrycie i pewność.

## 2. Architektura

```text
                    ┌──────────────────────────────────────┐
                    │  Source: path | URL | descriptor     │
                    │  (./my-project, https://api.x.com,   │
                    │   pypi:requests, npm:react, ...)     │
                    └─────────────────┬────────────────────┘
                                      │
                    ┌─────────────────▼────────────────────┐
                    │  ProbeRegistry                       │
                    │  - filesystem walker                 │
                    │  - URL fetcher (HEAD/GET/OPTIONS)    │
                    │  - registry lookups (PyPI, npm, ...)│
                    │  - container inspector              │
                    └─────────────────┬────────────────────┘
                                      │ N probes fire
                    ┌─────────────────▼────────────────────┐
                    │  ArtifactManifest (normalized)       │
                    │  {                                   │
                    │    types: ["python_pkg", "fastapi"], │
                    │    confidence: "partial",            │
                    │    evidence: [...],                  │
                    │    metadata: {...},                  │
                    │    dependencies: [...],              │
                    │    interfaces: [...],                │
                    │    children: [...]   # rekursja      │
                    │  }                                   │
                    └─────────────────┬────────────────────┘
                                      │
                    ┌─────────────────▼────────────────────┐
                    │  RecipeRegistry                      │
                    │  match(types, confidence) → [recipes]│
                    └─────────────────┬────────────────────┘
                                      │
                    ┌─────────────────▼────────────────────┐
                    │  Recipe.generate(manifest)           │
                    │  → TestPlan IR (z Fazy 0)            │
                    └─────────────────┬────────────────────┘
                                      │
                    ┌─────────────────▼────────────────────┐
                    │  DSLAdapter.render(plan)             │
                    │  → wybrany format DSL                │
                    └─────────────────┬────────────────────┘
                                      │
                    ┌─────────────────▼────────────────────┐
                    │  Existing Executor pipeline (Faza 1) │
                    │  → wykonanie + raport                │
                    └──────────────────────────────────────┘
```

Trzy nowe abstrakcje:

- `Probe` — wykrywa pojedyncze "ślady" istnienia artefaktu (`pyproject.toml` istnieje, `/openapi.json` zwraca 200, port 5432 odpowiada PG handshake).
- `ArtifactManifest` — znormalizowany opis artefaktu z metadanymi, evidence, confidence score.
- `Recipe` — generator testów dla danej kombinacji typów; produkuje `TestPlan` IR.

## 3. Taksonomia artefaktów IT (full catalog)

Poniżej kompletny katalog wspieranych typów artefaktów. Każda pozycja ma być obsługiwana przez minimum jeden Probe i jedną Recipe. Priorytety oznaczone: `[P0]` = MVP w 1.1.0, `[P1]` = 1.2.0, `[P2]` = 1.3.0, `[P3]` = 1.4.0+.

### 3.1 Paczki kodu (build manifests)

| Język / ekosystem | Pliki manifestu | Priorytet |
| --- | --- | --- |
| Python | `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements*.txt`, `Pipfile`, `poetry.lock`, `environment.yml` (conda) | P0 |
| Node / JS / TS | `package.json`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `bun.lockb`, `tsconfig.json` | P0 |
| Rust | `Cargo.toml`, `Cargo.lock` | P1 |
| Go | `go.mod`, `go.sum` | P1 |
| Java / JVM | `pom.xml`, `build.gradle(.kts)`, `ivy.xml` | P2 |
| .NET | `*.csproj`, `*.fsproj`, `*.sln`, `packages.config`, `paket.dependencies` | P2 |
| Ruby | `Gemfile`, `Gemfile.lock`, `*.gemspec` | P2 |
| PHP | `composer.json`, `composer.lock` | P2 |
| Elixir / Erlang | `mix.exs`, `mix.lock`, `rebar.config` | P3 |
| Haskell | `*.cabal`, `stack.yaml`, `package.yaml` | P3 |
| C / C++ | `CMakeLists.txt`, `Makefile`, `conanfile.txt`, `vcpkg.json`, `meson.build`, `BUILD` (Bazel) | P2 |
| Swift | `Package.swift`, `*.podspec` | P3 |
| Dart / Flutter | `pubspec.yaml` | P3 |
| Kotlin Multiplatform | `build.gradle.kts` (KMP) | P3 |
| Scala | `build.sbt` | P3 |
| R | `DESCRIPTION`, `renv.lock` | P3 |
| Perl | `cpanfile`, `Makefile.PL` | P3 |
| Lua | `*.rockspec` | P3 |
| Crystal | `shard.yml` | P3 |
| Nim | `*.nimble` | P3 |
| Zig | `build.zig`, `build.zig.zon` | P3 |

Recipes per paczka kodu (uniwersalne):

- `dependency-audit` — sprawdzenie znanych CVE w deklarowanych zależnościach
- `lockfile-integrity` — czy lockfile zgadza się z deklaracją
- `install-smoke` — `pip install .` / `npm install` przechodzi
- `import-smoke` — entry point importuje się bez błędu
- `version-consistency` — wersja spójna między plikami
- `license-check` — license deklarowana i kompatybilna
- `metadata-completeness` — name/version/description/author obecne

### 3.2 Web frontend / SSR

| Typ | Markery wykrywania | Priorytet |
| --- | --- | --- |
| React SPA | `react`, `react-dom` w `package.json`, `src/App.{j,t}sx` | P0 |
| Vue SPA | `vue` w deps, `*.vue` files | P1 |
| Angular | `@angular/core`, `angular.json` | P2 |
| Svelte / SvelteKit | `svelte` w deps, `svelte.config.js` | P1 |
| Next.js | `next` w deps, `next.config.{js,ts}` | P0 |
| Nuxt | `nuxt` w deps, `nuxt.config.{js,ts}` | P2 |
| Astro | `astro` w deps, `astro.config.mjs` | P2 |
| Remix | `@remix-run/*` | P2 |
| Solid / Qwik / Fresh | per-framework markers | P3 |
| Hugo | `config.{toml,yaml,json}` + `themes/`, `content/` | P2 |
| Jekyll | `_config.yml`, `_posts/` | P3 |
| MkDocs | `mkdocs.yml`, `docs/` | P1 |
| Docusaurus | `docusaurus.config.{js,ts}` | P2 |
| Sphinx | `conf.py`, `index.rst` | P2 |
| VitePress | `.vitepress/config.{js,ts}` | P3 |
| Bare HTML | `index.html` w korzeniu (no framework) | P0 |
| WordPress | `wp-config.php`, `wp-content/` | P2 |

Recipes:

- `build-smoke` — `npm run build` / `hugo` przechodzi
- `dev-server-starts` — port nasłuchuje, `/` zwraca 200
- `lighthouse-baseline` — performance/a11y minimalne progi
- `link-check` — broken links scan (htmlproofer-like)
- `meta-tags-presence` — title, description, OG tags
- `404-page-exists`
- `sitemap-valid`
- `robots-txt-valid`

### 3.3 Definicje API

| Format | Pliki / endpointy | Priorytet |
| --- | --- | --- |
| OpenAPI 2.0/3.0/3.1 | `openapi.{json,yaml}`, `swagger.{json,yaml}`, `/openapi.json` endpoint | P0 |
| AsyncAPI | `asyncapi.{json,yaml}` | P2 |
| gRPC / Protobuf | `*.proto`, `buf.yaml`, `buf.gen.yaml` | P1 |
| GraphQL | `*.graphql`, `*.gql`, `/graphql` endpoint (introspection) | P0 |
| WSDL / SOAP | `*.wsdl`, `?wsdl` endpoints | P3 |
| RAML | `*.raml` | P3 |
| API Blueprint | `*.apib` | P3 |
| JSON Schema | `*.schema.json`, `$schema` field | P1 |
| XSD | `*.xsd` | P3 |
| Avro | `*.avsc` | P2 |
| Thrift IDL | `*.thrift` | P3 |
| Postman / Insomnia / Bruno collections | `*.postman_collection.json`, `.bru` | P1 |
| HTTP files (`.http`) | `*.http`, `*.rest` (REST Client / IntelliJ) | P1 |
| HAR files | `*.har` (browser HTTP archives) | P2 |

Recipes:

- Wszystkie z TestQL Phase 1-3 (API, Proto, GraphQL adapters) zastosowane na manifest.

### 3.4 Bazy danych

| Typ | Markery | Priorytet |
| --- | --- | --- |
| PostgreSQL | port 5432, `pg_hba.conf`, `postgresql.conf` | P0 |
| MySQL / MariaDB | port 3306, `my.cnf` | P1 |
| SQLite | `*.db`, `*.sqlite`, `*.sqlite3` files | P0 |
| MS SQL Server | port 1433 | P2 |
| Oracle | port 1521 | P3 |
| MongoDB | port 27017, schemas | P1 |
| Redis | port 6379, `INFO` command | P1 |
| Cassandra / ScyllaDB | port 9042, CQL schemas | P3 |
| Neo4j | port 7687 (Bolt), Cypher schemas | P2 |
| InfluxDB / TimescaleDB | InfluxQL/SQL | P3 |
| Elasticsearch / OpenSearch | port 9200, `_cluster/health` | P2 |
| Vector DBs | Pinecone, Weaviate, Qdrant, Milvus | P2 |
| DuckDB | `*.duckdb` files | P2 |
| Migration tools | Flyway, Liquibase, Alembic, Knex, Prisma, Drizzle, TypeORM, Django, Rails | P1 |

### 3.5 Konteneryzacja / orkiestracja

| Typ | Markery | Priorytet |
| --- | --- | --- |
| Dockerfile | `Dockerfile`, `Containerfile`, `.dockerignore` | P0 |
| docker-compose | `docker-compose.yml`, `compose.yaml`, `docker-compose.override.yml` | P0 |
| Podman Quadlet | `*.container`, `*.volume`, `*.network`, `*.pod`, `*.kube`, `*.image` | P1 |
| Kubernetes manifests | `kind: Deployment/Service/Ingress/...` | P0 |
| Helm charts | `Chart.yaml`, `values.yaml`, `templates/` | P1 |
| Kustomize | `kustomization.yaml` | P2 |
| OpenShift | `BuildConfig`, `DeploymentConfig`, `Route` | P3 |
| Operators / CRD | `apiextensions.k8s.io/v1`, `kind: CustomResourceDefinition` | P3 |
| Service Mesh | Istio (`VirtualService`, `DestinationRule`), Linkerd, Consul Connect | P3 |
| Skaffold / Tilt | `skaffold.yaml`, `Tiltfile` | P3 |
| OCI image | image manifest (registry pull) | P1 |

Recipes (kontenery):

- `image-builds` — `docker build` przechodzi
- `image-runs` — kontener startuje, healthcheck przechodzi
- `image-vuln-scan` — Trivy/Grype/Snyk scan
- `image-size-budget` — rozmiar < threshold
- `image-non-root-user` — nie działa jako root
- `compose-up-smoke` — `docker compose up` + healthchecks
- `quadlet-syntax-valid` — `systemctl daemon-reload` na quadlet generuje poprawny unit
- `k8s-manifest-valid` — `kubectl apply --dry-run=server` przechodzi
- `helm-lint-passes` — `helm lint` + `helm template` valid
- `network-policy-default-deny` — sprawdzenie obecności default-deny

### 3.6 Infrastructure as Code

| Typ | Markery | Priorytet |
| --- | --- | --- |
| Terraform | `*.tf`, `*.tfvars`, `terraform.lock.hcl` | P1 |
| Pulumi | `Pulumi.yaml`, per-language project | P3 |
| AWS CloudFormation | `AWSTemplateFormatVersion`, `Resources:` keys | P2 |
| Azure ARM / Bicep | `*.bicep`, `azuredeploy.json` | P3 |
| GCP Deployment Manager | YAML configs | P3 |
| Ansible | `playbook.yml` (z `hosts:`/`tasks:`), inventory, `roles/` | P2 |
| Salt / Chef / Puppet | per-tool markers | P3 |
| CDK | `cdk.json`, per-language CDK app | P3 |
| Crossplane | per-CRD markers | P3 |

Recipes:

- `tf-validate` — `terraform validate`
- `tf-plan-no-destructive` — plan nie zawiera unexpected destroy
- `ansible-lint` + `ansible-playbook --check`
- `cfn-lint` / `cfn-nag`
- `tflint` / `tfsec` / `checkov` security scans

### 3.7 CI/CD pipelines

| System | Markery | Priorytet |
| --- | --- | --- |
| GitHub Actions | `.github/workflows/*.yml` | P0 |
| GitLab CI | `.gitlab-ci.yml` | P1 |
| CircleCI | `.circleci/config.yml` | P2 |
| Jenkins | `Jenkinsfile` | P2 |
| Azure Pipelines | `azure-pipelines.yml` | P3 |
| Bitbucket Pipelines | `bitbucket-pipelines.yml` | P3 |
| Drone CI | `.drone.yml` | P3 |
| BuildKite | `.buildkite/pipeline.yml` | P3 |
| Argo Workflows / Argo CD | `kind: Workflow`, `kind: Application` | P3 |
| Tekton | `tekton.dev/v1*` resources | P3 |
| Concourse | `pipeline.yml` | P3 |

Recipes:

- `workflow-syntax-valid` — actionlint / GitLab CI Lint API
- `secrets-not-leaked` — sekrety nie w plain text
- `pinned-action-versions` — tylko piny SHA, nie tagi
- `permissions-minimal` — `permissions:` deklarowane

### 3.8 Konfiguracja serwerów / sieci

| Typ | Markery | Priorytet |
| --- | --- | --- |
| nginx | `nginx.conf`, `sites-available/*` | P1 |
| Apache httpd | `httpd.conf`, `*.conf` | P3 |
| Traefik | `traefik.yml`, `traefik.toml`, dynamic config | P1 |
| HAProxy | `haproxy.cfg` | P3 |
| Envoy | `envoy.yaml` | P3 |
| Caddy | `Caddyfile` | P2 |
| iptables / nftables | rule files | P3 |
| WireGuard | `*.conf` w `/etc/wireguard/` | P3 |
| systemd units | `*.service`, `*.timer`, `*.socket` | P2 |
| systemd Quadlet | jak wyżej w 3.5 | P1 |
| SSH config | `sshd_config`, `ssh_config` | P3 |

Recipes:

- `config-syntax-valid` — `nginx -t`, `caddy validate`, `systemd-analyze verify`
- `tls-min-version` — TLS 1.2+
- `cipher-suite-secure` — żadnych legacy
- `headers-security` — HSTS, CSP, X-Frame-Options

### 3.9 Messaging / streaming

| System | Markery / artefakty | Priorytet |
| --- | --- | --- |
| Apache Kafka | topic configs, schema registry (Avro/Proto/JSON Schema) | P2 |
| RabbitMQ | exchange/queue declarations, `definitions.json` | P2 |
| NATS / JetStream | subjects, streams config | P3 |
| MQTT | topic patterns, retained messages | P3 |
| Redis Streams / Pub-Sub | stream/channel patterns | P2 |
| AWS SNS/SQS | queue ARNs, topic ARNs | P3 |
| Google Pub/Sub | topic/subscription configs | P3 |
| Azure Service Bus | namespace + queue/topic | P3 |
| EventBridge | rule definitions | P3 |

### 3.10 Observability

| Typ | Markery | Priorytet |
| --- | --- | --- |
| Prometheus metrics | `/metrics` endpoint, exposition format | P1 |
| Prometheus rules | `rules/*.yml` z `alert:` lub `record:` | P2 |
| Grafana dashboards | `*.json` z `schemaVersion`, `panels` | P2 |
| OpenTelemetry | OTLP collector configs, instrumentation | P2 |
| Jaeger / Zipkin | trace endpoints | P2 |
| Loki / Promtail | log queries, configs | P3 |
| ELK / OpenSearch Dashboards | Kibana dashboards exports | P3 |
| Health endpoints | `/health`, `/healthz`, `/ready`, `/live` | P0 |

### 3.11 Authentication / authorization

| Typ | Markery | Priorytet |
| --- | --- | --- |
| OAuth 2.0 / OIDC | `/.well-known/openid-configuration` | P1 |
| SAML metadata | `*-metadata.xml` | P3 |
| JWT | `Authorization: Bearer ...`, `iss`/`aud` claims | P1 |
| JWKS | `/.well-known/jwks.json` | P1 |
| OPA / Rego | `*.rego` policies | P2 |
| Casbin | `*.csv` model+policy | P3 |
| Keycloak | realm exports | P3 |
| mTLS / X.509 | `*.crt`, `*.pem`, certificate chain | P2 |

Recipes:

- `oidc-discovery-complete` — wszystkie wymagane pola
- `jwks-keys-valid` — klucze parsują się
- `jwt-signature-validates`
- `cert-not-expired`, `cert-chain-valid`
- `cors-policy-restrictive`

### 3.12 CLI tools

| Typ | Markery | Priorytet |
| --- | --- | --- |
| Click / argparse / typer (Python) | dekoratorów `@click.command`, `argparse.ArgumentParser` | P1 |
| commander / yargs (Node) | imports + setup | P2 |
| clap (Rust) | `derive(Parser)`, `clap::Command` | P2 |
| cobra (Go) | `cobra.Command{...}` | P2 |
| Shell scripts | `#!/bin/bash`, `#!/usr/bin/env *sh` | P1 |
| Man pages | `*.1`, `*.5`, `*.8` files | P3 |
| Tab completions | bash/zsh/fish completion files | P3 |

Recipes:

- `--help-exits-0` — pomoc nie zawiesza
- `--version-prints-semver`
- `unknown-flag-exits-2` — POSIX convention
- `subcommands-discovered`
- `completion-installs`

### 3.13 Build artifacts (binary)

| Typ | Markery | Priorytet |
| --- | --- | --- |
| ELF executables | magic `7f 45 4c 46` | P2 |
| Mach-O | macOS binaries | P3 |
| PE / COFF | Windows binaries | P3 |
| OCI container images | `manifest.json`, layers | P0 |
| WebAssembly | `*.wasm`, magic `00 61 73 6d` | P2 |
| JAR / WAR / EAR | ZIP + `META-INF/MANIFEST.MF` | P3 |
| APK | Android, ZIP + `AndroidManifest.xml` | P3 |
| IPA | iOS, ZIP + `Info.plist` | P3 |
| `.deb` / `.rpm` / `.apk` (Alpine) | package metadata | P2 |
| `.snap` / `.flatpak` / `.appimage` | per-format metadata | P3 |
| PyPI wheels (`.whl`) | ZIP + `*.dist-info/METADATA` | P1 |
| npm tarballs (`.tgz`) | TAR + `package/package.json` | P1 |

### 3.14 ML / AI artifacts

| Typ | Markery | Priorytet |
| --- | --- | --- |
| ONNX | `*.onnx`, magic | P2 |
| SafeTensors | `*.safetensors` | P2 |
| PyTorch | `*.pt`, `*.pth` | P3 |
| TensorFlow SavedModel | `saved_model.pb` + `variables/` | P3 |
| Keras | `*.h5` z grupami `model_config` | P3 |
| CoreML | `*.mlmodel` | P3 |
| TFLite | `*.tflite` | P3 |
| GGUF / GGML | `*.gguf` | P2 |
| HuggingFace model card | `README.md` z `model_type:` w frontmatter | P2 |
| Datasets | Parquet z metadata, Arrow IPC, HF datasets | P2 |
| vLLM / Ollama / TGI configs | per-tool YAML | P3 |
| LangChain prompts / LCEL | wykrywalne przez import patterns | P3 |
| Embeddings configs | model name + dim w configu | P2 |
| RAG / Vector DB schemas | per-vector-DB | P2 |

Recipes:

- `model-loads` — model parsuje się bez błędu
- `model-inference-smoke` — input shape → output shape oczekiwany
- `model-determinism` — ten sam input → ten sam output (przy `temperature=0`)
- `model-size-budget` — rozmiar < threshold
- `model-license-permissive` — licencja kompatybilna
- `dataset-schema-stable` — kolumny się nie zmieniły między wersjami

### 3.15 Mobile

| Typ | Markery | Priorytet |
| --- | --- | --- |
| Android Manifest | `AndroidManifest.xml` | P3 |
| iOS Info.plist | `Info.plist`, `*.entitlements` | P3 |
| React Native | `app.json`, `metro.config.js` | P3 |
| Flutter | `pubspec.yaml` z `flutter:` block | P3 |
| Capacitor / Cordova | `capacitor.config.{ts,json}` | P3 |

### 3.16 Browser / IDE / editor extensions

| Typ | Markery | Priorytet |
| --- | --- | --- |
| Chrome / Firefox extensions | `manifest.json` z `manifest_version` | P2 |
| VS Code extensions | `package.json` z `engines.vscode` + `contributes` | P2 |
| JetBrains plugins | `META-INF/plugin.xml` | P3 |
| Vim / Neovim plugins | `plugin/`, `lua/`, `init.lua` patterns | P3 |
| Emacs packages | `*-pkg.el`, `Package-Requires:` headers | P3 |

Recipes (extensions):

- `manifest-version-current` — MV3 dla Chrome, etc.
- `permissions-minimal` — tylko niezbędne
- `host-permissions-explicit`
- `csp-secure`
- `activation-events-narrow` (VS Code)

### 3.17 Konfiguracja / formaty danych

| Format | Markery | Priorytet |
| --- | --- | --- |
| YAML | `*.yml`, `*.yaml`, `---` separators | P0 |
| JSON | `*.json` + walidator parsera | P0 |
| TOML | `*.toml` | P0 |
| HCL | `*.hcl`, `*.tf` | P1 |
| Cue / Dhall / Jsonnet / Nickel | per-language | P3 |
| `.env` / dotenv | `.env*` files | P0 |
| XML / XSD / DTD | `*.xml` z schema | P2 |
| Properties | `*.properties` (Java) | P3 |
| Lua configs | `init.lua`, Neovim configs | P3 |
| EditorConfig | `.editorconfig` | P2 |

Recipes:

- `valid-syntax`
- `schema-conforms` (jeśli jest schema)
- `no-secrets-leaked` — pattern matching na API keys
- `keys-stable` — porównanie z baseline (drift detection)

### 3.18 Specifikacje testowe / kontrakty

| Format | Markery | Priorytet |
| --- | --- | --- |
| Cucumber / Gherkin | `*.feature` files | P2 |
| Playwright tests | `*.spec.{js,ts}` + `@playwright/test` | P1 |
| Cypress tests | `cypress/`, `cypress.config.{js,ts}` | P2 |
| Jest / Vitest / Mocha | `*.test.{js,ts}`, `*.spec.{js,ts}` | P1 |
| Pytest | `test_*.py`, `*_test.py`, `conftest.py` | P0 |
| Go test | `*_test.go` | P2 |
| JUnit / TestNG | `Test*.java`, `*Test.java` | P3 |
| RSpec | `*_spec.rb` | P3 |
| Postman collections | `*.postman_collection.json` | P1 |
| k6 / Locust | load test scripts | P3 |

### 3.19 Inne istotne

| Typ | Markery | Priorytet |
| --- | --- | --- |
| Git repository | `.git/` directory | P0 |
| Submodules | `.gitmodules` | P2 |
| LFS | `.gitattributes` z `filter=lfs` | P3 |
| Pre-commit hooks | `.pre-commit-config.yaml` | P1 |
| EditorConfig | `.editorconfig` | P2 |
| License | `LICENSE`, `COPYING` | P0 |
| Code of Conduct | `CODE_OF_CONDUCT.md` | P3 |
| Contributing guide | `CONTRIBUTING.md` | P2 |
| Security policy | `SECURITY.md` | P2 |
| Funding | `.github/FUNDING.yml` | P3 |
| Dependabot | `.github/dependabot.yml` | P2 |
| Renovate | `renovate.json` | P2 |

## 4. Probe API

```python
class Probe(ABC):
    name: str
    artifact_types: tuple[str, ...]
    cost: Literal["cheap", "medium", "expensive"]

    @abstractmethod
    def applicable(self, source: ArtifactSource) -> bool:
        """Quick check if this probe should run at all."""

    @abstractmethod
    def probe(self, source: ArtifactSource) -> ProbeResult:
        """Returns evidence list, partial manifest data, confidence score 0-100."""

@dataclass
class ProbeResult:
    matched: bool
    confidence: int
    artifact_types: list[str]
    evidence: list[Evidence]
    metadata: dict[str, Any]
    children: list[ArtifactSource]
```

### 4.1 Kategorie probe'ów

```text
testql/discovery/probes/
├── base.py
├── filesystem/
│   ├── package_python.py
│   ├── package_node.py
│   ├── api_openapi.py
│   ├── container_dockerfile.py
│   ├── container_compose.py
│   └── ...
├── network/
├── registry/
└── inspection/
```

### 4.2 Strategia uruchamiania probe'ów

- Cheap probes first (filesystem stat, file extension check).
- Medium probes (parse 1-2 plików, walidacja schematu).
- Expensive probes (network call, registry lookup) — tylko jeśli user wyrazi zgodę (`--scan-network`) lub poprzednie probe'y dały sygnał.
- Limit czasu — `--probe-timeout=30s` (default).
- Cache — `~/.cache/testql/probes/` z TTL 1h (per source path/URL).

## 5. ArtifactManifest

Znormalizowana struktura niezależna od typu artefaktu:

```python
@dataclass
class ArtifactManifest:
    source: ArtifactSource
    types: list[str]
    confidence: ManifestConfidence
    metadata: dict[str, Any]
    interfaces: list[Interface]
    dependencies: list[Dependency]
    artifacts: list[BuildArtifact]
    children: list[ArtifactManifest]
    evidence: list[Evidence]
    raw_probes: list[ProbeResult]

class ManifestConfidence(Enum):
    FULL = "full"
    PARTIAL = "partial"
    INFERRED = "inferred"
```

### 5.1 Confidence scoring rules

- `FULL`: ≥80% pól manifestu wypełnione, główne pliki (`pyproject`, `package.json`, `openapi.yaml`) dostępne i parsują się.
- `PARTIAL`: 30-80% pól, niektóre kluczowe brakują (np. brak version, brak openapi).
- `INFERRED`: <30% pól, manifest zbudowany głównie ze skanu plików.

Recipes mogą filtrować po confidence — np. `dependency-audit` wymaga `FULL`, `import-smoke` działa na `PARTIAL`, `directory-structure-sanity` działa na `INFERRED`.

## 6. Recipe API

```python
class Recipe(ABC):
    name: str
    applicable_types: tuple[str, ...]
    min_confidence: ManifestConfidence
    risk: Literal["read_only", "modifies_filesystem", "modifies_network"]

    @abstractmethod
    def applicable(self, manifest: ArtifactManifest) -> bool: ...

    @abstractmethod
    def generate(self, manifest: ArtifactManifest) -> TestPlan: ...
```

### 6.1 Recipe registry struktura

```text
testql/discovery/recipes/
├── base.py
├── universal/
├── python_pkg/
├── node_pkg/
├── openapi3/
├── fastapi/
├── dockerfile/
├── docker_compose/
├── quadlet/
├── k8s_manifest/
├── traefik/
├── nginx/
├── github_actions/
├── frontend_static/
├── ml_model_onnx/
└── ...
```

### 6.2 Recipe composition

Dla projektu z wielu typów (np. `python_pkg` + `fastapi` + `openapi3` + `dockerfile`) wszystkie pasujące recipes są uruchamiane. Wynikowy TestPlan jest sumą — pogrupowany w sekcje per typ.

## 7. CLI workflow

### 7.1 Basic discovery

```bash
testql discover ./my-project
testql discover ./my-project --generate
testql discover ./my-project --generate --dsl=nl --lang=pl --out scenarios/auto/
testql discover ./my-project --run
```

### 7.2 Network discovery

```bash
testql discover https://api.example.com --scan-network
testql discover https://api.example.com --hint=openapi:https://api.example.com/openapi.json
```

### 7.3 Container / compose

```bash
testql discover docker-compose.yml --recursive
testql discover ./*.container --type=quadlet
```

### 7.4 Hint i override

```bash
testql discover ./my-thing --type=python_pkg
testql discover ./my-project --skip-recipe=dependency_audit,vuln_scan
testql discover ./my-project --only-recipe=import_smoke,build_smoke
testql discover ./my-project --dry-run
```

### 7.5 Output formaty

```bash
testql discover ./my-project --format=manifest
testql discover ./my-project --format=summary
testql discover ./my-project --format=json
testql discover ./my-project --format=sumd
```

## 8. Faza 6 — decomposition

### 8.1 Faza 6.0 — Probe + Manifest core

Wersja: 1.1.0-rc1. Czas: 1-2 sesje.

Zakres:

- `testql/discovery/probes/base.py` z `BaseProbe`, `ProbeResult`
- `testql/discovery/manifest.py` z `ArtifactManifest`, confidence scoring
- `testql/discovery/registry.py` — auto-discovery pluginów
- 5 probe'ów P0: `package_python`, `package_node`, `api_openapi`, `container_dockerfile`, `container_compose`
- CLI: `testql discover <path>` (bez `--generate` jeszcze)

Kryteria sukcesu:

- [ ] `testql discover ./testql/` (sam siebie!) → wykrywa `python_pkg`, `fastapi`, `openapi3`, `confidence=FULL`
- [ ] `testql discover ./empty-dir/` → `confidence=INFERRED`, nie crashuje
- [ ] CC nowych modułów < 7
- [ ] Test coverage discovery ≥ 80%

### 8.2 Faza 6.1 — Recipe core + 5 recipes P0

Wersja: 1.1.0. Czas: 1-2 sesje.

Zakres:

- `testql/discovery/recipes/base.py` z `BaseRecipe`
- 5 recipes: `python_pkg/import_smoke`, `python_pkg/install_smoke`, `openapi3/all_endpoints_smoke`, `dockerfile/builds`, `dockerfile/non_root_user`
- CLI: `testql discover <path> --generate`
- Integracja z TestPlan IR (Phase 0)

Kryteria sukcesu:

- [ ] `testql discover ./my-pkg --generate --dsl=testtoon` produkuje plik wykonalny przez existing runner
- [ ] Recipe composition działa (multi-type project)
- [ ] CC < 7

### 8.3 Faza 6.2 — Network probes + run flow

Wersja: 1.2.0. Czas: 1-2 sesje.

Zakres:

- Network probes: `http_endpoint`, `openapi_endpoint`, `graphql_endpoint`, `health_endpoint`
- `testql discover URL --scan-network`
- `testql discover ... --run` (one-shot pipeline)
- Cache infrastructure (`~/.cache/testql/probes/`)

### 8.4 Faza 6.3 — P1 katalog rozszerzenie

Wersja: 1.3.0. Czas: 2-3 sesje.

Zakres: wszystkie pozycje P1 z taksonomii (3.1-3.19). Łącznie ~40 probe'ów + ~40 recipes.

Strategia: batch po kategorii, każda kategoria w PR-ze:

- PR #1: Quadlet + container_compose deep
- PR #2: Frontend (React/Next/Astro/Hugo/MkDocs)
- PR #3: CI (GitHub Actions deep + GitLab)
- PR #4: IaC (Terraform + Ansible)
- PR #5: Database probes (PG, SQLite, Redis, Mongo)
- PR #6: Server configs (nginx, Traefik, Caddy, systemd)

### 8.5 Faza 6.4 — Confidence scoring + LLM fallback

Wersja: 1.4.0. Czas: 1 sesja.

Zakres:

- Algorytm scoring zachowuje się przewidywalnie dla edge cases
- LLM-driven inference dla confidence: `INFERRED` cases (opt-in `--use-llm`)
- "Why this manifest?" wyjaśnienie (evidence chain)

### 8.6 Faza 6.5 — P2 + P3 katalog

Wersja: 1.5.0. Czas: 3-5 sesji rozłożone w czasie.

Zakres: pozostałe pozycje z taksonomii. Tu dopuszczalna jest community contribution — każda nowa kategoria to mały PR.

## 9. Quality gates per faza 6.x

| Faza | Wersja | coverage_min | vallm_pass_min | max_cc | max_fan_out | Probes | Recipes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 6.0 | 1.1.0-rc1 | 80 | 75 | 6 | 8 | 5 (P0) | 0 |
| 6.1 | 1.1.0 | 80 | 75 | 6 | 8 | 5 | 5 (P0) |
| 6.2 | 1.2.0 | 82 | 76 | 6 | 8 | +5 net | +5 net |
| 6.3 | 1.3.0 | 84 | 77 | 6 | 8 | +30 (P1) | +30 (P1) |
| 6.4 | 1.4.0 | 84 | 77 | 6 | 8 | bez zmian | bez zmian |
| 6.5 | 1.5.0 | 85 | 78 | 6 | 8 | +60 (P2+P3) | +60 (P2+P3) |

Zasada: każdy nowy probe i recipe musi mieć dedykowany test integracyjny ze "sample artifact" w `tests/fixtures/discovery/`. Bez tego PR nie jest mergowany.

## 10. Ryzyka i mitygacja

| Ryzyko | Prawd. | Wpływ | Mitygacja |
| --- | --- | --- | --- |
| Eksplozja kombinatoryczna probe × recipe | wysokie | wysokie | Recipes są "type-scoped" — uruchamiane tylko gdy odpowiedni typ wykryty. Limit `--max-recipes-per-type=10` |
| Network probes powolne | średnie | średnie | `--scan-network` opt-in; cache; concurrent execution z `asyncio.gather` |
| False positives w detekcji typu | wysokie | wysokie | Confidence scoring + ewidencja. User widzi "wykryłem X bo widzę pliki Y, Z". Można zoverridować przez `--type` |
| Recipes wykonują destrukcyjne operacje | średnie | wysokie | Każdy recipe ma `risk` field. Default: tylko read_only. Reszta wymaga `--allow-side-effects` |
| Manifest niekompletny → bezsensowne testy | wysokie | średnie | Confidence-gated recipes. Recipe wymagający FULL nie odpali się przy PARTIAL |
| Sekrety w plikach konfiguracyjnych ujawnione w testach | średnie | krytyczne | `secrets-scan` recipe uniwersalna, działa przed wszystkim innym. Match → abort + warn |
| Kompetencja per kategoria | wysokie | niskie | P3 jako community contrib. Core team utrzymuje P0+P1. P2 best-effort |
| Wzrost rozmiaru paczki przez ~150 probe'ów | średnie | niskie | Lazy loading; każda kategoria jako optional `extras_require` |
| LLM fallback w 6.4 nieprzewidywalny | średnie | średnie | Opt-in, deterministyczna ścieżka jako default, cost tracking |

## 11. Powiązanie z istniejącym ekosystemem

- SUMD (`sumd` package): `testql discover ... --format=sumd` produkuje fragment SUMD, który może być włączony do głównego `SUMD.md` projektu.
- DOQL (`doql` package): `ArtifactManifest` mapuje się 1:1 na DOQL `app/` + `interface[]` + `workflow[]`.
- semcod: discovery jest naturalnym fundamentem dla GitHub App — przy onboardingu repo najpierw odpalamy `testql discover .`, dostajemy manifest + auto-generated tests, włączamy do CI.
- pyqual: confidence scoring w manifestach jest analogiem do pyqual quality gates. Możemy reużyć `pyqual.yaml` schema dla `testql.yaml` (config dla discovery).
- vallm: walidacja semantyczna wygenerowanych testów — czy mają sens w kontekście manifestu?

## 12. Dlaczego ta architektura skaluje

- Plugin per typ — dodanie wsparcia dla nowego artefaktu = 1 probe + N recipes. Brak zmian w core. Community może contribuować.
- Unified manifest — wszystkie recipes konsumują tę samą strukturę. Brak special case'ów w runnerze.
- Confidence-gated recipes — recipes wybierają same czy mogą się odpalić. Brak centralnego `if/elif` piekła.
- Recursive children — jednorodne traktowanie compose / k8s / multi-package monorepos.
- `TestPlan` IR jako boundary — discovery i execution są niezależne.

## 13. Sekwencja LLM tasks

Faza 6.0:

1. Stwórz `testql/discovery/probes/base.py` + `manifest.py` + `registry.py`.
2. Implementuj 5 probe'ów P0: python, node, openapi, dockerfile, compose.
3. CLI `testql discover` (read-only, no generate yet).
4. Test fixtures: `tests/fixtures/discovery/{python_pkg,node_pkg,openapi3,dockerfile,compose}/`.
5. Integration tests dla każdego probe.

Faza 6.1:

6. Stwórz `testql/discovery/recipes/base.py`.
7. Implementuj 5 recipes P0.
8. CLI `--generate` flag.
9. Recipe composition test (multi-type project).
10. E2E: discover → generate → run → assert green.

Faza 6.2:

11. Network probes (4): http, openapi_endpoint, graphql_endpoint, health.
12. `--scan-network` flag z cache.
13. `--run` one-shot pipeline.

Faza 6.3: batch PR'y per kategoria (6 PR'ów).

Faza 6.4: confidence scoring polish + LLM fallback.

Faza 6.5: community-driven P2/P3 expansion.

## 14. Co dalej (poza 1.5.0)

- Self-healing recipes: gdy test fails, recipe sugeruje fix (analogicznie do pfix).
- Drift detection: cykliczne discovery + diff vs poprzedni manifest = alert "coś się zmieniło".
- Cross-artifact tests: testy spójności między artefaktami (np. czy port w `compose.yml` zgadza się z portem w `nginx.conf` zgadza się z portem w `Dockerfile`).
- Federated discovery: discovery na wielu repo (organization-wide) → unified manifest dla całej organizacji. Świetnie tnie się z semcod.
- AI-driven recipe inference: dla artefaktu którego nie znamy, LLM proponuje co warto testować. Human-in-the-loop approves → recipe staje się trwały.


## 15. Rozszerzenie: Topology-aware orchestration

Discovery nie powinno kończyć się na liście wykrytych artefaktów. Docelowo TestQL ma budować wielowarstwową topologię systemu, po której może poruszać się executor, LLM-agent albo usługa MCP.

Cel: z dowolnego obszaru wejściowego (`repo`, katalog, URL, działająca usługa, dokumentacja, książka, zbiór endpointów, strona WWW) zbudować graf zależności, wygenerować DSL testowy, uruchomić testy i zapisać rezultaty w ustrukturyzowanym formacie umożliwiającym dalsze wnioskowanie.

### 15.1 TopologyManifest

`ArtifactManifest` opisuje pojedynczy artefakt. `TopologyManifest` opisuje sieć artefaktów i relacji między nimi.

```python
@dataclass
class TopologyNode:
    id: str
    kind: str                       # service | endpoint | page | package | database | document | infra | test_result
    source: ArtifactSource
    manifest: ArtifactManifest | None
    metadata: dict[str, Any]
    evidence: list[Evidence]

@dataclass
class TopologyEdge:
    source_id: str
    target_id: str
    relation: str                   # calls | imports | serves | depends_on | links_to | documents | deploys_to
    protocol: str | None            # http | graphql | ws | grpc | file | sql | browser | mcp
    conditions: list[Condition]
    evidence: list[Evidence]

@dataclass
class TopologyManifest:
    root: ArtifactSource
    nodes: list[TopologyNode]
    edges: list[TopologyEdge]
    confidence: ManifestConfidence
    traces: list[TraversalTrace]
```

### 15.2 TopologyGraph jako plan nawigacji

Topologia ma być nie tylko raportem, ale też planem nawigacji:

- LLM może wybrać następny węzeł do zbadania na podstawie luk w evidence.
- Executor może odtworzyć ścieżkę: `page → form submit → REST API → database → event bus → websocket update`.
- Raport może pokazać deltę między oczekiwaną topologią z kodu a zachowaniem działającej usługi.
- User może dostać w NLP wyjaśnienie: „ten fragment UI nie działa, bo endpoint `/api/orders` zwraca 500, a kod handlera odwołuje się do brakującej zmiennej środowiskowej”.

Przykład TOON/YAML:

```yaml
topology:
  nodes:
    - id: page.home
      kind: page
      source: https://example.com/
    - id: api.orders
      kind: endpoint
      source: https://example.com/api/orders
    - id: service.orders
      kind: service
      source: ./services/orders
  edges:
    - source_id: page.home
      target_id: api.orders
      relation: calls
      protocol: http
      conditions:
        - when: click
          selector: "[data-testid=create-order]"
    - source_id: api.orders
      target_id: service.orders
      relation: implemented_by
      protocol: file
```

## 16. Schematy i formaty wymiany danych

TestQL powinien wspierać jawne schematy dla wejścia, topologii, DSL i rezultatów.

### 16.1 Formaty P0/P1

- `json` — pełna wymiana maszynowa, integracje CI/MCP/API.
- `yaml` — czytelny manifest i konfiguracja orchestracji.
- `toon` — kompaktowy format dla LLM i raportów wieloetapowych.
- `testtoon` — wykonywalny DSL testowy generowany z topologii.

### 16.2 Schematy walidujące

Nowe schematy:

- `ArtifactManifest.schema.json`
- `TopologyManifest.schema.json`
- `TraversalTrace.schema.json`
- `TestResultEnvelope.schema.json`
- `RefactorPlan.schema.json`
- `MCPDiscoveryRequest.schema.json`
- `MCPDiscoveryResponse.schema.json`

Każdy format powinien mieć round-trip test:

```text
json → model → yaml → model → toon → model → json
```

### 16.3 Result envelope

Wyniki testów powinny być zapisywane jako ustrukturyzowany envelope, a dopiero potem tłumaczone do NLP.

```python
@dataclass
class TestResultEnvelope:
    topology_id: str
    run_id: str
    status: Literal["passed", "failed", "partial", "blocked"]
    checks: list[CheckResult]
    failures: list[FailureFinding]
    traces: list[TraversalTrace]
    suggested_actions: list[SuggestedAction]
```

To umożliwia:

- generowanie raportów TOON/YAML/JSON,
- porównanie wyników między uruchomieniami,
- budowanie delty kod ↔ runtime,
- przekazanie wniosków userowi jako NLP.

## 17. MCP service layer

TestQL Discovery powinien być możliwy do użycia jako lokalna lub zdalna usługa MCP, tak aby IDE, LLM-agent, GitHub App lub system CI mógł pytać o topologię, testy i wyniki.

### 17.1 MCP resources

- `testql://manifest/{id}` — `ArtifactManifest`
- `testql://topology/{id}` — `TopologyManifest`
- `testql://trace/{run_id}` — przebieg nawigacji/testów
- `testql://result/{run_id}` — `TestResultEnvelope`
- `testql://refactor-plan/{run_id}` — plan refaktoryzacji wygenerowany z delty

### 17.2 MCP tools

- `discover_artifact(source, options)` → `ArtifactManifest`
- `build_topology(source, depth, options)` → `TopologyManifest`
- `generate_tests(topology, dsl)` → `TestPlan[]`
- `run_tests(test_plan, target)` → `TestResultEnvelope`
- `explain_results(result, language)` → NLP summary
- `propose_refactor(result, topology)` → `RefactorPlan`
- `generate_service(spec, topology_context)` → kod nowej usługi + testy kontraktowe

### 17.3 MCP bezpieczeństwo

- Network scanning opt-in.
- GUI/browser execution opt-in.
- Code generation wymaga oddzielnego approval.
- Side effects domyślnie zablokowane.
- Secrets redaction przed przekazaniem danych do LLM.

## 18. LLM navigator i generowanie DSL

LLM nie powinien działać na surowym repo bez struktury. Powinien dostawać skompresowany, walidowany kontekst:

1. `ArtifactManifest` dla znalezionych artefaktów.
2. `TopologyManifest` dla relacji.
3. `TraversalTrace` dla dotychczasowej nawigacji.
4. `TestResultEnvelope` dla wyników.
5. Budżet kosztów i ryzyka.

### 18.1 LLM tasks

- Wybierz kolejne węzły topologii do zbadania.
- Wygeneruj `testtoon` / `pytest` / `playwright` / `nl` dla danego fragmentu grafu.
- Wyjaśnij wyniki testów userowi w NLP.
- Zaproponuj minimalny plan naprawczy.
- Wygeneruj kod nowej usługi na bazie specyfikacji, topologii i brakujących kontraktów.

### 18.2 Deterministyczna granica

LLM może proponować, ale core musi być deterministyczny:

- Manifest i topology extraction są deterministic-first.
- LLM fallback tylko przez `--use-llm` lub MCP tool z jawnie podanym `allow_llm=true`.
- Każda sugestia LLM dostaje `evidence_refs` do węzłów, krawędzi, testów i plików.
- Wygenerowany kod nie jest stosowany automatycznie bez approval.

## 19. Runtime delta: kod ↔ uruchomiona usługa

Kluczowy workflow: analiza aktualnego kodu oraz działającej usługi z tego kodu.

```text
source code discovery
  → static topology
  → runtime discovery
  → GUI/API/WS/infra tests
  → result envelope
  → delta(static, runtime)
  → refactor plan
  → TOON report + NLP summary
```

### 19.1 Deltowanie

TestQL powinien umieć porównać:

- endpointy zadeklarowane w kodzie vs endpointy dostępne runtime,
- OpenAPI/GraphQL/proto schema vs realne odpowiedzi,
- routing UI vs realne przejścia w przeglądarce,
- deklarowane dependency/infrastructure vs działające zależności,
- health/readiness vs realna funkcjonalność,
- testy istniejące w repo vs pokrycie topologii.

### 19.2 RefactorPlan jako TOON

Wynik delty powinien dawać plan refaktoryzacji:

```yaml
refactor_plan:
  findings:
    - id: finding.api.orders.500
      severity: high
      node: api.orders
      evidence:
        - trace.run_123.step_5
        - file:services/orders/routes.py:42
      summary: Endpoint zwraca 500 po utworzeniu zamówienia.
      likely_cause: Brak obsługi pustej listy pozycji zamówienia.
      proposed_fix:
        type: code_change
        files:
          - services/orders/routes.py
        tests_to_add:
          - orders.empty-cart.testql.toon.yaml
```

## 20. Browser/GUI and online service orchestration

Dla stron WWW i usług online TestQL powinien uruchamiać wielopoziomową nawigację:

- browser automation: Playwright jako P0/P1 backend,
- DOM/page schema extraction,
- link crawling z limitem głębokości,
- formularze i akcje użytkownika,
- REST/GraphQL/WebSocket calls wykrywane z network logów,
- zależności CDN/assets,
- cookies/session/auth flows,
- accessibility/performance/basic UX checks,
- mapowanie strony do `TopologyManifest`.

### 20.1 Page schema

```python
@dataclass
class PageSchema:
    url: str
    title: str
    forms: list[FormSchema]
    actions: list[UserAction]
    links: list[LinkRef]
    network_calls: list[NetworkCall]
    console_errors: list[ConsoleError]
    screenshots: list[ArtifactRef]
```

### 20.2 Multi-layer test path

Przykładowa trasa:

```text
browser.page.checkout
  --click submit-->
api.orders.create
  --writes-->
db.orders
  --publishes-->
event.order_created
  --updates-->
ws.notifications
  --renders-->
browser.page.confirmation
```

Każdy krok ma warunki, asercje, timeouty, evidence i wynik. Dzięki temu TestQL może nie tylko powiedzieć „strona nie działa”, ale też wskazać, która warstwa grafu zawiodła.

### 20.3 Raport z orchestracji

Raport powinien istnieć w trzech postaciach:

- `result.toon.yaml` — struktura dla LLM i dalszego przetwarzania,
- `result.json` — integracje maszynowe,
- `summary.md` / NLP — opis dla usera.

## 21. Proponowane fazy po 6.5

### 21.1 Faza 7.0 — Topology core

- `TopologyManifest`, `TopologyNode`, `TopologyEdge`, `TraversalTrace`.
- Eksport/import `json`, `yaml`, `toon`.
- JSON Schema dla manifestów i rezultatów.
- CLI: `testql topology <source> --format=toon`.

### 21.2 Faza 7.1 — Runtime delta

- Static topology vs runtime topology.
- `TestResultEnvelope`.
- CLI: `testql inspect <source> --runtime <url> --out result.toon.yaml`.
- Refactor plan generation z wyników.

### 21.3 Faza 7.2 — Browser/GUI topology

- Playwright backend.
- Page schema extraction.
- Network log → API/asset dependency graph.
- GUI trace → `TraversalTrace`.

### 21.4 Faza 7.3 — MCP server

- MCP resources dla manifestów, topologii i wyników.
- MCP tools dla discovery, topology, run, explain, refactor, generate-service.
- IDE/LLM integration.

### 21.5 Faza 7.4 — LLM navigator and code generation

- LLM-guided traversal po topologii.
- LLM DSL generation z walidacją schema.
- NLP summaries z result envelope.
- Controlled service/code generation na bazie spec + topology context.

Plan rozszerza `testql-multi-dsl-refactor-plan.md` o szóstą fazę. Wykonalny niezależnie po zakończeniu Fazy 5 (release 1.0.0). Zgodny z konwencjami ekosystemu Semcod.
