#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
# SCRIPT DE VALIDAÇÃO DO SISTEMA - ANÁLISE GEOESPACIAL AVANÇADA
# ============================================================================
# Uso: python teste_sistema.py
# Valida: Dependências, estrutura de pastas, permissões
# ============================================================================

import sys
from pathlib import Path

print("\n" + "="*70)
print(" "*15 + "VALIDAÇÃO DO SISTEMA")
print("="*70)

# ========== TESTE 1: DEPENDÊNCIAS ==========
print("\n📦 Verificando dependências Python...")

dependencias = {
    'pandas': 'Manipulação de dados',
    'numpy': 'Computação numérica',
    'geopandas': 'Dados geoespaciais',
    'scipy': 'Computação científica',
    'libpysal': 'Análise espacial',
    'esda': 'Índice de Moran',
    'pykrige': 'Kriging',
    'matplotlib': 'Visualização',
    'seaborn': 'Gráficos avançados',
    'sklearn': 'Machine Learning',
    'shapely': 'Geometria',
}

dependencias_ok = 0
dependencias_faltando = []

for lib, descricao in dependencias.items():
    try:
        __import__(lib)
        print(f"  ✓ {lib:15} {descricao}")
        dependencias_ok += 1
    except ImportError:
        print(f"  ✗ {lib:15} {descricao} [FALTANDO]")
        dependencias_faltando.append(lib)

print(f"\n  Resultado: {dependencias_ok}/{len(dependencias)} OK")

if dependencias_faltando:
    print(f"\n  ⚠ Bibliotecas faltando: {', '.join(dependencias_faltando)}")
    print(f"\n  Instale com:")
    print(f"    pip install {' '.join(dependencias_faltando)}")
    print(f"  Ou: pip install -r requirements.txt")

# ========== TESTE 2: ESTRUTURA DE PASTAS ==========
print("\n\n📁 Verificando estrutura de pastas...")

pasta_raiz = Path(__file__).parent
pastas_esperadas = {
    'dados': 'Armazena entrada/saída',
    'dados/entrada': 'Arquivo de entrada do usuário',
    'dados/saida': 'Relatórios gerados',
    'analise': 'Módulos de análise',
    'executavel': 'Scripts principais',
}

pastas_ok = 0

for pasta, descricao in pastas_esperadas.items():
    caminho = pasta_raiz / pasta
    if caminho.exists():
        print(f"  ✓ {pasta:20} {descricao}")
        pastas_ok += 1
    else:
        print(f"  ✗ {pasta:20} {descricao} [NÃO EXISTE]")

print(f"\n  Resultado: {pastas_ok}/{len(pastas_esperadas)} OK")

# ========== TESTE 3: PERMISSÕES DE ESCRITA ==========
print("\n\n🔐 Verificando permissões de escrita...")

pasta_teste = pasta_raiz / 'dados' / 'saida'
arquivo_teste = pasta_teste / '.test_permissao.txt'

try:
    pasta_teste.mkdir(parents=True, exist_ok=True)
    arquivo_teste.write_text('teste')
    arquivo_teste.unlink()
    print(f"  ✓ Permissão de escrita OK em {pasta_teste}")
except PermissionError:
    print(f"  ✗ Sem permissão de escrita em {pasta_teste}")
except Exception as e:
    print(f"  ⚠ Erro ao testar: {e}")

# ========== TESTE 4: ARQUIVOS PRINCIPAIS ==========
print("\n\n📄 Verificando arquivos principais...")

arquivos_esperados = {
    'executavel/principal.py': 'Script principal',
    'analise/analisador.py': 'Análise central',
    'analise/gerador_relatorio_avancado.py': 'Gerador PDF',
    'analise/gerador_insights_avancado.py': 'Gerador de insights',
    'analise/mapas_interpolacao.py': 'Interpolações',
    'analise/visualizacoes_spatial.py': 'Visualizações espaciais',
    'analise/analise_espacial_avancada.py': 'Análise de Moran',
}

