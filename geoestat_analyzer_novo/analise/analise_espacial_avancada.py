# ============================================================================
# MÓDULO DE ANÁLISE ESPACIAL AVANÇADA
# ============================================================================
# Responsável por:
#   - Calcular Índice de Moran Global para cada variável
#   - Realizar LISA (Local Indicators of Spatial Association)
#   - Gerar estatísticas de autocorrelação espacial
#   - Criar visualizações de análise espacial
# ============================================================================

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
import warnings

# ========== IMPORTS DE ANÁLISE ESPACIAL ==========
from libpysal.weights import KNN
from esda.moran import Moran
# NOTA: Moran_Local removido por incompatibilidade com Numba em Python 3.12

warnings.filterwarnings('ignore')


class AnaliseSpatialAvancada:
    """
    Classe para análise espacial avançada usando índices de Moran.
    
    Calcula estatísticas de autocorrelação espacial global e local,
    identificando clusters espaciais nos dados geoespaciais.
    """
    
    def __init__(self, dataframe: pd.DataFrame, col_x: str, col_y: str, seed: int = 42):
        """
        Inicializa análise espacial.
        
        Args:
            dataframe: DataFrame com dados
            col_x: Nome da coluna de coordenada X
            col_y: Nome da coluna de coordenada Y
            seed: Seed para reprodutibilidade das simulações
        """
        self.df = dataframe.copy()
        self.col_x = col_x
        self.col_y = col_y
        self.seed = seed
        
        # ========== CRIA MATRIZ DE PESOS ESPACIAIS ==========
        # KNN (K-Nearest Neighbors) com K=4 vizinhos
        self.coordenadas = self.df[[col_x, col_y]].values
        self.pesos = KNN.from_array(self.coordenadas, k=4)
        
        # Dicionário para armazenar resultados
        self.resultados_moran = {}
        self.resultados_lisa = {}
        
        print(f"✓ Matriz de pesos espaciais criada (KNN, k=4)")
        print(f"  {len(self.df)} pontos | {self.pesos.n_components} componentes")
    
    def calcular_moran_global(self, variavel: str, num_simulacoes: int = 999) -> Dict:
        """
        Calcula Índice de Moran Global com teste de permutação.
        
        O teste de permutação gera simulações aleatórias para verificar
        se a autocorrelação é significativa estatisticamente.
        
        Args:
            variavel: Nome da coluna a analisar
            num_simulacoes: Número de permutações (padrão 999)
            
        Returns:
            Dicionário com: I, p-valor, z-score, significância
        """
        if variavel not in self.df.columns:
            print(f"⚠ Variável '{variavel}' não encontrada")
            return {}
        
        # ========== EXTRAI DADOS VÁLIDOS ==========
        dados = self.df[variavel].dropna().values
        
        # ========== FIXA SEED PARA REPRODUTIBILIDADE ==========
        np.random.seed(self.seed)
        
        # ========== CALCULA MORAN GLOBAL ==========
        # permutations=num_simulacoes realiza teste de permutação
        moran = Moran(dados, self.pesos, permutations=num_simulacoes)
        
        # ========== EXTRAI RESULTADOS ==========
        resultado = {
            'variavel': variavel,
            'I': moran.I,                      # Índice de Moran
            'EI': moran.EI,                    # Valor esperado sob HH0 (0)
            'p_valor': moran.p_norm,           # p-valor normalizado
            'z_score': moran.z_norm,           # z-score normalizado
            'significancia': moran.p_norm < 0.05,  # Significante a 5%
            'p_valor_permutacao': moran.p_sim,     # p-valor por permutação
            'variancia': moran.VI_norm,        # Variância
            'num_simulacoes': num_simulacoes,
            'objeto_moran': moran              # Objeto para uso posterior
        }
        
        # ========== ARMAZENA RESULTADO ==========
        self.resultados_moran[variavel] = resultado
        
        # ========== EXIBE RESULTADO ==========
        sigla = "✓" if resultado['significancia'] else "✗"
        print(f"\n{sigla} Moran Global: {variavel}")
        print(f"  I = {resultado['I']:.6f}")
        print(f"  p-valor = {resultado['p_valor']:.6f}")
        print(f"  z-score = {resultado['z_score']:.6f}")
        print(f"  Significativo: {'SIM (p < 0.05)' if resultado['significancia'] else 'NÃO'}")
        
        return resultado
    
    def calcular_moran_multiplas(self, variaveis: List[str], num_simulacoes: int = 999) -> pd.DataFrame:
        """
        Calcula Moran Global para múltiplas variáveis.
        
        Args:
            variaveis: Lista de colunas a analisar
            num_simulacoes: Número de permutações
            
        Returns:
            DataFrame com resultados comparados
        """
        print(f"\n{'='*60}")
        print("ANÁLISE DE MORAN GLOBAL - MÚLTIPLAS VARIÁVEIS")
        print(f"{'='*60}")
        
        for variavel in variaveis:
            self.calcular_moran_global(variavel, num_simulacoes)
        
        # ========== CRIA DATAFRAME COM RESULTADOS ==========
        resultados_lista = []
        for variavel, resultado in self.resultados_moran.items():
            resultados_lista.append({
                'Variável': variavel,
                'I de Moran': resultado['I'],
                'p-valor': resultado['p_valor'],
                'z-score': resultado['z_score'],
                'Significativo': 'Sim' if resultado['significancia'] else 'Não'
            })
        
        df_resultados = pd.DataFrame(resultados_lista)
        df_resultados = df_resultados.sort_values('I de Moran', ascending=False)
        
        print(f"\n{'='*60}")
        print("RESUMO - ÍNDICE DE MORAN GLOBAL")
        print(f"{'='*60}")
        print(df_resultados.to_string(index=False))
        print(f"\nMoran médio: {df_resultados['I de Moran'].mean():.6f}")
        
        return df_resultados
    
    def obter_variavel_maior_moran(self) -> Tuple[str, Dict]:
        """
        Retorna a variável com maior índice de Moran.
        
        Returns:
            Tupla (nome_variavel, resultado_dict)
        """
        if not self.resultados_moran:
            return None, {}
        
        variavel_max = max(self.resultados_moran.items(), 
                          key=lambda x: x[1]['I'])
        return variavel_max[0], variavel_max[1]
    
    def calcular_lisa(self, variavel: str) -> pd.DataFrame:
        """
        Calcula LISA (Local Indicators of Spatial Association).
        
        Identifica clusters locais: HH (alto-alto), LL (baixo-baixo),
        LH (baixo-alto) e HL (alto-baixo).
        
        Args:
            variavel: Nome da variável a analisar
            
        Returns:
            DataFrame com classificação dos pontos
        """
        if variavel not in self.df.columns:
            print(f"⚠ Variável '{variavel}' não encontrada")
            return pd.DataFrame()
        
        print(f"\n{'='*60}")
        print(f"ANÁLISE LISA: {variavel}")
        print(f"{'='*60}")
        
        # ========== EXTRAI DADOS VÁLIDOS ==========
        dados = self.df[variavel].dropna().values
        
        # ========== FIXA SEED PARA REPRODUTIBILIDADE ==========
        np.random.seed(self.seed)
        
        # ========== CALCULA LISA (Local Moran) ==========
        lisa = Moran_Local(dados, self.pesos, permutations=999)
        
        # ========== CLASSIFICA PONTOS NOS QUADRANTES ==========
        # Standardize os dados para comparação com vizinhos
        dados_padronizados = (dados - dados.mean()) / dados.std()
        
        # Lag espacial (média dos vizinhos)
        lag_espacial = self.pesos.sparse.dot(dados_padronizados)
        
        # Classifica em quadrantes
        cluster = np.zeros(len(dados), dtype=object)
        
        # HH: Alto-Alto (ambos positivos)
        cluster[(dados_padronizados > 0) & (lag_espacial > 0)] = 'HH'
        
        # LL: Baixo-Baixo (ambos negativos)
        cluster[(dados_padronizados < 0) & (lag_espacial < 0)] = 'LL'
        
        # LH: Baixo-Alto (valor baixo, vizinhos altos)
        cluster[(dados_padronizados < 0) & (lag_espacial > 0)] = 'LH'
        
        # HL: Alto-Baixo (valor alto, vizinhos baixos)
        cluster[(dados_padronizados > 0) & (lag_espacial < 0)] = 'HL'
        
        # NS: Não significativo (baseado em p-valor de LISA)
        cluster[lisa.p_sim > 0.05] = 'NS'
        
        # ========== CRIA DATAFRAME COM RESULTADOS ==========
        df_lisa = pd.DataFrame({
            'x': self.df[self.col_x],
            'y': self.df[self.col_y],
            'valor': dados,
            'cluster': cluster,
            'p_valor_lisa': lisa.p_sim,
            'i_local': lisa.Is
        })
        
        # ========== CONTAGEM POR CATEGORIA ==========
        contagem = df_lisa['cluster'].value_counts()
        print(f"\nClassificação dos pontos:")
        for cluster_type, count in contagem.items():
            pct = (count / len(df_lisa)) * 100
            print(f"  {cluster_type}: {count:4d} pontos ({pct:5.1f}%)")
        
        # ========== ARMAZENA RESULTADO ==========
        self.resultados_lisa[variavel] = {
            'dataframe': df_lisa,
            'objeto_lisa': lisa,
            'contagem': contagem
        }
        
        return df_lisa
    
    def obter_resumo_espacial(self) -> Dict:
        """
        Gera resumo executivo dos resultados geoespaciais.
        
        Returns:
            Dicionário com informações-chave
        """
        if not self.resultados_moran:
            return {}
        
        # ========== CALCULA MORAN MÉDIO ==========
        morans = [r['I'] for r in self.resultados_moran.values()]
        moran_medio = np.mean(morans)
        
        # ========== VARIÁVEL COM MAIOR MORAN ==========
        var_max, resultado_max = self.obter_variavel_maior_moran()
        
        # ========== CONTA PONTOS EM CLUSTERS ==========
        total_clusters = 0
        for variavel, resultado_lisa in self.resultados_lisa.items():
            df_lisa = resultado_lisa['dataframe']
            clusteres_significativos = df_lisa[df_lisa['cluster'] != 'NS']
            total_clusters += len(clusteres_significativos)
        
        resumo = {
            'moran_medio': moran_medio,
            'variavel_max_autocorrelacao': var_max,
            'moran_maximo': resultado_max['I'],
            'num_variaveis_analisadas': len(self.resultados_moran),
            'total_pontos_clusters': total_clusters,
            'total_pontos': len(self.df)
        }
        
        print(f"\n{'='*60}")
        print("RESUMO EXECUTIVO - ANÁLISE ESPACIAL")
        print(f"{'='*60}")
        print(f"Moran médio: {resumo['moran_medio']:.6f}")
        print(f"Maior autocorrelação: {var_max} (I = {resultado_max['I']:.6f})")
        print(f"Pontos em clusters: {total_clusters}/{len(self.df)} ({(total_clusters/len(self.df)*100):.1f}%)")
        
        return resumo
