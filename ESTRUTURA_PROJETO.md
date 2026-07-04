# Estrutura Canônica do Projeto

Este repositório tem duas árvores de código. Para evitar confusão, esta é a organização que deve ser tratada como oficial daqui para frente.

## Camada ativa

- [executar.py](executar.py) é o único launcher na raiz.
- [geoestat_analyzer_novo/](geoestat_analyzer_novo/) contém a implementação ativa.
- [geoestat_analyzer_novo/executavel/principal.py](geoestat_analyzer_novo/executavel/principal.py) é a pipeline principal.
- [geoestat_analyzer_novo/analise/](geoestat_analyzer_novo/analise/) concentra a lógica de análise, mapas, visualizações e relatórios.

## Camada de apoio

- [COMO_EXECUTAR.md](COMO_EXECUTAR.md) e [README_USUARIO.md](README_USUARIO.md) orientam o uso simples.
- [README_SISTEMA_COMPLETO.md](README_SISTEMA_COMPLETO.md) documenta a versão mais detalhada do fluxo.
- [requirements.txt](requirements.txt) fica na raiz para instalação rápida.

## Legado

- [geoestat_analyzer/](geoestat_analyzer/) é a árvore antiga e não deve receber novas funcionalidades.
- Se houver manutenção nessa área, ela deve ser tratada como migração ou compatibilidade, não como fonte principal.

## Regra prática

Novas mudanças devem começar em `geoestat_analyzer_novo/` e só depois, se necessário, refletir na documentação da raiz.
