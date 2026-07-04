#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
# TESTE DE SELEÇÃO DE ARQUIVO - DEMONSTRAÇÃO
# ============================================================================
# Este script demonstra como a seleção de arquivo funciona
# ============================================================================

import sys
from pathlib import Path

# Configura encoding para Windows
if sys.platform == 'win32':
    import os
    import io
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

pasta_raiz = Path(__file__).parent
sys.path.insert(0, str(pasta_raiz))

from executavel.principal import solicitar_arquivo_dados

print("\n" + "="*70)
print("TESTE DE SELEÇÃO DE ARQUIVO")
print("="*70 + "\n")

print("Este script testa a funcionalidade de seleção de arquivo.")
print("Quando executar o principal.py, será aberto um diálogo gráfico.")
print("\nVocê pode:")
print("  1. Selecionar qualquer arquivo Excel (.xlsx) ou CSV (.csv)")
print("  2. O arquivo será analisado e um PDF será gerado")
print("  3. Se cancelar o diálogo, o programa sair graciosamente")

print("\n" + "="*70)
print("Pressione Enter para abrir o diálogo de seleção...")
input()

arquivo = solicitar_arquivo_dados()

if arquivo:
    print(f"\n✅ Arquivo selecionado: {arquivo}")
    print(f"   Nome: {arquivo.name}")
    print(f"   Tamanho: {arquivo.stat().st_size / 1024:.1f} KB")
    print(f"\n📋 Você pode agora executar:")
    print(f"   python executavel/principal.py")
    print(f"\n   E selecionar este mesmo arquivo para gerar o PDF!")
else:
    print("\n❌ Nenhum arquivo foi selecionado")

print("\n" + "="*70 + "\n")
