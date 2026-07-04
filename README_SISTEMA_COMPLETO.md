# 🌐 GEOESTAT ANALYZER v2.1 - SISTEMA COMPLETO DE ANÁLISE GEOESTATÍSTICA

## 📋 Visão Geral

Sistema automatizado para análise geoestatística avançada com:
- **Análise Espacial**: Moran's I global (999 permutações) e LISA com 5 clusters
- **Mapas de Interpolação**: 5 tipos (Basemap, Hexbin, IDW, Kriging, GWM)
- **Visualizações de Distribuição**: Histogramas, Violins e Matriz de Correlação
- **Relatório PDF**: Integração automática de todos os resultados

---

## 📊 FUNCIONALIDADES PRINCIPAIS

### 1. ANÁLISE ESPACIAL AVANÇADA

**Arquivo**: `analise/analise_espacial_avancada.py`

✅ **Moran's I Global**
- Índice de autocorrelação espacial
- 999 permutações para teste de significância
- p-valor e z-score automáticos
- Detecta autocorrelação positiva/negativa

✅ **LISA (Local Indicators)**
- Análise local por ponto
- 5 categorias: HH (alto-alto), LL (baixo-baixo), LH, HL, NS
- Mapas de clusters com cores específicas
- Filtro de significância (p < 0.05)

### 2. MAPAS DE INTERPOLAÇÃO GEOESPACIAL (5 tipos)

**Arquivo**: `analise/mapas_interpolacao.py`

| # | Mapa | Método | Características |
|---|------|--------|-----------------|
| 1 | **Basemap OSM** | OpenStreetMap | EPSG:4326 (WGS84), mapa real, créditos |
| 2 | **Hexbin** | Contagem | 25 hexágonos, densidade de amostragem |
| 3 | **IDW** | Inverse Distance | Potência=2, 200×200 grid, 31.751 pontos |
| 4 | **Kriging** | Semivariograma | Esférico automático, dual-painel (pred+erro) |
| 5 | **GWM** | Gaussian Weights | Bandwidth automático, local averaging |

✅ Todos em 300 DPI PNG (4.0 MB total)

### 3. VISUALIZAÇÕES DE DISTRIBUIÇÃO (3 tipos)

**Arquivo**: `analise/visualizacoes_distribuicao.py`

| # | Visualização | Características |
|---|--------------|-----------------|
| 1 | **Histogramas Z-score** | KDE, média (vermelha), mediana (verde), anotações (n, DP, assimetria) |
| 2 | **Violin + Boxplot** | Eixo Y padronizado (-3 a +3σ), IQR anotado, paleta neutra |
| 3 | **Matriz Correlação** | Heatmap RdBu_r, bordas espessas em |r| > 0.6, Pearson |

✅ Todos em 300 DPI PNG (0.8 MB total)

---

## 🗂️ ESTRUTURA DO PROJETO

```
geoestat_analyzer_novo/
├── analise/
│   ├── analisador.py                      # Classe principal
│   ├── analise_espacial_avancada.py      # Moran + LISA
│   ├── visualizacoes_spatial.py          # Gráficos Moran/LISA
│   ├── mapas_interpolacao.py             # 5 tipos de mapas
│   ├── visualizacoes_distribuicao.py     # Histogramas, Violins, Correlação
│   ├── gerador_relatorio.py              # Relatório PDF
│   └── __init__.py
│
├── executavel/
│   └── principal.py                       # Pipeline completo (5 ETAPAS)
│
├── dados/
│   ├── entrada/
│   │   └── exemplo_dados_geoespaciais.xlsx
│   └── saida/
│       ├── mapas/                         # 5 mapas PNG
│       ├── visualizacoes/                 # 3 visualizações PNG + HTML
│       └── Relatorio_Geoestat_*.pdf      # PDF final
│
├── teste_analise_espacial.py
├── teste_mapas_rapido.py
├── teste_visualizacoes_distribuicao.py
│
└── GUIA_*.md                             # Documentação
```

---

## 🚀 COMO USAR

### Opção 1: Pipeline Completo (Recomendado)

```bash
cd geoestat_analyzer_novo/executavel
python principal.py
```

**Executa**:
1. ✅ Carregamento e detecção automática de dados
2. ✅ Análise de autocorrelação espacial (Moran + LISA)
3. ✅ Visualizações de análise espacial
4. ✅ Mapas de interpolação (5 tipos)
5. ✅ Visualizações de distribuição
6. ✅ Relatório PDF integrado

**Tempo**: ~5-7 minutos (incluindo Kriging que é intensivo)

**Saídas**:
- PDF completo: `Relatorio_Geoestat_*.pdf`
- Mapas: 5 PNG (dados/saida/mapas/)
- Visualizações: 3 PNG + HTML (dados/saida/visualizacoes/)

### Opção 2: Apenas Análise Espacial

```bash
python teste_analise_espacial.py
```

**Gera**: Moran's I e figuras LISA (~30 segundos)

### Opção 3: Apenas Mapas

```bash
python teste_mapas_rapido.py
```

**Gera**: 5 mapas de interpolação (~90 segundos)

### Opção 4: Apenas Visualizações de Distribuição

```bash
python teste_visualizacoes_distribuicao.py
```

**Gera**: 3 visualizações de distribuição (~10 segundos)

---

## 📈 EXEMPLO DE SAÍDA

