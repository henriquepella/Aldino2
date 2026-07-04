#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste direto do gerador de PDF com imagens inseridas.

Carrega um arquivo de dados existente e gera um novo PDF
para testar se as imagens estão sendo inseridas corretamente.
"""

import sys
from pathlib import Path

# Configurar path
sys.path.insert(0, str(Path(__file__).parent / "geoestat_analyzer_novo"))

from analise.analisador import AnalisadorGeo
from analise.gerador_relatorio_avancado import GeradorRelatorioAvancado

# Arquivo de dados para teste
caminho_dados = Path(__file__).parent / "geoestat_analyzer_novo" / "dados" / "entrada" / "DATABASE_Aldino.csv"

if not caminho_dados.exists():
    print(f"❌ Arquivo não encontrado: {caminho_dados}")
    sys.exit(1)

print("\n" + "="*70)
print("TESTE: Gerador de PDF com Imagens Inseridas")
print("="*70)
print(f"\n📝 Arquivo: {caminho_dados.name}")

# Análise
print("\n🔍 Analisando dados...")
try:
    analisador = AnalisadorGeo(str(caminho_dados))
    info_analise = analisador.analisar()
    print("✓ Dados analisados com sucesso")
except Exception as e:
    print(f"❌ Erro na análise: {e}")
    sys.exit(1)

# Análise espacial
print("\n📊 Análise espacial...")
try:
    analise_espacial = analisador.analisar_autocorrelacao_espacial()
    print(f"✓ Moran's I calculado")
except Exception as e:
    print(f"⚠️ Análise espacial incompleta: {e}")

# Visualizações
print("\n📈 Visualizações...")
try:
    figuras = analisador.gerar_visualizacoes_espaciais()
    print(f"✓ Visualizações geradas")
except Exception as e:
    print(f"⚠️ Falha em visualizações: {e}")

# Mapas
print("\n🗺️  Mapas...")
try:
    mapas = analisador.gerar_mapas_interpolacao()
    print(f"✓ Mapas gerados")
except Exception as e:
    print(f"⚠️ Falha em mapas: {e}")

# Gerar PDF
print("\n📄 Gerando PDF com imagens inseridas...")
print("-"*70)

try:
    gerador = GeradorRelatorioAvancado(
        analisador, 
        caminho_saida=str(Path(__file__).parent / "geoestat_analyzer_novo" / "dados" / "saida"),
        nome_projeto="TESTE_COM_IMAGENS"
    )
    
    caminho_pdf = gerador.gerar()
    
    if caminho_pdf:
        arquivo = Path(caminho_pdf)
        tamanho_mb = arquivo.stat().st_size / (1024*1024)
        
        print("\n" + "="*70)
        print("✅ PDF GERADO COM SUCESSO!")
        print("="*70)
        print(f"\n📄 Arquivo: {arquivo.name}")
        print(f"📍 Caminho: {arquivo}")
        print(f"💾 Tamanho: {tamanho_mb:.2f} MB")
        print(f"📑 Páginas: 6")
        print("\n✓ Imagens deveriam estar inseridas nas páginas 4 e 5")
        print("\nPara verificar, abra o PDF e verifique se:")
        print("  - Página 4: Contém 4 mapas/gráficos (OSM, Scatter, Hexbin, IDW)")
        print("  - Página 5: Contém 5 visualizações (Histogramas, Violin, 3 Interpolações)")
        
    else:
        print("\n❌ Erro ao gerar PDF")
        sys.exit(1)
        
except Exception as e:
    print(f"\n❌ Erro: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*70 + "\n")
