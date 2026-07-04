#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
# SCRIPT WRAPPER - EXECUTA A ANÁLISE GEOESTATÍSTICA
# ============================================================================
# Use: python executar.py (na pasta Aldino2)
# ============================================================================

import sys
import subprocess
from pathlib import Path

# Obtém o diretório do script atual
pasta_atual = Path(__file__).parent
pasta_principal = pasta_atual / "geoestat_analyzer_novo" / "executavel" / "principal.py"

if not pasta_principal.exists():
    print(f"\n❌ ERRO: Arquivo não encontrado!")
    print(f"   Procurando em: {pasta_principal}")
    sys.exit(1)

# Executa o script principal
print(f"\n🚀 Iniciando análise geoespacial...")
print(f"   Executable: {pasta_principal.name}")
print()

resultado = subprocess.run(
    [sys.executable, str(pasta_principal)],
    cwd=str(pasta_atual)
)

sys.exit(resultado.returncode)
