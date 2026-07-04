"""
Gerador de Relatório Técnico em PDF
Cria relatórios profissionais e organizados para análise geoespacial
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle
from matplotlib.table import Table
from datetime import datetime
from pathlib import Path
import numpy as np
from analyzer import GeoAnalyzer

class ReportGenerator:
    """Gera relatórios PDF profissionais"""
    
    def __init__(self, analyzer: GeoAnalyzer, output_path: str = None):
        """
        Inicializa o gerador de relatório
        
        Args:
            analyzer: Instância de GeoAnalyzer com os dados analisados
            output_path: Caminho para salvar o PDF (padrão: reports/)
        """
        self.analyzer = analyzer
        self.df = analyzer.df
        self.data_info = analyzer.export_data_for_report()
        
        if output_path is None:
            output_path = Path(__file__).parent / "reports"
            output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_file = Path(output_path) / f"Relatorio_Geoestat_{timestamp}.pdf"
        
        # Configurações do estilo
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (11, 8.5)
        plt.rcParams['font.size'] = 10
        plt.rcParams['font.family'] = 'DejaVu Sans'
    
    def _add_title_page(self, pdf: PdfPages):
        """Cria página de título"""
        fig = plt.figure(figsize=(11, 8.5))
        fig.patch.set_facecolor('white')
        ax = fig.add_subplot(111)
        ax.axis('off')
        
        # Título
        ax.text(0.5, 0.85, 'RELATÓRIO TÉCNICO', 
                ha='center', va='top', fontsize=28, fontweight='bold',
                transform=ax.transAxes)
        
        ax.text(0.5, 0.78, 'Análise Geoestatística de Dados Espaciais', 
                ha='center', va='top', fontsize=16,
                transform=ax.transAxes, style='italic')
        
        # Linha divisória
        ax.plot([0.1, 0.9], [0.72, 0.72], transform=ax.transAxes, 
                color='#2C3E50', linewidth=2)
        
        # Informações principais
        info_y = 0.60
        info_text = f"""
SUMÁRIO EXECUTIVO

Arquivo analisado: {self.analyzer.file_path.name}
Data da análise: {datetime.now().strftime('%d de %B de %Y').replace('January', 'janeiro').replace('February', 'fevereiro').replace('March', 'março').replace('April', 'abril').replace('May', 'maio').replace('June', 'junho').replace('July', 'julho').replace('August', 'agosto').replace('September', 'setembro').replace('October', 'outubro').replace('November', 'novembro').replace('December', 'dezembro')}

Total de amostras: {self.data_info['total_samples']:,}
Dimensionalidade: {len(self.df.columns)} variáveis

Coordenadas:
   X (Easting): {self.data_info['x_col']}
   Y (Northing): {self.data_info['y_col']}

Sistema de Referência: {self.data_info['crs']}

Variáveis analisadas: {len(self.data_info['variables'])}
Conversão CRS: EPSG:4326 (WGS84) - Automatizada

CONTEÚDO DO RELATÓRIO

1. Descrição dos Dados
2. Estatísticas Descritivas (com Coeficiente de Variação)
3. Distribuição das Variáveis
4. Georreferenciamento (Coordenadas WGS84)
5. Análise Espacial
6. Conclusões e Recomendações
"""
        
        ax.text(0.08, info_y, info_text, 
                ha='left', va='top', fontsize=11, family='monospace',
                transform=ax.transAxes, bbox=dict(boxstyle='round', 
                facecolor='#ECF0F1', alpha=0.8, pad=1))
        
        # Rodapé
        ax.text(0.5, 0.05, 'Gerador Automático de Relatórios Geoestatísticos', 
                ha='center', va='bottom', fontsize=9, style='italic', color='gray',
                transform=ax.transAxes)
        
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
    
    def _add_data_description_page(self, pdf: PdfPages):
        """Cria página descrevendo os dados"""
        fig, axes = plt.subplots(2, 1, figsize=(11, 8.5))
        fig.patch.set_facecolor('white')
        
        # Título
        fig.suptitle('1. DESCRIÇÃO DOS DADOS', fontsize=14, fontweight='bold', y=0.98)
        
        # Painel 1: Informações gerais
        ax1 = axes[0]
        ax1.axis('off')
        
        info_text = f"""
INFORMAÇÕES GERAIS

Arquivo original: {self.analyzer.file_path.name}
Tipo de dados: {'Geospatial - Tabular Data'}
Total de linhas: {self.data_info['total_samples']:,}
Total de colunas: {len(self.df.columns)}
Valores ausentes (NA): {self.df.isna().sum().sum()}

