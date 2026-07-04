# CHANGELOG - Histórico de Versões

## v2.0 - Funcionalidades Avançadas 🚀
**Data**: Abril 14, 2026

### ✨ Novas Funcionalidades

#### 1. Coeficiente de Variação (CV%) Automático
- [x] Cálculo de CV% = (Desvio Padrão / Média) × 100 para cada variável
- [x] Armazenamento e interpretação da heterogeneidade
- [x] Flag automático para CV > 100%

#### 2. Conversão de Coordenadas para WGS84
- [x] Transformação automática de EPSG:32733 (UTM 23S) para EPSG:4326 (WGS84)
- [x] Cálculo de estatísticas das coordenadas convertidas
- [x] Centro aproximado da área de estudo em graus decimais

#### 3. Tabelas Formatadas em PDF
- [x] Substituição de texto simples por tabelas profissionais
- [x] Alinhamento numérico para melhor legibilidade
- [x] Cores código: azul claro (normal) e vermelho (CV > 100%)
- [x] Headers destacados em azul escuro
- [x] Bordas e grid estruturados

#### 4. Nova Página de Georreferenciamento
- [x] Página dedicada às informações de CRS
- [x] Estatísticas das coordenadas convertidas
- [x] Centro em formato Google Maps/OSM pronto para uso
- [x] Explicação de conversão de sistemas

#### 5. Documentação Atualizada
- [x] README.md com novas funcionalidades
- [x] INSTRUCOES.txt com guia de uso avançado
- [x] MELHORIAS_v2.md com documentação técnica completa
- [x] CHANGELOG.md (este arquivo)

### 🔧 Alterações Técnicas

#### Em `analyzer.py`
**Imports Novos:**
```python
from pyproj import Transformer  # Para transformação de coordenadas
```

**Função Modificada:**
```python
get_summary_statistics() 
    # Agora retorna:
    - coef_variacao (CV%)
    - alta_heterogeneidade (boolean)
```

**Função Nova:**
```python
convert_coordinates_to_wgs84()
    # Retorna dict com:
    - crs_origem
    - crs_destino
    - longitude (min, max, media)
    - latitude (min, max, media)
    - centro (lat, lon)
```

#### Em `report_generator.py`
**Imports Novos:**
```python
from matplotlib.patches import Rectangle
from matplotlib.table import Table
```

**Função Modificada:**
```python
_add_statistics_page()
    # Antes: texto simples
    # Agora: tabela formatada com cores
```

**Fonction Nova:**
```python
_add_georeferencing_page()
    # Nova página com informações de CRS
```

**Função Atualizada:**
```python
generate()
    # Adicionada chamada a _add_georeferencing_page()
```

### 📊 Estrutura Reportório

**Antes (6 páginas):**
1. Título
2. Descrição dos Dados
3. Estatísticas (texto)
4. Visualizações
5. Análise Espacial
6. Conclusões

**Depois (7 páginas):**
1. Título ✅ Atualizado
2. Descrição dos Dados
3. **Estatísticas em Tabela** ⭐ Melhorado
4. Visualizações
5. **Georreferenciamento** ⭐ Novo
6. Análise Espacial
7. Conclusões

### 🎨 Esquema de Cores

| Elemento | Cor | Hex | Uso |
|----------|-----|-----|-----|
| Header Tabela | Azul Escuro | #2C3E50 | Identificação clara |
| Linha Normal | Azul Claro | #E8F4F8 | Variáveis CV < 100% |
| Linha Alertada | Vermelho Claro | #FFE6E6 | Variáveis CV > 100% |
| Nome Alertado | Vermelho | #FF6B6B | Destaque visual |
| Texto Geo | Verde Claro | #E8F8F5 | Seção georreferenciamento |

### 🧪 Testes Realizados

- [x] Teste com dados de exemplo (250 amostras, 4 variáveis)
- [x] Geração de PDF completo com 7 páginas
- [x] Conversão de coordenadas validada
- [x] Cálculo de CV% verificado
- [x] Renderização de tabelas em PDF confirmada
- [x] Cores e formatação validadas visualmente

**Exemplo de Teste:**
```
Arquivo: exemplo_dados_geoespaciais.xlsx
Amostras: 250
Variáveis: 4 (Teor_Au, Teor_Cu, Porosidade, Densidade)
CRS Entrada: EPSG:32733
CRS Saída: EPSG:4326
Status: ✅ Sucesso
Centro: (-26.615131°, 16.557129°)
```

