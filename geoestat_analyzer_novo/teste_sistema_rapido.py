#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
# SCRIPT DE VALIDAÇÃO DO SISTEMA - ANÁLISE GEOESPACIAL AVANÇADA (v2)
# ============================================================================
# Uso: python teste_sistema_rapido.py
# Funciona de qualquer pasta dentro da estrutura
# ============================================================================

import sys
import os
from pathlib import Path

print("\n" + "="*70)
print(" "*15 + "VALIDAÇÃO DO SISTEMA")
print("="*70 + "\n")

# Detectar raiz do projeto
current = Path.cwd()
raiz_possiveis = [
    current / 'geoestat_analyzer_novo',
    current,
    current.parent,
    current / '..' / 'geoestat_analyzer_novo',
]

# Procura por pasta com 'analise'
pasta_raiz = None
for p in raiz_possiveis:
    if (p / 'analise').exists():
        pasta_raiz = p
        break

if not pasta_raiz or not pasta_raiz.exists():
    print("❌ Não consegui encontrar a raiz do projeto!")
    print(f"   Pasta atual: {current}")
    print("   Estrutura esperada: geoestat_analyzer_novo/analise/")
    sys.exit(1)

print(f"📁 Pasta raiz detectada: {pasta_raiz}")
print()

# ========== TESTE 1: DEPENDÊNCIAS ==========
print("📦 Verificando dependências Python...")

dependencias = {
    'pandas': 'Manipulação de dados',
    'numpy': 'Computação numérica',
    'geopandas': 'Dados geoespaciais',
    'scipy': 'Computação científica',
    'libpysal': 'Análise espacial',
    'esda': 'Índice de Moran',
    'pykrige': 'Kriging',
    'matplotlib': 'Visualização',
}

dependencias_ok = 0
erros = []

for lib, descricao in dependencias.items():
    try:
        __import__(lib)
        print(f"  ✓ {lib:15} OK")
        dependencias_ok += 1
    except ImportError as e:
        print(f"  ✗ {lib:15} FALTANDO")
        erros.append(lib)

print(f"\n  Resultado: {dependencias_ok}/{len(dependencias)} OK\n")

# ========== TESTE 2: ARQUIVOS PRINCIPAIS ==========
print("📄 Verificando arquivos principais...")

arquivos = {
    'analise/analisador.py': 'Análise central',
    'analise/gerador_relatorio_avancado.py': 'Gerador PDF',
    'analise/gerador_insights_avancado.py': 'Insights automáticos',
    'executavel/principal.py': 'Script principal',
}

arquivos_ok = 0

for arquivo, descricao in arquivos.items():
    caminho = pasta_raiz / arquivo
    if caminho.exists():
        tamanho = caminho.stat().st_size / 1024
        print(f"  ✓ {arquivo:40} ({tamanho:.0f} KB)")
        arquivos_ok += 1
    else:
        print(f"  ✗ {arquivo:40} FALTANDO")

print(f"\n  Resultado: {arquivos_ok}/{len(arquivos)} OK\n")

# ========== TESTE 3: IMPORTS ==========
print("⚙️  Testando imports dos módulos...\n")

sys.path.insert(0, str(pasta_raiz))

try:
    from analise.analisador import AnalisadorGeo
    print("  ✓ AnalisadorGeo importado")
except Exception as e:
    print(f"  ✗ AnalisadorGeo: {str(e)[:50]}")
    erros.append("AnalisadorGeo")

try:
    from analise.gerador_relatorio_avancado import GeradorRelatorioAvancado
    print("  ✓ GeradorRelatorioAvancado importado")
except Exception as e:
    print(f"  ✗ GeradorRelatorioAvancado: {str(e)[:50]}")
    erros.append("Gerador PDF")

try:
    from analise.gerador_insights_avancado import GeradorInsightsAvancado
    print("  ✓ GeradorInsightsAvancado importado")
except Exception as e:
    print(f"  ✗ GeradorInsightsAvancado: {str(e)[:50]}")
    erros.append("Insights")

print()

# ========== TESTE 4: DADOS DE TESTE ==========
print("📊 Verificando dados de teste...")

arquivo_teste = pasta_raiz / 'dados' / 'entrada' / 'exemplo_dados_geoespaciais.xlsx'

if arquivo_teste.exists():
    try:
        import pandas as pd
        df = pd.read_excel(arquivo_teste)
        print(f"  ✓ Dados carregados: {df.shape[0]} linhas, {df.shape[1]} colunas")
    except Exception as e:
        print(f"  ⚠ Erro ao carregar: {e}")
else:
    print(f"  ℹ Dados de teste não encontrados")

print()

# ========== RESUMO ==========
print("="*70)
print("RESUMO")
print("="*70)

print(f"\n✓ Dependências:  {dependencias_ok}/{len(dependencias)}")
print(f"✓ Arquivos:      {arquivos_ok}/{len(arquivos)}")

if erros:
    print(f"\n⚠️  {len(erros)} problema(s) detectado(s):")
    for erro in erros:
        print(f"   - {erro}")
    
    if any('Faltando' in str(e) for e in erros):
        print(f"\n  Instale dependências com:")
        print(f"    pip install -r requirements.txt")

if dependencias_ok == len(dependencias) and arquivos_ok == len(arquivos):
    print("\n✅ SISTEMA PRONTO PARA EXECUÇÃO!")
    sys.exit(0)
else:
    print("\n⚠️  Alguns problemas detectados")
    sys.exit(1)
