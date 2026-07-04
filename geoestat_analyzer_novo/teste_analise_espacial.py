#!/usr/bin/env python3
# ============================================================================
# SCRIPT DE TESTE RÁPIDO - ANÁLISE ESPACIAL
# ============================================================================

import sys
from pathlib import Path
import os

# Adiciona pasta raiz ao path
pasta_raiz = Path(__file__).parent
sys.path.insert(0, str(pasta_raiz))

from analise.analisador import AnalisadorGeo

# Procura arquivo em dados/entrada/
pasta_entrada = pasta_raiz / "dados" / "entrada"
arquivos = list(pasta_entrada.glob("*.xlsx")) + list(pasta_entrada.glob("*.csv"))

if arquivos:
    arquivo = arquivos[0]
    print(f"📂 Testando análise com {arquivo.name}")
    
    # Análise básica
    analisador = AnalisadorGeo(str(arquivo))
    analisador.analisar()
    
    # Análise espacial
    print("\n🔍 Iniciando análise de autocorrelação espacial...")
    resultado = analisador.analisar_autocorrelacao_espacial()
    
    if resultado:
        print("✓ Análise de autocorrelação concluída com sucesso!")
        print(f"✓ Variável com maior I: {resultado['variavel_max']}")
        print(f"✓ Valor I: {resultado['resumo']['moran_maximo']:.6f}")
    else:
        print("⚠ Análise de autocorrelação falhou")
    
    # Visualizações
    print("\n📈 Iniciando geração de visualizações...")
    figs = analisador.gerar_visualizacoes_espaciais()
    
    if figs:
        print(f"✓ {len(figs)} visualizações geradas com sucesso!")
    else:
        print("⚠ Geração de visualizações falhou")
    
else:
    print(f"⚠ Nenhum arquivo encontrado em {pasta_entrada}")
