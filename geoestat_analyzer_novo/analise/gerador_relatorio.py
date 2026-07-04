# ============================================================================
# MÓDULO GERADOR DE RELATÓRIO EM PDF
# ============================================================================
# Responsável por:
#   - Gerar relatórios PDF profissionais
#   - Criar tabelas formatadas com alinhamento numérico
#   - Destacar variáveis com alta heterogeneidade (CV > 100%)
#   - Incluir análises espaciais e georreferenciamento
# ============================================================================

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime
from pathlib import Path
import numpy as np
from .analisador import AnalisadorGeo


class GeradorRelatorio:
    """
    Gera relatórios PDF profissionais para análise geoestatística.
    
    Cria tabelas formatadas, visualizações e análises espaciais
    em um documento PDF estruturado e visualmente agradável.
    """
    
    def __init__(self, analisador: AnalisadorGeo, caminho_saida: str = None):
        """
        Inicializa o gerador de relatório.
        
        Args:
            analisador: Instância de AnalisadorGeo com dados analisados
            caminho_saida: Caminho para salvar o PDF (padrão: pasta saida/)
        """
        self.analisador = analisador
        self.df = analisador.df
        self.info_dados = analisador.exportar_dados_relatorio()
        
        # Define caminho de saída
        if caminho_saida is None:
            caminho_saida = Path(__file__).parent.parent / "dados" / "saida"
            caminho_saida.mkdir(exist_ok=True)
        
        # Nome do arquivo com timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.arquivo_saida = Path(caminho_saida) / f"Relatorio_Geoestat_{timestamp}.pdf"
        
        # Configurações de estilo matplotlib
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (11, 8.5)
        plt.rcParams['font.size'] = 10
    
    def _adicionar_pagina_titulo(self, pdf: PdfPages):
        """Cria página de título com sumário executivo."""
        fig = plt.figure(figsize=(11, 8.5))
        fig.patch.set_facecolor('white')
        ax = fig.add_subplot(111)
        ax.axis('off')
        
        # Título principal
        ax.text(0.5, 0.85, 'RELATÓRIO TÉCNICO', 
                ha='center', va='top', fontsize=28, fontweight='bold',
                transform=ax.transAxes)
        
        # Subtítulo
        ax.text(0.5, 0.78, 'Análise Geoestatística de Dados Espaciais', 
                ha='center', va='top', fontsize=16,
                transform=ax.transAxes, style='italic')
        
        # Linha divisória
        ax.plot([0.1, 0.9], [0.72, 0.72], transform=ax.transAxes, 
                color='#2C3E50', linewidth=2)
        
        # Conteúdo principal
        info_y = 0.60
        texto_info = f"""
SUMÁRIO EXECUTIVO

Arquivo analisado: {self.analisador.caminho_arquivo.name}
Data da análise: {datetime.now().strftime('%d/%m/%Y às %H:%M')}

Total de amostras: {self.info_dados['total_amostras']:,}
Total de colunas: {len(self.df.columns)}

Coordenadas identificadas:
   X (Easting): {self.info_dados['col_x']}
   Y (Northing): {self.info_dados['col_y']}

Sistema de Referência: {self.info_dados['crs']}

Variáveis analisadas: {len(self.info_dados['variaveis'])}
Conversão CRS: EPSG:4326 (WGS84) ✓ Automatizada
"""
        
        ax.text(0.08, info_y, texto_info, 
                ha='left', va='top', fontsize=10, family='monospace',
                transform=ax.transAxes, bbox=dict(boxstyle='round', 
                facecolor='#ECF0F1', alpha=0.8, pad=1))
        
        # Rodapé
        ax.text(0.5, 0.05, 'Gerador Automático de Relatórios Geoestatísticos v2.0', 
                ha='center', va='bottom', fontsize=9, style='italic', color='gray',
                transform=ax.transAxes)
        
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
    
    def _adicionar_pagina_descricao(self, pdf: PdfPages):
        """Cria página com descrição dos dados e variáveis."""
        fig, eixos = plt.subplots(2, 1, figsize=(11, 8.5))
        fig.patch.set_facecolor('white')
        fig.suptitle('1. DESCRIÇÃO DOS DADOS', fontsize=14, fontweight='bold', y=0.98)
        
        # Painel 1: Informações gerais
        ax1 = eixos[0]
        ax1.axis('off')
        
        texto_info = f"""
INFORMAÇÕES GERAIS DO DATASET

Arquivo original: {self.analisador.caminho_arquivo.name}
Total de linhas: {self.info_dados['total_amostras']:,}
Total de colunas: {len(self.df.columns)}
Valores ausentes (NA): {self.df.isna().sum().sum()}

COORDENADAS ESPACIAIS

Coluna X: '{self.info_dados['col_x']}' (Easting)
Coluna Y: '{self.info_dados['col_y']}' (Northing)

Intervalo X: [{self.df[self.info_dados['col_x']].min():.2f}, {self.df[self.info_dados['col_x']].max():.2f}]
Intervalo Y: [{self.df[self.info_dados['col_y']].min():.2f}, {self.df[self.info_dados['col_y']].max():.2f}]

SISTEMA DE REFERÊNCIA (CRS)

EPSG: {self.info_dados['crs']}
Tipo: UTM (Universal Transverse Mercator)
Zona: 23 Sul (Brasil Padrão)
"""
        
        ax1.text(0.05, 0.95, texto_info, 
                ha='left', va='top', fontsize=10, family='monospace',
                transform=ax1.transAxes, 
                bbox=dict(boxstyle='round', facecolor='#f9f9f9', alpha=0.9, pad=1))
        
        # Painel 2: Lista de variáveis
        ax2 = eixos[1]
        ax2.axis('off')
        
        texto_vars = "VARIÁVEIS NUMÉRICAS IDENTIFICADAS\n\n"
        for idx, variavel in enumerate(self.info_dados['variaveis'], 1):
            texto_vars += f"{idx}. {variavel}\n"
        
        ax2.text(0.05, 0.95, texto_vars, 
                ha='left', va='top', fontsize=10, family='monospace',
                transform=ax2.transAxes,
                bbox=dict(boxstyle='round', facecolor='#e8f4f8', alpha=0.9, pad=1))
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
    
    def _adicionar_pagina_estatisticas(self, pdf: PdfPages):
        """
        Cria página com estatísticas descritivas em tabela formatada.
        
        Destaca variáveis com CV > 100% em cores vermelhas.
        """
        variaveis = self.info_dados['variaveis'][:6]
        dict_stats = self.info_dados.get('estatisticas', {})
        
        fig = plt.figure(figsize=(11, 8.5))
        fig.patch.set_facecolor('white')
        
        fig.suptitle('2. ESTATÍSTICAS DESCRITIVAS', fontsize=14, fontweight='bold', y=0.98)
        
        ax = fig.add_subplot(111)
        ax.axis('off')
        
        # Prepara dados para a tabela
        dados_tabela = []
        header = ['Variável', 'Contagem', 'Mínimo', 'Máximo', 'Média', 'Mediana', 
                  'Desvio Padrão', 'CV (%)']
        dados_tabela.append(header)
        
        # Cores para destaque
        cores_celulas = [['#2C3E50'] * len(header)]  # Cor do header
        
        for variavel in variaveis:
            if variavel in dict_stats:
                s = dict_stats[variavel]
                cv = s['coef_variacao']
                alta_hetero = s['alta_heterogeneidade']
                
                # Formata linha de dados
                linha = [
                    variavel,
                    f"{s['contagem']}",
                    f"{s['minimo']:.4f}",
                    f"{s['maximo']:.4f}",
                    f"{s['media']:.4f}",
                    f"{s['mediana']:.4f}",
                    f"{s['desvio_padrao']:.4f}",
                    f"{cv:.2f}{'*' if alta_hetero else ''}",
                ]
                dados_tabela.append(linha)
                
                # Define cores: vermelho claro para CV > 100%
                if alta_hetero:
                    cores_linha = ['#FFE6E6'] * len(header)
                    cores_linha[0] = '#FF6B6B'  # Nome em vermelho mais escuro
                else:
                    cores_linha = ['#F9F9F9'] * len(header)
                    cores_linha[0] = '#E8F4F8'  # Nome em azul claro
                
                cores_celulas.append(cores_linha)
        
        # Cria tabela matplotlib
        tabela = ax.table(cellText=dados_tabela, cellLoc='right', loc='center',
                         colWidths=[0.18, 0.10, 0.12, 0.12, 0.12, 0.12, 0.12, 0.12])
        
        tabela.auto_set_font_size(False)
        tabela.set_fontsize(9)
        tabela.scale(1, 2.2)
        
        # Aplica cores e formatação a cada célula
        for i, linha in enumerate(dados_tabela):
            for j in range(len(linha)):
                celula = tabela[(i, j)]
                celula.set_facecolor(cores_celulas[i][j])
                
                if i == 0:  # Header
                    celula.set_text_props(weight='bold', color='white')
                    celula.set_facecolor('#2C3E50')
                else:
                    celula.set_text_props(weight='bold' if j == 0 else 'normal')
                    celula.set_edgecolor('#CCCCCC')
        
        # Adiciona legenda explicativa
        legenda_y = 0.15
        texto_legenda = """
NOTAS TÉCNICAS

• CV (%): Coeficiente de Variação = (Desvio Padrão / Média) × 100
• (*): Variáveis com CV > 100% indicam ALTA HETEROGENEIDADE espacial
• Essas variáveis requerem análise geoestatística especializada

INTERPRETAÇÃO DO CV:
  • CV < 15%  : Baixa variabilidade (normal)
  • CV 15-30% : Variabilidade moderada
  • CV 30-100%: Alta variabilidade
  • CV > 100% : Muito alta variabilidade (heterogeneidade extrema) ⚠️
"""
        
        ax.text(0.05, legenda_y, texto_legenda, 
               ha='left', va='top', fontsize=9, family='monospace',
               transform=ax.transAxes,
               bbox=dict(boxstyle='round', facecolor='#FFF9E6', alpha=0.8, pad=1))
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
    
    def _adicionar_pagina_visualizacao(self, pdf: PdfPages):
        """Cria página com visualizações (histogramas) das variáveis."""
        variaveis = self.info_dados['variaveis'][:4]
        
        fig, eixos = plt.subplots(2, 2, figsize=(11, 8.5))
        fig.patch.set_facecolor('white')
        fig.suptitle('3. DISTRIBUIÇÃO DAS VARIÁVEIS', fontsize=14, fontweight='bold')
        
        eixos = eixos.flatten()
        
        # Cria um histograma para cada variável
        for idx, variavel in enumerate(variaveis):
            if idx < len(eixos) and variavel in self.df.columns:
                ax = eixos[idx]
                dados = self.df[variavel].dropna()
                
                ax.hist(dados, bins=30, color='#3498db', alpha=0.7, edgecolor='black')
                ax.set_title(f'{variavel}', fontweight='bold')
                ax.set_xlabel('Valor')
                ax.set_ylabel('Frequência')
                ax.grid(True, alpha=0.3)
        
        # Ocuta subplots não utilizados
        for idx in range(len(variaveis), len(eixos)):
            eixos[idx].axis('off')
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
    
    def _adicionar_pagina_georreferenciamento(self, pdf: PdfPages):
        """
        Cria página com informações de georreferenciamento.
        
        Mostra coordenadas convertidas para WGS84 e centro aprox.
        """
        fig = plt.figure(figsize=(11, 8.5))
        fig.patch.set_facecolor('white')
        ax = fig.add_subplot(111)
        ax.axis('off')
        
        fig.suptitle('4. GEORREFERENCIAMENTO', fontsize=14, fontweight='bold', y=0.98)
        
        col_x = self.info_dados['col_x']
        col_y = self.info_dados['col_y']
        crs_original = self.info_dados.get('crs', 'EPSG:32733')
        
        info_wgs84 = self.info_dados.get('coordenadas_wgs84', {})
        
        if info_wgs84:
            centro = info_wgs84.get('centro', {})
            lon_stats = info_wgs84.get('longitude', {})
            lat_stats = info_wgs84.get('latitude', {})
            
            texto_geo = f"""
SISTEMAS DE REFERÊNCIA UTILIZADOS

Sistema de Entrada (CRS Origem):
  Código EPSG:           {crs_original}
  Tipo:                  UTM (Universal Transverse Mercator)
  Coluna X:              {col_x} (Easting)
  Coluna Y:              {col_y} (Northing)

Sistema de Destino (Conversão):
  Código EPSG:           EPSG:4326 (WGS84)
  Tipo:                  Graus Decimais (Latitude/Longitude)
  Padrão Global:         Sim (compatível com Google Maps, OSM)

ESTATÍSTICAS DAS COORDENADAS CONVERTIDAS

Longitude (graus decimais - Leste/Oeste):
  Mínimo:                {lon_stats.get('minimo', 0):.8f}°
  Máximo:                {lon_stats.get('maximo', 0):.8f}°
  Média:                 {lon_stats.get('media', 0):.8f}°

Latitude (graus decimais - Norte/Sul):
  Mínimo:                {lat_stats.get('minimo', 0):.8f}°
  Máximo:                {lat_stats.get('maximo', 0):.8f}°
  Média:                 {lat_stats.get('media', 0):.8f}°

CENTRO APROXIMADO DE ÁREA DE ESTUDO

  Latitude:              {centro.get('latitude', 0):.8f}°
  Longitude:             {centro.get('longitude', 0):.8f}°
  
  Para Google Maps/OSM (copie):
  {centro.get('latitude', 0):.8f}, {centro.get('longitude', 0):.8f}

OBSERVAÇÕES TÉCNICAS

✓ Coordenadas convertidas automaticamente para WGS84
✓ Formato compatível com todas as ferramentas geoespaciais
✓ Valores em graus decimais (não em DMS)
✓ Latitude positiva = Norte | Latitude negativa = Sul
✓ Longitude positiva = Leste | Longitude negativa = Oeste
"""
            
            ax.text(0.05, 0.95, texto_geo, 
                   ha='left', va='top', fontsize=9, family='monospace',
                   transform=ax.transAxes,
                   bbox=dict(boxstyle='round', facecolor='#E8F8F5', alpha=0.9, pad=1))
        else:
            ax.text(0.05, 0.95, "⚠ Informações de georreferenciamento não disponíveis", 
                   ha='left', va='top', fontsize=11, style='italic',
                   transform=ax.transAxes)
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
    
    def _adicionar_pagina_analise_espacial(self, pdf: PdfPages):
        """Cria página com visualización espacial dos dados (mapas de pontos)."""
        col_x = self.info_dados['col_x']
        col_y = self.info_dados['col_y']
        
        fig, eixos = plt.subplots(1, 2, figsize=(11, 8.5))
        fig.patch.set_facecolor('white')
        fig.suptitle('5. ANÁLISE ESPACIAL', fontsize=14, fontweight='bold')
        
        # Mapa de localização dos pontos
        ax1 = eixos[0]
        ax1.scatter(self.df[col_x], self.df[col_y], 
                   c='#e74c3c', alpha=0.5, s=30, edgecolors='darkred')
        ax1.set_xlabel(f'X ({col_x})')
        ax1.set_ylabel(f'Y ({col_y})')
        ax1.set_title('Localização dos Pontos Amostrados')
        ax1.grid(True, alpha=0.3)
        
        # Densidade espacial com coloração
        ax2 = eixos[1]
        if len(self.info_dados['variaveis']) > 0:
            variavel = self.info_dados['variaveis'][0]
            scatter2 = ax2.scatter(self.df[col_x], self.df[col_y], 
                                  c=self.df[variavel], cmap='viridis', 
                                  alpha=0.6, s=30, edgecolors='black', linewidth=0.5)
            ax2.set_xlabel(f'X ({col_x})')
            ax2.set_ylabel(f'Y ({col_y})')
            ax2.set_title(f'Distribuição Espacial: {variavel}')
            plt.colorbar(scatter2, ax=ax2, label=variavel)
            ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
    
    def _adicionar_pagina_conclusoes(self, pdf: PdfPages):
        """Cria página final com conclusões e recomendações."""
        fig = plt.figure(figsize=(11, 8.5))
        fig.patch.set_facecolor('white')
        ax = fig.add_subplot(111)
        ax.axis('off')
        
        texto_conclusao = f"""
6. CONCLUSÕES E RECOMENDAÇÕES

RESUMO DA ANÁLISE

Este relatório apresenta uma análise geoestatística automática de dados espaciais. 
Os dados foram processados e os seguintes padrões foram identificados:

• Total de {self.info_dados['total_amostras']:,} amostras processadas
• {len(self.info_dados['variaveis'])} variáveis numéricas analisadas
• Coordenadas detectadas em sistema UTM (EPSG:{self.info_dados['crs'].split(':')[1]})
• Cobertura espacial definida pelos limites das coordenadas X e Y

PRÓXIMOS PASSOS RECOMENDADOS

1. Validação dos dados: Verificar outliers e valores ausentes
2. Análise de autocorrelação espacial: Realizar testes de Moran's I
3. Modelagem: Ajuste de variogramas e kriging ordinário
4. Validação cruzada: Comparação de predições com valores observados
5. Mapeamento: Geração de mapas de predição e incerteza

CONSIDERAÇÕES SOBRE HETEROGENEIDADE

Variáveis com CV > 100%:
→ Indicam heterogeneidade extrema
→ Requerem análise geoestatística especializada
→ Considere kriging indicador ou análise por domínios geológicos

NOTAS TÉCNICAS

CRS utilizado: {self.info_dados['crs']}
Data do relatório: {datetime.now().strftime('%d/%m/%Y às %H:%M')}
Método de análise: Automático com detecção de padrões
Coordenadas convertidas para: EPSG:4326 (WGS84)

Este é um relatório preliminar gerado automaticamente. Análises mais aprofundadas
e validações adicionais são recomendadas para aplicações críticas.
"""
        
        ax.text(0.08, 0.95, texto_conclusao, 
               ha='left', va='top', fontsize=10,
               transform=ax.transAxes,
               bbox=dict(boxstyle='round', facecolor='#ecf0f1', alpha=0.8, pad=1.5))
        
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
    
    def gerar(self) -> Path:
        """
        Gera o relatório PDF completo com todas as páginas.
        
        Returns:
            Caminho do arquivo PDF gerado
        """
        print(f"\n📄 Gerando relatório PDF...")
        print(f"   Arquivo de saída: {self.arquivo_saida}")
        
        with PdfPages(self.arquivo_saida) as pdf:
            print("   ✓ Página de título")
            self._adicionar_pagina_titulo(pdf)
            
            print("   ✓ Descrição dos dados")
            self._adicionar_pagina_descricao(pdf)
            
            print("   ✓ Estatísticas descritivas")
            self._adicionar_pagina_estatisticas(pdf)
            
            print("   ✓ Visualizações")
            self._adicionar_pagina_visualizacao(pdf)
            
            print("   ✓ Georreferenciamento")
            self._adicionar_pagina_georreferenciamento(pdf)
            
            print("   ✓ Análise espacial")
            self._adicionar_pagina_analise_espacial(pdf)
            
            print("   ✓ Conclusões")
            self._adicionar_pagina_conclusoes(pdf)
        
        print(f"\n✅ Relatório gerado com sucesso!\n   {self.arquivo_saida}\n")
        return self.arquivo_saida


def main():
    """Função de exemplo de uso do gerador de relatório."""
    # Procura por arquivos na pasta entrada
    pasta_entrada = Path(__file__).parent.parent / "dados" / "entrada"
    arquivos_dados = list(pasta_entrada.glob("*.xlsx")) + list(pasta_entrada.glob("*.csv"))
    
    if not arquivos_dados:
        print("⚠ Nenhum arquivo encontrado em dados/entrada/")
        return
    
    # Analisa e gera relatório
    caminho_arquivo = arquivos_dados[0]
    analisador = AnalisadorGeo(str(caminho_arquivo))
    analisador.analisar()
    
    gerador = GeradorRelatorio(analisador)
    caminho_relatorio = gerador.gerar()
    
    return caminho_relatorio


if __name__ == "__main__":
    main()
