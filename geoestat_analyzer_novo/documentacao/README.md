# Analisador Geoestatístico v2.0

Sistema profissional para análise de dados geoespaciais com geração automática de relatórios técnicos em PDF.

## 📁 Estrutura do Projeto

```
geoestat_analyzer_novo/
│
├── configuracao/                # Configurações do projeto
│   └── requirements.txt         # Dependências Python
│
├── dados/                       # Gerenciamento de dados
│   ├── entrada/                # 📁 Cole seus arquivos aqui
│   │   └── exemplo_dados_geoespaciais.xlsx
│   └── saida/                  # Relatórios PDF gerados
│
├── analise/                     # Lógica de análise
│   ├── __init__.py
│   ├── analisador.py           # Detecção e análise dos dados
│   └── gerador_relatorio.py    # Geração de PDF
│
├── utilitarios/                 # Funções auxiliares
│   ├── __init__.py
│   └── criar_dados_exemplo.py  # Script para gerar dados de teste
│
├── executavel/                  # Scripts para executar
│   └── principal.py            # Script principal de execução
│
├── documentacao/                # Documentação
│   └── README.md               # Este arquivo
│
└── .gitignore                   # Configuração Git
```

## 🎯 Como Usar

### 1. Instalar Dependências

```bash
pip install -r configuracao/requirements.txt
```

### 2. Adicionar Dados

Coloque seu arquivo (.xlsx ou .csv) em:
```
dados/entrada/seu_arquivo.xlsx
```

**Requisitos do arquivo:**
- Coluna X ou Longitude (coordenadas horizontais)
- Coluna Y ou Latitude (coordenadas verticais)
- Uma ou mais colunas numéricas para análise

### 3. Executar Análise

```bash
python executavel/principal.py
```

### 4. Acessar Relatório

O PDF será salvo em:
```
dados/saida/Relatorio_Geoestat_[YYYYMMDD_HHMMSS].pdf
```

## 📊 O que o Sistema Faz

✅ **Detecção Automática** - Encontra coordenadas e variáveis numéricas
✅ **Estatísticas Completas** - Calcula média, mediana, desvio padrão, CV%
✅ **Destaque Visual** - Marca variáveis com CV > 100% em vermelho
✅ **Conversão de CRS** - Transforma para WGS84 (EPSG:4326) automaticamente
✅ **Tabelas Profissionais** - Formata dados em tabelas com cores
✅ **Relatório em PDF** - Gera documento com 6 páginas de análise

## 🔧 Estrutura de Código

### `analise/analisador.py`
Classe `AnalisadorGeo` responsável por:
- Carregar arquivos Excel/CSV
- Detectar coordenadas automáticamente
- Identificar variáveis numéricas
- Calcular estatísticas descritivas
- Converter para WGS84

### `analise/gerador_relatorio.py`
Classe `GeradorRelatorio` responsável por:
- Criar relatórios PDF profissionais
- Gerar tabelas formatadas
- Destacar variáveis com alta heterogeneidade
- Incluir gráficos e análises espaciais

### `utilitarios/criar_dados_exemplo.py`
Script para gerar dataset de exemplo para testes

### `executavel/principal.py`
Script principal que executa:
1. Procura pelo arquivo em `dados/entrada/`
2. Cria instância de `AnalisadorGeo`
3. Executa análise completa
4. Gera relatório via `GeradorRelatorio`

## 📋 Coeficiente de Variação (CV%)

O CV% mede a heterogeneidade relativa:

**Fórmula:** CV = (Desvio Padrão / Média) × 100

**Interpretação:**
- CV < 15%: Baixa variabilidade ✓
- CV 15-30%: Variabilidade moderada ✓
- CV 30-100%: Alta variabilidade ⚠️
- CV > 100%: Heterogeneidade extrema 🚨

## 🌍 Conversão de Coordenadas

Transforma automaticamente sistema de entrada para WGS84:

**Entrada:**
- EPSG:32733 (UTM 23 Sul) - Brasil padrão
- Em metros (local)

**Saída:**
- EPSG:4326 (WGS84)
- Em graus decimais (global)
- Compatible com Google Maps, OpenStreetMap

## 📈 Arquivo de Exemplo

Para testar o sistema:

```bash
python utilitarios/criar_dados_exemplo.py
python executavel/principal.py
```

Isto gera um arquivo de teste e cria o relatório automaticamente.

## 🔗 Comentários em Código

Todo o código está comentado em português para fácil compreensão:
- Cada arquivo tem cabeçalho explicativo
- Funções têm docstring completa
- Lógica é comentada em seções claras

## ✅ Requisitos

- Python 3.8+
- pandas, numpy, matplotlib, seaborn
- reportlab (para PDF)
- pyproj (para transformação CRS)

Veja `configuracao/requirements.txt` para lista completa.

---

**Versão:** 2.0 (Reorganizada)
**Status:** ✅ Pronto para produção
**Data:** Abril 2026
