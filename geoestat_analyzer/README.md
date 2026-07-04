# Analisador Geoestatístico Automático 🗺️📊

Sistema profissional para análise de dados geoespaciais com geração automática de relatórios técnicos em PDF.

## 🎯 Funcionalidades

✅ **Detecção Automática de Coordenadas** - Identifica colunas X/Y ou Lat/Lon
✅ **Reconhecimento de Variáveis** - Detecta até 6 variáveis numéricas  
✅ **Coeficiente de Variação** - Calcula CV% para cada variável
✅ **Destaque Visual** - Realça variáveis com CV > 100% (alta heterogeneidade)
✅ **Conversão de Coordenadas** - Transforma automaticamente para EPSG:4326 (WGS84/Lat-Lon)
✅ **Tabelas Formatadas** - Apresenta estatísticas em tabelas profissionais
✅ **Análise CRS** - Identifica ou usa padrão EPSG:32733 (Brasil)
✅ **Estatísticas Completas** - Min, máx, média, mediana, desvio padrão, CV%
✅ **Visualizações** - Gráficos de distribuição e análise espacial
✅ **Relatório Profissional** - PDF moderno com 7+ páginas

## 📋 Pré-requisitos

- Python 3.8+
- pip (gerenciador de pacotes)

## 🚀 Instalação e Uso

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2. Adicionar Arquivo de Dados

Coloque seu arquivo na pasta `data/`:
```
geoestat_analyzer/
├── data/
│   └── seu_arquivo.xlsx  ← AQUI
├── analyzer.py
├── main.py
└── ...
```

**Formatos aceitos:**
- `.xlsx` (Excel)
- `.csv` (Comma-separated values)

### 3. Executar Análise

```bash
python main.py
```

O sistema irá:
1. 📂 Carregar o arquivo
2. 🔍 Detectar coordenadas e variáveis
3. 📊 Calcular estatísticas
4. 📄 Gerar relatório PDF

### 4. Acessar o Relatório

O relatório será salvo em:
```
geoestat_analyzer/reports/Relatorio_Geoestat_YYYYMMDD_HHMMSS.pdf
```

## 📊 Estrutura do Relatório

O PDF gerado contém:

1. **Página de Título** - Sumário executivo com informações principais
2. **Descrição dos Dados** - Informações gerais, coordenadas e variáveis
3. **Estatísticas Descritivas** - Tabela formatada com:
   - Média, Mediana, Desvio Padrão
   - Mínimo, Máximo
   - **Coeficiente de Variação (CV%)**
   - **Destaque em vermelho para CV > 100%** ⚠️
4. **Distribuição das Variáveis** - Histogramas e análise de frequência
5. **Georreferenciamento** - Coordenadas convertidas para WGS84 (EPSG:4326)
6. **Análise Espacial** - Mapas de localização e distribuição
7. **Conclusões** - Recomendações técnicas

## 📋 Requisitos de Dados

O arquivo deve conter:

| Requisito | Descrição |
|-----------|-----------|
| **Coordenadas** | Colunas nomadas X, Y, Longitude, Latitude, Easting, Northing |
| **Formato** | Valores numéricos (não texto) |
| **Mínimo** | 10 amostras recomendadas |
| **Variáveis** | Uma ou mais colunas numéricas para análise |

### Exemplo de Formato

```
X          Y          Variavel1   Variavel2
400000.5   6500000.2  45.3        12.1
400100.1   6500100.5  47.2        11.8
400200.3   6500200.8  46.1        12.5
...
```

## 🔧 Configurações Personalizáveis

Para modificar padrões, edite `analyzer.py`:

```python
# Padrão de CRS (linha 22)
DEFAULT_CRS = "EPSG:32733"  # Troque para outro código EPSG

# Limite de variáveis (linha 89)
numeric_cols = numeric_cols[:6]  # Altere para mais/menos variáveis
```

