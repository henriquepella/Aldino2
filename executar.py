#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
# PONTO ÚNICO DE ENTRADA - EXECUTA A ANÁLISE GEOESTATÍSTICA
# ============================================================================
# Use: python executar.py (na pasta Aldino2)
# ============================================================================

import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def carregar_main(caminho_arquivo: Path):
    """Carrega a função main do script principal sem criar um subprocesso."""
    especificacao = spec_from_file_location("geoestat_principal", caminho_arquivo)

    if especificacao is None or especificacao.loader is None:
        raise RuntimeError(f"Não foi possível carregar {caminho_arquivo}")

    modulo = module_from_spec(especificacao)
    especificacao.loader.exec_module(modulo)

    if not hasattr(modulo, "main"):
        raise RuntimeError(f"A função main não foi encontrada em {caminho_arquivo}")

    return modulo.main


def main():
    """Executa a pipeline principal do projeto."""
    pasta_atual = Path(__file__).parent
    pasta_principal = pasta_atual / "geoestat_analyzer_novo" / "executavel" / "principal.py"

    if not pasta_principal.exists():
        print("\n❌ ERRO: Arquivo não encontrado!")
        print(f"   Procurando em: {pasta_principal}")
        return False

    print("\n🚀 Iniciando análise geoespacial...")
    print(f"   Executable: {pasta_principal.name}")
    print()

    main_principal = carregar_main(pasta_principal)
    return bool(main_principal())


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