### Pipeline Completo
```
======================================================================
ANALISADOR GEOESTATÍSTICO v2.0
======================================================================

✓ Arquivo carregado: exemplo_dados_geoespaciais.xlsx
✓ Dimensões: 250 amostras × 6 colunas

============================================================
ANÁLISE DE MORAN GLOBAL
============================================================
✓ Teor_Au: I=0.548, p<0.001 (SIGNIFICATIVO)
✗ Teor_Cu: I=0.005, p=0.822 (NÃO SIGNIFICATIVO)
...

============================================================
ANÁLISE LISA: Teor_Au
============================================================
99 pontos em clusters significativos:
  - 75 em clusters HH (Alto-Alto)
  - 24 em clusters LL (Baixo-Baixo)
...

✅ ANÁLISE COMPLETA COM SUCESSO!

📄 Relatório PDF: Relatorio_Geoestat_20260414_140936.pdf
🗺️  Mapas (5 tipos): dados/saida/mapas/
📊 Visualizações (3 tipos): dados/saida/visualizacoes/
```

---

## 📊 ESPECIFICAÇÕES TÉCNICAS

### Dados de Entrada

- **Formato**: .xlsx ou .csv
- **Coordenadas**: Detectadas automaticamente (X/Y, Lon/Lat)
- **Variáveis**: Todas as colunas numéricas são analisadas
- **CRS**: Padrão EPSG:32733 (UTM Zona 23S Brasil)
- **Reprojection**: Automática para EPSG:4326 (WGS84) para mapas

### Análise Espacial

- **Matriz Pesos**: KNN com k=4 vizinhos
- **Moran's I**: Com 999 permutações
- **Significância**: α = 0.05
- **Interpolação**: Convex hull com buffer 5%

### Mapas (300 DPI)

| Mapa | Tempo | Tamanho | Método |
|------|-------|---------|--------|
| Basemap | 5 seg | 0.2 MB | OpenStreetMap contextily |
| Hexbin | 2 seg | 0.6 MB | Matplotlib hexbin |
| IDW | 15 seg | 1.1 MB | Scipy griddata (potência=2) |
| Kriging | 60 seg | 1.1 MB | PyKrige ordinária esférica |
| GWM | 20 seg | 1.0 MB | Gaussian weights locais |
| **Total** | **~100 seg** | **4.0 MB** | |

### Visualizações (300 DPI)

| Visualização | Tempo | Tamanho | Características |
|--------------|-------|---------|-----------------|
| Histogramas | 3 seg | 0.4 MB | KDE, linhas média/mediana, anotações |
| Violin+Box | 2 seg | 0.3 MB | IQR, paleta neutra |
| Correlação | 1 seg | 0.2 MB | Heatmap, bordas em r > 0.6 |
| **Total** | **~6 seg** | **0.9 MB** | |

---

## 🔧 DEPENDÊNCIAS

```
pandas>=1.3.0
numpy>=1.20.0
matplotlib>=3.4.0
seaborn>=0.11.0
scipy>=1.7.0
scikit-learn>=0.24.0
geopandas>=0.9.0
shapely>=1.7.0
pyproj>=3.2.0
libpysal>=4.7.0
esda>=2.3.0
contextily>=1.3.0
pykrige>=1.7.0
reportlab>=3.6.0
```

**Instalação**:
```bash
pip install -r configuracao/requirements.txt
```

---

## 📚 GUIAS COMPLEMENTARES

1. **GUIA_ANALISE_ESPACIAL.md** - Detalhes de Moran's I e LISA
2. **GUIA_MAPAS_INTERPOLACAO.md** - Especificações dos 5 mapas
3. **GUIA_VISUALIZACOES_DISTRIBUICAO.md** - Detalhes das 3 visualizações

---

## ✅ STATUS DO PROJETO

**v2.1 - COMPLETO**

- ✅ Análise espacial (Moran + LISA)
- ✅ 5 mapas de interpolação
- ✅ 3 visualizações de distribuição
- ✅ Relatório PDF automático
- ✅ Tratamento robusto de erros
- ✅ Detecção automática de coordenadas
- ✅ Reprojection automática
- ✅ Scripts de teste independentes
- ✅ Documentação completa

---

## 🎯 PRÓXIMAS ETAPAS (Opcional)

- [ ] Cross-validation para interpolações
- [ ] Diagnósticos de semivariograma
- [ ] Exportação para Shapefile/GeoJSON
- [ ] Análise multivariada
- [ ] Gráficos interativos com Folium
- [ ] API REST para processamento remoto

---

## 💡 DICAS DE USO

1. **Performance**: Kriging é o mais lento (~60s). Para testes rápidos, use apenas IDW/GWM.

2. **Dados Faltantes**: NaN são removidos automaticamente das análises.

3. **Coordenadas**: Qualquer coluna com nomes como 'X', 'Y', 'Lon', 'Lat' é detectada.

4. **Variáveis**: Todas as colunas numéricas são analisadas automaticamente.

5. **Saída**: Todos os arquivos são salvos com timestamps automáticos.

6. **HTML Report**: Abra `relatorio_visualizacoes.html` em navegador para visualizar.

---

## 📞 SUPORTE

Para dúvidas sobre:
- **Análise Espacial**: Ver `GUIA_ANALISE_ESPACIAL.md`
- **Mapas**: Ver `GUIA_MAPAS_INTERPOLACAO.md`
- **Visualizações**: Ver `GUIA_VISUALIZACOES_DISTRIBUICAO.md`
- **Código**: Análise direta em `/analise/`

---

**Sistema pronto para produção** ✨
**Última atualização: 14/04/2026**

