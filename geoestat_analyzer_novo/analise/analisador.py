# ============================================================================
# MÓDULO ANALISADOR GEOESTATÍSTICO
# ============================================================================
# Responsável por:
#   - Carregar arquivos de dados (.xlsx ou .csv)
#   - Detectar automaticamente colunas de coordenadas (X/Y, Lat/Lon)
#   - Identificar variáveis numéricas disponíveis
#   - Calcular estatísticas descritivas completas
#   - Converter coordenadas para WGS84 (EPSG:4326)
# ============================================================================

import pandas as pd
import numpy as np
import re
from pathlib import Path
from typing import Tuple, List, Dict, Optional
from pyproj import Transformer

# ========== IMPORTS DE ANÁLISE ESPACIAL AVANÇADA ==========
try:
    from .analise_espacial_avancada import AnaliseSpatialAvancada
    from .visualizacoes_spatial import VisualizacoesSpatial
except ImportError:
    # Se não conseguir importar, torna funcionalidade opcional
    AnaliseSpatialAvancada = None
    VisualizacoesSpatial = None

# ========== IMPORTS DE MAPAS E INTERPOLAÇÃO ==========
try:
    from .mapas_interpolacao import MapasInterpolacao
except ImportError:
    MapasInterpolacao = None

# ========== IMPORTS DE VISUALIZAÇÕES DE DISTRIBUIÇÃO ==========
try:
    from .visualizacoes_distribuicao import VisualizacoesDistribuicao
except ImportError:
    VisualizacoesDistribuicao = None


