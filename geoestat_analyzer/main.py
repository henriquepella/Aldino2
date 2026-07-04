"""
Script Principal - Análise Completa e Geração de Relatório
Executa a análise geoespacial e gera relatório PDF automaticamente
"""

import sys
from pathlib import Path
from analyzer import GeoAnalyzer
from report_generator import ReportGenerator


def find_data_file():
    """Procura por arquivo de dados na pasta 'data'"""
    data_folder = Path(__file__).parent / "data"
    
    if not data_folder.exists():
        return None
    
    # Procura por xlsx primeiro, depois csv
    xlsx_files = list(data_folder.glob("*.xlsx"))
    csv_files = list(data_folder.glob("*.csv"))
    
    if xlsx_files:
        return xlsx_files[0]
    elif csv_files:
        return csv_files[0]
    
    return None


def main():
    """Executa a pipeline completa de análise"""
    
    print("\n" + "="*70)
    print(" "*15 + "ANALISADOR GEOETATÍSTICO v1.0")
    print("="*70)
    
    # Procura pelo arquivo de dados
    data_file = find_data_file()
    
    if not data_file:
        print("\n⚠️  ERRO: Nenhum arquivo de dados encontrado!")
        print("\n📍 Instruções:")
        print("   1. Coloque seu arquivo (.xlsx ou .csv) na pasta: data/")
        print("   2. Execute novamente este script")
        print("\n" + "="*70)
        return False
    
    try:
        # Etapa 1: Análise dos dados
        print(f"\n📂 Arquivo encontrado: {data_file.name}")
        print("\n" + "-"*70)
        
        analyzer = GeoAnalyzer(str(data_file))
        analysis_info = analyzer.analyze()
        
        print("\n" + "-"*70)
        
        # Etapa 2: Geração do relatório
        print("\n📊 Gerando relatório PDF...")
        print("-"*70)
        
        report_gen = ReportGenerator(analyzer)
        report_path = report_gen.generate()
        
        # Resumo final
        print("="*70)
        print("\n✅ ANÁLISE CONCLUÍDA COM SUCESSO!")
        print(f"\n📄 Relatório salvo em:")
        print(f"   {report_path}")
        print("\n" + "="*70 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO durante a análise:")
        print(f"   {str(e)}")
        print("\n" + "="*70 + "\n")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
