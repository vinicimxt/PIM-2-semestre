# 🤖 Chatbot Acadêmico UNIP

## 📖 Sobre o Projeto
O **ChatBot UNIP** é um assistente virtual voltado para **pesquisas e consultas acadêmicas**, desenvolvido com **Flask** e integrado à **API Gemini (Google AI)**.  
Ele foi projetado para auxiliar estudantes e professores em pesquisas, gerar resumos e visualizar conteúdos em PDF de forma rápida e interativa.  

O projeto também conta com um **instalador visual**, que facilita a configuração inicial — permitindo ao usuário inserir sua chave da API Gemini e instalar automaticamente todas as dependências necessárias.

---

## 🧩 Estrutura do Projeto

| Diretório / Arquivo | Descrição |
|----------------------|-----------|
| **Assets** | Conteúdo para consultas |
| **Pdf** | Geração de resumos ou visualização de PDFs |
| **Tools** | Funções para compilar e executar códigos em C |
| **Web** | Armazena os conteúdos Flask |
| ├── **Static** | Arquivos CSS e JavaScript |
| └── **Templates** | Páginas HTML da interface |
| **Teste-C** | Arquivos de teste em linguagem C |
| **.env** | Gerado automaticamente pelo instalador (armazena a chave da API Gemini) |
| **requirements.txt** | Dependências do projeto |
| **chatbot.py** | Arquivo principal — inicializa o chatbot |
| **instalador.py / setup.exe** | Aplicativo visual para configurar a chave da API e instalar dependências |

---

## ⚙️ Tecnologias Utilizadas
- **Python 3**
- **Flask**
- **Google Gemini API**
- **HTML / CSS / JavaScript**
- **dotenv**
- **PySimpleGUI / Tkinter (instalador)**
- **C Compiler Integration**

---

## 🚀 Como Executar o Projeto

### 🪄 Instalação Automática (Recomendada)
1. Execute o instalador **`python chatbot.py`**.  
2. Na janela exibida, cole sua **chave da API Gemini**.  
   - Caso ainda não possua, clique em **“Obter chave do Gemini”** e siga as instruções.  
3. Clique em **“Instalar”**.  
   - O instalador criará o arquivo `.env` com sua chave e instalará automaticamente as dependências do projeto.  
4. Após a instalação, o chatbot estará pronto para uso!

---

### ⚙️ Instalação Manual (opcional)
Se preferir configurar manualmente:
```bash
git clone https://github.com/vinicimxt/PIM-2-semestre.git
cd PIM-2-semestre
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
