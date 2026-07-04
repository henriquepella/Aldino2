# ============================================================================
# MÓDULO DE MAPAS INTERPOLAÇÃO GEOESPACIAL AVANÇADA
# ============================================================================
# Responsável por:
#   - Mapa georreferenciado com basemap (OSM/Stamen)
#   - Mapa de densidade hexagonal (hexbin)
#   - Mapa de interpolação IDW (Inverse Distance Weighting)
#   - Mapa de Krigagem Ordinária
#   - Mapa GWM (Geographically Weighted Mean)
# ============================================================================

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import TwoSlopeNorm, LinearSegmentedColormap
import geopandas as gpd
from shapely.geometry import Point, box
from typing import Dict, Tuple, Optional, List
import warnings

# ========== IMPORTS PARA INTERPOLAÇÃO ==========
from scipy.interpolate import griddata
from scipy.spatial import cKDTree
from pykrige.ok import OrdinaryKriging

warnings.filterwarnings('ignore')


class MapasInterpolacao:
    """
    Classe para geração de mapas geoespaciais avançados com interpolação.
    
    Cria visualizações de dados espaciais incluindo:
    - Mapas basemap com OSM/Stamen
    - Mapas de densidade
    - Interpolações IDW, Kriging e GWM
    """
    
    def __init__(self, dataframe: pd.DataFrame, col_x: str, col_y: str, 
                 variavel: str, crs_original: str = "EPSG:32733"):
        """
        Inicializa gerador de mapas.
        
        Args:
            dataframe: DataFrame com dados geoespaciais
            col_x: Coluna de coordenada X
            col_y: Coluna de coordenada Y
            variavel: Variável para visualizar/interpolar
            crs_original: CRS dos dados originais (padrão UTM 23S)
        """
        self.df = dataframe.copy()
        self.col_x = col_x
        self.col_y = col_y
        self.variavel = variavel
        self.crs_original = crs_original
        
        # Extrai dados da variável (remove NaN)
        validos = ~self.df[variavel].isna()
        self.df = self.df[validos].copy()
        self.valores = self.df[variavel].values
        self.coords_xy = self.df[[col_x, col_y]].values
        
        # Converte para WGS84 para basemap
        try:
            from pyproj import Transformer
            transf = Transformer.from_crs(crs_original, "EPSG:4326", always_xy=True)
            lon, lat = transf.transform(self.coords_xy[:, 0], self.coords_xy[:, 1])
            self.coords_wgs84 = np.column_stack([lon, lat])
        except Exception as e:
            print(f"⚠ Aviso: Conversão WGS84 falhou: {e}")
            self.coords_wgs84 = self.coords_xy
        
        # Cria GeoDataFrame
        self.gdf = gpd.GeoDataFrame(
            {variavel: self.valores},
            geometry=[Point(xy) for xy in self.coords_xy],
            crs=crs_original
        )
        
        # Estatísticas
        self.vmin, self.vmax = self.valores.min(), self.valores.max()
        self.vmean = self.valores.mean()
        
        print(f"✓ Gerador de mapas inicializado")
        print(f"  Variável: {variavel}")
        print(f"  Amostras: {len(self.df)}")
        print(f"  Intervalo: [{self.vmin:.2f}, {self.vmax:.2f}]")
    
    def plotar_mapa_basemap_osm(self, titulo: str = None, dpi: int = 300) -> plt.Figure:
        """
        Cria mapa georreferenciado (versão simplificada).
        
        Exibe pontos coloridos pela variável analisada.
        Nota: Basemap OSM desabilitado por incompatibilidade em Python 3.12.
        
        Args:
            titulo: Título do mapa
            dpi: Resolução em pontos por polegada
            
        Returns:
            Figura matplotlib
        """
        print(f"\n📍 Gerando mapa (versão simplificada, sem basemap)...")
        
        fig, ax = plt.subplots(figsize=(14, 10), dpi=100)  # DPI para exibição
        
        # Fundo simples
        ax.set_facecolor('#E8F4F8')
        
        # ========== NORMALIZAÇÃO DIVERGENTE ==========
        # Azul → Branco → Vermelho
        vcentral = (self.vmax + self.vmin) / 2
        norm = TwoSlopeNorm(vmin=self.vmin, vcenter=vcentral, vmax=self.vmax)
        
        colors_lista = ['#0033FF', '#FFFFFF', '#FF0000']  # Azul-Branco-Vermelho
        cmap = LinearSegmentedColormap.from_list('divergente', colors_lista)
        
        # ========== PLOTA PONTOS ==========
        scatter = ax.scatter(self.coords_wgs84[:, 0], self.coords_wgs84[:, 1],
                           c=self.valores, cmap=cmap, norm=norm,
                           s=80, alpha=0.7, edgecolors='black', linewidth=0.5)
        
        # ========== BARRA DE CORES ==========
        cbar = plt.colorbar(scatter, ax=ax, label=self.variavel, pad=0.02, shrink=0.8)
        cbar.set_label(f'{self.variavel} (Intervalo: {self.vmin:.2f} - {self.vmax:.2f})',
                      fontsize=11, fontweight='bold')
        
        # ========== FORMATAÇÃO ==========
        if titulo is None:
            titulo = f'Mapa Georreferenciado: {self.variavel}\nEPSG:4326 (WGS84)'
        
        ax.set_title(titulo, fontsize=13, fontweight='bold', pad=20)
        ax.set_xlabel('Longitude', fontsize=11, fontweight='bold')
        ax.set_ylabel('Latitude', fontsize=11, fontweight='bold')
        
        # Extensão geográfica
        n_pontos = len(self.df)
        ext_lat = f"{self.coords_wgs84[:, 1].min():.4f} - {self.coords_wgs84[:, 1].max():.4f}"
        ext_lon = f"{self.coords_wgs84[:, 0].min():.4f} - {self.coords_wgs84[:, 0].max():.4f}"
        
        info_text = f'{n_pontos} pontos | Lat: {ext_lat}\nLon: {ext_lon}'
        ax.text(0.01, 0.11, info_text, transform=ax.transAxes, fontsize=8,
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        
        return fig
    
    def plotar_mapa_densidade_hexbin(self, titulo: str = None, dpi: int = 300) -> plt.Figure:
        """
        Cria mapa de densidade com hexágonos (hexbin).
        
        Agrupa pontos em hexágonos e mostra contagem de amostra por célula.
        
        Args:
            titulo: Título do mapa
            dpi: Resolução
            
        Returns:
            Figura matplotlib
        """
        print(f"\n📊 Gerando mapa de densidade hexbin...")
        
        fig, ax = plt.subplots(figsize=(12, 9), dpi=100)
        
        # ========== HEXBIN: Amarelo claro → Azul escuro ==========
        cmap_hex = plt.cm.YlGnBu  # Amarelo-Verde-Azul
        
        hexbin = ax.hexbin(self.coords_xy[:, 0], self.coords_xy[:, 1],
                          gridsize=25, cmap=cmap_hex, mincnt=1,
                          edgecolors='black', linewidths=0.5, alpha=0.8)
        
        # ========== BARRA DE CORES ==========
        cbar = plt.colorbar(hexbin, ax=ax)
        cbar.set_label('Contagem de Pontos', fontsize=11, fontweight='bold')
        
        # ========== FORMATAÇÃO ==========
        if titulo is None:
            titulo = f'Mapa de Densidade Espacial (Hexbin): {self.variavel}'
        
        ax.set_title(titulo, fontsize=13, fontweight='bold', pad=20)
        ax.set_xlabel(f'Coordenada X (UTM) [{self.crs_original}]', fontsize=11, fontweight='bold')
        ax.set_ylabel(f'Coordenada Y (UTM)', fontsize=11, fontweight='bold')
        
        # Estatísticas
        n_hexs = len(np.unique(hexbin.get_array()))
        n_pts = len(self.coords_xy)
        
        info_text = f'{n_hexs} hexágonos | {n_pts} pontos totais'
        ax.text(0.02, 0.98, info_text, transform=ax.transAxes, fontsize=9,
               verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        
        return fig
    
    def plotar_mapa_idw(self, potencia: float = 2.0, grid_points: int = 200,
                        buffer_pct: float = 0.05, titulo: str = None, dpi: int = 300) -> plt.Figure:
        """
        Cria mapa de interpolação IDW (Inverse Distance Weighting).
        
        Args:
            potencia: Potência do inverso da distância (padrão 2)
            grid_points: Pontos na grade interpolada
            buffer_pct: Buffer percentual com relação aos dados
            titulo: Título do mapa
            dpi: Resolução
            
        Returns:
            Figura matplotlib
        """
        print(f"\n🔍 Gerando mapa IDW (potência={potencia})...")
        
        # ========== CRIA GRADE REGULAR ==========
        xmin, ymin = self.coords_xy.min(axis=0)
        xmax, ymax = self.coords_xy.max(axis=0)
        
        buffer_x = (xmax - xmin) * buffer_pct
        buffer_y = (ymax - ymin) * buffer_pct
        
        x_grid = np.linspace(xmin - buffer_x, xmax + buffer_x, grid_points)
        y_grid = np.linspace(ymin - buffer_y, ymax + buffer_y, grid_points)
        xx, yy = np.meshgrid(x_grid, y_grid)
        
        # ========== CALCULA CONVEX HULL COMO MÁSCARA ==========
        from shapely.geometry import MultiPoint
        hull = MultiPoint(self.coords_xy).convex_hull
        
        # ========== IDW INTERPOLATION ==========
        def idw_interpolate(points, values, xi, potencia=2):
            """Interpolação IDW."""
            tree = cKDTree(points)
            d, idx = tree.query(xi, k=len(points))
            
            # Evita divisão por zero
            d = np.maximum(d, 1e-10)
            
            # Pesos (inverso da distância)
            w = 1.0 / (d ** potencia)
            w /= w.sum(axis=1, keepdims=True)
            
            return np.sum(values[idx] * w, axis=1)
        
        # Pontos de predição
        pred_points = np.column_stack([xx.ravel(), yy.ravel()])
        
        # Filtra apenas pontos dentro do convex hull
        mascara = np.array([hull.contains(Point(p)) for p in pred_points])
        
        # Interpola
        print(f"  Interpolando {np.sum(mascara)} pontos...")
        z_interp = np.full(len(pred_points), np.nan)
        z_interp[mascara] = idw_interpolate(self.coords_xy, self.valores,
                                            pred_points[mascara], potencia)
        
        z_grid = z_interp.reshape(xx.shape)
        
        # ========== PLOTAGEM ==========
        fig, ax = plt.subplots(figsize=(12, 9), dpi=100)
        
        # Escala azul-claro → vermelho
        cmap_idw = plt.cm.RdYlBu_r
        
        # Mapeia valores
        vmin_plot, vmax_plot = np.nanmin(z_grid), np.nanmax(z_grid)
        
        contourf = ax.contourf(xx, yy, z_grid, levels=30, cmap=cmap_idw, alpha=0.9)
        contour = ax.contour(xx, yy, z_grid, levels=10, colors='black', linewidths=0.3, alpha=0.3)
        
        # Plota pontos originais
        scatter = ax.scatter(self.coords_xy[:, 0], self.coords_xy[:, 1],
                           c=self.valores, cmap=cmap_idw,
                           s=50, edgecolors='black', linewidth=0.5, zorder=5)
        
        # Barra de cores
        cbar = plt.colorbar(contourf, ax=ax)
        cbar.set_label(f'{self.variavel} (IDW)', fontsize=11, fontweight='bold')
        
        # Formatação
        if titulo is None:
            titulo = f'Mapa IDW (p={potencia}): {self.variavel}'
        
        ax.set_title(titulo, fontsize=13, fontweight='bold', pad=20)
        ax.set_xlabel(f'Coordenada X (UTM)', fontsize=11, fontweight='bold')
        ax.set_ylabel(f'Coordenada Y (UTM)', fontsize=11, fontweight='bold')
        
        # Contagem de pontos
        n_interp = np.sum(~np.isnan(z_grid))
        info = f'{len(self.coords_xy)} pontos origem | {n_interp} células interpoladas'
        ax.text(0.02, 0.98, info, transform=ax.transAxes, fontsize=9,
               verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        
        return fig
    
    def plotar_mapa_kriging(self, grid_points: int = 200, buffer_pct: float = 0.05,
                           titulo: str = None, dpi: int = 300) -> Tuple[plt.Figure, Dict]:
        """
        Cria mapa de Krigagem Ordinária com semivariograma esférico.
        
        Args:
            grid_points: Pontos na grade
            buffer_pct: Buffer percentual
            titulo: Título
            dpi: Resolução
            
        Returns:
            Tupla (figura, dicionário com estatísticas do modelo)
        """
        print(f"\n🔮 Gerando mapa de Kriging Ordinária...")
        
        # ========== CRIA GRADE REGULAR ==========
        xmin, ymin = self.coords_xy.min(axis=0)
        xmax, ymax = self.coords_xy.max(axis=0)
        
        buffer_x = (xmax - xmin) * buffer_pct
        buffer_y = (ymax - ymin) * buffer_pct
        
        x_grid = np.linspace(xmin - buffer_x, xmax + buffer_x, grid_points)
        y_grid = np.linspace(ymin - buffer_y, ymax + buffer_y, grid_points)
        
        # ========== CONVEX HULL ==========
        from shapely.geometry import MultiPoint
        hull = MultiPoint(self.coords_xy).convex_hull
        
        # ========== KRIGING ORDINÁRIA ==========
        print(f"  Ajustando semivariograma...")
        
        # Normaliza coordenadas para kriging (evita problemas numéricos)
        coords_norm = (self.coords_xy - self.coords_xy.mean(axis=0)) / self.coords_xy.std(axis=0)
        
        # Cria kriging com modelo esférico
        ok = OrdinaryKriging(
            coords_norm[:, 0], coords_norm[:, 1], self.valores,
            variogram_model='spherical',
            verbose=False,
            enable_plotting=False,
            nlags=6
        )
        
        # Grid normalizado
        xx, yy = np.meshgrid(x_grid, y_grid)
        xx_norm = (xx - self.coords_xy[:, 0].mean()) / self.coords_xy[:, 0].std()
        yy_norm = (yy - self.coords_xy[:, 1].mean()) / self.coords_xy[:, 1].std()
        
        # Prepara pontos para predição
        from shapely.geometry import Point
        pred_points = np.column_stack([xx.ravel(), yy.ravel()])
        mascara = np.array([hull.contains(Point(p)) for p in pred_points])
        
        # Predições
        print(f"  Predizendo em {np.sum(mascara)} pontos...")
        z_pred = np.full(len(pred_points), np.nan)
        ss_pred = np.full(len(pred_points), np.nan)
        
        if np.sum(mascara) > 0:
            z_pred[mascara], ss_pred[mascara] = ok.execute(
                'points',
                xx_norm[mascara.reshape(xx.shape)].ravel(),
                yy_norm[mascara.reshape(yy.shape)].ravel()
            )
        
        z_grid = z_pred.reshape(xx.shape)
        ss_grid = ss_pred.reshape(xx.shape)
        
        # ========== EXTRAI PARÂMETROS DO MODELO ==========
        params_modelo = {
            'modelo': 'Esférico',
            'nugget': ok.variogram_model_parameters[0] if hasattr(ok, 'variogram_model_parameters') else 0,
            'sill': ok.variogram_model_parameters[1] if len(ok.variogram_model_parameters) > 1 else 0,
            'range': ok.variogram_model_parameters[2] if len(ok.variogram_model_parameters) > 2 else 0,
            'min_predito': np.nanmin(z_grid),
            'max_predito': np.nanmax(z_grid),
            'media_predita': np.nanmean(z_grid),
            'dp_predito': np.nanstd(z_grid),
            'media_ss': np.nanmean(ss_grid)
        }
        
        # ========== PLOTAGEM ==========
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7), dpi=100)
        
        cmap_krig = plt.cm.RdYlBu_r
        
        # Predições
        contourf1 = ax1.contourf(xx, yy, z_grid, levels=30, cmap=cmap_krig, alpha=0.9)
        ax1.scatter(self.coords_xy[:, 0], self.coords_xy[:, 1],
                   c=self.valores, cmap=cmap_krig, s=50, edgecolors='black', linewidth=0.5, zorder=5)
        cbar1 = plt.colorbar(contourf1, ax=ax1)
        cbar1.set_label(f'{self.variavel}', fontsize=10, fontweight='bold')
        
        ax1.set_title(f'Kriging Ordinária: Predições', fontsize=12, fontweight='bold')
        ax1.set_xlabel(f'Coordenada X (UTM)', fontsize=10)
        ax1.set_ylabel(f'Coordenada Y (UTM)', fontsize=10)
        ax1.grid(True, alpha=0.3)
        
        # Erro padrão
        contourf2 = ax2.contourf(xx, yy, ss_grid, levels=20, cmap='YlOrRd', alpha=0.9)
        cbar2 = plt.colorbar(contourf2, ax=ax2)
        cbar2.set_label(f'Erro Padrão (SS)', fontsize=10, fontweight='bold')
        
        ax2.set_title(f'Kriging Ordinária: Erro Padrão', fontsize=12, fontweight='bold')
        ax2.set_xlabel(f'Coordenada X (UTM)', fontsize=10)
        ax2.set_ylabel(f'Coordenada Y (UTM)', fontsize=10)
        ax2.grid(True, alpha=0.3)
        
        # Info do modelo
        info_modelo = (f"Modelo: {params_modelo['modelo']}\n"
                      f"Range: {params_modelo['range']:.2f}\n"
                      f"Nugget: {params_modelo['nugget']:.4f}\n"
                      f"Sill: {params_modelo['sill']:.4f}")
        
        fig.suptitle(f"Mapa de Kriging Ordinária: {self.variavel}", fontsize=13, fontweight='bold', y=0.98)
        fig.text(0.02, 0.02, info_modelo, fontsize=9,
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
        
        plt.tight_layout()
        
        return fig, params_modelo
    
    def plotar_mapa_gwm(self, grid_points: int = 200, buffer_pct: float = 0.05,
                       titulo: str = None, dpi: int = 300) -> Tuple[plt.Figure, Dict]:
        """
        Cria mapa de GWM (Geographically Weighted Mean).
        
        Calcula média local com bandwidth automático.
        
        Args:
            grid_points: Pontos na grade
            buffer_pct: Buffer
            titulo: Título
            dpi: Resolução
            
        Returns:
            Tupla (figura, dicionário com bandwidth usado)
        """
        print(f"\n📍 Gerando mapa GWM (Geographically Weighted Mean)...")
        
        # ========== CALCULA BANDWIDTH AUTOMÁTICO ==========
        # Distância mediana × 2
        from scipy.spatial.distance import cdist
        
        # Calcula matriz de distâncias
        distancias_mat = cdist(self.coords_xy, self.coords_xy)
        
        # Pega distâncias não-zero (excluindo diagonal)
        dists_nonzero = distancias_mat[distancias_mat > 0]
        bandwidth = np.median(dists_nonzero) * 2.0
        
        print(f"  Bandwidth automático: {bandwidth:.2f}")
        
        # ========== CRIA GRADE ==========
        xmin, ymin = self.coords_xy.min(axis=0)
        xmax, ymax = self.coords_xy.max(axis=0)
        
        buffer_x = (xmax - xmin) * buffer_pct
        buffer_y = (ymax - ymin) * buffer_pct
        
        x_grid = np.linspace(xmin - buffer_x, xmax + buffer_x, grid_points)
        y_grid = np.linspace(ymin - buffer_y, ymax + buffer_y, grid_points)
        xx, yy = np.meshgrid(x_grid, y_grid)
        
        # ========== CONVEX HULL ==========
        from shapely.geometry import MultiPoint, Point
        hull = MultiPoint(self.coords_xy).convex_hull
        
        # ========== GWM INTERPOLATION ==========
        def gwm_weights(dist, bandwidth):
            """Pesos Gaussianos para GWM."""
            return np.exp(-(dist ** 2) / (bandwidth ** 2))
        
        # Pontos de predição
        pred_points = np.column_stack([xx.ravel(), yy.ravel()])
        mascara = np.array([hull.contains(Point(p)) for p in pred_points])
        
        # Calcula GWM
        z_gwm = np.full(len(pred_points), np.nan)
        
        if np.sum(mascara) > 0:
            print(f"  Calculando GWM em {np.sum(mascara)} pontos...")
            
            for i, ponto in enumerate(pred_points[mascara]):
                distancias_i = np.linalg.norm(self.coords_xy - ponto, axis=1)
                pesos = gwm_weights(distancias_i, bandwidth)
                pesos /= pesos.sum()
                z_gwm[i] = np.sum(self.valores * pesos)
        
        z_grid = z_gwm.reshape(xx.shape)
        
        # ========== PLOTAGEM ==========
        fig, ax = plt.subplots(figsize=(12, 9), dpi=100)
        
        cmap_gwm = plt.cm.RdYlBu_r
        
        contourf = ax.contourf(xx, yy, z_grid, levels=30, cmap=cmap_gwm, alpha=0.9)
        ax.scatter(self.coords_xy[:, 0], self.coords_xy[:, 1],
                  c=self.valores, cmap=cmap_gwm, s=50, edgecolors='black', linewidth=0.5, zorder=5)
        
        cbar = plt.colorbar(contourf, ax=ax)
        cbar.set_label(f'{self.variavel} (GWM)', fontsize=11, fontweight='bold')
        
        if titulo is None:
            titulo = f'Mapa GWM (Bandwidth={bandwidth:.2f}): {self.variavel}'
        
        ax.set_title(titulo, fontsize=13, fontweight='bold', pad=20)
        ax.set_xlabel(f'Coordenada X (UTM)', fontsize=11, fontweight='bold')
        ax.set_ylabel(f'Coordenada Y (UTM)', fontsize=11, fontweight='bold')
        
        # Estatísticas
        vmin_gwm, vmax_gwm = np.nanmin(z_grid), np.nanmax(z_grid)
        vmean_gwm = np.nanmean(z_grid)
        info = f'Bandwidth: {bandwidth:.2f} | Min: {vmin_gwm:.2f} | Média: {vmean_gwm:.2f} | Max: {vmax_gwm:.2f}'
        
        ax.text(0.02, 0.98, info, transform=ax.transAxes, fontsize=9,
               verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        
        params_gwm = {
            'bandwidth': bandwidth,
            'min': vmin_gwm,
            'media': vmean_gwm,
            'max': vmax_gwm,
            'dp': np.nanstd(z_grid)
        }
        
        return fig, params_gwm
    
    def salvar_mapas(self, pasta_saida: str, dpi: int = 300):
        """
        Gera e salva todos os 5 mapas em alta resolução.
        
        Args:
            pasta_saida: Pasta para salvar os mapas
            dpi: Resolução (padrão 300 dpi)
        """
        from pathlib import Path
        
        pasta = Path(pasta_saida)
        pasta.mkdir(parents=True, exist_ok=True)
        
        print(f"\n{'='*60}")
        print(f"SALVANDO MAPAS EM ALTA RESOLUÇÃO (DPI={dpi})")
        print(f"{'='*60}")
        
        # Mapa 1: Basemap OSM
        fig1 = self.plotar_mapa_basemap_osm()
        arquivo1 = pasta / f"01_mapa_osm_{self.variavel}.png"
        fig1.savefig(arquivo1, dpi=dpi, bbox_inches='tight')
        plt.close(fig1)
        print(f"✓ {arquivo1.name} ({arquivo1.stat().st_size / 1024 / 1024:.1f} MB)")
        
        # Mapa 2: Hexbin
        fig2 = self.plotar_mapa_densidade_hexbin()
        arquivo2 = pasta / f"02_mapa_densidade_hexbin.png"
        fig2.savefig(arquivo2, dpi=dpi, bbox_inches='tight')
        plt.close(fig2)
        print(f"✓ {arquivo2.name} ({arquivo2.stat().st_size / 1024 / 1024:.1f} MB)")
        
        # Mapa 3: IDW
        fig3 = self.plotar_mapa_idw()
        arquivo3 = pasta / f"03_mapa_idw_{self.variavel}.png"
        fig3.savefig(arquivo3, dpi=dpi, bbox_inches='tight')
        plt.close(fig3)
        print(f"✓ {arquivo3.name} ({arquivo3.stat().st_size / 1024 / 1024:.1f} MB)")
        
        # Mapa 4: Kriging
        fig4, params_krig = self.plotar_mapa_kriging()
        arquivo4 = pasta / f"04_mapa_kriging_{self.variavel}.png"
        fig4.savefig(arquivo4, dpi=dpi, bbox_inches='tight')
        plt.close(fig4)
        print(f"✓ {arquivo4.name} ({arquivo4.stat().st_size / 1024 / 1024:.1f} MB)")
        
        # Mapa 5: GWM
        fig5, params_gwm = self.plotar_mapa_gwm()
        arquivo5 = pasta / f"05_mapa_gwm_{self.variavel}.png"
        fig5.savefig(arquivo5, dpi=dpi, bbox_inches='tight')
        plt.close(fig5)
        print(f"✓ {arquivo5.name} ({arquivo5.stat().st_size / 1024 / 1024:.1f} MB)")
        
        print(f"\n{'='*60}")
        print(f"✓ TODOS OS 5 MAPAS SALVOS COM SUCESSO!")
        print(f"{'='*60}\n")
        
        # Retorna dados para integração posterior
        return {
            'mapa_osm': arquivo1,
            'mapa_hexbin': arquivo2,
            'mapa_idw': arquivo3,
            'mapa_kriging': arquivo4,
            'mapa_gwm': arquivo5,
            'params_kriging': params_krig,
            'params_gwm': params_gwm
        }