COORDENADAS IDENTIFICADAS

Coluna X: '{self.data_info['x_col']}'
Coluna Y: '{self.data_info['y_col']}'

Intervalo X: [{self.df[self.data_info['x_col']].min():.2f}, {self.df[self.data_info['x_col']].max():.2f}]
Intervalo Y: [{self.df[self.data_info['y_col']].min():.2f}, {self.df[self.data_info['y_col']].max():.2f}]

SISTEMA DE REFERÊNCIA (CRS)

EPSG: {self.data_info['crs']}
Tipo: UTM (Universal Transverse Mercator)
"""
        
        ax1.text(0.05, 0.95, info_text, 
                ha='left', va='top', fontsize=10, family='monospace',
                transform=ax1.transAxes, 
                bbox=dict(boxstyle='round', facecolor='#f9f9f9', alpha=0.9, pad=1))
        
        # Painel 2: Lista de variáveis
        ax2 = axes[1]
        ax2.axis('off')
        
        var_text = "VARIÁVEIS NUMÉRICAS IDENTIFICADAS\n\n"
        for i, var in enumerate(self.data_info['variables'], 1):
            var_text += f"{i}. {var}\n"
        
        ax2.text(0.05, 0.95, var_text, 
                ha='left', va='top', fontsize=10, family='monospace',
                transform=ax2.transAxes,
                bbox=dict(boxstyle='round', facecolor='#e8f4f8', alpha=0.9, pad=1))
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
    
    def _add_statistics_page(self, pdf: PdfPages):
        """Cria página com estatísticas descritivas em tabela formatada"""
        variables = self.data_info['variables'][:6]
        stats_dict = self.data_info.get('statistics', {})
        
        fig = plt.figure(figsize=(11, 8.5))
        fig.patch.set_facecolor('white')
        
        fig.suptitle('2. ESTATÍSTICAS DESCRITIVAS', fontsize=14, fontweight='bold', y=0.98)
        
        ax = fig.add_subplot(111)
        ax.axis('off')
        
        # Prepara dados para a tabela
        table_data = []
        header = ['Variável', 'Contagem', 'Mínimo', 'Máximo', 'Média', 'Mediana', 
                  'Desvio Padrão', 'CV (%)']
        table_data.append(header)
        
        # Cores para destaque
        cell_colors = [['#2C3E50'] * len(header)]  # Header color
        
        for var in variables:
            if var in stats_dict:
                s = stats_dict[var]
                cv = s['coef_variacao']
                alta_hetero = s['alta_heterogeneidade']
                
                row = [
                    var,
                    f"{s['contagem']}",
                    f"{s['minimo']:.4f}",
                    f"{s['maximo']:.4f}",
                    f"{s['media']:.4f}",
                    f"{s['mediana']:.4f}",
                    f"{s['desvio_padrao']:.4f}",
                    f"{cv:.2f}{'*' if alta_hetero else ''}",
                ]
                table_data.append(row)
                
                # Cor para destaque: vermelho claro para CV > 100%
                if alta_hetero:
                    row_colors = ['#FFE6E6'] * len(header)
                    row_colors[0] = '#FF6B6B'  # Nome em vermelho mais escuro
                else:
                    row_colors = ['#F9F9F9'] * len(header)
                    row_colors[0] = '#E8F4F8'  # Nome em azul claro
                
                cell_colors.append(row_colors)
        
        # Cria a tabela
        table = ax.table(cellText=table_data, cellLoc='right', loc='center',
                        colWidths=[0.18, 0.10, 0.12, 0.12, 0.12, 0.12, 0.12, 0.12])
        
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 2.2)
        
        # Aplica cores e formatação
        for i, row in enumerate(table_data):
            for j in range(len(row)):
                cell = table[(i, j)]
                cell.set_facecolor(cell_colors[i][j])
                
                if i == 0:  # Header
                    cell.set_text_props(weight='bold', color='white')
                    cell.set_facecolor('#2C3E50')
                else:
                    cell.set_text_props(weight='bold' if j == 0 else 'normal')
                    cell.set_edgecolor('#CCCCCC')
        
        # Adiciona legenda
        legend_y = 0.15
        legend_text = """
NOTAS TÉCNICAS