class AnalisadorGeo:
    """
    Classe principal para análise automática de dados geoespaciais.
    
    Detecta automaticamente coordenadas, variáveis numéricas e calcula
    estatísticas descritivas com suporte a conversão de sistemas de referência.
    """
    
    # Padrões reconhecidos para nomes de colunas de coordenadas
    PADROES_COORDENADAS = {
        'x': [r'^x$', r'x_coord', r'easting', r'lon', r'longitude', r'long'],
        'y': [r'^y$', r'y_coord', r'northing', r'lat', r'latitude'],
    }
    
    # Sistema de Referência padrão para Brasil
    CRS_PADRAO = "EPSG:32733"  # UTM zona 23S
    
    def __init__(self, caminho_arquivo: str):
        """
        Inicializa o analisador com um arquivo de dados.
        
        Args:
            caminho_arquivo: Caminho do arquivo .xlsx ou .csv
            
        Raises:
            FileNotFoundError: Se o arquivo não existir
            ValueError: Se o formato não for suportado
        """
        self.caminho_arquivo = Path(caminho_arquivo)
        self.df = None
        self.info_dados = {}
        self._carregar_arquivo()
        
    def _carregar_arquivo(self):
        """Carrega o arquivo (xlsx ou csv) em um DataFrame."""
        if not self.caminho_arquivo.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {self.caminho_arquivo}")
        
        # Detecta formato e carrega
        if self.caminho_arquivo.suffix.lower() == '.xlsx':
            self.df = pd.read_excel(self.caminho_arquivo)
        elif self.caminho_arquivo.suffix.lower() == '.csv':
            self.df = pd.read_csv(self.caminho_arquivo)
        else:
            raise ValueError("Formato não suportado. Use .xlsx ou .csv")
        
        # Exibe informações do carregamento
        print(f"✓ Arquivo carregado: {self.caminho_arquivo.name}")
        print(f"✓ Dimensões: {self.df.shape[0]} amostras × {self.df.shape[1]} colunas")
    
    def detectar_coordenadas(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Detecta automaticamente as colunas de coordenadas.
        
        Procura por padrões conhecidos (X, Y, Longitude, Latitude, etc.)
        e retorna os nomes das colunas detectadas.
        
        Returns:
            Tupla (coluna_x, coluna_y) ou (None, None) se não encontrar
        """
        colunas_minusculas = [col.lower() for col in self.df.columns]
        
        col_x, col_y = None, None
        
        # Procura por colunas X/Longitude
        for padrao in self.PADROES_COORDENADAS['x']:
            for idx, col_minuscula in enumerate(colunas_minusculas):
                if re.search(padrao, col_minuscula):
                    col_x = self.df.columns[idx]
                    break
            if col_x:
                break
        
        # Procura por colunas Y/Latitude
        for padrao in self.PADROES_COORDENADAS['y']:
            for idx, col_minuscula in enumerate(colunas_minusculas):
                if re.search(padrao, col_minuscula):
                    col_y = self.df.columns[idx]
                    break
            if col_y:
                break
        
        # Fallback: tenta usar as primeiras 2 colunas numéricas
        if not col_x or not col_y:
            colunas_numericas = self.df.select_dtypes(include=[np.number]).columns.tolist()
            if len(colunas_numericas) >= 2:
                if not col_x:
                    col_x = colunas_numericas[0]
                if not col_y:
                    col_y = colunas_numericas[1]
        
        # Armazena e exibe resultado
        if col_x and col_y:
            print(f"✓ Coordenadas detectadas: X='{col_x}', Y='{col_y}'")
            self.info_dados['col_x'] = col_x
            self.info_dados['col_y'] = col_y
        else:
            print("⚠ Não foi possível detectar colunas de coordenadas automaticamente")
        
        return col_x, col_y
    
    def detectar_variaveis_numericas(self, excluir_coordenadas: bool = True) -> List[str]:
        """
        Detecta variáveis numéricas disponíveis (até 6).
        
        Args:
            excluir_coordenadas: Se True, exclui colunas de coordenadas da lista
            
        Returns:
            Lista com até 6 variáveis numéricas
        """
        colunas_numericas = self.df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Remove coordenadas se solicitado
        if excluir_coordenadas:
            col_x = self.info_dados.get('col_x')
            col_y = self.info_dados.get('col_y')
            colunas_numericas = [col for col in colunas_numericas 
                                if col not in [col_x, col_y]]
        
        # Limita a 6 variáveis
        colunas_numericas = colunas_numericas[:6]
        
        # Exibe resultado
        print(f"✓ Variáveis numéricas detectadas ({len(colunas_numericas)}):")
        for idx, col in enumerate(colunas_numericas, 1):
            print(f"   {idx}. {col}")
        
        self.info_dados['variaveis_numericas'] = colunas_numericas
        return colunas_numericas
    
    def obter_crs(self) -> str:
        """
        Retorna informação do CRS (padrão EPSG:32733 para Brasil).
        
        Returns:
            Código EPSG do sistema de referência
        """
        crs = self.CRS_PADRAO
        print(f"✓ CRS detectado (padrão): {crs}")
        self.info_dados['crs'] = crs
        return crs
    
    def calcular_estatisticas(self, variaveis: List[str]) -> Dict:
        """
        Calcula estatísticas descritivas completas para as variáveis.
        
        Incluindo: min, max, média, mediana, desvio padrão e 
        coeficiente de variação (CV%).
        
        Args:
            variaveis: Lista de colunas a analisar
            
        Returns:
            Dicionário com estatísticas completas
        """
        estatisticas = {}
        
        for variavel in variaveis:
            if variavel in self.df.columns:
                dados_limpos = self.df[variavel].dropna()
                media = dados_limpos.mean()
                desvio = dados_limpos.std()
                
                # Calcula Coeficiente de Variação (CV%)
                cv = (desvio / media * 100) if media != 0 else 0
                
                # Armazena todas as estatísticas
                estatisticas[variavel] = {
                    'contagem': len(dados_limpos),
                    'minimo': dados_limpos.min(),
                    'maximo': dados_limpos.max(),
                    'media': media,
                    'mediana': dados_limpos.median(),
                    'desvio_padrao': desvio,
                    'coef_variacao': cv,
                    'alta_heterogeneidade': cv > 100,  # Flag para destaque visual
                    'q25': dados_limpos.quantile(0.25),
                    'q75': dados_limpos.quantile(0.75),
                }
        
        return estatisticas
    
    def converter_coordenadas_wgs84(self) -> Dict:
        """
        Converte coordenadas de um CRS para WGS84 (EPSG:4326).
        
        Usa pyproj para transformação automática de sistmas de referência.
        Armazena as coordenadas convertidas no DataFrame.
        
        Returns:
            Dicionário com estatísticas das coordenadas convertidas
        """
        col_x = self.info_dados.get('col_x')
        col_y = self.info_dados.get('col_y')
        crs_entrada = self.info_dados.get('crs', self.CRS_PADRAO)
        
        if not col_x or not col_y:
            return {}
        
        try:
            # Cria transformador de coordenadas
            transformador = Transformer.from_crs(crs_entrada, "EPSG:4326", always_xy=True)
            
            # Converte coordenadas
            longitudes, latitudes = transformador.transform(
                self.df[col_x].values, 
                self.df[col_y].values
            )
            
            # Armazena coordenadas convertidas no DataFrame
            self.df['longitude_wgs84'] = longitudes
            self.df['latitude_wgs84'] = latitudes
            
            # Calcula estatísticas das coordenadas convertidas
            estatisticas_convertidas = {
                'crs_origem': crs_entrada,
                'crs_destino': 'EPSG:4326 (WGS84)',
                'longitude': {
                    'minimo': longitudes.min(),
                    'maximo': longitudes.max(),
                    'media': longitudes.mean(),
                },
                'latitude': {
                    'minimo': latitudes.min(),
                    'maximo': latitudes.max(),
                    'media': latitudes.mean(),
                },
                'centro': {
                    'latitude': np.median(latitudes),
                    'longitude': np.median(longitudes),
                }
            }
            
            self.info_dados['coordenadas_wgs84'] = estatisticas_convertidas
            print(f"✓ Coordenadas convertidas para WGS84 (EPSG:4326)")
            print(f"  Centro aprox: ({estatisticas_convertidas['centro']['latitude']:.6f}, "
                  f"{estatisticas_convertidas['centro']['longitude']:.6f})")
            
            return estatisticas_convertidas
            
        except Exception as erro:
            print(f"⚠ Erro ao converter coordenadas: {str(erro)}")
            return {}
    
    def analisar(self) -> Dict:
        """
        Executa análise completa e automática dos dados.
        
        Detecta coordenadas, variáveis, calcula estatísticas e 
        converte coordenadas para WGS84.
        
        Returns:
            Dicionário com todos os dados da análise
        """
        print("\n" + "="*60)
        print("INICIANDO ANÁLISE GEOESPACIAL")
        print("="*60 + "\n")
        
        # Detecta coordenadas
        col_x, col_y = self.detectar_coordenadas()
        
        # Detecta variáveis numéricas
        variaveis = self.detectar_variaveis_numericas()
        
        # Obtém informação do CRS
        crs = self.obter_crs()
        
        # Calcula estatísticas
        estatisticas = self.calcular_estatisticas(variaveis)
        self.info_dados['estatisticas'] = estatisticas
        
        # Converte coordenadas para WGS84
        self.converter_coordenadas_wgs84()
        
        print("\n" + "="*60)
        print("ANÁLISE COMPLETA")
        print("="*60 + "\n")
        
        return self.info_dados
    
    def analisar_autocorrelacao_espacial(self) -> Dict:
        """
        Ativa análise avançada de autocorrelação espacial.
        
        Calcula Índice de Moran Global para cada variável e realiza
        análise LISA (Local Indicators of Spatial Association).
        
        Requer que detectar_coordenadas() tenha sido executado antes.
        
        Returns:
            Dicionário com resultados de autocorrelação espacial
        """
        if not AnaliseSpatialAvancada:
            print("⚠ Módulos de análise espacial não disponíveis")
            return {}
        
        col_x = self.info_dados.get('col_x')
        col_y = self.info_dados.get('col_y')
        variaveis = self.info_dados.get('variaveis_numericas', [])
        
        if not col_x or not col_y:
            print("⚠ Coordenadas não detectadas. Execute detectar_coordenadas() primeiro")
            return {}
        
        if not variaveis:
            print("⚠ Nenhuma variável numérica disponível")
            return {}
        
        try:
            # ========== INICIALIZA ANÁLISE ESPACIAL ==========
            analise_espacial = AnaliseSpatialAvancada(self.df, col_x, col_y, seed=42)
            
            # ========== CALCULA MORAN GLOBAL ==========
            df_moran = analise_espacial.calcular_moran_multiplas(variaveis)
            
            # ========== CALCULA LISA PARA VARIÁVEL COM MAIOR MORAN ==========
            # LISA desabilitado: Numba é incompatível com Python 3.12
            # As visualizações funcionam sem LISA usando apenas dados Moran Global
            variavel_max, resultado_max = analise_espacial.obter_variavel_maior_moran()
            df_lisa = None  # LISA desabilitado por incompatibilidade Numba/Python 3.12
            
            # ========== OBTÉM RESUMO EXECUTIVO ==========
            resumo = analise_espacial.obter_resumo_espacial()
            
            # ========== ARMAZENA RESULTADOS ==========
            self.info_dados['analise_espacial'] = {
                'objeto': analise_espacial,
                'resultados_moran': df_moran,
                'variavel_max': variavel_max,
                'resumo': resumo
            }
            
            print("\n✓ Análise de autocorrelação espacial concluída")
            return self.info_dados['analise_espacial']
            
        except Exception as erro:
            print(f"⚠ Erro na análise espacial: {str(erro)}")
            import traceback
            traceback.print_exc()
            return {}
    
    def gerar_visualizacoes_espaciais(self) -> Dict:
        """
        Gera visualizações de autocorrelação espacial.
        
        Cria scatter plots de Moran, lollipop ranking e mapas LISA.
        
        Requer que analisar_autocorrelacao_espacial() tenha sido executado antes.
        
        Returns:
            Dicionário com figuras matplotlib
        """
        if not VisualizacoesSpatial:
            print("⚠ Módulos de visualização espacial não disponíveis")
            return {}
        
        analise_espacial = self.info_dados.get('analise_espacial', {}).get('objeto')
        variaveis = self.info_dados.get('variaveis_numericas', [])
        
        if not analise_espacial or not variaveis:
            print("⚠ Análise espacial não realizada. Execute analisar_autocorrelacao_espacial() primeiro")
            return {}
        
        try:
            # ========== INICIALIZA VISUALIZADOR ==========
            visualizador = VisualizacoesSpatial(analise_espacial)
            
            # ========== GERA SCATTER PLOT DE MORAN ==========
            print("\n" + "="*60)
            print("GERANDO VISUALIZAÇÕES DE AUTOCORRELAÇÃO ESPACIAL")
            print("="*60)
            for variavel in variaveis:
                if variavel in analise_espacial.resultados_moran:
                    visualizador.plotar_scatter_moran(variavel)
            
            # ========== GERA LOLLIPOP RANKING ==========
            visualizador.plotar_lollipop_moran()
            
            # ========== GERA MAPAS LISA ==========
            variavel_max = self.info_dados['analise_espacial']['variavel_max']
            if variavel_max:
                visualizador.plotar_mapa_lisa(variavel_max)
                visualizador.plotar_estatisticas_clusters(variavel_max)
            
            # ========== ARMAZENA VISUALIZADOR ==========
            self.info_dados['visualizador_espacial'] = visualizador
            
            figuras = visualizador.obter_figuras()
            print(f"\n✓ {len(figuras)} visualizações geradas com sucesso")
            
            return figuras
            
        except Exception as erro:
            print(f"⚠ Erro ao gerar visualizações: {str(erro)}")
            import traceback
            traceback.print_exc()
            return {}
    
    def gerar_mapas_interpolacao(self, pasta_saida: str = None) -> Dict:
        """
        Gera mapas de interpolação geoespacial avançada.
        
        Cria 5 tipos de mapas:
        1. Mapa com basemap OSM (EPSG:4326)
        2. Mapa de densidade hexbin
        3. Mapa IDW (Inverse Distance Weighting)
        4. Mapa de Kriging Ordinária
        5. Mapa GWM (Geographically Weighted Mean)
        
        Todos em alta resolução (300 dpi).
        
        Args:
            pasta_saida: Pasta para salvar os mapas. Se None, usa dados/saida/
            
        Returns:
            Dicionário com caminhos dos mapas e parâmetros
        """
        if not MapasInterpolacao:
            print("⚠ Módulo de mapas não disponível")
            return {}
        
        variavel_max = self.info_dados.get('analise_espacial', {}).get('variavel_max')
        
        if not variavel_max:
            # Se não conseguir índice de Moran, usa primeira variável numérica
            variaveis = self.info_dados.get('variaveis_numericas', [])
            if not variaveis:
                print("⚠ Nenhuma variável disponível para interpolação")
                return {}
            variavel_max = variaveis[0]
        
        col_x = self.info_dados.get('col_x')
        col_y = self.info_dados.get('col_y')
        crs = self.info_dados.get('crs', 'EPSG:32733')
        
        if not col_x or not col_y:
            print("⚠ Coordenadas não detectadas")
            return {}
        
        if pasta_saida is None:
            pasta_saida = Path(__file__).parent.parent / "dados" / "saida" / "mapas"
        
        try:
            print(f"\n{'='*60}")
            print(f"GERANDO MAPAS DE INTERPOLAÇÃO GEOESPACIAL")
            print(f"{'='*60}")
            print(f"Variável: {variavel_max}")
            print(f"Amostras: {len(self.df)}")
            
            # Cria gerador de mapas
            mapa_gen = MapasInterpolacao(self.df, col_x, col_y, variavel_max, crs)
            
            # Salva todos os mapas
            resultado = mapa_gen.salvar_mapas(pasta_saida, dpi=300)
            
            # Armazena informações
            self.info_dados['mapas_interpolacao'] = resultado
            
            return resultado
            
        except Exception as erro:
            print(f"⚠ Erro ao gerar mapas: {str(erro)}")
            import traceback
            traceback.print_exc()
            return {}
    
    def gerar_visualizacoes_distribuicao(self, pasta_saida: str = None) -> Dict:
        """
        Gera visualizações de distribuição e correlação das variáveis.
        
        Cria:
        1. Histogramas padronizados (z-score) com KDE
        2. Violin plots + boxplots combinados
        3. Matriz de correlação de Pearson com anotações
        
        Args:
            pasta_saida: Pasta para salvar as visualizações. Se None, usa dados/saida/visualizacoes
            
        Returns:
            Dicionário com caminhos dos arquivos e relatório HTML
        """
        if not VisualizacoesDistribuicao:
            print("⚠ Módulo de visualizações de distribuição não disponível")
            return {}
        
        variaveis = self.info_dados.get('variaveis_numericas', [])
        if not variaveis:
            print("⚠ Nenhuma variável numérica disponível")
            return {}
        
        if pasta_saida is None:
            pasta_saida = Path(__file__).parent.parent / "dados" / "saida" / "visualizacoes"
        
        try:
            print(f"\n{'='*60}")
            print(f"GERANDO VISUALIZAÇÕES DE DISTRIBUIÇÃO")
            print(f"{'='*60}")
            print(f"Variáveis: {len(variaveis)}")
            print(f"Amostras: {len(self.df)}")
            
            # Cria gerador de visualizações
            vis_dist = VisualizacoesDistribuicao(self.df, variaveis)
            
            # Salva todas as visualizações
            arquivos = vis_dist.salvar_visualizacoes(pasta_saida, dpi=300)
            
            # Gera relatório HTML
            html_path = vis_dist.gerar_relatorio_html(pasta_saida)
            arquivos['relatorio_html'] = html_path
            
            # Armazena informações
            self.info_dados['visualizacoes_distribuicao'] = arquivos
            
            print(f"✓ Visualizações salvas em: {pasta_saida}")
            print(f"✓ Relatório HTML gerado: {html_path}")
            
            return arquivos
            
        except Exception as erro:
            print(f"⚠ Erro ao gerar visualizações: {str(erro)}")
            import traceback
            traceback.print_exc()
            return {}
    
    def exportar_dados_relatorio(self) -> Dict:
        """
        Exporta dados estruturados para geração de relatório.
        
        Inclui dados geoespaciais básicos, estatísticas e resultados
        de análise avançada (Moran, LISA, visualizações).
        
        Returns:
            Dicionário contendo todos os dados necessários
        """
        return {
            'dataframe': self.df,
            'info': self.info_dados,
            'col_x': self.info_dados.get('col_x'),
            'col_y': self.info_dados.get('col_y'),
            'variaveis': self.info_dados.get('variaveis_numericas', []),
            'crs': self.info_dados.get('crs'),
            'total_amostras': len(self.df),
            'estatisticas': self.info_dados.get('estatisticas', {}),
            'coordenadas_wgs84': self.info_dados.get('coordenadas_wgs84', {}),
            # ========== DADOS DE ANÁLISE ESPACIAL ==========
            'analise_espacial': self.info_dados.get('analise_espacial', {}),
            'visualizador': self.info_dados.get('visualizador_espacial', None),
        }
