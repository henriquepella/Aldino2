#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para gerador de relatório PDF avançado
"""

import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from analise.analisador import AnalisadorGeo
from analise.gerador_relatorio_avancado import GeradorRelatorioAvancado

def main():
    print("="*70)
    print("TESTE DO GERADOR DE RELATÓRIO PDF AVANÇADO")
    print("="*70)
    
    # Carregar dados
    caminho_dados = Path(__file__).parent / "dados" / "entrada" / "exemplo_dados_geoespaciais.xlsx"
    
    if not caminho_dados.exists():
        print(f"❌ Arquivo não encontrado: {caminho_dados}")
        return
    
    print(f"\n✓ Carregando dados: {caminho_dados.name}")
    
    try:
        # Análise
        print("✓ Analisando dados...")
        analisador = AnalisadorGeo(str(caminho_dados))
        analisador.analisar()
        analisador.analisar_autocorrelacao_espacial()
        
        # Gerar relatório
        print("✓ Gerando relatório PDF (6 páginas)...")
        gerador = GeradorRelatorioAvancado(
            analisador,
            nome_projeto="Análise Geoestatística - Teste"
        )
        
        caminho_pdf = gerador.gerar()
        
        if caminho_pdf and Path(caminho_pdf).exists():
            tamanho_mb = Path(caminho_pdf).stat().st_size / (1024*1024)
            print(f"\n✅ SUCESSO!")
            print(f"   Arquivo: {Path(caminho_pdf).name}")
            print(f"   Tamanho: {tamanho_mb:.2f} MB")
            print(f"   Caminho: {caminho_pdf}")
        else:
            print(f"\n❌ Erro na geração")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
