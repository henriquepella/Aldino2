# ============================================================================
# MÓDULO GERADOR DE RELATÓRIO PDF AVANÇADO
# ============================================================================
# Responsável por:
#   - Gerar relatórios PDF profissionais com design visual
#   - Estrutura de 6 páginas com conteúdo estratificado
#   - Integração de todas as visualizações (estatísticas, mapas, distribuições)
#   - Cabeçalho/rodapé persistente
#   - Fonts e paleta de cores profissionais
# ============================================================================

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
import warnings

warnings.filterwarnings('ignore')


class GeradorRelatorioAvancado:
    """
    Gerador avançado de relatórios PDF com design profissional.
    
    Cria relatórios estruturados em 6 páginas com conteúdo estratificado,
    design visual consistente e integração de todas as análises.
    """
    
    # Paleta de cores
    COR_PRIMARIA = '#1A3A5C'        # Azul-petróleo (headers)
    COR_SECUNDARIA = '#2E5C8A'      # Azul mais claro
    COR_FUNDO = '#FFFFFF'           # Branco
    COR_CINZA_CLARO = '#F5F5F5'    # Cinza claro (tabelas)
    COR_DESTAQUE = '#E74C3C'        # Vermelho (valores destacados)
    COR_SUCESSO = '#27AE60'         # Verde (valores positivos)
    
    def __init__(self, analisador, caminho_saida: str = None, nome_projeto: str = None):
        """
        Inicializa o gerador avançado de relatório.
        
        Args:
            analisador: Instância de AnalisadorGeo com dados analisados
            caminho_saida: Caminho para salvar o PDF
            nome_projeto: Nome do projeto (se None, extrai do arquivo)
        """
        self.analisador = analisador
        self.df = analisador.df
        self.info_dados = analisador.exportar_dados_relatorio()
        
        # Nome do projeto
        if nome_projeto is None:
            nome_projeto = analisador.caminho_arquivo.stem
        self.nome_projeto = nome_projeto
        
        # Configurar caminho de saída
        if caminho_saida is None:
            caminho_saida = Path(__file__).parent.parent / "dados" / "saida"
            caminho_saida.mkdir(exist_ok=True)
        
        # Nome do arquivo com timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.arquivo_saida = Path(caminho_saida) / f"Relatorio_{self.nome_projeto}_{timestamp}.pdf"
        
        # Configurações matplotlib
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
        
        self.data_relatorio = datetime.now().strftime("%d de %B de %Y")
        self.total_amostras = len(self.df)
        self.total_variaveis = len(self.info_dados.get('variaveis', []))
    
    # ========== PÁGINA 1: CAPA ==========
    
    def _gerar_pagina_capa(self, pdf: PdfPages):
        """Gera página de capa profissional."""
        fig = plt.figure(figsize=(11, 8.5))
        fig.patch.set_facecolor(self.COR_FUNDO)
        ax = fig.add_subplot(111)
        ax.axis('off')
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        
        # Faixa colorida horizontal no topo
        rect_top = mpatches.Rectangle((0, 9), 10, 1, 
                                      facecolor=self.COR_PRIMARIA, 
                                      edgecolor='none')
        ax.add_patch(rect_top)
        
        # Título principal
        ax.text(5, 7.5, 'ANÁLISE GEOESTATÍSTICA', 
                ha='center', va='center', fontsize=32, fontweight='bold',
                color=self.COR_PRIMARIA)
        
        # Subtítulo (nome do projeto)
        ax.text(5, 6.8, f'Estudo: {self.nome_projeto}', 
                ha='center', va='center', fontsize=18,
                color=self.COR_SECUNDARIA, style='italic')
        
        # Linha divisória
        ax.plot([1, 9], [6.3, 6.3], color=self.COR_PRIMARIA, linewidth=2)
        
        # Informações principais
        info_y = 5.5
        info_text = f"""
Data da Análise: {self.data_relatorio}

Número de Amostras: {self.total_amostras:,}
Variáveis Analisadas: {self.total_variaveis}

Sistema de Referência (CRS): {self.info_dados.get('crs', 'EPSG:32733')}
Coordenadas Detectadas:
  • X (Easting): {self.info_dados.get('col_x', 'Não detectado')}
  • Y (Northing): {self.info_dados.get('col_y', 'Não detectado')}

Extensão Geográfica:
  • X: [{self.df[self.info_dados.get('col_x', 'X')].min():.2f}, {self.df[self.info_dados.get('col_x', 'X')].max():.2f}]
  • Y: [{self.df[self.info_dados.get('col_y', 'Y')].min():.2f}, {self.df[self.info_dados.get('col_y', 'Y')].max():.2f}]
"""
        
        ax.text(2, info_y, info_text, 
                ha='left', va='top', fontsize=11,
                bbox=dict(boxstyle='round,pad=1', facecolor=self.COR_CINZA_CLARO, 
                         edgecolor=self.COR_PRIMARIA, linewidth=1.5),
                family='monospace')
        
        # Rodapé
        ax.text(5, 0.5, 'Gerador Automático de Relatórios Geoestatísticos v2.1', 
                ha='center', va='bottom', fontsize=9, style='italic', 
                color='#999999')
        ax.text(5, 0.1, f'Arquivo de saída: {self.arquivo_saida.name}', 
                ha='center', va='bottom', fontsize=8, 
                color='#AAAAAA')
        
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
        print(f"✓ Página 1 (Capa): {self.arquivo_saida.name}")
    
    # ========== PÁGINA 2: RESUMO EXECUTIVO ==========
    
    def _gerar_pagina_resumo_executivo(self, pdf: PdfPages):
        """Gera página de resumo executivo com cards de métricas."""
        fig = plt.figure(figsize=(11, 8.5))
        fig.patch.set_facecolor(self.COR_FUNDO)
        
        # Cabeçalho
        ax_header = fig.add_axes([0, 0.92, 1, 0.08])
        ax_header.axis('off')
        ax_header.text(0.05, 0.5, f'{self.nome_projeto} | {self.data_relatorio}', 
                      fontsize=11, fontweight='bold', color=self.COR_PRIMARIA,
                      va='center', transform=ax_header.transAxes)
        
        # Linha divisória
        line = mpatches.Rectangle((0, 0), 1, 0.02, 
                                 transform=ax_header.transAxes,
                                 facecolor=self.COR_PRIMARIA, 
                                 edgecolor='none')
        ax_header.add_patch(line)
        
        # Título da página
        ax_title = fig.add_axes([0, 0.82, 1, 0.06])
        ax_title.axis('off')
        ax_title.text(0.05, 0.5, '2. RESUMO EXECUTIVO', 
                     fontsize=16, fontweight='bold', color=self.COR_PRIMARIA,
                     va='center', transform=ax_title.transAxes)
        
        # Texto síntese
        ax_sintese = fig.add_axes([0.05, 0.60, 0.9, 0.16])
        ax_sintese.axis('off')
        
        # Buscar informações de Moran se disponível
        moran_info = self.info_dados.get('analise_espacial', {})
        moran_text = f"Autocorrelação espacial (Moran's I) significativa detectada" if moran_info else "Dados analisados com sucesso"
        
        sintese = f"""
Este relatório apresenta uma análise geoestatística completa do dataset '{self.nome_projeto}' 
com {self.total_amostras:,} amostras e {self.total_variaveis} variáveis analisadas.

Os dados foram georeferenciados no sistema {self.info_dados.get('crs', 'EPSG:32733')} (UTM Zona 23S) 
e convertidos para WGS84 (EPSG:4326) para visualização em mapas digitais.

Análises realizadas:
• Estatística descritiva multivariada com destaque para variáveis heterogêneas
• Análise de autocorrelação espacial (Moran's I com 999 permutações)
• Identificação de clusters espaciais (LISA - Local Indicators of Spatial Association)
• Interpolação geoespacial por múltiplos métodos (IDW, Kriging, GWM)
• Análise de distribuições univariadas com visualizações padronizadas
"""
        
        ax_sintese.text(0.05, 0.95, sintese.strip(), 
                       ha='left', va='top', fontsize=10,
                       wrap=True, transform=ax_sintese.transAxes)
        
        # Cards de métricas (4 em linha)
        cards_data = [
            ('Amostras', f'{self.total_amostras:,}', self.COR_PRIMARIA),
            ('Variáveis', f'{self.total_variaveis}', self.COR_SECUNDARIA),
            ('CRS Entrada', self.info_dados.get('crs', 'UTM').split(':')[1], '#27AE60'),
            ('Clusters LISA', self._contar_clusters(), '#F39C12'),
        ]
        
        card_y = 0.45
        card_height = 0.15
        card_width = 0.2
        
        for i, (titulo, valor, cor) in enumerate(cards_data):
            x_pos = 0.05 + i * (card_width + 0.03)
            
            # Retângulo do card
            card_rect = mpatches.FancyBboxPatch(
                (x_pos, card_y), card_width, card_height,
                boxstyle="round,pad=0.01", 
                transform=fig.transFigure,
                facecolor=cor, alpha=0.1, 
                edgecolor=cor, linewidth=2
            )
            fig.add_artist(card_rect)
            
            # Texto do card
            fig.text(x_pos + card_width/2, card_y + 0.10, valor,
                    ha='center', va='center', fontsize=18, fontweight='bold',
                    color=cor)
            fig.text(x_pos + card_width/2, card_y + 0.04, titulo,
                    ha='center', va='center', fontsize=9, color='#666666')
        
        # Rodapé com numeração
        fig.text(0.95, 0.02, 'Página 2', ha='right', fontsize=9, color='#999999')
        
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
        print(f"✓ Página 2 (Resumo Executivo): Gerada")
    
    # ========== PÁGINA 3: ESTATÍSTICAS DESCRITIVAS ==========
    
    def _gerar_pagina_estatisticas(self, pdf: PdfPages):
        """Gera página com tabela de estatísticas descritivas formatada."""
        fig = plt.figure(figsize=(11, 8.5))
        fig.patch.set_facecolor(self.COR_FUNDO)
        
        # Cabeçalho
        fig.text(0.05, 0.96, f'{self.nome_projeto} | {self.data_relatorio}', 
                fontsize=10, fontweight='bold', color=self.COR_PRIMARIA)
        fig.text(0.05, 0.93, '3. ESTATÍSTICAS DESCRITIVAS', 
                fontsize=14, fontweight='bold', color=self.COR_PRIMARIA)
        
        # Linha divisória
        fig.add_artist(mpatches.Rectangle((0.05, 0.915), 0.9, 0.01, 
                                          transform=fig.transFigure,
                                          facecolor=self.COR_PRIMARIA, 
                                          edgecolor='none'))
        
        # Criar tabela
        ax = fig.add_axes([0.05, 0.15, 0.9, 0.75])
        ax.axis('off')
        
        variaveis = self.info_dados.get('variaveis', [])
        dict_stats = self.info_dados.get('estatisticas', {})
        
        # Preparar dados
        dados_tabela = []
        header = ['Variável', 'n', 'Mín.', 'Máx.', 'Média', 'Mediana', 'DP', 'CV (%)']
        
        for var in variaveis:
            if var in dict_stats:
                s = dict_stats[var]
                linha = [
                    var,
                    f"{s.get('contagem', 0)}",
                    f"{s.get('minimo', 0):.3f}",
                    f"{s.get('maximo', 0):.3f}",
                    f"{s.get('media', 0):.3f}",
                    f"{s.get('mediana', 0):.3f}",
                    f"{s.get('desvio_padrao', 0):.3f}",
                    f"{s.get('coef_variacao', 0):.1f}",
                ]
                dados_tabela.append(linha)
        
        # Criar tabela matplotlib
        tabela = ax.table(cellText=dados_tabela, colLabels=header,
                         cellLoc='center', loc='center',
                         colWidths=[0.18, 0.10, 0.10, 0.10, 0.10, 0.10, 0.10, 0.12])
        
        tabela.auto_set_font_size(False)
        tabela.set_fontsize(9)
        tabela.scale(1, 2.2)
        
        # Formatação das células
        for i in range(len(header)):
            celula = tabela[(0, i)]
            celula.set_facecolor(self.COR_PRIMARIA)
            celula.set_text_props(weight='bold', color='white')
        
        # Alternância de cores nas linhas
        for i in range(1, len(dados_tabela) + 1):
            for j in range(len(header)):
                celula = tabela[(i, j)]
                if i % 2 == 0:
                    celula.set_facecolor(self.COR_CINZA_CLARO)
                else:
                    celula.set_facecolor('white')
                
                # Destaque para CV alto
                if j == 7 and i < len(dados_tabela) + 1:
                    try:
                        cv_val = float(dados_tabela[i-1][7].replace('%', ''))
                        if cv_val > 100:
                            celula.set_facecolor(self.COR_DESTAQUE)
                            celula.set_text_props(color='white', weight='bold')
                    except:
                        pass
        
        # Legenda
        legenda = "Nota: CV > 100% indica ALTA HETEROGENEIDADE espacial requer análise geoestatística especializada"
        fig.text(0.05, 0.10, legenda, fontsize=8, style='italic', color='#666666')
        
        # Rodapé
        fig.text(0.95, 0.02, 'Página 3', ha='right', fontsize=9, color='#999999')
        
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
        print(f"✓ Página 3 (Estatísticas): Gerada")
    
    # ========== PÁGINA 4: VISUALIZAÇÕES PRINCIPAIS ==========
    
    def _gerar_pagina_visualizacoes_principais(self, pdf: PdfPages):
        """Gera página com mapa, scatter Moran, hexbin e LISA."""
        fig = plt.figure(figsize=(11, 8.5))
        fig.patch.set_facecolor(self.COR_FUNDO)
        
        # Cabeçalho
        fig.text(0.05, 0.96, f'{self.nome_projeto} | {self.data_relatorio}', 
                fontsize=10, fontweight='bold', color=self.COR_PRIMARIA)
        fig.text(0.05, 0.93, '4. VISUALIZAÇÕES PRINCIPAIS', 
                fontsize=14, fontweight='bold', color=self.COR_PRIMARIA)
        
        # Linha divisória
        fig.add_artist(mpatches.Rectangle((0.05, 0.915), 0.9, 0.01, 
                                          transform=fig.transFigure,
                                          facecolor=self.COR_PRIMARIA, 
                                          edgecolor='none'))
        
        # Procurar imagens na pasta de saída
        pasta_mapas = Path(self.arquivo_saida).parent / "mapas"
        pasta_viz = Path(self.arquivo_saida).parent / "visualizacoes"
        
        # Mapas disponíveis
        mapa_osm = None
        mapa_densidade = None
        mapa_idw = None
        mapa_lisa = None
        
        if pasta_mapas.exists():
            arquivos_mapas = list(pasta_mapas.glob("*.png"))
            
            # Buscar mapa OSM (basemap)
            osm_files = list(pasta_mapas.glob("01_mapa_osm_*.png"))
            if osm_files:
                mapa_osm = osm_files[0]
            
            # Buscar mapa de densidade
            dens_files = list(pasta_mapas.glob("02_mapa_densidade_*.png"))
            if dens_files:
                mapa_densidade = dens_files[0]
            
            # Mapa IDW
            idw_files = list(pasta_mapas.glob("03_mapa_idw_*.png"))
            if idw_files:
                mapa_idw = idw_files[0]
        
        # Visualizações
        viz_moran = None
        if pasta_viz.exists():
            viz_files = list(pasta_viz.glob("*.png"))
            # Procurar por scatter ou qualquer visualização
            if viz_files:
                viz_moran = viz_files[0]
        
        # Grid de subplots (2x2)
        ax1 = fig.add_axes([0.05, 0.50, 0.45, 0.35])
        ax2 = fig.add_axes([0.52, 0.50, 0.45, 0.35])
        ax3 = fig.add_axes([0.05, 0.10, 0.45, 0.35])
        ax4 = fig.add_axes([0.52, 0.10, 0.45, 0.35])
        
        # Inserir mapa OSM
        if mapa_osm and mapa_osm.exists():
            try:
                from PIL import Image
                img = Image.open(mapa_osm)
                ax1.imshow(img)
                ax1.set_title('Mapa Georreferenciado (Basemap OSM)', 
                             fontsize=10, fontweight='bold', pad=10)
            except:
                ax1.text(0.5, 0.5, 'Mapa OSM\n(não disponível)',
                        ha='center', va='center', fontsize=9, 
                        color='#999999', transform=ax1.transAxes)
        else:
            ax1.text(0.5, 0.5, '[Mapa OSM]',
                    ha='center', va='center', fontsize=9, 
                    color='#CCCCCC', transform=ax1.transAxes)
        
        ax1.axis('off')
        
        # Inserir visualização de Moran/Scatter
        if viz_moran and viz_moran.exists():
            try:
                from PIL import Image
                img = Image.open(viz_moran)
                ax2.imshow(img)
                ax2.set_title("Scatter de Moran's I", 
                             fontsize=10, fontweight='bold', pad=10)
            except:
                ax2.text(0.5, 0.5, "Scatter de Moran's I\n(não disponível)",
                        ha='center', va='center', fontsize=9, 
                        color='#999999', transform=ax2.transAxes)
        else:
            ax2.text(0.5, 0.5, "[Scatter Moran's I]",
                    ha='center', va='center', fontsize=9, 
                    color='#CCCCCC', transform=ax2.transAxes)
        
        ax2.axis('off')
        
        # Inserir mapa de densidade
        if mapa_densidade and mapa_densidade.exists():
            try:
                from PIL import Image
                img = Image.open(mapa_densidade)
                ax3.imshow(img)
                ax3.set_title('Densidade Hexbin', 
                             fontsize=10, fontweight='bold', pad=10)
            except:
                ax3.text(0.5, 0.5, 'Densidade Hexbin\n(não disponível)',
                        ha='center', va='center', fontsize=9, 
                        color='#999999', transform=ax3.transAxes)
        else:
            ax3.text(0.5, 0.5, '[Densidade Hexbin]',
                    ha='center', va='center', fontsize=9, 
                    color='#CCCCCC', transform=ax3.transAxes)
        
        ax3.axis('off')
        
        # Inserir mapa IDW como clusters (ou qualquer outro mapa)
        if mapa_idw and mapa_idw.exists():
            try:
                from PIL import Image
                img = Image.open(mapa_idw)
                ax4.imshow(img)
                ax4.set_title('Interpolação IDW', 
                             fontsize=10, fontweight='bold', pad=10)
            except:
                ax4.text(0.5, 0.5, 'Interpolação\n(não disponível)',
                        ha='center', va='center', fontsize=9, 
                        color='#999999', transform=ax4.transAxes)
        else:
            ax4.text(0.5, 0.5, '[Interpolação]',
                    ha='center', va='center', fontsize=9, 
                    color='#CCCCCC', transform=ax4.transAxes)
        
        ax4.axis('off')
        
        # Rodapé
        fig.text(0.95, 0.02, 'Página 4', ha='right', fontsize=9, color='#999999')
        
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
        print(f"✓ Página 4 (Visualizações Principais): Gerada")
    
    
    # ========== PÁGINA 5: DISTRIBUIÇÕES E INTERPOLAÇÕES ==========
    
    def _gerar_pagina_distribuicoes_interpolacoes(self, pdf: PdfPages):
        """Gera página com histogramas, violin plots e mapas de interpolação."""
        fig = plt.figure(figsize=(11, 8.5))
        fig.patch.set_facecolor(self.COR_FUNDO)
        
        # Cabeçalho
        fig.text(0.05, 0.96, f'{self.nome_projeto} | {self.data_relatorio}', 
                fontsize=10, fontweight='bold', color=self.COR_PRIMARIA)
        fig.text(0.05, 0.93, '5. ANÁLISE DE DISTRIBUIÇÕES E INTERPOLAÇÕES', 
                fontsize=14, fontweight='bold', color=self.COR_PRIMARIA)
        
        # Linha divisória
        fig.add_artist(mpatches.Rectangle((0.05, 0.915), 0.9, 0.01, 
                                          transform=fig.transFigure,
                                          facecolor=self.COR_PRIMARIA, 
                                          edgecolor='none'))
        
        # Procurar imagens na pasta de saída
        pasta_mapas = Path(self.arquivo_saida).parent / "mapas"
        pasta_viz = Path(self.arquivo_saida).parent / "visualizacoes"
        
        # Imagens de visualização
        histogramas = None
        violin = None
        idw = None
        kriging = None
        gwm = None
        
        if pasta_viz.exists():
            viz_files = list(pasta_viz.glob("*.png"))
            hist_files = list(pasta_viz.glob("01_histogramas*.png"))
            violin_files = list(pasta_viz.glob("02_violin*.png"))
            
            if hist_files:
                histogramas = hist_files[0]
            if violin_files:
                violin = violin_files[0]
        
        if pasta_mapas.exists():
            # Mapas de interpolação
            idw_files = list(pasta_mapas.glob("03_mapa_idw_*.png"))
            krig_files = list(pasta_mapas.glob("04_mapa_kriging_*.png"))
            gwm_files = list(pasta_mapas.glob("05_mapa_gwm_*.png"))
            
            if idw_files:
                idw = idw_files[0]
            if krig_files:
                kriging = krig_files[0]
            if gwm_files:
                gwm = gwm_files[0]
        
        # Seção 1: Distribuições (histogramas + violin)
        fig.text(0.05, 0.88, 'Distribuições (Z-score normalizadas)', 
                fontsize=11, weight='bold', color=self.COR_SECUNDARIA)
        
        ax_hist = fig.add_axes([0.05, 0.55, 0.43, 0.30])
        ax_violin = fig.add_axes([0.52, 0.55, 0.43, 0.30])
        
        # Inserir histogramas
        if histogramas and histogramas.exists():
            try:
                from PIL import Image
                img = Image.open(histogramas)
                ax_hist.imshow(img)
                ax_hist.text(0.5, 1.05, 'Histogramas (K DE)', 
                            ha='center', fontsize=9, weight='bold',
                            transform=ax_hist.transAxes)
            except:
                ax_hist.text(0.5, 0.5, '[Histogramas]',
                            ha='center', va='center', fontsize=9, 
                            color='#CCCCCC', transform=ax_hist.transAxes)
                ax_hist.text(0.5, 1.05, 'Histogramas (K DE)', 
                            ha='center', fontsize=9, weight='bold',
                            transform=ax_hist.transAxes)
        else:
            ax_hist.text(0.5, 0.5, '[Histogramas]',
                        ha='center', va='center', fontsize=9, 
                        color='#CCCCCC', transform=ax_hist.transAxes)
            ax_hist.text(0.5, 1.05, 'Histogramas (K DE)', 
                        ha='center', fontsize=9, weight='bold',
                        transform=ax_hist.transAxes)
        
        ax_hist.axis('off')
        
        # Inserir violin plot
        if violin and violin.exists():
            try:
                from PIL import Image
                img = Image.open(violin)
                ax_violin.imshow(img)
                ax_violin.text(0.5, 1.05, 'Violin + Boxplot', 
                              ha='center', fontsize=9, weight='bold',
                              transform=ax_violin.transAxes)
            except:
                ax_violin.text(0.5, 0.5, '[Violin Plot]',
                              ha='center', va='center', fontsize=9, 
                              color='#CCCCCC', transform=ax_violin.transAxes)
                ax_violin.text(0.5, 1.05, 'Violin + Boxplot', 
                              ha='center', fontsize=9, weight='bold',
                              transform=ax_violin.transAxes)
        else:
            ax_violin.text(0.5, 0.5, '[Violin Plot]',
                          ha='center', va='center', fontsize=9, 
                          color='#CCCCCC', transform=ax_violin.transAxes)
            ax_violin.text(0.5, 1.05, 'Violin + Boxplot', 
                          ha='center', fontsize=9, weight='bold',
                          transform=ax_violin.transAxes)
        
        ax_violin.axis('off')
        
        # Seção 2: Interpolações (IDW, Kriging, GWM)
        fig.text(0.05, 0.50, 'Interpolações Geoespaciais', 
                fontsize=11, weight='bold', color=self.COR_SECUNDARIA)
        
        ax_idw = fig.add_axes([0.05, 0.25, 0.28, 0.22])
        ax_krig = fig.add_axes([0.36, 0.25, 0.28, 0.22])
        ax_gwm = fig.add_axes([0.67, 0.25, 0.28, 0.22])
        
        # IDW
        if idw and idw.exists():
            try:
                from PIL import Image
                img = Image.open(idw)
                ax_idw.imshow(img)
            except:
                ax_idw.text(0.5, 0.5, '[IDW]',
                           ha='center', va='center', fontsize=8, 
                           color='#CCCCCC', transform=ax_idw.transAxes)
        else:
            ax_idw.text(0.5, 0.5, '[IDW]',
                       ha='center', va='center', fontsize=8, 
                       color='#CCCCCC', transform=ax_idw.transAxes)
        
        ax_idw.text(0.5, 1.10, 'IDW', 
                   ha='center', fontsize=9, weight='bold',
                   transform=ax_idw.transAxes)
        ax_idw.axis('off')
        
        # Kriging Ordinária
        if kriging and kriging.exists():
            try:
                from PIL import Image
                img = Image.open(kriging)
                ax_krig.imshow(img)
            except:
                ax_krig.text(0.5, 0.5, '[Kriging]',
                            ha='center', va='center', fontsize=8, 
                            color='#CCCCCC', transform=ax_krig.transAxes)
        else:
            ax_krig.text(0.5, 0.5, '[Kriging]',
                        ha='center', va='center', fontsize=8, 
                        color='#CCCCCC', transform=ax_krig.transAxes)
        
        ax_krig.text(0.5, 1.10, 'Kriging Ordinária', 
                    ha='center', fontsize=9, weight='bold',
                    transform=ax_krig.transAxes)
        ax_krig.axis('off')
        
        # GWM
        if gwm and gwm.exists():
            try:
                from PIL import Image
                img = Image.open(gwm)
                ax_gwm.imshow(img)
            except:
                ax_gwm.text(0.5, 0.5, '[GWM]',
                           ha='center', va='center', fontsize=8, 
                           color='#CCCCCC', transform=ax_gwm.transAxes)
        else:
            ax_gwm.text(0.5, 0.5, '[GWM]',
                       ha='center', va='center', fontsize=8, 
                       color='#CCCCCC', transform=ax_gwm.transAxes)
        
        ax_gwm.text(0.5, 1.10, 'GWM', 
                   ha='center', fontsize=9, weight='bold',
                   transform=ax_gwm.transAxes)
        ax_gwm.axis('off')
        
        # Rodapé
        fig.text(0.95, 0.02, 'Página 5', ha='right', fontsize=9, color='#999999')
        
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
        print(f"✓ Página 5 (Distribuições e Interpolações): Gerada")
    
    
    # ========== PÁGINA 6: INSIGHTS E CONCLUSÕES ==========
    
    def _gerar_pagina_insights_conclusoes(self, pdf: PdfPages):
        """Gera página com insights analíticos e conclusões."""
        fig = plt.figure(figsize=(11, 8.5))
        fig.patch.set_facecolor(self.COR_FUNDO)
        
        # Cabeçalho
        fig.text(0.05, 0.96, f'{self.nome_projeto} | {self.data_relatorio}', 
                fontsize=10, fontweight='bold', color=self.COR_PRIMARIA)
        fig.text(0.05, 0.93, '6. INSIGHTS AVANÇADOS E RECOMENDAÇÕES', 
                fontsize=14, fontweight='bold', color=self.COR_PRIMARIA)
        
        # Linha divisória
        fig.add_artist(mpatches.Rectangle((0.05, 0.915), 0.9, 0.01, 
                                          transform=fig.transFigure,
                                          facecolor=self.COR_PRIMARIA, 
                                          edgecolor='none'))
        
        # Tenta extrair insights avançados
        insights_data = self.info_dados.get('insights', {})
        
        # Construir texto dinâmico baseado em insights
        insights_texto = []
        
        # Variável com estrutura espacial máxima
        var_max = insights_data.get('variavel_maxima', {})
        if var_max and var_max.get('variavel'):
            insights_texto.append("1. VARIÁVEL COM MAIOR ESTRUTURA ESPACIAL\n")
            insights_texto.append(f"   Variável: {var_max['variavel']}")
            insights_texto.append(f"   Moran's I: {var_max.get('I_moran', 'N/A'):.6f}")
            insights_texto.append(f"   p-valor: {var_max.get('p_valor', 'N/A'):.2e}")
            insights_texto.append(f"   Significância: {'SIM ✓' if var_max.get('significativo') else 'NÃO'}")
            insights_texto.append(f"   Interpretação: {var_max.get('interpretacao', 'Padrão não significativo')}\n")
        
        # Clusters significativos
        clusters = insights_data.get('clusters_significativos', {})
        if clusters and clusters.get('pontos_cluster', 0) > 0:
            insights_texto.append("2. CLUSTERS SIGNIFICATIVOS (p < 0.05)\n")
            insights_texto.append(f"   Total de pontos: {clusters.get('total_pontos', 'N/A')}")
            insights_texto.append(f"   Pontos em clusters: {clusters.get('pontos_cluster', 0)} " +
                                f"({clusters.get('percentual_cluster', 0):.1f}%)")
            insights_texto.append(f"   Quadrante dominante: {clusters.get('quadrante_dominante', 'N/A')}")
            dist = clusters.get('distribuicao', {})
            if dist:
                insights_texto.append(f"   Distribuição: HH:{dist.get('HH',0)} LL:{dist.get('LL',0)} " +
                                    f"HL:{dist.get('HL',0)} LH:{dist.get('LH',0)} NS:{dist.get('NS',0)}\n")
        
        # Heterogeneidade
        het = insights_data.get('heterogeneidade', {})
        if het:
            variaveis_het = het.get('variaveis_heterogeneas', [])
            insights_texto.append("3. HETEROGENEIDADE ESTATÍSTICA\n")
            if variaveis_het:
                insights_texto.append(f"   Variáveis com CV > 100%: {', '.join(variaveis_het)}\n")
            else:
                insights_texto.append("   Todas as variáveis têm heterogeneidade controlada (CV < 100%)\n")
        
        # Quadrantes geográficos
        quadrantes = insights_data.get('clusters_quadrantes', {})
        if quadrantes:
            insights_texto.append("4. DISTRIBUIÇÃO GEOGRÁFICA POR QUADRANTE\n")
            for quad in ['NE', 'NO', 'SE', 'SO']:
                if quad in quadrantes:
                    q = quadrantes[quad]
                    insights_texto.append(f"   {quad}: {q.get('total', 0)} pontos, " +
                                        f"{q.get('clusters', 0)} clusters ({q.get('percentual', 0):.1f}%)")
            insights_texto.append("")
        
        # Extensão geográfica
        ext = insights_data.get('extensao_geografica', {})
        if ext and ext.get('lon_min'):
            insights_texto.append("5. EXTENSÃO GEOGRÁFICA EXATA\n")
            insights_texto.append(f"   Longitude: {ext.get('lon_min', 0):.6f}° a {ext.get('lon_max', 0):.6f}°")
            insights_texto.append(f"   Latitude:  {ext.get('lat_min', 0):.6f}° a {ext.get('lat_max', 0):.6f}°")
            insights_texto.append(f"   Centro: ({ext.get('centro_lat', 0):.6f}°, {ext.get('centro_lon', 0):.6f}°)")
            insights_texto.append(f"   Dimensões: {ext.get('altura_km', 0):.2f} km × {ext.get('largura_km', 0):.2f} km\n")
        
        # Recomendações
        rec = insights_data.get('recomendacoes', {})
        if rec:
            insights_texto.append("6. RECOMENDAÇÕES TÉCNICAS\n")
            
            if rec.get('monitoramento'):
                insights_texto.append("   📌 Monitoramento:")
                for i, r in enumerate(rec['monitoramento'], 1):
                    insights_texto.append(f"      {i}. {r}")
            
            if rec.get('coleta_dados'):
                insights_texto.append("\n   📌 Coleta de Dados:")
                for i, r in enumerate(rec['coleta_dados'], 1):
                    insights_texto.append(f"      {i}. {r}")
            
            if rec.get('interpolacao'):
                insights_texto.append("\n   📌 Interpolação:")
                for i, r in enumerate(rec['interpolacao'], 1):
                    insights_texto.append(f"      {i}. {r}")
            
            if rec.get('analise_futura'):
                insights_texto.append("\n   📌 Análise Futura:")
                for i, r in enumerate(rec['analise_futura'], 1):
                    insights_texto.append(f"      {i}. {r}")
        
        # Se não houver insights avançados, exibir texto padrão
        if not insights_texto:
            insights_texto = [
                "ACHADOS PRINCIPAIS\n",
                "✓ Estatística Descritiva:",
                f"  • Foram analisadas {self.total_variaveis} variáveis numéricas",
                f"  • {self.total_amostras:,} amostras com cobertura espacial completa",
                "\n✓ Análise Espacial:",
                "  • Índice de Moran's I calculado com permutações",
                "  • Identificação de clusters locais (LISA)",
                "\n✓ Interpolação Geoespacial:",
                "  • Três métodos: IDW, Kriging Ordinária, GWM",
                "\nRECOMENDAÇÕES:\nProceda com validação cruzada dos modelos e análise \ndetalhada do variograma para interpolações mais precisas."
            ]
        
        # Exibir texto
        ax_insights = fig.add_axes([0.05, 0.05, 0.9, 0.85])
        ax_insights.axis('off')
        texto_final = "\n".join(insights_texto)
        ax_insights.text(0.02, 0.98, texto_final.strip(),
                        ha='left', va='top', fontsize=8.5,
                        family='monospace',
                        transform=ax_insights.transAxes)
        
        # Rodapé
        fig.text(0.95, 0.02, 'Página 6', ha='right', fontsize=9, color='#999999')
        
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
        print(f"✓ Página 6 (Insights e Recomendações): Gerada")
    
    # ========== MÉTODOS AUXILIARES ==========
    
    def _contar_clusters(self) -> int:
        """Conta número de pontos em clusters LISA."""
        try:
            analise = self.info_dados.get('analise_espacial', {})
            if 'clusters' in analise:
                return len([c for c in analise['clusters'] if c != 'NS'])
            return 0
        except:
            return 0
    
    # ========== MÉTODO PRINCIPAL ==========
    
    def gerar(self) -> str:
        """
        Gera o relatório PDF completo com todas as 6 páginas.
        
        Returns:
            Caminho do arquivo PDF gerado
        """
        print(f"\n{'='*60}")
        print(f"GERANDO RELATÓRIO PDF AVANÇADO")
        print(f"{'='*60}\n")
        print(f"Arquivo: {self.arquivo_saida.name}")
        print(f"Projeto: {self.nome_projeto}")
        print(f"Amostras: {self.total_amostras:,}")
        print(f"Variáveis: {self.total_variaveis}\n")
        
        try:
            with PdfPages(self.arquivo_saida) as pdf:
                self._gerar_pagina_capa(pdf)
                self._gerar_pagina_resumo_executivo(pdf)
                self._gerar_pagina_estatisticas(pdf)
                self._gerar_pagina_visualizacoes_principais(pdf)
                self._gerar_pagina_distribuicoes_interpolacoes(pdf)
                self._gerar_pagina_insights_conclusoes(pdf)
            
            print(f"\n{'='*60}")
            print(f"✅ RELATÓRIO GERADO COM SUCESSO!")
            print(f"{'='*60}")
            print(f"\n📄 Arquivo: {self.arquivo_saida}")
            print(f"📊 Páginas: 6")
            print(f"💾 Tamanho: {self.arquivo_saida.stat().st_size / (1024*1024):.2f} MB")
            
            return str(self.arquivo_saida)
            
        except Exception as erro:
            print(f"\n❌ ERRO ao gerar relatório: {str(erro)}")
            import traceback
            traceback.print_exc()
            return None