arquivos_ok = 0

for arquivo, descricao in arquivos_esperados.items():
    caminho = pasta_raiz / arquivo
    if caminho.exists():
        tamanho_kb = caminho.stat().st_size / 1024
        print(f"  ✓ {arquivo:35} ({tamanho_kb:.1f} KB)")
        arquivos_ok += 1
    else:
        print(f"  ✗ {arquivo:35} [NÃO EXISTE]")

print(f"\n  Resultado: {arquivos_ok}/{len(arquivos_esperados)} OK")

# ========== TESTE 5: IMPORTS DE MÓDULOS ==========
print("\n\n⚙️  Testando imports dos módulos...")

try:
    sys.path.insert(0, str(pasta_raiz))
    
    print("  → Importando analisador...")
    from analise.analisador import AnalisadorGeo
    print("    ✓ AnalisadorGeo")
    
    print("  → Importando gerador de relatório...")
    from analise.gerador_relatorio_avancado import GeradorRelatorioAvancado
    print("    ✓ GeradorRelatorioAvancado")
    
    print("  → Importando gerador de insights...")
    from analise.gerador_insights_avancado import GeradorInsightsAvancado
    print("    ✓ GeradorInsightsAvancado")
    
    print("  → Importando análise espacial...")
    from analise.analise_espacial_avancada import AnaliseSpatialAvancada
    print("    ✓ AnaliseSpatialAvancada")
    
    print("\n  Resultado: Todos os módulos importam OK")
    
except ImportError as e:
    print(f"  ✗ Erro ao importar: {e}")

# ========== TESTE 6: DADOS DE TESTE ==========
print("\n\n📊 Verificando arquivo de teste...")

arquivo_teste = pasta_raiz / 'dados' / 'entrada' / 'exemplo_dados_geoespaciais.xlsx'

if arquivo_teste.exists():
    tamanho_kb = arquivo_teste.stat().st_size / 1024
    print(f"  ✓ Arquivo de teste existe ({tamanho_kb:.1f} KB)")
    
    # Tentar carregar
    try:
        import pandas as pd
        df_teste = pd.read_excel(arquivo_teste)
        print(f"  ✓ Arquivo carregado com sucesso")
        print(f"    Dimensões: {df_teste.shape[0]} linhas × {df_teste.shape[1]} colunas")
        print(f"    Colunas: {', '.join(df_teste.columns[:5].tolist())}")
    except Exception as e:
        print(f"  ⚠ Erro ao carregar: {e}")
else:
    print(f"  ℹ Nenhum arquivo de teste encontrado")
    print(f"    Coloque um arquivo .xlsx em: {arquivo_teste.parent}/")

# ========== RESUMO FINAL ==========
print("\n\n" + "="*70)
print("RESUMO DA VALIDAÇÃO")
print("="*70)

print(f"\n✓ Dependências:   {dependencias_ok}/{len(dependencias)}")
print(f"✓ Pastas:         {pastas_ok}/{len(pastas_esperadas)}")
print(f"✓ Arquivos:       {arquivos_ok}/{len(arquivos_esperados)}")

if (dependencias_ok == len(dependencias) and 
    pastas_ok == len(pastas_esperadas) and 
    arquivos_ok == len(arquivos_esperados)):
    print("\n✅ SISTEMA PRONTO PARA EXECUÇÃO!")
    print("\nPróximos passos:")
    print("  1. Coloque seu arquivo de dados em: dados/entrada/")
    print("  2. Execute: python executavel/principal.py")
    print("  3. Relatório será salvo em: dados/saida/")
    sys.exit(0)
else:
    print("\n⚠️  ALGUNS PROBLEMAS DETECTADOS")
    if dependencias_faltando:
        print(f"\nResolva instalando as dependências faltando:")
        print(f"  pip install -r requirements.txt")
    print("\n" + "="*70 + "\n")
    sys.exit(1)
