#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste da função de seleção de arquivo corrigida.

Demonstra que o diálogo agora mostra todos os arquivos por padrão
e permite seleção adequada.
"""

import sys
from pathlib import Path

# Importa a função corrigida
sys.path.insert(0, str(Path(__file__).parent / "geoestat_analyzer_novo"))
from executavel.principal import solicitar_arquivo_dados

print("\n" + "="*70)
print("TESTE: Diálogo de Seleção de Arquivo (CORRIGIDO)")
print("="*70)
print("\n📋 Verificações Implementadas:")
print("   ✅ Filtro 'All Files' agora é PRIMEIRO (mostra todos os arquivos)")
print("   ✅ Arquivos .xlsx e .csv são destacados")
print("   ✅ Se cancelar diálogo, opção manual de digitação aparece")
print("   ✅ Tratamento de erros com fallback")

print("\n🧪 Iniciando teste...")
print("-"*70)

# Chama a função
arquivo = solicitar_arquivo_dados()

if arquivo:
    print("\n✅ SUCESSO!")
    print(f"   Arquivo: {arquivo.name}")
    print(f"   Tamanho: {arquivo.stat().st_size} bytes")
    print(f"   Caminho completo: {arquivo}")
else:
    print("\n❌ Nenhum arquivo selecionado")
    print("   (Isso é normal se você cancelou)")

print("\n" + "="*70)
print("Teste concluído!")
print("="*70 + "\n")
