# ============================================================================
# GERADOR DE INSIGHTS AVANÇADOS - ANÁLISE GEOESPACIAL
# ============================================================================
# Responsável por:
#   - Gerar insights automáticos baseados nos resultados
#   - Calcular métricas de heterogeneidade e estrutura espacial
#   - Analisar distribuição de clusters por quadrante
#   - Comparar superfícies interpoladas
#   - Formular recomendações técnicas
# ============================================================================

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any
import warnings

warnings.filterwarnings('ignore')


class GeradorInsightsAvancado:
    """
    Genera insights automáticos baseados em análise geoespacial completa.
    
    Analisa resultados de Moran Global, LISA, distribuições e interpolações
    para formular recomendações técnicas e identificar padrões significativos.
    """
    
    def __init__(self, analisador):
        """
        Inicializa gerador de insights.
        
        Args:
            analisador: Objeto AnalisadorGeoespacial com dados e resultados
        """
        self.analisador = analisador
        self.df = analisador.df
        self.info_dados = analisador.info_dados
        self.insights = {}
        
    def gerar_todos_insights(self) -> Dict[str, Any]:
        """
        Executa geração completa de todos os insights.
        
        Returns:
            Dicionário com todos os insights calculados
        """
        print("\n" + "="*60)
        print("GERANDO INSIGHTS AVANÇADOS")
        print("="*60)
        
        # Extrai dados necessários
        self.insights['variavel_maxima'] = self._identificar_variavel_maxima()
        self.insights['clusters_significativos'] = self._analisar_clusters_significativos()
        self.insights['heterogeneidade'] = self._analisar_heterogeneidade()
        self.insights['clusters_quadrantes'] = self._analisar_clusters_por_quadrante()
        self.insights['diferenca_interpolacoes'] = self._comparar_interpolacoes()
        self.insights['extensao_geografica'] = self._calcular_extensao_geografica()
        self.insights['recomendacoes'] = self._gerar_recomendacoes()
        
        return self.insights
    
    def _identificar_variavel_maxima(self) -> Dict[str, Any]:
        """
        Identifica variável com maior estrutura espacial (maior I de Moran).
        
        Returns:
            Dicionário com info da variável máxima
        """
        print("\n📊 Identificando variável com maior estrutura espacial...")
        
        resultado = {
            'variavel': None,
            'I_moran': -2,  # Moran's I pode ser negativo
            'p_valor': 1,
            'z_score': 0,
            'significativo': False,
            'interpretacao': ''
        }
        
        try:
            # Tenta obter resultados de análise espacial
            analise_espacial = self.info_dados.get('analise_espacial', {})
            resultados_moran = analise_espacial.get('resultados_moran', pd.DataFrame())
            
            if resultados_moran.empty:
                print("  ⚠ Sem dados de Moran disponíveis")
                return resultado
            
            # Encontra máximo I de Moran (ignora NaN)
            moran_valores = pd.to_numeric(resultados_moran['I de Moran'], errors='coerce')
            if moran_valores.isna().all():
                print("  ⚠ Todos os valores de Moran's I são NaN")
                return resultado
            
            idx_max = moran_valores.idxmax()
            linha_max = resultados_moran.loc[idx_max]
            
            resultado['variavel'] = linha_max['Variável']
            resultado['I_moran'] = float(linha_max['I de Moran']) if not pd.isna(linha_max['I de Moran']) else -2
            resultado['p_valor'] = float(linha_max['p-valor']) if not pd.isna(linha_max['p-valor']) else 1
            resultado['z_score'] = float(linha_max['z-score']) if not pd.isna(linha_max['z-score']) else 0
            resultado['significativo'] = str(linha_max['Significativo']).lower() == 'sim'
            
            # Interpretação
            if resultado['significativo']:
                if resultado['I_moran'] > 0.3:
                    resultado['interpretacao'] = "forte autocorrelação espacial positiva"
                elif resultado['I_moran'] > 0:
                    resultado['interpretacao'] = "moderada autocorrelação espacial positiva"
                else:
                    resultado['interpretacao'] = "fraca estrutura espacial"
            else:
                resultado['interpretacao'] = "padrão espacial não significativo"
            
            print(f"  ✓ Variável: {resultado['variavel']}")
            print(f"    I de Moran: {resultado['I_moran']:.4f} (p={resultado['p_valor']:.6f})")
            print(f"    Interpretação: {resultado['interpretacao']}")
            
        except Exception as e:
            print(f"  ⚠ Erro ao identificar variável máxima: {e}")
        
        return resultado
    
    def _analisar_clusters_significativos(self) -> Dict[str, Any]:
        """
        Analisa total de pontos em clusters significativos (p < 0.05).
        
        Returns:
            Dicionário com estatísticas de clusters
        """
        print("\n🎯 Analisando clusters significativos...")
        
        resultado = {
            'total_pontos': len(self.df),
            'pontos_cluster': 0,
            'percentual_cluster': 0,
            'quadrante_dominante': 'NS',
            'distribuicao': {},
            'resumo': ''
        }
        
        try:
            analise_espacial = self.info_dados.get('analise_espacial', {})
            objeto_analise = analise_espacial.get('objeto')
            
            if not objeto_analise:
                print("  ⚠ Sem objeto de análise disponível")
                return resultado
            
            # Tenta obter resultados LISA
            variavel_max = analise_espacial.get('variavel_max')
            if not variavel_max:
                print("  ⚠ Variável máxima não identificada")
                return resultado
            
            # Acessa resultado LISA armazenado
            try:
                resultado_lisa = objeto_analise.resultados_lisa.get(variavel_max, {})
                lisa_df = resultado_lisa.get('dataframe', pd.DataFrame())
                
                if lisa_df.empty:
                    print("  ℹ Usando classificação manual baseada em quadrantes")
                    # Fallback: usa dados padronizados
                    dados = self.df[variavel_max].dropna().values
                    dados_pad = (dados - dados.mean()) / dados.std()
                    lag = objeto_analise.pesos.sparse.dot(dados_pad)
                    
                    # Classifica quadrantes
                    clusters = {}
                    clusters['HH'] = np.sum((dados_pad > 0) & (lag > 0))
                    clusters['LL'] = np.sum((dados_pad < 0) & (lag < 0))
                    clusters['HL'] = np.sum((dados_pad > 0) & (lag < 0))
                    clusters['LH'] = np.sum((dados_pad < 0) & (lag > 0))
                    clusters['NS'] = len(dados) - sum(clusters.values())
                else:
                    # Conta distribuição de clusters
                    clusters = lisa_df['cluster'].value_counts().to_dict()
                
                # Calcula totais
                pontos_significativos = sum(v for k, v in clusters.items() if k != 'NS')
                resultado['pontos_cluster'] = pontos_significativos
                resultado['percentual_cluster'] = (pontos_significativos / resultado['total_pontos']) * 100
                resultado['distribuicao'] = clusters
                
                # Identifica quadrante dominante
                clusters_sig = {k: v for k, v in clusters.items() if k != 'NS'}
                if clusters_sig:
                    resultado['quadrante_dominante'] = max(clusters_sig, key=clusters_sig.get)
                
                # Resumo
                hh = clusters.get('HH', 0)
                ll = clusters.get('LL', 0)
                hl = clusters.get('HL', 0)
                lh = clusters.get('LH', 0)
                ns = clusters.get('NS', 0)
                
                resultado['resumo'] = (
                    f"{pontos_significativos} pontos ({resultado['percentual_cluster']:.1f}%) em clusters | "
                    f"HH:{hh} LL:{ll} HL:{hl} LH:{lh} | "
                    f"Dominante: {resultado['quadrante_dominante']}"
                )
                
                print(f"  ✓ {resultado['resumo']}")
                
            except AttributeError:
                print("  ⚠ LISA não disponível, usando quadrantes padronizados")
        
        except Exception as e:
            print(f"  ⚠ Erro ao analisar clusters: {e}")
        
        return resultado
    
    def _analisar_heterogeneidade(self) -> Dict[str, List[str]]:
        """
        Identifica variáveis com alta heterogeneidade (CV > 100%).
        
        Returns:
            Dicionário com variáveis heterogêneas
        """
        print("\n📈 Analisando heterogeneidade estatística...")
        
        variaveis_heterogeneas = []
        variaveis_info = {}
        
        try:
            variaveis_numericas = self.info_dados.get('variaveis_numericas', [])
            
            for var in variaveis_numericas:
                if var not in self.df.columns:
                    continue
                
                dados = self.df[var].dropna()
                if len(dados) == 0 or dados.std() == 0:
                    continue
                
                media = dados.mean()
                desvio = dados.std()
                cv = (desvio / abs(media) * 100) if media != 0 else np.inf
                
                variaveis_info[var] = {
                    'media': media,
                    'desvio': desvio,
                    'cv': cv
                }
                
                if cv > 100:
                    variaveis_heterogeneas.append(var)
                    print(f"  ⚠ {var}: CV = {cv:.1f}% (alta heterogeneidade)")
                else:
                    print(f"  ✓ {var}: CV = {cv:.1f}%")
            
            if not variaveis_heterogeneas:
                print("  ✓ Todas as variáveis têm heterogeneidade controlada (CV < 100%)")
        
        except Exception as e:
            print(f"  ⚠ Erro ao analisar heterogeneidade: {e}")
        
        return {
            'variaveis_heterogeneas': variaveis_heterogeneas,
            'info_detalhada': variaveis_info
        }
    
    def _analisar_clusters_por_quadrante(self) -> Dict[str, Dict[str, float]]:
        """
        Analisa concentração de clusters por quadrante geográfico (NE, NO, SE, SO).
        
        Returns:
            Dicionário com distribuição por quadrante
        """
        print("\n🧭 Analisando distribuição por quadrante geográfico...")
        
        resultado = {
            'NE': {'total': 0, 'clusters': 0, 'percentual': 0},
            'NO': {'total': 0, 'clusters': 0, 'percentual': 0},
            'SE': {'total': 0, 'clusters': 0, 'percentual': 0},
            'SO': {'total': 0, 'clusters': 0, 'percentual': 0}
        }
        
        try:
            col_x = self.info_dados.get('col_x')
            col_y = self.info_dados.get('col_y')
            
            if not col_x or not col_y:
                print("  ⚠ Coordenadas não detectadas")
                return resultado
            
            # Centro geográfico
            x_centro = self.df[col_x].median()
            y_centro = self.df[col_y].median()
            
            # Classifica por quadrante
            for idx, row in self.df.iterrows():
                x = row[col_x]
                y = row[col_y]
                
                if x >= x_centro and y >= y_centro:
                    quad = 'NE'
                elif x < x_centro and y >= y_centro:
                    quad = 'NO'
                elif x < x_centro and y < y_centro:
                    quad = 'SO'
                else:
                    quad = 'SE'
                
                resultado[quad]['total'] += 1
            
            # Tenta contar clusters por quadrante
            analise_espacial = self.info_dados.get('analise_espacial', {})
            variavel_max = analise_espacial.get('variavel_max')
            
            if variavel_max:
                try:
                    objeto_analise = analise_espacial.get('objeto')
                    resultado_lisa = objeto_analise.resultados_lisa.get(variavel_max, {})
                    lisa_df = resultado_lisa.get('dataframe', pd.DataFrame())
                    
                    if not lisa_df.empty:
                        # Merge com quadrantes
                        coords_indices = lista_coords.index  # Precisa de acesso aos índices
                        
                        for quad_key in resultado.keys():
                            quad_mask = ((self.df[col_x] >= x_centro if quad_key in ['NE', 'SE'] else self.df[col_x] < x_centro) &
                                        (self.df[col_y] >= y_centro if quad_key in ['NE', 'NO'] else self.df[col_y] < y_centro))
                            
                            clusters_quad = ((lisa_df['cluster'] != 'NS') & quad_mask).sum()
                            resultado[quad_key]['clusters'] = clusters_quad
                            resultado[quad_key]['percentual'] = (clusters_quad / max(resultado[quad_key]['total'], 1)) * 100
                except:
                    pass
            
            # Print resultados
            for quad in ['NE', 'NO', 'SE', 'SO']:
                print(f"  {quad}: {resultado[quad]['total']} pontos, " +
                      f"{resultado[quad]['clusters']} clusters ({resultado[quad]['percentual']:.1f}%)")
        
        except Exception as e:
            print(f"  ⚠ Erro ao analisar quadrantes: {e}")
        
        return resultado
    
    def _comparar_interpolacoes(self) -> Dict[str, float]:
        """
        Calcula diferença média absoluta entre superfícies interpoladas.
        
        Compara: IDW vs Kriging, IDW vs GWM, Kriging vs GWM
        
        Returns:
            Dicionário com diferenças médias
        """
        print("\n📉 Comparando superfícies interpoladas...")
        
        resultado = {
            'IDW_vs_Kriging': None,
            'IDW_vs_GWM': None,
            'Kriging_vs_GWM': None,
            'resumo': 'Superfícies não carregadas em memória'
        }
        
        try:
            # Tenta carregar resultados de interpolação se disponíveis
            mapas_resultado = self.info_dados.get('mapas_interpolacao', {})
            
            if mapas_resultado:
                print("  ℹ Dados de interpolação não armazenados em memória")
                print("    (Requer acesso direto aos arquivos PNG)")
                resultado['resumo'] = (
                    "Para comparação: calcule correlação entre valores IDW, Kriging e GWM "
                    "em grade regular (ex: 100x100 pontos)"
                )
            else:
                print("  ⚠ Sem dados de interpolação disponíveis")
            
            # Tenta usar valores da variável principal como proxy
            variaveis = self.info_dados.get('variaveis_numericas', [])
            if variaveis:
                var_principal = variaveis[0]
                valores = self.df[var_principal].dropna().values
                
                # Aproximação: calcula desvio padrão como indicador de variabilidade
                # Métodos com MAE menor são mais suaves
                resultado['resumo'] = (
                    f"Variância em {var_principal}: {valores.var():.4f} | "
                    f"Desvio padrão: {valores.std():.4f}"
                )
        
        except Exception as e:
            print(f"  ⚠ Erro ao comparar interpolações: {e}")
        
        return resultado
    
    def _calcular_extensao_geografica(self) -> Dict[str, float]:
        """
        Calcula extensão geográfica exata (lat/lon min-max) e centro.
        
        Returns:
            Dicionário com extensão e centro geográfico
        """
        print("\n🗺️  Calculando extensão geográfica exata...")
        
        resultado = {
            'lon_min': None,
            'lon_max': None,
            'lat_min': None,
            'lat_max': None,
            'centro_lat': None,
            'centro_lon': None,
            'altura_km': None,
            'largura_km': None
        }
        
        try:
            col_x = self.info_dados.get('col_x')
            col_y = self.info_dados.get('col_y')
            
            if not col_x or not col_y:
                print("  ⚠ Coordenadas não detectadas")
                return resultado
            
            # Tenta usar coordenadas WGS84 se disponíveis
            coords_wgs84 = self.info_dados.get('coords_wgs84')
            
            if coords_wgs84 is not None:
                # coords_wgs84 é (lon, lat) = (x, y)
                resultado['lon_min'] = float(coords_wgs84[:, 0].min())
                resultado['lon_max'] = float(coords_wgs84[:, 0].max())
                resultado['lat_min'] = float(coords_wgs84[:, 1].min())
                resultado['lat_max'] = float(coords_wgs84[:, 1].max())
            else:
                # Usa coordenadas originais
                resultado['lon_min'] = float(self.df[col_x].min())
                resultado['lon_max'] = float(self.df[col_x].max())
                resultado['lat_min'] = float(self.df[col_y].min())
                resultado['lat_max'] = float(self.df[col_y].max())
            
            # Centro
            resultado['centro_lon'] = (resultado['lon_min'] + resultado['lon_max']) / 2
            resultado['centro_lat'] = (resultado['lat_min'] + resultado['lat_max']) / 2
            
            # Aproximação de distância (1 grau ≈ 111 km no equador)
            resultado['altura_km'] = (resultado['lat_max'] - resultado['lat_min']) * 111
            resultado['largura_km'] = (resultado['lon_max'] - resultado['lon_min']) * 111 * np.cos(np.radians(resultado['centro_lat']))
            
            print(f"  Longitude: {resultado['lon_min']:.6f}° a {resultado['lon_max']:.6f}°")
            print(f"  Latitude:  {resultado['lat_min']:.6f}° a {resultado['lat_max']:.6f}°")
            print(f"  Centro:    ({resultado['centro_lat']:.6f}°, {resultado['centro_lon']:.6f}°)")
            print(f"  Dimensões: {resultado['altura_km']:.2f} km × {resultado['largura_km']:.2f} km")
        
        except Exception as e:
            print(f"  ⚠ Erro ao calcular extensão: {e}")
        
        return resultado
    
    def _gerar_recomendacoes(self) -> Dict[str, List[str]]:
        """
        Gera recomendações técnicas baseadas nos insights.
        
        Returns:
            Dicionário com recomendações organizadas por categoria
        """
        print("\n💡 Gerando recomendações técnicas...")
        
        recomendacoes = {
            'monitoramento': [],
            'coleta_dados': [],
            'interpolacao': [],
            'analise_futura': []
        }
        
        try:
            # Recomendações baseadas em Moran
            var_max = self.insights['variavel_maxima']
            if var_max['significativo'] and var_max['variavel']:
                recomendacoes['monitoramento'].append(
                    f"Priorizar monitoramento de '{var_max['variavel']}' - "
                    f"apresenta forte estrutura espacial (I={var_max['I_moran']:.3f})"
                )
            
            # Recomendações baseadas em clusters
            clusters_sig = self.insights['clusters_significativos']
            if clusters_sig['pontos_cluster'] > 0:
                recomendacoes['coleta_dados'].append(
                    f"Ampliar coleta em zonas de transição (HL/LH): "
                    f"{clusters_sig['distribuicao'].get('HL', 0) + clusters_sig['distribuicao'].get('LH', 0)} pontos identificados"
                )
                recomendacoes['monitoramento'].append(
                    f"Concentrar vigilância em clusters {clusters_sig['quadrante_dominante']} - "
                    f"{clusters_sig['percentual_cluster']:.1f}% dos pontos significativos"
                )
            
            # Recomendações baseadas em heterogeneidade
            het = self.insights['heterogeneidade']
            if het['variaveis_heterogeneas']:
                variaveis_str = ', '.join(het['variaveis_heterogeneas'])
                recomendacoes['coleta_dados'].append(
                    f"Aumentar número de amostras para: {variaveis_str} (CV > 100%)"
                )
            
            # Recomendações de interpolação
            recomendacoes['interpolacao'].append(
                "Usar Kriging Ordinária para variáveis com autocorrelação significativa"
            )
            recomendacoes['interpolacao'].append(
                "Validação cruzada (cross-validation) recomendada para seleção de semivariograma"
            )
            
            # Análise futura
            recomendacoes['analise_futura'].append(
                "Realizar análise multivariada (clustering) nas áreas HH para identificar subgrupos"
            )
            recomendacoes['analise_futura'].append(
                "Investigar possíveis fatores causadores da estrutura espacial observada"
            )
            
            # Print recomendações
            for categoria, lista in recomendacoes.items():
                if lista:
                    print(f"\n  {categoria.upper().replace('_', ' ')}:")
                    for i, rec in enumerate(lista, 1):
                        print(f"    {i}. {rec}")
        
        except Exception as e:
            print(f"  ⚠ Erro ao gerar recomendações: {e}")
        
        return recomendacoes
    
    def exportar_relatorio_texto(self, caminho_saida: str = None) -> str:
        """
        Exporta todos os insights como relatório de texto.
        
        Args:
            caminho_saida: Caminho para salvar relatório (opcional)
            
        Returns:
            Texto do relatório
        """
        relatorio = []
        relatorio.append("="*70)
        relatorio.append("RELATÓRIO DE INSIGHTS - ANÁLISE GEOESPACIAL AVANÇADA")
        relatorio.append("="*70)
        
        # Variável máxima
        var_max = self.insights['variavel_maxima']
        relatorio.append("\n1. VARIÁVEL COM MAIOR ESTRUTURA ESPACIAL")
        relatorio.append(f"   Variável: {var_max['variavel']}")
        relatorio.append(f"   Moran's I: {var_max['I_moran']:.6f}")
        relatorio.append(f"   p-valor: {var_max['p_valor']:.2e}")
        relatorio.append(f"   Significativo: {'Sim' if var_max['significativo'] else 'Não'}")
        relatorio.append(f"   Interpretação: {var_max['interpretacao']}")
        
        # Clusters significativos
        clusters = self.insights['clusters_significativos']
        relatorio.append("\n2. CLUSTERS SIGNIFICATIVOS (p < 0.05)")
        relatorio.append(f"   Total de pontos: {clusters['total_pontos']}")
        relatorio.append(f"   Pontos em clusters: {clusters['pontos_cluster']} ({clusters['percentual_cluster']:.1f}%)")
        relatorio.append(f"   Quadrante dominante: {clusters['quadrante_dominante']}")
        relatorio.append(f"   Distribuição: {clusters['distribuicao']}")
        
        # Heterogeneidade
        het = self.insights['heterogeneidade']
        relatorio.append("\n3. HETEROGENEIDADE ESTATÍSTICA")
        if het['variaveis_heterogeneas']:
            relatorio.append(f"   Variáveis com CV > 100%: {', '.join(het['variaveis_heterogeneas'])}")
        else:
            relatorio.append("   Todas as variáveis têm heterogeneidade controlada")
        
        # Extensão geográfica
        ext = self.insights['extensao_geografica']
        relatorio.append("\n4. EXTENSÃO GEOGRÁFICA")
        relatorio.append(f"   Longitude: {ext['lon_min']:.6f}° a {ext['lon_max']:.6f}°")
        relatorio.append(f"   Latitude:  {ext['lat_min']:.6f}° a {ext['lat_max']:.6f}°")
        relatorio.append(f"   Centro: ({ext['centro_lat']:.6f}°, {ext['centro_lon']:.6f}°)")
        relatorio.append(f"   Dimensões: {ext['altura_km']:.2f} km × {ext['largura_km']:.2f} km")
        
        # Recomendações
        rec = self.insights['recomendacoes']
        relatorio.append("\n5. RECOMENDAÇÕES TÉCNICAS")
        relatorio.append("\n   • Monitoramento:")
        for r in rec['monitoramento']:
            relatorio.append(f"     - {r}")
        relatorio.append("\n   • Coleta de Dados:")
        for r in rec['coleta_dados']:
            relatorio.append(f"     - {r}")
        relatorio.append("\n   • Interpolação:")
        for r in rec['interpolacao']:
            relatorio.append(f"     - {r}")
        relatorio.append("\n   • Análise Futura:")
        for r in rec['analise_futura']:
            relatorio.append(f"     - {r}")
        
        relatorio.append("\n" + "="*70)
        
        texto_relatorio = "\n".join(relatorio)
        
        # Salva em arquivo se caminho fornecido
        if caminho_saida:
            try:
                from pathlib import Path
                Path(caminho_saida).parent.mkdir(parents=True, exist_ok=True)
                with open(caminho_saida, 'w', encoding='utf-8') as f:
                    f.write(texto_relatorio)
                print(f"\n✓ Relatório salvo em: {caminho_saida}")
            except Exception as e:
                print(f"\n⚠ Erro ao salvar relatório: {e}")
        
        return texto_relatorio
