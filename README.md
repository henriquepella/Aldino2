# Plataforma de Análise Geoestatística

Aplicação web que transforma uma planilha de dados espaciais (Excel/CSV) em uma
cadeia completa de análises, mapas e um **relatório técnico em PDF** — de ponta a
ponta e de forma automatizada.

> **Regra principal:** o usuário só envia o arquivo e confirma as colunas. Todo o
> restante é automático.

```
Dados → Estatística Descritiva → ESDA → Testes → Moran → IDW → Krigagem Ordinária
      → Krigagem com Deriva Externa → GWR/GWM → Co-Krigagem → Validação Cruzada
      → Comparação de Métodos → Mapas → Gráficos → Relatório PDF
```

---

## Sumário

- [Arquitetura](#arquitetura)
- [Início rápido (local)](#início-rápido-local)
- [Início rápido (Docker)](#início-rápido-docker)
- [Fluxo de uso](#fluxo-de-uso)
- [Análises implementadas](#análises-implementadas)
- [Qualidade científica e reprodutibilidade](#qualidade-científica-e-reprodutibilidade)
- [API](#api)
- [Configuração](#configuração)
- [Testes](#testes)
- [Estrutura do projeto](#estrutura-do-projeto)

---

## Arquitetura

| Camada | Tecnologia |
|---|---|
| **Frontend** | Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS, Radix UI, TanStack Query, Recharts |
| **Backend / API** | FastAPI, Pydantic v2, SQLAlchemy 2 |
| **Motor científico** | NumPy, SciPy, pandas, scikit-learn, statsmodels, GeoPandas, PyProj, **libpysal + esda** (ESDA), **PyKrige** (krigagem), **mgwr** (GWR/GWM), Matplotlib |
| **Relatório** | ReportLab (capa, sumário, cabeçalho/rodapé, tabelas, mapas em 300 DPI) |
| **Banco de dados** | SQLite (local) · PostgreSQL/PostGIS (produção) |
| **Fila de jobs** | ThreadPool em processo (local) · Celery + Redis (produção) |

O motor científico é **genérico**: não depende de nomes fixos de colunas e adapta
as análises disponíveis às características de cada base.

---

## Início rápido (local)

Pré-requisitos: **Python 3.12+** e **Node.js 20+**.

### Windows (PowerShell)

```powershell
git clone <repo> aldino && cd aldino
./scripts/setup.ps1     # venv + deps + dados demo + seed
./scripts/dev.ps1       # sobe backend (8000) e frontend (3000)
```

### Linux / macOS

```bash
git clone <repo> aldino && cd aldino
chmod +x scripts/*.sh
./scripts/setup.sh
./scripts/dev.sh
```

Acesse **http://localhost:3000** e entre com a conta de demonstração:

```
E-mail: demo@demo.local
Senha : demo12345
```

O projeto **“Análise de Solo 2026”** já vem carregado com um dataset sintético
(~480 pontos, 12 variáveis de fertilidade do solo) — basta clicar em
**🚀 Executar análise completa**.

### Passo a passo manual

```bash
python -m venv .venv
.venv/Scripts/pip install -r backend/requirements.txt      # (Linux: .venv/bin/pip)
python sample_data/generate_demo.py                         # gera demo_soil.xlsx / .csv
cp .env.example .env
python scripts/seed_demo.py                                 # cria usuário + projeto demo
cd backend && ../.venv/Scripts/python -m uvicorn app.main:app --reload --port 8000
# noutro terminal:
cd frontend && npm install && npm run dev
```

---

## Início rápido (Docker)

```bash
cp .env.example .env          # ajuste SECRET_KEY
docker compose up --build
```

Sobe PostgreSQL/PostGIS, Redis, o backend (uvicorn), um worker Celery e o
frontend. Depois:

```bash
docker compose exec backend python scripts/seed_demo.py
```

- Frontend: http://localhost:3000
- API / Swagger: http://localhost:8000/docs

---

## Fluxo de uso

1. **Novo projeto** — nome, cliente, responsável.
2. **Upload** — arraste um `.xlsx`, `.xls` ou `.csv`. Um modelo de planilha está
   disponível em *Baixar modelo Excel*.
3. **Confirmar colunas** — o sistema detecta automaticamente coordenadas
   (X/Y, Long/Lat, Easting/Northing), CRS e variáveis numéricas; você confirma ou
   ajusta e escolhe os papéis (principal, secundárias, explicativas, auxiliar).
4. **Diagnóstico da base** — ausentes, duplicatas, pontos coincidentes,
   coordenadas inválidas, outliers. Você pode excluir registros problemáticos.
5. **Configurações** — informações do projeto + parâmetros avançados (opcional).
6. **🚀 Executar análise completa** — pipeline assíncrono com barra de progresso.
7. **Dashboard + seções** — cards, tabelas, gráficos e mapas interativos.
8. **Downloads** — Relatório PDF, pacote `Projeto_Geoestatistico.zip`
   (`dados/ tabelas/ graficos/ mapas/ relatorio/ configuracoes/`), tabelas `.xlsx`.

Análises que não fazem sentido para os dados (ex.: deriva externa sem covariável
adequada) são **ignoradas com o motivo registrado** — o restante continua
normalmente.

---

## Análises implementadas

| Seção | Método | Biblioteca |
|---|---|---|
| Estatística descritiva | média, mediana, CV, quartis, assimetria, curtose, percentis; histograma, boxplot, KDE, ECDF | NumPy/SciPy |
| ESDA univariada | I de Moran global e local (LISA), C de Geary, Getis-Ord Gi\* | `esda` / `libpysal` |
| Testes | permutação (999), normalidade (D’Agostino) | `esda`, SciPy |
| Moran Scatter | dispersão de Moran, quadrantes HH/LH/HL/LL | `esda` |
| ESDA bivariada | I de Moran bivariado, LISA bivariado | `esda` |
| IDW | interpolação + validação cruzada em grade de potência × vizinhos | próprio (cKDTree) |
| Krigagem Ordinária | variograma experimental, ajuste de 5 modelos, seleção por CV, superfície + variância | `PyKrige` |
| Krigagem com Deriva Externa | regressão-krigagem (OLS + krigagem dos resíduos) | `statsmodels` + `PyKrige` |
| GWR / GWM | coeficientes locais, R² local/global, AICc, bandwidth fixo/adaptativo | `mgwr` |
| Co-Krigagem | co-krigagem colocada (Markov Model I) vs. krigagem ordinária | próprio (documentado) |
| Comparação | ranking por RMSE/MAE/R² da validação cruzada | — |

Todos os mapas são renderizados **sobre um mapa-base real** (imagem de satélite
Esri por padrão — mostra o terreno onde os pontos foram amostrados) e incluem
título, legenda, barra de escala, seta de norte, coordenadas, pontos amostrais,
método, unidade e CRS — exportáveis em PNG, SVG, PDF e **GeoTIFF**.

O mapa-base requer internet no momento da renderização; sem conexão, o mapa é
gerado sem o fundo (não quebra). Configurável por projeto em *Configurações →
Parâmetros avançados → Mapa-base* (`satellite` / `streets` / `gray` / `topo` /
`terrain` / `none`) ou via `DEFAULT_BASEMAP` no `.env`.

---

## Qualidade científica e reprodutibilidade

- **Sem invenção de resultados.** A interpretação em texto é gerada por gabaritos
  determinísticos a partir dos números reais (`app/analysis/interpret.py`).
  Se um resultado não é significativo, isso é dito explicitamente.
- **Seleção de modelos por validação cruzada** (leave-one-out ou k-fold),
  nunca por ajuste visual. O modelo vencedor é destacado; os piores continuam
  visíveis na tabela.
- **Manifesto `run.json`** com parâmetros, CRS, modelos escolhidos, versões das
  bibliotecas, timestamps e métricas — incluído no pacote de exportação.
- Coordenadas geográficas são reprojetadas para UTM automaticamente para os
  cálculos de distância (variograma, IDW, krigagem, pesos espaciais).

### Co-krigagem — nota metodológica

Não há biblioteca Python consolidada de co-krigagem multivariável. A plataforma
implementa **co-krigagem colocada sob o Markov Model I** (regressão da primária
sobre a secundária + krigagem ordinária do resíduo), documentada no código e
sempre comparada, na mesma validação cruzada, com a krigagem ordinária pura.

---

## API

`http://localhost:8000/docs` (OpenAPI). Principais rotas (prefixo `/api`):

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/auth/register`, `/auth/login` | JWT (OAuth2 password) |
| `GET` | `/meta/template.xlsx` | modelo de planilha |
| `GET/POST` | `/projects` … | CRUD de projetos, duplicar |
| `POST` | `/projects/{id}/datasets` | upload (valida extensão/tamanho/parse) |
| `PATCH` | `/datasets/{id}/config` | confirma colunas → valida → gera versão limpa |
| `POST` | `/datasets/{id}/clean` | remove registros problemáticos |
| `POST` | `/projects/{id}/runs` | dispara o pipeline (job assíncrono) |
| `GET` | `/runs/{id}` | status / progresso / passos / log |
| `GET` | `/runs/{id}/results` | resultados estruturados (tabelas, figuras, interpretação) |
| `GET` | `/runs/{id}/report.pdf` · `/package.zip` · `/tables.xlsx` | downloads |

Cada usuário só acessa os próprios projetos (isolamento por `owner_id`).

---

## Configuração

Todas as variáveis têm padrão para desenvolvimento local — veja `.env.example`.
Destaques:

| Variável | Padrão | Descrição |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./storage/app.db` | use `postgresql+psycopg2://…` em produção |
| `JOB_BACKEND` | `thread` | `celery` em produção |
| `MAX_UPLOAD_MB` | `50` | limite de upload |
| `DEFAULT_N_PERMUTATIONS` | `999` | permutações dos testes de Moran |
| `DEFAULT_GRID_RESOLUTION` | `80` | células por eixo na grade de interpolação |
| `SECRET_KEY` | inseguro | **obrigatório trocar em produção** |

Parâmetros avançados (nº de vizinhos, potência IDW, modelos de variograma,
métrica de seleção, bandwidth…) podem ser ajustados por projeto na tela de
*Configurações* ou por execução via `advanced` no `POST /runs`.

---

## Testes

```bash
cd backend && ../.venv/Scripts/python -m pytest -q      # 44 testes
cd frontend && npm run build                            # typecheck + build
```

Cobrem: detecção de colunas, validação/limpeza, ingestão (formatos BR/intl),
cada módulo de análise, o **pipeline completo** (até PDF + ZIP) e o
**ciclo de vida da API** (upload → run → resultados → downloads → isolamento).

---

## Estrutura do projeto

```
backend/
  app/
    api/            routers FastAPI (auth, projects, datasets, runs, reports, exports, meta)
    core/           config, segurança (JWT), logging, dependencies
    models/         SQLAlchemy (User, Project, Dataset, AnalysisRun, ResultArtifact)
    schemas/        Pydantic
    services/       ingest, detection, validation, pipeline, jobs, packaging, storage
    analysis/       base(interface), weights, descriptive, esda, moran, bivariate,
                    idw, kriging, external_drift, gwr, cokriging, comparison, interpret
    maps/           renderização de mapas profissionais (Matplotlib)
    reports/        gerador de PDF (ReportLab)
    worker/         tarefas Celery
  alembic/          migrações
  tests/
frontend/
  app/              rotas (auth, projects/[id]/{upload,configure,diagnostics,settings,run,
                    dashboard, e as seções de resultado})
  components/       ui/ (primitivos), results/ (tabelas, figuras, interpretação), shell
  lib/              api, hooks (react-query), auth, types, format
sample_data/        gerador de dados sintéticos + demo_soil.xlsx/.csv
scripts/            setup / dev / seed_demo
docker-compose.yml  db (PostGIS) + redis + backend + worker + frontend
```

---

## Licença

MIT — veja `LICENSE`.
