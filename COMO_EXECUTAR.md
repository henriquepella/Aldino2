# 🚀 ANÁLISE GEOESTATÍSTICA AVANÇADA

## Como Executar (Super Fácil!)

### Comando Único:

```bash
python executar.py
```

**Pronto! Isso é tudo que o usuário precisa fazer:**

1. ✅ Uma janela de seleção de arquivo abre
2. ✅ Selecione qualquer arquivo Excel (.xlsx) ou CSV (.csv) do seu computador
3. ✅ Clique em "Abrir"
4. ✅ O programa processa automaticamente
5. ✅ Um PDF abre no navegador com opção de baixar

## O que o Sistema Faz

- 📊 Detecta coordenadas automaticamente (X, Y / Lon, Lat)
- 🧮 Calcula Moran Global Index (autocorrelação espacial)
- 🗺️ Gera 5 mapas de interpolação em alta definição (300 DPI)
- 📈 Cria gráficos e visualizações
- 💡 Gera insights automáticos
- 📄 Produz PDF profissional com 6 páginas
- 💾 Abre automaticamente no navegador (sem salvar no PC)

### Opção 2: Executar Diretamente

```bash
cd geoestat_analyzer_novo/executavel
python principal.py
```

## Estrutura do Projeto

```
Aldino2/
├── executar.py                          # ← Script para rodar tudo
├── geoestat_analyzer_novo/
│   ├── executavel/
│   │   └── principal.py                 # Script principal
│   ├── analise/
│   │   ├── analisador.py
│   │   ├── gerador_relatorio_avancado.py
│   │   └── gerador_insights_avancado.py
│   ├── dados/
│   │   ├── entrada/                     # Coloque seus arquivos Excel/CSV aqui
│   │   └── saida/                       # PDFs e mapas são gerados aqui
│   └── ...outros arquivos
```

## Fluxo de Execução

1. **Seleção de Arquivo (Diálogo Gráfico)**
   - Abre janela de seleção do Windows Explorer
   - Clique em um arquivo .xlsx ou .csv
   - Clique em "Abrir"

2. **Análise Espacial**
   - Detecta coordenadas (X, Y / Lon, Lat)
   - Calcula Moran Global Index
   - Identifica clusters HH, LL, HL, LH

3. **Visualizações**
   - Scatter plots de Moran
   - Gráficos Lollipop
   - Mapas de interpolação (IDW, Kriging, GWM)

4. **Relatório PDF**
   - 6 páginas profissional
   - Página 6: Insights automáticos
   - Recomendações técnicas

5. **Saída de Dados**
   - `Relatorio_*.pdf` - Relatório completo
   - Mapas PNG em `dados/saida/mapas/`
   - Gráficos em `dados/saida/visualizacoes/`
   - Insights em `Insights_*.txt`

## Requisitos

- Python 3.8+
- Todas as dependências em `requirements.txt`

Veja `GUIA_OPERACIONAL.md` para más detalhes técnicos.

## Exemplos

### Para análise rápida
```bash
cd Aldino2
python executar.py
# Uma janela abrirá - selecione seu arquivo Excel (.xlsx) ou CSV (.csv)
# Clique em "Abrir"
```

### Para análise com arquivo específico
```bash
cd Aldino2
python executar.py
# 1. Abra o diálogo que aparecerá
# 2. Navegue até seu arquivo
# 3. Selecione e clique "Abrir"
```

## Troubleshooting

**Erro: "No module named 'analise'"**
- Certifique-se de executar de dentro de `Aldino2/` ou use `python executar.py`

**Erro: "Nenhum arquivo encontrado"**
- Coloque um arquivo .xlsx ou .csv em `geoestat_analyzer_novo/dados/entrada/`

**Erro ao gerar mapas**
- Verifique se matplotlib/contextily estão instalados
- Execute: `pip install -r requirements.txt`

---

**Versão:** 2.0 com Seleção Interativa de Arquivo  
**Data:** 14/04/2026  
**Desenvolvido com:** Python + GeoPandas + Geostatística