### 📈 Compatibilidade

- ✅ Python 3.8+
- ✅ Pandas 2.1.4+
- ✅ NumPy 1.24.3+
- ✅ PyProj 3.6.1+ (novo)
- ✅ Matplotlib 3.8.2+
- ✅ Relatório PDF em qualquer leitor (Adobe, Chrome, etc.)

### 🐛 Correções

- [x] Melhorada legibilidade de estatísticas com alinhamento numérico
- [x] Reduzido overhead de texto em relatório (agora em tabelas)
- [x] Adicionada validação de conversão CRS
- [x] Tratamento de erro para coordenadas inválidas

### 📚 Documentação

| Arquivo | Tipo | Atualização |
|---------|------|------------|
| README.md | Técnica | ✅ Completa |
| INSTRUCOES.txt | Uso | ✅ Completa |
| MELHORIAS_v2.md | Detalhada | ✅ Nova |
| CHANGELOG.md | Histórico | ✅ Este arquivo |
| QUICKSTART.py | Guia | ✅ Compatível |

### 🔄 Migração da v1.0 para v2.0

**Para usuários existentes:**
1. Instale dependência nova: `pip install pyproj>=3.6.1`
2. Substitua arquivos `analyzer.py` e `report_generator.py`
3. Atualize `requirements.txt`
4. Execute normalmente: `python main.py`

**Compatibilidade:**
- ✅ Arquivos de dados v1.0 funcionam em v2.0
- ✅ Estrutura de pastas idêntica
- ✅ Relatório v2.0 é superset de v1.0

### 🚀 Performance

- ⚡ Tempo de análise: ~5-10 segundos (250 amostras)
- ⚡ Tempo de geração PDF: ~10-15 segundos
- ⚡ Tamanho do PDF: ~500 KB típico
- 💾 Uso de memória: ~100 MB

### 📋 Requisitos do Sistema

| Componente | Mínimo | Recomendado |
|-----------|--------|-----------|
| Python | 3.8 | 3.10+ |
| RAM | 2GB | 4GB+ |
| HD | 500MB | 2GB+ |
| SO | Windows/Linux/Mac | Qualquer |

---

## v1.0 - Versão Inicial
**Data**: Abril 14, 2026

### Funcionalidades Base
- [x] Detecção automática de coordenadas (X/Y, Lon/Lat)
- [x] Identificação de variáveis numéricas (até 6)
- [x] Cálculo de estatísticas descritivas básicas
- [x] Geração de PDF com 6 páginas
- [x] Visualizações gráficas
- [x] Análise espacial preliminar
- [x] Suporte para .xlsx e .csv

---

## Roadmap Futuro 🗺️

### v3.0 - Análise Geoestatística Avançada
- [ ] Variogramas automáticos
- [ ] Ajuste de semivariogramas
- [ ] Kriging ordinário/indicador
- [ ] Validação cruzada
- [ ] Mapas de incerteza

### v3.5 - Análise Espacial
- [ ] Teste de Moran's I
- [ ] Cluster analysis (k-means)
- [ ] Isolíneas interpoladas
- [ ] Análise de hot-spots

### v4.0 - Temporal
- [ ] Suporte a séries temporais
- [ ] Análise de tendências
- [ ] Predição temporal
- [ ] Gráficos de evolução

---

## Notas de Desenvolvimento

### Decisões de Design

1. **Tabelas em PDF**: Preferido sobre texto para profissionalismo
2. **WGS84**: Escolhido como padrão de saída para interoperabilidade
3. **CV%**: Métrica simples mas poderosa para heterogeneidade
4. **PyProj**: Biblioteca padrão Python para transformações CRS

### Desafios Superados

- ✅ Formatação de tabelas em Matplotlib/PDF (não trivial)
- ✅ Cores dinâmicas baseadas em CV%
- ✅ Suporte a múltiplos CRS com validação
- ✅ Performance com datasets grandes

### Lições Aprendidas

- Tabelas em PDF requerem posicionamento manual
- PyProj é robusto - confiável para transformações
- Cores auxiliam muito na interpretação visual
- Documentação é crítica para ferramentas automáticas

---

**Versão Atual**: v2.0
**Status**: ✅ Estável
**Próxima Major**: v3.0 (Geoestatística Avançada)
**Data Esperada**: Junho 2026
