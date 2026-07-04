# ============================================================================
# UTILITÁRIO - CRIAR DADOS DE EXEMPLO
# ============================================================================
# Script para gerar um arquivo de dados de exemplo para testes
# ============================================================================

import pandas as pd
import numpy as np
from pathlib import Path


def criar_dados_exemplo():
    """Cria um dataset de exemplo com dados geoespaciais simulados."""
    
    print("\n📊 Gerando dados de exemplo...\n")
    
    np.random.seed(42)
    
    # ========== GERA COORDENADAS ==========
    # Coordenadas em UTM zona 23S (Brasil)
    num_amostras = 250
    x = np.random.uniform(650000, 660000, num_amostras)  # Easting
    y = np.random.uniform(7050000, 7060000, num_amostras)  # Northing
    
    # ========== GERA VARIÁVEIS SIMULADAS ==========
    # Variáveis com correlação espacial simulada
    var1 = 50 + 10 * np.sin(x/10000) + np.random.normal(0, 2, num_amostras)
    var2 = 100 + 5 * np.cos(y/10000) + np.random.normal(0, 3, num_amostras)
    var3 = var1 * 0.5 + var2 * 0.3 + np.random.normal(0, 5, num_amostras)
    var4 = np.random.gamma(2, 2, num_amostras)
    
    # ========== CRIA DATAFRAME ==========
    df = pd.DataFrame({
        'X': x,
        'Y': y,
        'Teor_Au': np.clip(var1, 0, None),      # Teor de ouro
        'Teor_Cu': np.clip(var3, 0, None),      # Teor de cobre
        'Porosidade': np.clip(50 + var2, 0, 100),  # Porosidade
        'Densidade': 2.5 + var4 * 0.1            # Densidade
    })
    
    # ========== SALVA ARQUIVO ==========
    # Define caminho e cria se necessário
    pasta_entrada = Path(__file__).parent.parent / "dados" / "entrada"
    pasta_entrada.mkdir(exist_ok=True, parents=True)
    
    arquivo_saida = pasta_entrada / "exemplo_dados_geoespaciais.xlsx"
    df.to_excel(arquivo_saida, index=False)
    
    # ========== EXIBE INFORMAÇÕES ==========
    print(f"✅ Arquivo de exemplo criado: {arquivo_saida}")
    print(f"\n📋 Estatísticas dos dados gerados:")
    print(f"  • {len(df)} amostras")
    print(f"  • {len(df.columns)} variáveis")
    print(f"  • Coordenadas: X (Easting) e Y (Northing)")
    print(f"  • CRS: EPSG:32733 (UTM 23S)")
    print(f"\n📊 Primeiras 10 linhas:\n")
    print(df.head(10))
    print(f"\n")


if __name__ == "__main__":
    criar_dados_exemplo()