• Contagem: Número de observações válidas
• CV (%): Coeficiente de Variação = (Desvio Padrão / Média) × 100
• (*): Variáveis com CV > 100% indicam ALTA HETEROGENEIDADE espacial
• Essas variáveis podem requer análise geoestatística mais detalhada

INTERPRETAÇÃO DO CV:
  ─ CV < 15%  : Baixa variabilidade
  ─ CV 15-30% : Variabilidade moderada
  ─ CV 30-100%: Alta variabilidade
  ─ CV > 100% : Muito alta variabilidade (heterogeneidade extrema)
"""
        
        ax.text(0.05, legend_y, legend_text, 
               ha='left', va='top', fontsize=9, family='monospace',
               transform=ax.transAxes,
               bbox=dict(boxstyle='round', facecolor='#FFF9E6', alpha=0.8, pad=1))
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
    
    def _add_visualization_page(self, pdf: PdfPages):
        """Cria página com visualizações"""
        variables = self.data_info['variables'][:4]
        
        fig, axes = plt.subplots(2, 2, figsize=(11, 8.5))
        fig.patch.set_facecolor('white')
        fig.suptitle('3. DISTRIBUIÇÃO DAS VARIÁVEIS', fontsize=14, fontweight='bold')
        
        axes = axes.flatten()
        
        for idx, var in enumerate(variables):
            if idx < len(axes) and var in self.df.columns:
                ax = axes[idx]
                data = self.df[var].dropna()
                
                ax.hist(data, bins=30, color='#3498db', alpha=0.7, edgecolor='black')
                ax.set_title(f'{var}', fontweight='bold')
                ax.set_xlabel('Valor')
                ax.set_ylabel('Frequência')
                ax.grid(True, alpha=0.3)
        
        # Hide unused subplots
        for idx in range(len(variables), len(axes)):
            axes[idx].axis('off')
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
    
    def _add_georeferencing_page(self, pdf: PdfPages):
        """Cria página com informações de georreferenciamento e coordenadas WGS84"""
        fig = plt.figure(figsize=(11, 8.5))
        fig.patch.set_facecolor('white')
        ax = fig.add_subplot(111)
        ax.axis('off')
        
        fig.suptitle('3.5 GEORREFERENCIAMENTO', fontsize=14, fontweight='bold', y=0.98)
        
        x_col = self.data_info['x_col']
        y_col = self.data_info['y_col']
        crs_orig = self.data_info.get('crs', 'EPSG:32733')
        
        wgs84_info = self.data_info.get('coordenadas_wgs84', {})
        
        if wgs84_info:
            centro = wgs84_info.get('centro', {})
            lon_stats = wgs84_info.get('longitude', {})
            lat_stats = wgs84_info.get('latitude', {})
            
            geo_text = f"""
SISTEMAS DE REFERÊNCIA UTILIZADOS

Sistema de Entrada (CRS Origem):
  Código EPSG:           {crs_orig}
  Tipo:                  UTM (Universal Transverse Mercator)
  Coluna X:              {x_col} (Easting)
  Coluna Y:              {y_col} (Northing)

Sistema de Destino (Conversão):
  Código EPSG:           EPSG:4326 (WGS84)
  Tipo:                  Graus Decimais (Lat/Lon)
  Padrão Global:         Sim (compatível com Google Maps, OSM, etc.)

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
  
  Formato para Google Maps/OSM:
  {centro.get('latitude', 0):.8f}, {centro.get('longitude', 0):.8f}

OBSERVAÇÕES

