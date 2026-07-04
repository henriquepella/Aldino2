# ============================================================================
# MÓDULO DE ANÁLISE GEOESTATÍSTICA
# ============================================================================
# Pacote contendo os módulos principais de análise de dados geoespaciais
# ============================================================================

from .analisador import AnalisadorGeo
from .gerador_relatorio import GeradorRelatorio

# ========== TENTA IMPORTAR ANÁLISE ESPACIAL AVANÇADA ==========
try:
    from .analise_espacial_avancada import AnaliseSpatialAvancada
    from .visualizacoes_spatial import VisualizacoesSpatial
except ImportError as e:
    AnaliseSpatialAvancada = None
    VisualizacoesSpatial = None

__all__ = [
    'AnalisadorGeo',
    'GeradorRelatorio',
    'AnaliseSpatialAvancada',
    'VisualizacoesSpatial'
]
