#!/usr/bin/env python3
"""
🚀 GUIA RÁPIDO DE STARTUP
Execute este arquivo para instruções passo-a-passo
"""

import sys
from pathlib import Path

def show_instructions():
    print("\n" + "="*75)
    print(" "*20 + "⚙️  GUIA DE CONFIGURAÇÃO INICIAL")
    print("="*75 + "\n")
    
    print("📋 PASSO 1: Instalar Dependências")
    print("-" * 75)
    print("Execute no terminal dentro da pasta 'geoestat_analyzer':\n")
    print("   pip install -r requirements.txt\n")
    
    print("📋 PASSO 2: Preparar Dados")
    print("-" * 75)
    print("Opção A - Usar arquivo real:")
    print("   1. Coloque seu arquivo (.xlsx ou .csv) na pasta: data/")
    print("   2. O arquivo deve ter colunas: X, Y ou Longitude, Latitude")
    print("   3. Uma ou mais variáveis numéricas\n")
    
    print("Opção B - Testar com dados de exemplo:")
    print("   Execute: python create_sample_data.py")
    print("   Isso criará um arquivo de exemplo em data/\n")
    
    print("📋 PASSO 3: Executar Análise")
    print("-" * 75)
    print("Execute no terminal:\n")
    print("   python main.py\n")
    print("O sistema irá:")
    print("   ✓ Carregar o arquivo de dados")
    print("   ✓ Detectar coordenadas e variáveis")
    print("   ✓ Calcular estatísticas descritivas")
    print("   ✓ Gerar visualizações")
    print("   ✓ Criar relatório PDF profissional\n")
    
    print("📋 PASSO 4: Acessar Resultado")
    print("-" * 75)
    print("O relatório PDF será salvo em:")
    print("   geoestat_analyzer/reports/Relatorio_Geoestat_YYYYMMDD_HHMMSS.pdf\n")
    
    print("="*75 + "\n")
    
    print("💡 DICAS ÚTEIS\n")
    print("• Se as colunas não forem detectadas, renomeie para padrões conhecidos:")
    print("  X, Y, Longitude, Latitude, Easting, Northing\n")
    print("• Para alterar o CRS padrão, edite analyzer.py linha 22")
    print("• Máximo de 6 variáveis são analisadas automaticamente")
    print("• Mínimo recomendado: 10 amostras\n")
    
    print("📚 ESTRUTURA DO PROJETO\n")
    print("geoestat_analyzer/")
    print("├── data/                   ← Coloque arquivos aqui")
    print("├── reports/                ← Relatórios gerados")
    print("├── analyzer.py             ← Módulo de análise")
    print("├── report_generator.py     ← Gerador de relatórios")
    print("├── main.py                 ← Script principal")
    print("├── create_sample_data.py   ← Criar dados de exemplo")
    print("├── requirements.txt        ← Dependências Python")
    print("└── README.md               ← Documentação completa\n")
    
    print("="*75)
    print("\n✅ Sistema pronto! Siga os passos acima para começar.\n")


if __name__ == "__main__":
    show_instructions()