✓ As coordenadas foram automaticamente convertidas para WGS84
✓ Este formato é compatível com ferramentas de georreferenciamento global
✓ Os valores estão em graus decimais (não em graus, minutos e segundos)
✓ Latitude positiva = Norte; Latitude negativa = Sul
✓ Longitude positiva = Leste; Longitude negativa = Oeste
"""
            
            ax.text(0.05, 0.95, geo_text, 
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
    
    def _add_spatial_page(self, pdf: PdfPages):
        """Cria página com visualização espacial"""
        x_col = self.data_info['x_col']
        y_col = self.data_info['y_col']
        
        fig, axes = plt.subplots(1, 2, figsize=(11, 8.5))
        fig.patch.set_facecolor('white')
        fig.suptitle('4. ANÁLISE ESPACIAL', fontsize=14, fontweight='bold')
        
        # Mapa de localização dos pontos
        ax1 = axes[0]
        scatter = ax1.scatter(self.df[x_col], self.df[y_col], 
                             c='#e74c3c', alpha=0.5, s=30, edgecolors='darkred')
        ax1.set_xlabel(f'X ({x_col})')
        ax1.set_ylabel(f'Y ({y_col})')
        ax1.set_title('Localização dos Pontos Amostrados')
        ax1.grid(True, alpha=0.3)
        
        # Densidade espacial
        ax2 = axes[1]
        if len(self.data_info['variables']) > 0:
            var = self.data_info['variables'][0]
            scatter2 = ax2.scatter(self.df[x_col], self.df[y_col], 
                                  c=self.df[var], cmap='viridis', 
                                  alpha=0.6, s=30, edgecolors='black', linewidth=0.5)
            ax2.set_xlabel(f'X ({x_col})')
            ax2.set_ylabel(f'Y ({y_col})')
            ax2.set_title(f'Distribuição Espacial: {var}')
            plt.colorbar(scatter2, ax=ax2, label=var)
            ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
    
    def _add_conclusion_page(self, pdf: PdfPages):
        """Cria página de conclusão"""
        fig = plt.figure(figsize=(11, 8.5))
        fig.patch.set_facecolor('white')
        ax = fig.add_subplot(111)
        ax.axis('off')
        
        conclusion_text = f"""
5. CONCLUSÕES E RECOMENDAÇÕES

RESUMO DA ANÁLISE

Este relatório apresenta uma análise geoestatística automática de dados espaciais. 
Os dados foram processados e os seguintes padrões foram identificados:

• Total de {self.data_info['total_samples']:,} amostras processadas
• {len(self.data_info['variables'])} variáveis numéricas analisadas
• Coordenadas detectadas em sistema UTM (EPSG:{self.data_info['crs'].split(':')[1]})
• Cobertura espacial definida pelos limites das coordenadas X e Y

PRÓXIMOS PASSOS RECOMENDADOS

1. Validação dos dados: Verificar outliers e valores ausentes
2. Análise de autocorrelação espacial: Realizar testes de Moran's I
3. Modelagem: Ajuste de variogramas e kriging ordinário
4. Validação cruzada: Comparação de predições com valores observados
5. Mapeamento: Geração de mapas de predição e incerteza

NOTAS TÉCNICAS

CRS utilizado: {self.data_info['crs']}
Data do relatório: {datetime.now().strftime('%d/%m/%Y às %H:%M')}
Método de análise: Automático com detecção de padrões

Este é um relatório preliminar gerado automaticamente. Análises mais aprofundadas
e validações adicionais são recomendadas para aplicações críticas.
"""
        
        ax.text(0.08, 0.95, conclusion_text, 
               ha='left', va='top', fontsize=10,
               transform=ax.transAxes,
               bbox=dict(boxstyle='round', facecolor='#ecf0f1', alpha=0.8, pad=1.5))
        
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
    
    def generate(self) -> Path:
        """
        Gera o relatório PDF completo
        
        Returns:
            Caminho do arquivo PDF gerado
        """
        print(f"\n📄 Gerando relatório PDF...")
        print(f"   Arquivo de saída: {self.output_file}")
        
        with PdfPages(self.output_file) as pdf:
            print("   ✓ Página de título")
            self._add_title_page(pdf)
            
            print("   ✓ Descrição dos dados")
            self._add_data_description_page(pdf)
            
            print("   ✓ Estatísticas descritivas")
            self._add_statistics_page(pdf)
            
            print("   ✓ Visualizações")
            self._add_visualization_page(pdf)
            
            print("   ✓ Georreferenciamento")
            self._add_georeferencing_page(pdf)
            
            print("   ✓ Análise espacial")
            self._add_spatial_page(pdf)
            
            print("   ✓ Conclusões")
            self._add_conclusion_page(pdf)
        
        print(f"\n✅ Relatório gerado com sucesso!\n   {self.output_file}\n")
        return self.output_file


def main():
    """Exemplo de uso completo"""
    # Procura por arquivos na pasta data
    data_folder = Path(__file__).parent / "data"
    data_files = list(data_folder.glob("*.xlsx")) + list(data_folder.glob("*.csv"))
    
    if not data_files:
        print("⚠ Nenhum arquivo encontrado em 'data/'")
        return
    
    # Analisa e gera relatório
    file_path = data_files[0]
    analyzer = GeoAnalyzer(str(file_path))
    analyzer.analyze()
    
    report_gen = ReportGenerator(analyzer)
    report_path = report_gen.generate()
    
    return report_path


if __name__ == "__main__":
    main()
