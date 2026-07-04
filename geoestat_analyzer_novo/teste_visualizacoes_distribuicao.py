#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para visualizações de distribuição e correlação
Gera: Histogramas, Violin+Boxplot, Matriz de Correlação
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Adiciona pasta ao path
sys.path.insert(0, str(Path(__file__).parent))

from analise.visualizacoes_distribuicao import VisualizacoesDistribuicao

def main():
    """Executa teste de visualizações."""
    
    # Carrega dados de teste (mesmo arquivo do teste de mapas)
    caminho_dados = Path(__file__).parent / "dados" / "entrada" / "exemplo_dados_geoespaciais.xlsx"
    
    if not caminho_dados.exists():
        print("⚠ Arquivo de dados não encontrado!")
        print(f"  Procurando em: {caminho_dados}")
        return
    
    print(f"✓ Carregando dados: {caminho_dados.name}")
    df = pd.read_excel(caminho_dados)
    
    print(f"✓ Dimensões: {df.shape[0]} amostras × {df.shape[1]} colunas")
    print(f"✓ Colunas: {list(df.columns)}")
    
    # Criar pasta de saída
    pasta_saida = Path(__file__).parent / "dados" / "saida" / "visualizacoes"
    pasta_saida.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"TESTE DE VISUALIZAÇÕES DE DISTRIBUIÇÃO")
    print(f"{'='*60}\n")
    
    try:
        # Inicializar visualizador
        print("Inicializando visualizador...")
        vis = VisualizacoesDistribuicao(df)
        
        # Salvar visualizações
        print("\nGerando visualizações...")
        print("  → Histogramas padronizados (z-score)...")
        vis.plotar_histogramas_padronizados()
        print("     ✓ Gerado")
        
        print("  → Violin plots + boxplots...")
        vis.plotar_violin_boxplot()
        print("     ✓ Gerado")
        
        print("  → Matriz de correlação...")
        vis.plotar_matriz_correlacao()
        print("     ✓ Gerado")
        
        # Salvar em disco
        print("\nSalvando arquivos (300 dpi)...")
        arquivos = vis.salvar_visualizacoes(pasta_saida, dpi=300)
        
        # Gerar relatório HTML
        print("\nGerando relatório HTML...")
        html_path = vis.gerar_relatorio_html(pasta_saida)
        
        # Exibir resultado
        print(f"\n{'='*60}")
        print(f"✅ SUCESSO! Visualizações geradas em:")
        print(f"{pasta_saida}\n")
        
        for nome, caminho in arquivos.items():
            tamanho_mb = caminho.stat().st_size / (1024 * 1024)
            print(f"  ✓ {caminho.name} ({tamanho_mb:.1f} MB)")
        
        print(f"\n  📄 Relatório HTML: {Path(html_path).name}")
        print(f"{'='*60}\n")
        
    except Exception as erro:
        print(f"\n❌ ERRO: {str(erro)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
