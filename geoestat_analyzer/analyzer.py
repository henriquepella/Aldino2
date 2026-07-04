"""
Analisador Geoestatístico - Detecção Automática de Dados Espaciais
Módulo principal para análise de coordenadas e variáveis geoespaciais
"""

import pandas as pd
import numpy as np
import re
from pathlib import Path
from typing import Tuple, List, Dict, Optional
from pyproj import Transformer

class GeoAnalyzer:
    """Classe para análise automática de dados geoespaciais"""
    
    # Padrões reconhecidos de nomes de colunas
    COORDS_PATTERNS = {
        'x': [r'^x$', r'x_coord', r'easting', r'lon', r'longitude', r'long'],
        'y': [r'^y$', r'y_coord', r'northing', r'lat', r'latitude'],
    }
    
    DEFAULT_CRS = "EPSG:32733"  # UTM zona 23S (padrão Brasil)
    
    def __init__(self, file_path: str):
        """
        Inicializa o analisador com um arquivo
        
        Args:
            file_path: Caminho do arquivo .xlsx ou .csv
        """
        self.file_path = Path(file_path)
        self.df = None
        self.data_info = {}
        self._load_file()
        
    def _load_file(self):
        """Carrega o arquivo (xlsx ou csv)"""
        if not self.file_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {self.file_path}")
        
        if self.file_path.suffix.lower() == '.xlsx':
            self.df = pd.read_excel(self.file_path)
        elif self.file_path.suffix.lower() == '.csv':
            self.df = pd.read_csv(self.file_path)
        else:
            raise ValueError("Formato não suportado. Use .xlsx ou .csv")
        
        print(f"✓ Arquivo carregado: {self.file_path.name}")
        print(f"✓ Dimensões: {self.df.shape[0]} amostras × {self.df.shape[1]} colunas")
    
    def detect_coordinate_columns(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Detecta automaticamente as colunas de coordenadas
        
        Returns:
            Tupla (coluna_x, coluna_y) ou (None, None) se não encontrar
        """
        columns_lower = [col.lower() for col in self.df.columns]
        
        x_col, y_col = None, None
        
        # Procura por colunas X
        for pattern in self.COORDS_PATTERNS['x']:
            for i, col_lower in enumerate(columns_lower):
                if re.search(pattern, col_lower):
                    x_col = self.df.columns[i]
                    break
            if x_col:
                break
        
        # Procura por colunas Y
        for pattern in self.COORDS_PATTERNS['y']:
            for i, col_lower in enumerate(columns_lower):
                if re.search(pattern, col_lower):
                    y_col = self.df.columns[i]
                    break
            if y_col:
                break
        
        # Se não encontrou, tenta identificar pelas primeiras colunas numéricas
        if not x_col or not y_col:
            numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
            if len(numeric_cols) >= 2:
                if not x_col:
                    x_col = numeric_cols[0]
                if not y_col:
                    y_col = numeric_cols[1]
        
        if x_col and y_col:
            print(f"✓ Coordenadas detectadas: X='{x_col}', Y='{y_col}'")
            self.data_info['x_col'] = x_col
            self.data_info['y_col'] = y_col
        else:
            print("⚠ Não foi possível detectar colunas de coordenadas automaticamente")
        
        return x_col, y_col
    
    def detect_numeric_variables(self, exclude_coords: bool = True) -> List[str]:
        """
        Detecta variáveis numéricas disponíveis (até 6)
        
        Args:
            exclude_coords: Se True, exclui colunas de coordenadas
            
        Returns:
            Lista com até 6 variáveis numéricas
        """
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Remove coordenadas se solicitado
        if exclude_coords:
            x_col = self.data_info.get('x_col')
            y_col = self.data_info.get('y_col')
            numeric_cols = [col for col in numeric_cols if col not in [x_col, y_col]]
        
        # Limita a 6 variáveis
        numeric_cols = numeric_cols[:6]
        
        print(f"✓ Variáveis numéricas detectadas ({len(numeric_cols)}):")
        for i, col in enumerate(numeric_cols, 1):
            print(f"   {i}. {col}")
        
        self.data_info['numeric_vars'] = numeric_cols
        return numeric_cols
    
    def get_crs_info(self) -> str:
        """
        Retorna informação do CRS (padrão EPSG:32733 para Brasil)
        
        Returns:
            Código EPSG do CRS
        """
        crs = self.DEFAULT_CRS
        print(f"✓ CRS detectado (padrão): {crs}")
        self.data_info['crs'] = crs
        return crs
    
    def get_summary_statistics(self, variables: List[str]) -> Dict:
        """
        Calcula estatísticas descritivas completas para as variáveis
        
        Args:
            variables: Lista de colunas a analisar
            
        Returns:
            Dicionário com estatísticas completas incluindo CV%
        """
        stats = {}
        for var in variables:
            if var in self.df.columns:
                clean_data = self.df[var].dropna()
                media = clean_data.mean()
                desvio = clean_data.std()
                
                # Calcula Coeficiente de Variação
                cv = (desvio / media * 100) if media != 0 else 0
                
                stats[var] = {
                    'contagem': len(clean_data),
                    'minimo': clean_data.min(),
                    'maximo': clean_data.max(),
                    'media': media,
                    'mediana': clean_data.median(),
                    'desvio_padrao': desvio,
                    'coef_variacao': cv,
                    'q25': clean_data.quantile(0.25),
                    'q75': clean_data.quantile(0.75),
                    'alta_heterogeneidade': cv > 100,  # Flag para destaque
                }
        return stats
    
    def convert_coordinates_to_wgs84(self) -> Dict:
        """
        Converte coordenadas do CRS de entrada para WGS84 (EPSG:4326)
        
        Returns:
            Dicionário com estatísticas das coordenadas convertidas
        """
        x_col = self.data_info.get('x_col')
        y_col = self.data_info.get('y_col')
        crs_input = self.data_info.get('crs', self.DEFAULT_CRS)
        
        if not x_col or not y_col:
            return {}
        
        try:
            # Cria transformador de coordenadas
            transformer = Transformer.from_crs(crs_input, "EPSG:4326", always_xy=True)
            
            # Converte coordenadas
            lons, lats = transformer.transform(self.df[x_col].values, self.df[y_col].values)
            
            # Armazena coordenadas convertidas no DataFrame
            self.df['longitude_wgs84'] = lons
            self.df['latitude_wgs84'] = lats
            
            # Calcula estatísticas das coordenadas convertidas
            converted_stats = {
                'crs_origem': crs_input,
                'crs_destino': 'EPSG:4326 (WGS84)',
                'longitude': {
                    'minimo': lons.min(),
                    'maximo': lons.max(),
                    'media': lons.mean(),
                },
                'latitude': {
                    'minimo': lats.min(),
                    'maximo': lats.max(),
                    'media': lats.mean(),
                },
                'centro': {
                    'longitude': np.median(lons),
                    'latitude': np.median(lats),
                }
            }
            
            self.data_info['coordenadas_wgs84'] = converted_stats
            print(f"✓ Coordenadas convertidas para WGS84 (EPSG:4326)")
            print(f"  Centro aproximado: ({converted_stats['centro']['latitude']:.6f}, {converted_stats['centro']['longitude']:.6f})")
            
            return converted_stats
            
        except Exception as e:
            print(f"⚠ Erro ao converter coordenadas: {str(e)}")
            return {}
    
    def analyze(self) -> Dict:
        """
        Executa análise completa automática
        
        Returns:
            Dicionário com todos os dados da análise
        """
        print("\n" + "="*60)
        print("INICIANDO ANÁLISE GEOESPACIAL")
        print("="*60 + "\n")
        
        # Detecta coordenadas
        x_col, y_col = self.detect_coordinate_columns()
        
        # Detecta variáveis numéricas
        numeric_vars = self.detect_numeric_variables()
        
        # Obtém informação do CRS
        crs = self.get_crs_info()
        
        # Calcula estatísticas
        stats = self.get_summary_statistics(numeric_vars)
        self.data_info['statistics'] = stats
        
        # Converte coordenadas para WGS84
        self.convert_coordinates_to_wgs84()
        
        print("\n" + "="*60)
        print("ANÁLISE COMPLETA")
        print("="*60)
        
        return self.data_info
    
    def export_data_for_report(self) -> Dict:
        """Exporta dados estruturados para geração de relatório"""
        return {
            'dataframe': self.df,
            'info': self.data_info,
            'x_col': self.data_info.get('x_col'),
            'y_col': self.data_info.get('y_col'),
            'variables': self.data_info.get('numeric_vars', []),
            'crs': self.data_info.get('crs'),
            'total_samples': len(self.df),
            'statistics': self.data_info.get('statistics', {}),
        }


def main():
    """Exemplo de uso"""
    # Procura por arquivos na pasta data
    data_folder = Path(__file__).parent / "data"
    data_files = list(data_folder.glob("*.xlsx")) + list(data_folder.glob("*.csv"))
    
    if not data_files:
        print("⚠ Nenhum arquivo encontrado em 'data/' ")
        print("Por favor, coloque um arquivo .xlsx ou .csv na pasta 'data/'")
        return
    
    # Analisa o primeiro arquivo encontrado
    file_path = data_files[0]
    print(f"Analisando: {file_path.name}\n")
    
    analyzer = GeoAnalyzer(str(file_path))
    analysis_results = analyzer.analyze()
    
    return analyzer


if __name__ == "__main__":
    main()
