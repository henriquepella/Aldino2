# Plataforma de Análise Geoestatística — Guia de Entrega

Aplicação web que transforma uma planilha de dados espaciais (Excel/CSV) em uma
cadeia completa de análises, mapas e um **relatório técnico em PDF** — de forma
automatizada.

> **Princípio:** o usuário só envia o arquivo e confirma as colunas.
> Todo o restante é automático.

---

## O que a plataforma faz

```
Dados → Estatística → ESDA → Testes → Moran → IDW → Krigagem →
Deriva Externa → GWR/GWM → Co-Krigagem → Comparação → Mapas → Relatório PDF
```

**Fluxo de uso:** Novo projeto → Upload da planilha → Confirmar colunas (detecção
automática) → Diagnóstico da base → Configurações → **Executar análise completa**
→ Explorar painel e seções → Baixar relatório PDF / pacote ZIP.

Análises que não fazem sentido para os dados são **ignoradas com o motivo
registrado**; o restante continua normalmente.

---

## O que o sistema entrega

| Saída | Detalhe |
|---|---|
| **Relatório PDF** | Capa, sumário, 16 seções, tabelas, mapas, conclusão e anexo de reprodutibilidade. Gerado automaticamente (~5 MB na demonstração). |
| **Mapas sobre imagem de satélite** | Cada mapa mostra o terreno onde os pontos foram amostrados, com legenda, escala, norte e coordenadas. Export PNG e GeoTIFF. |
| **Pacote `Projeto_Geoestatistico.zip`** | `dados/ tabelas/ graficos/ mapas/ relatorio/ configuracoes/` (~30 MB na demonstração). |
| **Painel interativo** | Indicadores + 16 seções de resultado + exportações CSV/Excel. |

---

## Métodos de análise

| Análise | Biblioteca |
|---|---|
| Estatística descritiva (histograma, boxplot, densidade, ECDF) | NumPy / SciPy |
| ESDA univariada — I de Moran global/local (LISA), Geary C, Getis-Ord Gi\* | esda / libpysal |
| Testes estatísticos (permutação 999, normalidade) | esda / SciPy |
| Moran Scatter Plot (quadrantes AA/BA/AB/BB) | esda |
| ESDA bivariada (Moran e LISA bivariados) | esda |
| IDW + validação cruzada em grade de parâmetros | próprio (cKDTree) |
| Krigagem Ordinária (variograma, 5 modelos, seleção por CV, incerteza) | PyKrige |
| Krigagem com Deriva Externa (regressão-krigagem) | statsmodels + PyKrige |
| GWR / GWM (coef. locais, R² local/global, AICc, bandwidth) | mgwr |
| Co-Krigagem colocada (Markov Model I), comparada com OK | próprio (documentado) |
| Comparação de métodos (ranking por RMSE/MAE/R² da CV) | — |

**Qualidade científica:** interpretação em texto 100% determinística (sem
invenção de resultados); seleção de modelos por validação cruzada, nunca por
ajuste visual; manifesto `run.json` de reprodutibilidade em cada execução.

---

## Arquitetura

| Camada | Tecnologia |
|---|---|
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS |
| API | FastAPI, Pydantic v2, SQLAlchemy 2, autenticação JWT |
| Motor científico | NumPy, SciPy, pandas, scikit-learn, statsmodels, GeoPandas, PyProj, libpysal + esda, PyKrige, mgwr |
| Mapas | Matplotlib + contextily + rasterio |
| Relatório | ReportLab |
| Banco | SQLite (local) · PostgreSQL/PostGIS (produção) |
| Fila de tarefas | Threads (local) · Celery + Redis (produção) |

---

## Como rodar

### Requisitos
- **Python 3.12+** e **Node.js 20+** (instalação local), ou **Docker**.
- ~2 GB de disco.
- Internet apenas na primeira instalação e, opcionalmente, ao gerar mapas
  (imagens de satélite). Sem internet, os mapas saem sem o fundo — não quebra.

### Opção A — Windows (PowerShell), a partir da pasta do projeto

```powershell
.\scripts\setup.ps1     # instala backend + frontend, gera dados e projeto demo
.\scripts\dev.ps1       # sobe backend (8000) e frontend (3000)
```

### Opção B — Linux / macOS

```bash
chmod +x scripts/*.sh
./scripts/setup.sh
./scripts/dev.sh
```

### Opção C — Docker (stack de produção)

```bash
cp .env.example .env
docker compose up --build
docker compose exec backend python scripts/seed_demo.py
```

### Acesso (qualquer opção)

- Interface: **http://localhost:3000** — abre direto na lista de projetos (sem login)
- API / documentação: **http://localhost:8000/docs**
- O projeto *“Análise de Solo 2026”* já vem carregado — clique em
  **Executar análise completa**.

### Verificar a instalação

```bash
cd backend
../.venv/Scripts/python -m pytest -q      # todos passam
```

---

## Estrutura de pastas

```
projeto/
├─ backend/
│  ├─ app/api/          rotas FastAPI
│  ├─ app/analysis/     motor científico (10 análises + comparação + interpretação)
│  ├─ app/services/     ingestão, detecção, validação, pipeline, jobs, empacotamento
│  ├─ app/maps/         renderização de mapas
│  ├─ app/reports/      gerador de PDF
│  ├─ tests/            testes automatizados
│  └─ requirements.txt
├─ frontend/
│  ├─ app/              26 telas (assistente, painel, seções de resultado)
│  ├─ components/       UI + componentes de resultado
│  └─ lib/              cliente da API, hooks, tipos
├─ sample_data/         gerador de dados + demo_soil.xlsx / .csv
├─ scripts/             setup · dev · seed_demo
├─ docker-compose.yml
├─ .env.example
└─ README.md            documentação técnica completa
```

---

## Notas de operação

- **Arquivos originais preservados** em `backend/storage/`, separados dos resultados.
- **Reprocessar do zero:** apague `backend/storage/app.db` e `backend/storage/users/`,
  depois rode `python scripts/seed_demo.py`.
- **Produção:** use `DATABASE_URL` com PostgreSQL/PostGIS e `JOB_BACKEND=celery`
  — tudo já está no `.env.example` e no `docker-compose.yml`.
- **Mapa-base:** configurável por projeto (Configurações → Parâmetros avançados)
  ou via `DEFAULT_BASEMAP` no `.env` (`satellite` / `streets` / `gray` / `topo` /
  `terrain` / `none`).
