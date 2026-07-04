#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
# SCRIPT PRINCIPAL - ANÁLISE GEOESTATÍSTICA
# ============================================================================
# Executa a pipeline completa:
#   1. Carrega dados
#   2. Detecta coordenadas e variáveis
#   3. Calcula estatísticas
#   4. Converte coordenadas para WGS84
#   5. Gera relatório PDF
# ============================================================================

import sys
import io
from pathlib import Path

# Configurar UTF-8 para Windows
if sys.platform == 'win32':
    import os
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ========== IMPORTS DO SISTEMA ==========
# Adiciona pasta pai ao path para importar módulos
pasta_raiz = Path(__file__).parent.parent
sys.path.insert(0, str(pasta_raiz))

from analise.analisador import AnalisadorGeo
from analise.gerador_relatorio_avancado import GeradorRelatorioAvancado
from analise.gerador_insights_avancado import GeradorInsightsAvancado


def abrir_pdf_navegador(caminho_pdf):
    """
    Abre o PDF no navegador padrão do sistema.
    
    Args:
        caminho_pdf: Path do arquivo PDF
    """
    try:
        import webbrowser
        
        # Converte para URL file://
        url = caminho_pdf.as_uri()
        
        print(f"\n🌐 Abrindo PDF no navegador...")
        webbrowser.open(url)
        
        return True
    except Exception as e:
        print(f"\n⚠️  Não foi possível abrir no navegador: {e}")
        print(f"   O arquivo está em: {caminho_pdf}")
        return False


def abrir_pasta_resultados(caminho_pasta):
    """
    Abre a pasta de resultados no Windows Explorer.
    
    Args:
        caminho_pasta: Path da pasta a abrir
    """
    try:
        import os
        if sys.platform == 'win32':
            # Windows: usa explorer
            os.startfile(str(caminho_pasta))
        elif sys.platform == 'darwin':
            # macOS: usa open
            os.system(f'open "{str(caminho_pasta)}"')
        else:
            # Linux: usa xdg-open
            os.system(f'xdg-open "{str(caminho_pasta)}"')
    except Exception as e:
        pass  # Continua mesmo se falhar ao abrir


