# ============================================================================
# MÓDULO DE VISUALIZAÇÕES DE ANÁLISE ESPACIAL
# ============================================================================
# Responsável por:
#   - Gráficos de scatter de Moran com quadrantes
#   - Gráficos Lollipop para ranking de autocorrelação
#   - Mapas de clusters LISA com cores específicas
# ============================================================================

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from typing import Dict, Tuple
import warnings

warnings.filterwarnings('ignore')


class VisualizacoesSpatial:
    """
    Classe para criar visualizações de análise espacial.
    
    Cria gráficos especializados para interpretação de autocorrelação
    espacial e identification de clusters.
    """
    
    # ========== CORES PARA CLASSIFICAÇÕES LISA ==========
    # Padrão fixo conforme especificação
    CORES_LISA = {
        'HH': '#FF0000',      # Vermelho: Alto-Alto
        'LL': '#0000FF',      # Azul: Baixo-Baixo
        'LH': '#FF69B4',      # Rosa: Baixo-Alto
        'HL': '#00FFFF',      # Ciano: Alto-Baixo
        'NS': '#CCCCCC'       # Cinza: Não significativo
    }
    
    def __init__(self, analise_espacial):
        """
        Inicializa visualizações com objeto de análise.
        
        Args:
            analise_espacial: Objeto AnaliseSpatialAvancada
        """
        self.analise = analise_espacial
        self.figuras = {}
        print("✓ Visualizador de análise espacial inicializado")
    
    def plotar_scatter_moran(self, variavel: str, figsize: Tuple[int, int] = (10, 8)) -> plt.Figure:
        """
        Cria scatter plot de Moran com quadrantes.
        
        O gráfico mostra a relação entre valores padronizados e seus
        lags espaciais (médias dos vizinhos), com linha de tendência
        e intervalo de confiança de 95%.
        
        Args:
            variavel: Nome da variável
            figsize: Tamanho da figura
            
        Returns:
            Objeto Figure do matplotlib
        """
        if variavel not in self.analise.resultados_moran:
            print(f"⚠ Variável '{variavel}' não analisada")
            return None
        
        print(f"\nGerando scatter plot de Moran: {variavel}")
        
        # ========== EXTRAI DADOS ==========
        dados = self.analise.df[variavel].dropna().values
        
        # Verifica se dados têm variância
        if np.std(dados) == 0:
            print(f"⚠ {variavel} tem variância zero, ignorando scatter")
            return None
        
        dados_padronizados = (dados - dados.mean()) / dados.std()
        
        # Calcula lag espacial
        lag_espacial = self.analise.pesos.sparse.dot(dados_padronizados)
        
        # ========== CRIA FIGURA ==========
        fig, ax = plt.subplots(figsize=figsize)
        
        # ========== PLOTA PONTOS ==========
        ax.scatter(dados_padronizados, lag_espacial, alpha=0.6, s=80, color='steelblue', edgecolors='darkblue', linewidth=0.5)
        
        # ========== ADICIONA QUADRANTES ==========
        # Linhas verticais e horizontais (média = 0)
        ax.axhline(y=0, color='gray', linestyle='--', linewidth=1.5, alpha=0.7)
        ax.axvline(x=0, color='gray', linestyle='--', linewidth=1.5, alpha=0.7)
        
        # ========== LABELS DOS QUADRANTES ==========
        # Obtém limites dos eixos
        ylim = ax.get_ylim()
        xlim = ax.get_xlim()
        
        # Adiciona identificação dos quadrantes
        ax.text(xlim[1]*0.8, ylim[1]*0.8, 'HH\n(Alto-Alto)', fontsize=11, 
                ha='center', va='center', alpha=0.3, fontweight='bold')
        ax.text(xlim[0]*0.8, ylim[1]*0.8, 'LH\n(Baixo-Alto)', fontsize=11,
                ha='center', va='center', alpha=0.3, fontweight='bold')
        ax.text(xlim[0]*0.8, ylim[0]*0.8, 'LL\n(Baixo-Baixo)', fontsize=11,
                ha='center', va='center', alpha=0.3, fontweight='bold')
        ax.text(xlim[1]*0.8, ylim[0]*0.8, 'HL\n(Alto-Baixo)', fontsize=11,
                ha='center', va='center', alpha=0.3, fontweight='bold')
        
        # ========== LINHA DE TENDÊNCIA E IC 95% ==========
        try:
            # Calcula regressão linear com tratamento de erro
            coef = np.polyfit(dados_padronizados, lag_espacial, 1)
            p = np.poly1d(coef)
            x_linha = np.linspace(dados_padronizados.min(), dados_padronizados.max(), 100)
            y_linha = p(x_linha)
            
            # Plota linha
            ax.plot(x_linha, y_linha, color='red', linestyle='-', linewidth=2.5, label='Tendência linear')
            
            # Calcula intervalo de confiança
            residuos = lag_espacial - p(dados_padronizados)
            desvio_padrao_residuos = np.std(residuos)
            
            # ========== IC 95% ==========
            # Calcula erro padrão para cada ponto na linha
            n = len(dados_padronizados)
            x_medio = dados_padronizados.mean()
            sxx = np.sum((dados_padronizados - x_medio) ** 2)
            
            if sxx > 0:
                # Erro padrão para predição
                se_pred = desvio_padrao_residuos * np.sqrt(1 + 1/n + (x_linha - x_medio)**2 / sxx)
                
                # Bandas (z=1.96 para 95% de confiança)
                banda_superior = y_linha + 1.96 * se_pred
                banda_inferior = y_linha - 1.96 * se_pred
                
                # Plota intervalos
                ax.fill_between(x_linha, banda_inferior, banda_superior, alpha=0.2, color='red', label='IC 95%')
        
        except Exception as e:
            print(f"  ⚠ Aviso: Não foi possível calcular linha de tendência ({str(e)[:40]})")
        
        # ========== FORMATAÇÃO ==========
        ax.set_xlabel(f'Valores padronizados: {variavel}', fontsize=12, fontweight='bold')
        ax.set_ylabel('Lag espacial (média dos vizinhos)', fontsize=12, fontweight='bold')
        
        # Info do Moran
        moran_info = self.analise.resultados_moran.get(variavel, {})
        titulo = f'Scatter Plot de Moran: {variavel}'
        if moran_info:
            titulo += f'\nI = {moran_info.get("I", 0):.6f} | p-valor = {moran_info.get("p_valor", 0):.4f}'
        
        ax.set_title(titulo, fontsize=13, fontweight='bold', pad=20)
        
        if 'label' in locals():
            ax.legend(loc='upper left', fontsize=10)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # ========== ARMAZENA FIGURA ==========
        self.figuras[f'scatter_{variavel}'] = fig
        
        return fig
    
    def plotar_lollipop_moran(self, figsize: Tuple[int, int] = (12, 7)) -> plt.Figure:
        """
        Cria gráfico Lollipop para ranking de Moran's I.
        
        Compara visualmente o índice de Moran entre variáveis,
        destacando quais apresentam maior autocorrelação espacial.
        
        Args:
            figsize: Tamanho da figura
            
        Returns:
            Objeto Figure
        """
        if not self.analise.resultados_moran:
            print("⚠ Nenhuma análise de Moran realizada")
            return None
        
        print("Gerando gráfico Lollipop de Moran")
        
        # ========== PREPARA DADOS ==========
        morans = []
        variaveis = []
        significancia = []
        
        for var, resultado in self.analise.resultados_moran.items():
            variaveis.append(var)
            morans.append(resultado['I'])
            significancia.append(resultado['significancia'])
        
        # Ordena por valor de Moran (decrescente)
        indices_ordenados = np.argsort(morans)[::-1]
        variaveis_ord = [variaveis[i] for i in indices_ordenados]
        morans_ord = [morans[i] for i in indices_ordenados]
        sig_ord = [significancia[i] for i in indices_ordenados]
        
        # ========== CRIA FIGURA ==========
        fig, ax = plt.subplots(figsize=figsize)
        
        # ========== DEFINE CORES ==========
        # Cores diferentes para significativos e não-significativos
        cores = ['#2E86AB' if sig else '#A23B72' for sig in sig_ord]
        
        # ========== PLOTA LOLLIPOPS ==========
        y_pos = np.arange(len(variaveis_ord))
        
        # Sticks (linhas)
        for i, (y, valor, cor) in enumerate(zip(y_pos, morans_ord, cores)):
            ax.plot([0, valor], [y, y], color=cor, linewidth=2.5, zorder=2)
        
        # Pops (círculos)
        ax.scatter(morans_ord, y_pos, s=150, color=cores, edgecolors='black', 
                  linewidth=1.5, zorder=3, alpha=0.8)
        
        # ========== VALORES NOS PONTOS ==========
        for i, (valor, sig) in enumerate(zip(morans_ord, sig_ord)):
            sigla = "✓" if sig else ""
            ax.text(valor + 0.01, i, f"{valor:.5f} {sigla}", va='center', fontsize=9)
        
        # ========== FORMATAÇÃO ==========
        ax.set_yticks(y_pos)
        ax.set_yticklabels(variaveis_ord, fontsize=11)
        ax.set_xlabel("Índice de Moran (I)", fontsize=12, fontweight='bold')
        ax.set_title("Ranking de Autocorrelação Espacial Global\n(✓ = Significativo a 5%)", 
                    fontsize=13, fontweight='bold', pad=20)
        
        # Linha de significância
        ax.axvline(x=0, color='gray', linestyle='--', linewidth=1, alpha=0.7)
        
        ax.set_xlim(left=0)
        ax.grid(True, alpha=0.3, axis='x')
        ax.invert_yaxis()  # Maior valor no topo
        
        plt.tight_layout()
        
        # ========== ARMAZENA FIGURA ==========
        self.figuras['lollipop_ranking'] = fig
        
        return fig
    
    def plotar_mapa_lisa(self, variavel: str, figsize: Tuple[int, int] = (12, 10)) -> plt.Figure:
        """
        Cria mapa de clusters LISA com cores específicas.
        
        Visualiza no mapa geoespacial os clusters identificados
        por LISA (HH, LL, LH, HL, NS) com cores padronizadas.
        
        Args:
            variavel: Variável para LISA
            figsize: Tamanho da figura
            
        Returns:
            Objeto Figure
        """
        if variavel not in self.analise.resultados_lisa:
            print(f"⚠ LISA não calculada para '{variavel}'")
            return None
        
        print(f"Gerando mapa LISA: {variavel}")
        
        # ========== EXTRAI DADOS LISA ==========
        df_lisa = self.analise.resultados_lisa[variavel]['dataframe']
        contagem = self.analise.resultados_lisa[variavel]['contagem']
        
        # ========== CRIA FIGURA ==========
        fig, ax = plt.subplots(figsize=figsize)
        
        # ========== PLOTA CADA CLUSTER ==========
        for cluster_type in ['HH', 'LL', 'LH', 'HL', 'NS']:
            if cluster_type in df_lisa['cluster'].values:
                # Filtra dados deste cluster
                mask = df_lisa['cluster'] == cluster_type
                dados_cluster = df_lisa[mask]
                
                # Conta pontos
                num_pontos = len(dados_cluster)
                
                # Plota
                ax.scatter(dados_cluster['x'], dados_cluster['y'],
                          c=self.CORES_LISA[cluster_type],
                          label=f'{cluster_type} ({num_pontos} pts)',
                          s=100, alpha=0.7, edgecolors='black', linewidth=0.5,
                          zorder=3)
        
        # ========== FORMATAÇÃO ==========
        ax.set_xlabel(f'Coordenada X (UTM)', fontsize=11, fontweight='bold')
        ax.set_ylabel(f'Coordenada Y (UTM)', fontsize=11, fontweight='bold')
        ax.set_title(f'Mapa de Clusters LISA: {variavel}\nIdentificação de Aglomerações Espaciais', 
                    fontsize=13, fontweight='bold', pad=20)
        
        ax.legend(loc='upper right', fontsize=10, framealpha=0.95)
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')
        
        plt.tight_layout()
        
        # ========== ARMAZENA FIGURA ==========
        self.figuras[f'lisa_{variavel}'] = fig
        
        return fig
    
    def plotar_estatisticas_clusters(self, variavel: str, figsize: Tuple[int, int] = (10, 6)) -> plt.Figure:
        """
        Cria gráfico de barras com contagem de pontos por cluster LISA.
        
        Args:
            variavel: Variável para LISA
            figsize: Tamanho da figura
            
        Returns:
            Objeto Figure
        """
        if variavel not in self.analise.resultados_lisa:
            print(f"⚠ LISA não calculada para '{variavel}'")
            return None
        
        print(f"Gerando estatísticas de clusters: {variavel}")
        
        # ========== EXTRAI CONTAGENS ==========
        contagem = self.analise.resultados_lisa[variavel]['contagem']
        
        # ========== CRIA FIGURA ==========
        fig, ax = plt.subplots(figsize=figsize)
        
        # ========== ORDENA PARA EXIBIÇÃO ==========
        ordem = ['HH', 'LL', 'LH', 'HL', 'NS']
        clusters_presentes = [c for c in ordem if c in contagem.index]
        valores = [contagem[c] for c in clusters_presentes]
        cores_lista = [self.CORES_LISA[c] for c in clusters_presentes]
        
        # ========== PLOTA BARRAS ==========
        barras = ax.bar(clusters_presentes, valores, color=cores_lista, edgecolor='black', linewidth=1.5, alpha=0.8)
        
        # ========== VALORES NAS BARRAS ==========
        for barra, valor in zip(barras, valores):
            altura = barra.get_height()
            pct = (valor / sum(valores)) * 100
            ax.text(barra.get_x() + barra.get_width()/2, altura,
                   f'{int(valor)}\n({pct:.1f}%)',
                   ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        # ========== FORMATAÇÃO ==========
        ax.set_ylabel('Número de pontos', fontsize=11, fontweight='bold')
        ax.set_xlabel('Tipo de cluster', fontsize=11, fontweight='bold')
        ax.set_title(f'Distribuição de clusters LISA: {variavel}', fontsize=12, fontweight='bold', pad=15)
        ax.grid(True, alpha=0.3, axis='y')
        
        # Legenda dos tipos
        legendas_clusters = {
            'HH': 'Alto-Alto (Cluster quente)',
            'LL': 'Baixo-Baixo (Cluster frio)',
            'LH': 'Baixo-Alto (Outlier)',
            'HL': 'Alto-Baixo (Outlier)',
            'NS': 'Não-significativo'
        }
        
        labels_full = [f"{c}: {legendas_clusters.get(c, c)}" for c in clusters_presentes]
        ax.set_xticklabels([f"{c}\n{legendas_clusters.get(c, '')}" for c in clusters_presentes], fontsize=10)
        
        plt.tight_layout()
        
        # ========== ARMAZENA FIGURA ==========
        self.figuras[f'stats_{variavel}'] = fig
        
        return fig
    
    def obter_figuras(self) -> Dict:
        """
        Retorna dicionário com todas as figuras geradas.
        
        Returns:
            Dictionary com figures do matplotlib
        """
        return self.figuras
    
    def fechar_todas(self):
        """Fecha todas as figuras."""
        plt.close('all')
        self.figuras = {}
        print("✓ Todas as figuras foram fechadas")