## 📐 Métricas Geoestatísticas Utilizadas

### Coeficiente de Variação (CV%)

O CV% é usado para identificar a heterogeneidade espacial das variáveis:

**Fórmula:** CV = (Desvio Padrão / Média) × 100

**Interpretação:**
- **CV < 15%**: Baixa variabilidade
- **CV 15-30%**: Variabilidade moderada  
- **CV 30-100%**: Alta variabilidade
- **CV > 100%**: ⚠️ Muito alta variabilidade (heterogeneidade extrema)

Variáveis com **CV > 100%** são destacadas em **vermelho** no relatório e indicam que análises geoestatísticas especializadas (como kriging adaptativo) podem ser necessárias.

### Conversão de Coordenadas (CRS)

O sistema converte automaticamente:

| Origem | Destino | Uso |
|--------|---------|-----|
| EPSG:32733 (UTM 23S) | EPSG:4326 (WGS84) | Georreferenciamento global |
| Metros (local) | Graus decimais (global) | Compatibilidade com Google Maps, OSM |

Os valores convertidos aparecem na página de **Georreferenciamento** do relatório em graus decimais, prontos para uso em plataformas online.

## 📍 Códigos EPSG Comuns

| Região | EPSG | Descrição |
|--------|------|-----------|
| Brasil (UTM 23S) | 32733 | Padrão para sul do Brasil |
| Brasil (UTM 22S) | 32722 | Para regiões de transição |
| Brasil (Lat/Lon) | 4674 | SIRGAS 2000 |
| Global | 4326 | WGS84 |

## 🛠️ Estrutura de Arquivos

```
geoestat_analyzer/
├── data/                    # 📁 Coloque arquivos aqui
│   └── seu_arquivo.xlsx
├── reports/                 # 📁 Relatórios gerados
│   └── Relatorio_Geoestat_...pdf
├── analyzer.py              # Módulo de análise
├── report_generator.py      # Gerador de PDF
├── main.py                  # Script principal
├── requirements.txt         # Dependências
└── README.md               # Este arquivo
```

## 📝 Logs de Execução

Durante a execução, o sistema exibe:

```
======================================================================
                    ANALISADOR GEOETATÍSTICO v1.0
======================================================================

📂 Arquivo encontrado: dados.xlsx

============================================================
INICIANDO ANÁLISE GEOESPACIAL
============================================================

✓ Arquivo carregado: dados.xlsx
✓ Dimensões: 500 amostras × 4 colunas
✓ Coordenadas detectadas: X='X', Y='Y'
✓ Variáveis numéricas detectadas (2):
   1. Variavel1
   2. Variavel2
✓ CRS detectado (padrão): EPSG:32733

============================================================
ANÁLISE COMPLETA
============================================================

📊 Gerando relatório PDF...
   ✓ Página de título
   ✓ Descrição dos dados
   ✓ Estatísticas descritivas
   ✓ Visualizações
   ✓ Análise espacial
   ✓ Conclusões

✅ Relatório gerado com sucesso!
```

## ⚠️ Resolução de Problemas

### "Nenhum arquivo encontrado"
→ Coloque o arquivo na pasta `data/`

### "Colunas não detectadas"
→ Renomeie as colunas para um padrão reconhecido (X, Y, Lat, Lon)

### "Erro ao importar módulos"
→ Execute: `pip install -r requirements.txt --upgrade`

### "Arquivo muito grande"
→ Considere fazer uma amostragem antes

## 📞 Suporte

Para dúvidas ou problemas, verifique:
1. Se as dependências estão instaladas
2. Se o arquivo está no formato correto
3. Se as colunas estão nomeadas apropriadamente

## 📄 Licença

Sistema de análise geoestatística automática - Uso livre para fins educacionais e profissionais.

---

**Versão:** 1.0  
**Última atualização:** Abril 2026  
**Desenvolvido para:** Análise profissional de dados geoespaciais