def solicitar_arquivo_dados():
    """
    Abre diálogo de seleção de arquivo em QUALQUER LUGAR do computador.
    
    Usa tkinter para abrir um explorador completo do sistema.
    Primeira tentativa com diálogo. Se cancelado, permite digitação manual.
    
    Returns:
        Path do arquivo selecionado ou None se cancelado
    """
    print("\n" + "="*70)
    print("📂 SELEÇÃO DE ARQUIVO DE DADOS")
    print("="*70)
    print("\n🖥️  Abrindo explorador de arquivos...")
    print("    Selecione um arquivo .xlsx ou .csv em seu computador")
    
    try:
        from tkinter import Tk, filedialog
        import os
        
        root = Tk()
        root.withdraw()  # Esconde janela principal
        root.attributes('-topmost', True)  # Traz janela para frente
        
        # Começa na pasta do usuário
        pasta_inicial = str(Path.home())
        
        # Abre diálogo - APENAS ARQUIVOS (não pastas)
        # IMPORTANTE: "All Files" primeiro para evitar filtro problema do Windows
        caminho = filedialog.askopenfilename(
            title="📊 Selecione um arquivo EXCEL ou CSV para análise\n\n(Se não conseguir selecionar, cancele e aparecerá outra opção)",
            initialdir=pasta_inicial,
            filetypes=[
                ("All Files", "*.*"),
                ("Excel Files", "*.xlsx"),
                ("CSV Files", "*.csv")
            ]
        )
        
        root.destroy()
        
        if caminho and caminho.strip():
            arquivo = Path(caminho)
            if arquivo.is_file():
                print(f"\n✅ Arquivo selecionado: {arquivo.name}")
                print(f"   Local: {arquivo.parent}")
                return arquivo
            else:
                print(f"\n❌ Seleção não é um arquivo válido")
                return None
        else:
            # Se usuário cancelou diálogo, oferece alternativa de digitação manual
            print("\n🔄 Nenhum arquivo selecionado no diálogo")
            print("\n💡 OPÇÃO 2: Digite o caminho do arquivo manualmente")
            print("   (Cole o caminho completo do arquivo)")
            print("\nExemplos:")
            print("   C:\\Users\\seu_usuario\\Downloads\\dados.xlsx")
            print("   C:\\Users\\seu_usuario\\Desktop\\analise.csv")
            
            caminho_digitado = input("\n📝 Caminho do arquivo (ou Enter para cancelar): ").strip()
            
            if caminho_digitado:
                arquivo = Path(caminho_digitado)
                if arquivo.is_file():
                    print(f"\n✅ Arquivo encontrado: {arquivo.name}")
                    return arquivo
                else:
                    print(f"\n❌ Arquivo não encontrado: {caminho_digitado}")
                    return None
            else:
                print("\n❌ Nenhum arquivo foi selecionado")
                return None
            
    except Exception as e:
        print(f"\n❌ Erro ao abrir diálogo: {e}")
        print("\n💡 OPÇÃO 2: Digite o caminho do arquivo manualmente")
        print("   (Cole o caminho completo do arquivo)")
        
        caminho_digitado = input("\n📝 Caminho do arquivo (ou Enter para cancelar): ").strip()
        
        if caminho_digitado:
            arquivo = Path(caminho_digitado)
            if arquivo.is_file():
                print(f"\n✅ Arquivo encontrado: {arquivo.name}")
                return arquivo
            else:
                print(f"\n❌ Arquivo não encontrado: {caminho_digitado}")
                return None
        else:
            return None


