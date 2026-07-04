# ============================================================================
# MÓDULO DE VISUALIZAÇÕES DE DISTRIBUIÇÃO E CORRELAÇÃO
# ============================================================================
# Responsável por:
#   - Histogramas com dados padronizados (z-score)
#   - Violin plots + boxplots combinados
#   - Matriz de correlação de Pearson com anotações
# ============================================================================

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import warnings

warnings.filterwarnings('ignore')


class VisualizacoesDistribuicao:
    """
    Classe para criar visualizações de distribuição e correlação de dados.
    
    Gera histogramas padronizados, violin plots e matrizes de correlação
    com características especificadas.
    """
    
    def __init__(self, dataframe: pd.DataFrame, colunas_numericas: List[str] = None):
        """
        Inicializa o visualizador de distribuição.
        
        Args:
            dataframe: DataFrame com os dados
            colunas_numericas: Lista de colunas a analisar (default: todas numéricas)
        """
        self.df = dataframe.copy()
        
        if colunas_numericas is None:
            self.colunas_numericas = self.df.select_dtypes(include=[np.number]).columns.tolist()
        else:
            self.colunas_numericas = colunas_numericas
        
        # Remover colunas de coordenadas se existirem
        pattern_coords = r'(^x$|^y$|lon|lat|easting|northing|coord)'
        self.colunas_numericas = [
            col for col in self.colunas_numericas 
            if not any(p in col.lower() for p in ['x', 'y', 'lon', 'lat'])
        ]
        
        self.figuras = {}
        print(f"✓ Visualizador de distribuição inicializado ({len(self.colunas_numericas)} variáveis)")
    
    # ========== a) HISTOGRAMAS COM DADOS PADRONIZADOS ==========
    
    def plotar_histogramas_padronizados(self, figsize: Tuple[int, int] = None) -> plt.Figure:
        """
        Cria histogramas com dados normalizados (z-score).
        
        Características:
        - Dados normalizados para z-score (média=0, DP=1)
        - KDE sobreposto
        - Média (linha sólida vermelha) e mediana (linha tracejada verde)
        - Anotações: n, DP, assimetria (canto superior esquerdo)
        - Paleta: azul-aço claro com fundo branco
        
        Returns:
            Figure com subplots (um por variável)
        """
        n_vars = len(self.colunas_numericas)
        n_cols = min(3, n_vars)
        n_rows = (n_vars + n_cols - 1) // n_cols
        
        if figsize is None:
            figsize = (n_cols * 5, n_rows * 4)
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
        axes = axes.flatten() if n_vars > 1 else [axes]
        
        plt.style.use('default')
        fig.patch.set_facecolor('white')
        
        for idx, col in enumerate(self.colunas_numericas):
            ax = axes[idx]
            
            # Remover NaN e retirar infinitos
            dados = self.df[col].dropna()
            dados = dados[np.isfinite(dados)]
            
            # Pular se não houver dados válidos
            if len(dados) < 2:
                ax.text(0.5, 0.5, f'Insuficientes dados\npara {col}', 
                       ha='center', va='center', transform=ax.transAxes)
                ax.set_title(f'Histograma: {col} (Dados insuficientes)', fontsize=11, fontweight='bold')
                continue
            
            # Normalizar para z-score
            dados_zscore = (dados - dados.mean()) / dados.std()
            
            # Verificar se há dados válidos após normalização
            if not np.all(np.isfinite(dados_zscore)):
                ax.text(0.5, 0.5, f'Dados inválidos\npara {col}', 
                       ha='center', va='center', transform=ax.transAxes)
                ax.set_title(f'Histograma: {col} (Dados inválidos)', fontsize=11, fontweight='bold')
                continue
            
            # Cores
            cor_barras = '#4682B4'  # Azul-aço
            cor_media = '#FF0000'   # Vermelho
            cor_mediana = '#00AA00' # Verde
            
            # Histograma
            ax.hist(dados_zscore, bins=30, color=cor_barras, alpha=0.7, 
                   density=True, edgecolor='black', linewidth=0.5)
            
            # KDE sobreposto
            try:
                from scipy.stats import gaussian_kde
                kde = gaussian_kde(dados_zscore)
                x_kde = np.linspace(dados_zscore.min(), dados_zscore.max(), 200)
                ax.plot(x_kde, kde(x_kde), color='navy', linewidth=2, label='KDE')
            except:
                pass
            
            # Linha de média (vermelha, sólida)
            media_z = 0  # Media do z-score é sempre 0
            ax.axvline(media_z, color=cor_media, linestyle='-', linewidth=2, label='Média')
            
            # Linha de mediana (verde, tracejada)
            mediana_z = (dados.median() - dados.mean()) / dados.std()
            ax.axvline(mediana_z, color=cor_mediana, linestyle='--', linewidth=2, label='Mediana')
            
            # Calcular estatísticas
            n = len(dados)
            dp = dados.std()
            assimetria = stats.skew(dados)
            
            # Anotar no canto superior esquerdo
            texto_anotacao = f'n = {n}\nDP = {dp:.3f}\nAssimetria = {assimetria:.3f}'
            ax.text(0.02, 0.98, texto_anotacao, transform=ax.transAxes,
                   fontsize=9, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
            
            # Formatação
            ax.set_xlabel('Z-score', fontsize=10, fontweight='bold')
            ax.set_ylabel('Densidade', fontsize=10, fontweight='bold')
            ax.set_title(f'Histograma: {col} (Normalizado)', fontsize=11, fontweight='bold')
            ax.set_facecolor('white')
            ax.grid(True, alpha=0.3, linestyle='--')
            ax.legend(loc='upper right', fontsize=9)
        
        # Remover subplots vazios
        for idx in range(len(self.colunas_numericas), len(axes)):
            fig.delaxes(axes[idx])
        
        plt.tight_layout()
        self.figuras['histogramas'] = fig
        return fig
    
    # ========== b) VIOLIN + BOXPLOT COMBINADO ==========
    
    def plotar_violin_boxplot(self, figsize: Tuple[int, int] = (14, 6)) -> plt.Figure:
        """
        Cria violin plot com boxplot interno.
        
        Características:
        - Todos em escala padronizada (z-score)
        - Violin com KDE, boxplot interno
        - Anotações de IQR em cada violin
        - Eixo Y padronizado: -3 a +3 (ou automático)
        - Paleta: cinza/azul neutra
        
        Returns:
            Figure com violin plots
        """
        fig, ax = plt.subplots(figsize=figsize)
        fig.patch.set_facecolor('white')
        
        # Preparar dados padronizados
        dados_padronizados = []
        labels = []
        
        for col in self.colunas_numericas:
            dados = self.df[col].dropna()
            dados_z = (dados - dados.mean()) / dados.std()
            dados_padronizados.append(dados_z)
            labels.append(col)
        
        # Criar violin plot
        partes = ax.violinplot(dados_padronizados, positions=range(len(labels)),
                              widths=0.7, showmeans=False, showmedians=False)
        
        # Colorir violins (paleta neutra cinza-azul)
        cor_violin = '#7A8B99'  # Azul-cinzento
        for pc in partes['bodies']:
            pc.set_facecolor(cor_violin)
            pc.set_alpha(0.7)
            pc.set_edgecolor('black')
            pc.set_linewidth(1.5)
        
        # Adicionar boxplot interno
        bp = ax.boxplot(dados_padronizados, positions=range(len(labels)),
                       widths=0.3, patch_artist=True, showfliers=False,
                       boxprops=dict(facecolor='white', edgecolor='black', linewidth=1.5),
                       whiskerprops=dict(color='black', linewidth=1),
                       capprops=dict(color='black', linewidth=1),
                       medianprops=dict(color='red', linewidth=2))
        
        # Anotar IQR em cada violin
        for i, dados_z in enumerate(dados_padronizados):
            q1 = np.percentile(dados_z, 25)
            q3 = np.percentile(dados_z, 75)
            iqr = q3 - q1
            
            # Anotar IQR no topo
            y_pos = dados_z.max() + 0.3
            ax.text(i, y_pos, f'IQR={iqr:.2f}', ha='center', fontsize=9,
                   bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7))
        
        # Formatação do eixo Y
        ax.set_ylim(-3.5, max([d.max() + 0.5 for d in dados_padronizados] + [3.5]))
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8, alpha=0.5)
        ax.axhline(y=3, color='red', linestyle='--', linewidth=0.8, alpha=0.3, label='±3σ')
        ax.axhline(y=-3, color='red', linestyle='--', linewidth=0.8, alpha=0.3)
        
        # Rótulos e formatação
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=10)
        ax.set_ylabel('Z-score (Padronizado)', fontsize=11, fontweight='bold')
        ax.set_title('Distribuição de Variáveis (Violin + Boxplot em Escala Padronizada)', 
                    fontsize=12, fontweight='bold')
        ax.set_facecolor('white')
        ax.grid(True, alpha=0.3, axis='y', linestyle='--')
        
        plt.tight_layout()
        self.figuras['violin_boxplot'] = fig
        return fig
    
    # ========== c) MATRIZ DE CORRELAÇÃO DE PEARSON ==========
    
    def plotar_matriz_correlacao(self, figsize: Tuple[int, int] = (10, 8)) -> plt.Figure:
        """
        Cria matriz de correlação de Pearson com anotações.
        
        Características:
        - Heatmap com anotação dos coeficientes
        - Destaca células com |r| > 0.6 com borda espessa
        - Paleta: divergente (azul-branco-vermelho)
        
        Returns:
            Figure com heatmap de correlação
        """
        fig, ax = plt.subplots(figsize=figsize)
        fig.patch.set_facecolor('white')
        
        # Calcular matriz de correlação
        df_numericas = self.df[self.colunas_numericas].copy()
        corr_matrix = df_numericas.corr(method='pearson')
        
        # Criar heatmap base
        sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='RdBu_r',
                   center=0, vmin=-1, vmax=1, square=True, ax=ax,
                   cbar_kws={'label': 'Coeficiente de Correlação'},
                   linewidths=0.5, linecolor='gray')
        
        # Destacar correlações fortes (|r| > 0.6) com borda espessa
        for i in range(len(corr_matrix)):
            for j in range(len(corr_matrix)):
                if i != j and abs(corr_matrix.iloc[i, j]) > 0.6:
                    # Desenhar retângulo com borda espessa
                    rect = plt.Rectangle((j, i), 1, 1, fill=False, 
                                        edgecolor='black', linewidth=3)
                    ax.add_patch(rect)
        
        # Formatação
        ax.set_title('Matriz de Correlação de Pearson\n(Bordas espessas: |r| > 0.6)',
                    fontsize=12, fontweight='bold', pad=20)
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right', fontsize=10)
        ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=10)
        
        plt.tight_layout()
        self.figuras['correlacao'] = fig
        return fig
    
    # ========== MÉTODO GERAL DE REALIZAÇÃO ==========
    
    def salvar_visualizacoes(self, pasta_saida: str = None, dpi: int = 300) -> Dict[str, Path]:
        """
        Gera e salva todas as visualizações.
        
        Args:
            pasta_saida: Caminho da pasta de saída (default: dados/saida/visualizacoes)
            dpi: Resolução dos arquivos PNG
            
        Returns:
            Dicionário com caminhos dos arquivos salvos
        """
        if pasta_saida is None:
            pasta_saida = 'dados/saida/visualizacoes'
        
        pasta_saida = Path(pasta_saida)
        pasta_saida.mkdir(parents=True, exist_ok=True)
        
        arquivos_salvos = {}
        
        # Gerar todas as visualizações
        print("\n📊 Gerando visualizações de distribuição...")
        
        # 1. Histogramas
        print("  → Gerando histogramas padronizados...")
        self.plotar_histogramas_padronizados()
        caminho_hist = pasta_saida / '01_histogramas_zscore.png'
        self.figuras['histogramas'].savefig(caminho_hist, dpi=dpi, bbox_inches='tight')
        arquivos_salvos['histogramas'] = caminho_hist
        print(f"     ✓ Salvo: {caminho_hist.name}")
        
        # 2. Violin + Boxplot
        print("  → Gerando violin plots + boxplots...")
        self.plotar_violin_boxplot()
        caminho_violin = pasta_saida / '02_violin_boxplot.png'
        self.figuras['violin_boxplot'].savefig(caminho_violin, dpi=dpi, bbox_inches='tight')
        arquivos_salvos['violin_boxplot'] = caminho_violin
        print(f"     ✓ Salvo: {caminho_violin.name}")
        
        # 3. Matriz de correlação
        print("  → Gerando matriz de correlação...")
        self.plotar_matriz_correlacao()
        caminho_corr = pasta_saida / '03_matriz_correlacao.png'
        self.figuras['correlacao'].savefig(caminho_corr, dpi=dpi, bbox_inches='tight')
        arquivos_salvos['correlacao'] = caminho_corr
        print(f"     ✓ Salvo: {caminho_corr.name}")
        
        # Fechar figuras para liberar memória
        plt.close('all')
        
        print(f"\n✅ Todas as visualizações salvas em: {pasta_saida}")
        print(f"   → Total de arquivos: {len(arquivos_salvos)}")
        
        return arquivos_salvos
    
    def gerar_relatorio_html(self, pasta_saida: str = None) -> str:
        """
        Gera relatório HTML com as visualizações.
        
        Args:
            pasta_saida: Caminho da pasta de saída
            
        Returns:
            Caminho do arquivo HTML gerado
        """
        if pasta_saida is None:
            pasta_saida = 'dados/saida/visualizacoes'
        
        pasta_saida = Path(pasta_saida)
        
        # Gerar visualizações se ainda não existirem
        if 'histogramas' not in self.figuras:
            self.salvar_visualizacoes(pasta_saida)
        
        # Criar HTML
        html_content = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório de Distribuições e Correlações</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f5f5f5;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #0066cc;
            padding-bottom: 10px;
        }
        h2 {
            color: #0066cc;
            margin-top: 30px;
        }
        .image-section {
            margin: 30px 0;
            text-align: center;
        }
        .image-section img {
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .description {
            background-color: #f9f9f9;
            padding: 15px;
            border-left: 4px solid #0066cc;
            margin: 15px 0;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Relatório de Distribuições e Correlações</h1>
        
        <h2>1. Histogramas com Dados Padronizados (Z-score)</h2>
        <div class="description">
            <p><strong>Descrição:</strong> Histogramas de cada variável normalizadas para z-score (média=0, desvio padrão=1).</p>
            <ul>
                <li>Barras em azul-aço claro</li>
                <li>Curva KDE sobreposta</li>
                <li>Linha vermelha: Média</li>
                <li>Linha verde tracejada: Mediana</li>
                <li>Anotações: n (tamanho), DP (desvio padrão), Assimetria</li>
            </ul>
        </div>
        <div class="image-section">
            <img src="01_histogramas_zscore.png" alt="Histogramas Padronizados">
        </div>
        
        <h2>2. Violin Plots + Boxplots (Escala Padronizada)</h2>
        <div class="description">
            <p><strong>Descrição:</strong> Distribuição de todas as variáveis combinando violins e boxplots.</p>
            <ul>
                <li>Eixo Y em z-score (-3 a +3σ)</li>
                <li>Violins com KDE (preenchimento azul-cinzento)</li>
                <li>Boxplot interno mostrando quartis</li>
                <li>Anotações de IQR (Intervalo Interquartil) em cada violin</li>
            </ul>
        </div>
        <div class="image-section">
            <img src="02_violin_boxplot.png" alt="Violin + Boxplot">
        </div>
        
        <h2>3. Matriz de Correlação de Pearson</h2>
        <div class="description">
            <p><strong>Descrição:</strong> Heatmap com coeficientes de correlação de Pearson.</p>
            <ul>
                <li>Escala divergente: Azul (negativa) → Branco (zero) → Vermelho (positiva)</li>
                <li>Coeficientes anotados em cada célula</li>
                <li>Bordas espessas destacam correlações |r| > 0.6</li>
                <li>Diagonal principal = 1.0 (correlação perfeita com si mesmo)</li>
            </ul>
        </div>
        <div class="image-section">
            <img src="03_matriz_correlacao.png" alt="Matriz de Correlação">
        </div>
        
    </div>
</body>
</html>
        """
        
        # Salvar HTML
        caminho_html = pasta_saida / 'relatorio_visualizacoes.html'
        with open(caminho_html, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(caminho_html)
