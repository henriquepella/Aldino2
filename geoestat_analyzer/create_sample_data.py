"""
Criar arquivo de dados de exemplo para demonstração
Execute: python create_sample_data.py
"""

import pandas as pd
import numpy as np
from pathlib import Path

def create_sample_data():
    """Cria um dataset de exemplo com dados geoespaciais"""
    
    np.random.seed(42)
    
    # Cria coordenadas (UTM zona 23S - Brasil)
    n_samples = 250
    x = np.random.uniform(650000, 660000, n_samples)  # Easting
    y = np.random.uniform(7050000, 7060000, n_samples)  # Northing
    
    # Cria variáveis com correlação espacial simulada
    var1 = 50 + 10 * np.sin(x/10000) + np.random.normal(0, 2, n_samples)
    var2 = 100 + 5 * np.cos(y/10000) + np.random.normal(0, 3, n_samples)
    var3 = var1 * 0.5 + var2 * 0.3 + np.random.normal(0, 5, n_samples)
    var4 = np.random.gamma(2, 2, n_samples)
    
    # Cria DataFrame
    df = pd.DataFrame({
        'X': x,
        'Y': y,
        'Teor_Au': np.clip(var1, 0, None),  # Simula teor de ouro
        'Teor_Cu': np.clip(var3, 0, None),  # Simula teor de cobre
        'Porosidade': np.clip(50 + var2, 0, 100),
        'Densidade': 2.5 + var4 * 0.1
    })
    
    # Salva na pasta data
    data_folder = Path(__file__).parent / "data"
    data_folder.mkdir(exist_ok=True)
    
    output_file = data_folder / "exemplo_dados_geoespaciais.xlsx"
    df.to_excel(output_file, index=False)
    
    print(f"✅ Arquivo de exemplo criado: {output_file}")
    print(f"\nDados de exemplo:")
    print(df.head(10))
    print(f"\nResumo:")
    print(f"  • {len(df)} amostras")
    print(f"  • {len(df.columns)} variáveis")
    print(f"  • Coordenadas: X (Easting) e Y (Northing)")
    print(f"  • CRS: EPSG:32733 (UTM 23S)")


if __name__ == "__main__":
    create_sample_data()