def main():
    """
    Executa a pipeline complete de análise e geração de relatório.
    
    Inclui análise espacial avançada (Moran Global, LISA) e visualizações.
    
    Returns:
        True se sucesso, False se erro
    """
    
    # ========== EXIBE CABEÇALHO ==========
    print("\n" + "="*70)
    print(" "*15 + "ANALISADOR GEOESTATÍSTICO v2.0")
    print(" "*10 + "Com Análise Avançada de Autocorrelação Espacial")
    print("="*70)
    
    # ========== SOLICITA ARQUIVO AO USUÁRIO ==========
    arquivo_dados = solicitar_arquivo_dados()  # Seleciona de qualquer lugar do PC
    
    if not arquivo_dados:
        print("\n❌ ERRO: Nenhum arquivo de dados selecionado!")
        print("\n📍 Instruções:")
        print("   1. Selecione um arquivo Excel (.xlsx) ou CSV (.csv) da lista")
        print("   2. O arquivo precisa conter colunas com coordenadas (X, Y, Lon, Lat, etc)")
        print("   3. Execute novamente este script")
        print("\n" + "="*70 + "\n")
        return False
    
    try:
        # ========== ETAPA 1: ANÁLISE DOS DADOS ==========
        print(f"\n📂 Arquivo encontrado: {arquivo_dados.name}")
        print("\n" + "-"*70)
        
        analisador = AnalisadorGeo(str(arquivo_dados))
        info_analise = analisador.analisar()
        
        print("\n" + "-"*70)
        
        # ========== ETAPA 2: ANÁLISE DE AUTOCORRELAÇÃO ESPACIAL ==========
        print("\n🔍 Realizando análise de autocorrelação espacial...")
        print("-"*70)
        
        analise_espacial = analisador.analisar_autocorrelacao_espacial()
        
        if analise_espacial:
            print("\n✓ Análise de Moran completa")
        else:
            print("\n⚠ Análise espacial não disponível")
        
        print("\n" + "-"*70)
        
        # ========== ETAPA 3: GERAÇÃO DE VISUALIZAÇÕES ESPACIAIS ==========
        if analise_espacial:
            print("\n📈 Gerando visualizações de autocorrelação espacial...")
            print("-"*70)
            
            figuras = analisador.gerar_visualizacoes_espaciais()
            
            print("\n" + "-"*70)
        
        # ========== ETAPA 4: GERAÇÃO DE MAPAS DE INTERPOLAÇÃO ==========
        print("\n🗺️  Gerando mapas de interpolação geoespacial...")
        print("-"*70)
        
        mapas_resultado = analisador.gerar_mapas_interpolacao()
        
        print("\n" + "-"*70)
        
        # ========== ETAPA 5: GERAÇÃO DE VISUALIZAÇÕES DE DISTRIBUIÇÃO ==========
        print("\n📊 Gerando visualizações de distribuição e correlação...")
        print("-"*70)
        
        vis_resultado = analisador.gerar_visualizacoes_distribuicao()
        
        print("\n" + "-"*70)
        
        # ========== ETAPA 6: GERAÇÃO DE INSIGHTS AVANÇADOS ==========
        print("\n💡 Gerando insights avançados baseados nos resultados...")
        print("-"*70)
        
        gerador_insights = GeradorInsightsAvancado(analisador)
        insights = gerador_insights.gerar_todos_insights()
        
        # Armazena insights no analisador para uso no relatório
        analisador.info_dados['insights'] = insights
        
        # Exporta relatório de texto
        from pathlib import Path as PathlibPath
        import tempfile
        
        # Usa pasta TEMPORÁRIA do sistema (não salva no projeto)
        pasta_saida = PathlibPath(tempfile.gettempdir()) / "GeoestatAnalise"
        pasta_saida.mkdir(parents=True, exist_ok=True)
        
        arquivo_insights = pasta_saida / f"Insights_{PathlibPath(analisador.caminho_arquivo).stem}.txt"
        texto_insights = gerador_insights.exportar_relatorio_texto(str(arquivo_insights))
        
        print("\n" + "-"*70)
        
        # ========== ETAPA 7: GERAÇÃO DO RELATÓRIO PDF AVANÇADO ==========
        print("\n📋 Gerando relatório PDF profissional (6 páginas + Insights)...")
        print("-"*70)
        
        # Passa a pasta temporária para o gerador
        gerador = GeradorRelatorioAvancado(analisador, caminho_saida=str(pasta_saida))
        caminho_relatorio = gerador.gerar()
        
        # ========== RESUMO FINAL ==========
        print("="*70)
        print("\n✅ ANÁLISE COMPLETA COM SUCESSO!")
        print(f"\n📄 Relatório PDF:")
        print(f"   {Path(caminho_relatorio).name}")
        
        # Abre automaticamente no navegador
        print("\n🌐 Abrindo PDF no navegador...")
        abrir_pdf_navegador(Path(caminho_relatorio))
        
        if mapas_resultado and isinstance(mapas_resultado, dict) and 'mapa_osm' in mapas_resultado:
            print(f"\n✓ Mapas interpolados: 5 mapas em alta definição (300 DPI)")
        
        if vis_resultado and isinstance(vis_resultado, dict) and 'histogramas' in vis_resultado:
            print(f"✓ Visualizações: 3 gráficos de análise + relatório HTML")
        
        print(f"\n💾 Todos os arquivos estão em pasta temporária do seu computador")
        print(f"   (Você pode baixar diretamente do navegador)")
        
        print("\n" + "="*70 + "\n")
        print("✅ Para mais análises, execute novamente: python executar.py")
        
        return True
        
    except Exception as erro:
        # ========== TRATAMENTO DE ERROS ==========
        print(f"\n❌ ERRO durante a análise:")
        print(f"   {str(erro)}")
        import traceback
        traceback.print_exc()
        print("\n" + "="*70 + "\n")
        return False


if __name__ == "__main__":
    # Executa e define código de saída
    sucesso = main()
    sys.exit(0 if sucesso else 1)
