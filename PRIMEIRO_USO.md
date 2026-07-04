# 🚀 PRIMEIRO USO - GUIA PASSO A PASSO

## 🎬 Vídeo Mental: 30 Segundos de Uso

```
⏱️ 0:00  → "python executar.py" + Enter
⏱️ 0:03  → Diálogo abre (explorador de arquivos)
⏱️ 0:05  → Você clica em um arquivo Excel/CSV
⏱️ 0:06  → Clica em "Abrir"
⏱️ 0:08-1:30 → Programa processa (barra de progresso)
⏱️ 1:30  → PDF abre no navegador AUTOMATICAMENTE ✨
⏱️ 1:35  → Você clica em Download
⏱️ 2:00  → Pronto! PDF está no seu Downloads
```

---

## 📋 Checklist Antes de Começar

- ✅ Python 3.8+ instalado
- ✅ Tem um arquivo `.xlsx` (Excel) ou `.csv` (CSV) com dados
- ✅ O arquivo tem colunas com:
  - Latitude (ou Y, ou coordenada norte-sul)
  - Longitude (ou X, ou coordenada leste-oeste)
  - Pelo menos 1 coluna com números para análise

**Não tem dados?** Nenhum problema! Existe um arquivo de teste incluído.

---

## 🎯 AGORA VAMOS COMEÇAR

### Etapa 1️⃣ - Abra o PowerShell
```
Pressione na teclado:  Windows + R
Digite:               powershell
Pressione:            Enter
```

Você vai ver algo como:
```
PS C:\Users\seu_usuario>
```

### Etapa 2️⃣ - Vá para a Pasta Certa
```powershell
cd "C:\Users\seu_usuario\OneDrive\Documentos\Vscode\.github\Aldino2"
```

(Substitua `seu_usuario` pelo seu nome de usuário do Windows)

Vai ficar assim:
```
PS C:\Users\seu_usuario\OneDrive\Documentos\Vscode\.github\Aldino2>
```

### Etapa 3️⃣ - Execute o Programa
```powershell
python executar.py
```

### Etapa 4️⃣ - Selecione Seu Arquivo

Uma **janelinha de explorador** vai abrir. 

Você verá:
- 📁 Pastas (pode abrir qualquer uma)
- 📄 **Todos os arquivos** do seu computador
- Excel `.xlsx` e CSV `.csv` destacados

**O que fazer:**
1. Navegue para encontrar seu arquivo
2. **🖱️ Clique 1 vez** no arquivo para selecioná-lo
3. **Clique no botão "Abrir"**

**Se não conseguir selecionar:**
- Se o diálogo não deixar selecionar, clique em "Cancelar"
- Uma **opção manual** vai aparecer
- Cole ou digite o caminho completo do arquivo
- Exemplo: `C:\Users\seu_usuario\Downloads\dados.xlsx`

**Se quiser testar agora:**
- Seu arquivo PODE estar em:
  ```
  Aldino2/geoestat_analyzer_novo/dados/entrada/
  ```
- Ou **qualquer outro lugar do seu computador**
- O programa busca em TODO LUGAR! 🔍

### Etapa 5️⃣ - Deixe o Programa Trabalhar

Você verá uma progresso assim:
```
Carregando dados...
Detectando coordenadas...
Calculando análise espacial...
Gerando mapas...
Criando relatório...
Abrindo PDF no navegador...
```

⏳ **Demora 30 segundos a 2 minutos** (depende do tamanho do arquivo)

### Etapa 6️⃣ - PDF Abre Automaticamente! 🎉

Seu navegador padrão (Chrome, Edge, Firefox) abre com o PDF.

Você vê:
- 📄 Página 1: Sumário
- 📄 Página 2: Análise Espacial (I de Moran)
- 📄 Página 3-4: Mapas
- 📄 Página 5: Visualizações
- 📄 Página 6: Insights Automáticos

### Etapa 7️⃣ - Salve o PDF

No Navegador (canto superior):
```
Clique em ⬇️ (botão de Download)
```

Escolha onde salvar (Desktop, Downloads, etc.)

---

## ✨ Deu Certo?

Se você conseguiu:
- ✅ Ver o diálogo de arquivo
- ✅ Selecionar um arquivo
- ✅ Ver o programa processando
- ✅ PDF abrir no navegador
- ✅ Baixar o PDF

## **PARABÉNS! 🎊 Você está pronto para usar!**

---

## 🆘 O Que Fazer Se Deu Erro?

### ❌ "python: comando não encontrado"
**Causa:** Python não está instalado ou não está no PATH

**Solução:**
1. Abra https://www.python.org/downloads/
2. Baixe Python 3.10+
3. **IMPORTANTE:** Marque a caixa ☑️ "Add Python to PATH"
4. Termine a instalação
5. Feche o PowerShell e abra novamente
6. Rode `python executar.py` de novo

---

### ❌ "arquivo não encontra" (em Português estranho)
**Causa:** Arquivo não está em formato Excel/CSV, ou caminho está errado

**Solução:**
1. Verifique se seu arquivo termina em `.xlsx` ou `.csv`
2. Tente com o arquivo de teste:
   ```
   Aldino2/geoestat_analyzer_novo/dados/entrada/exemplo_dados_geoespaciais.xlsx
   ```
3. Se o teste funcionar, o seu arquivo tinha problema de formato

---

### ❌ "No module named 'geopandas'"
**Causa:** Dependências não estão instaladas

**Solução:**
1. Digite no PowerShell:
   ```powershell
   pip install -r geoestat_analyzer_novo/requirements.txt
   ```
2. Aguarde terminar (leva 2-3 minutos)
3. Rode `python executar.py` novamente

---

### ❌ PDF não abre
**Causa:** Navegador não está configurado como padrão

**Solução:**
1. Procure a pasta:
   ```
   Aldino2/geoestat_analyzer_novo/dados/saida/
   ```
2. Vire o arquivo `.pdf` manualmente
3. Clique duas vezes nele

---

### ❌ A janela fechou rapidamente
**Causa:** Erro aconteceu muito rápido

**Solução:**
1. Rode assim em vez disso:
   ```powershell
   python executar.py | more
   ```
2. Você verá a mensagem de erro
3. Me mande a mensagem de erro!

---

## 🎓 Entendendo a Análise

O programa calcula:

| Item | O Que É |
|------|---------|
| **I de Moran** | Se seus dados agrupados (clusters) ou espalhados |
| **Mapas** | 5 visualizações diferentes de sua área |
| **Interpolação** | Previsão de valores em áreas sem medições |
| **Insights** | Observações automáticas dos resultados |

**Você não precisa entender isso para usar!** O PDF explica tudo.

---

## 📞 Help! Nada Funcionou

Se tudo deu errado, envie:

1. A mensagem de erro exata (copie e cole do PowerShell)
2. O nome do seu arquivo de dados
3. O tamanho do arquivo (pequeno, médio, grande)
4. A versão do Windows (Win 10, Win 11, etc.)

---

## 🎯 Próximos Passos

Agora que sabe usar:

1. **Teste com seus próprios dados** - Qualquer Excel/CSV com coordenadas
2. **Explore os resultados** - O PDF tem 6 páginas de análises
3. **Compartilhe os PDFs** - Leve para reuniões, apresentações, etc.

---

## 🎉 Aproveite!

Você tem um programa profissional de **análise geoespacial** na mão. 

Divirta-se com os mapas e análises!

**Qualquer dúvida, me avise!** 💬

