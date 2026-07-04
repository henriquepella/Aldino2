#!/usr/bin/env python3
# ============================================================================
# TESTE RÁPIDO - GERAÇÃO DE MAPAS
# ============================================================================

import sys
from pathlib import Path
import numpy as np

pasta_raiz = Path(__file__).parent.parent
sys.path.insert(0, str(pasta_raiz))

from analise.mapas_interpolacao import MapasInterpolacao
import pandas as pd

# ========== CARREGA DADOS ==========
arquivo = Path(__file__).parent / "dados" / "entrada" / "exemplo_dados_geoespaciais.xlsx"

if not arquivo.exists():
    print(f"⚠ Arquivo não encontrado: {arquivo}")
    sys.exit(1)

print("Carregando dados...")
df = pd.read_excel(arquivo)

# ========== GERA MAPAS ==========
print("\nGerando 5 mapas de interpolação geoespacial...")
print("(Esta operação pode levar alguns minutos, especialmente Kriging)")

pasta_saida = Path(__file__).parent / "dados" / "saida" / "mapas"

try:
    mapa_gen = MapasInterpolacao(df, 'X', 'Y', 'Teor_Au', 'EPSG:32733')
    resultado = mapa_gen.salvar_mapas(pasta_saida, dpi=300)
    
    print("\n✅ SUCESSO! Todos os mapas foram gerados em:")
    print(f"   {pasta_saida}")
    
    if resultado:
        print("\nArquivos gerados:")
        for chave, caminho in resultado.items():
            if isinstance(caminho, Path):
                tamanho = caminho.stat().st_size / 1024 / 1024
                print(f"  ✓ {caminho.name} ({tamanho:.1f} MB)")
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
