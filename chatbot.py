import os
import sqlite3
from flask import Flask, render_template, request, jsonify, send_from_directory
from dotenv import load_dotenv
import fitz
from setup import run_setup
import google.generativeai as genai

# ===============================
# CONFIGURAÇÃO INICIAL
# ===============================

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    run_setup()
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ Nenhuma chave GEMINI_API_KEY encontrada.")
    exit(1)

genai.configure(api_key=api_key)

app = Flask(
    __name__,
    template_folder="web/templates",
    static_folder="web/static"
)

DB_FILE = "chat.db"

# ===============================
# MODELO / PROMPT
# ===============================

system_instruction = {
    "role": "user",
    "parts": [
        "Você é um assistente virtual corporativo de TI, atuando como suporte técnico de primeiro nível (Service Desk). "
        "Ajude colaboradores com dúvidas sobre redes, usuários, impressoras, planilhas e sistemas internos. "
        "Responda de forma clara, objetiva e profissional."
    ]
}

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash-lite",
    system_instruction=system_instruction["parts"][0]
)

chat = model.start_chat()


# ===============================
# BANCO DE DADOS
# ===============================

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_base (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            title TEXT,
            content TEXT
        )
    """)

    conn.commit()
    conn.close()

init_db()

def search_by_title(message):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
        SELECT content
        FROM knowledge_base
        WHERE LOWER(title) LIKE ?
        LIMIT 1
    """, (f"%{message.lower()}%",))

    result = c.fetchone()
    conn.close()

    return result[0] if result else None

def search_knowledge_base(message):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    keywords = message.lower().split()
    conditions = " OR ".join(["content LIKE ?"] * len(keywords))
    params = [f"%{k}%" for k in keywords]

    query = f"""
        SELECT content
        FROM knowledge_base
        WHERE {conditions}
        LIMIT 3
    """

    c.execute(query, params)
    results = c.fetchall()
    conn.close()

    return "\n\n".join([r[0] for r in results])

def search_by_category(message):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
        SELECT title
        FROM knowledge_base
        WHERE LOWER(category) LIKE ?
    """, (f"%{message.lower()}%",))

    results = c.fetchall()
    conn.close()

    return [r[0] for r in results]


# ===============================
# ROTAS
# ===============================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/send_message", methods=["POST"])
def send_message():
    data = request.get_json()
    user_message = data.get("message", "").strip()

    # 1️⃣ Busca direta por título (resposta exata)
    direct_answer = search_by_title(user_message)
    if direct_answer:
        return jsonify({
            "response": direct_answer.replace("\n", "<br>")
        })

    # 2️⃣ Busca por categoria (listar assuntos)
    category_hits = search_by_category(user_message)
    if category_hits:
        sugestoes = "\n".join([f"- {t}" for t in category_hits])
        return jsonify({
            "response": (
                f"📂 Encontrei informações relacionadas a **{user_message}**:\n\n"
                f"{sugestoes}\n\n"
                "👉 Você pode perguntar sobre qualquer um desses tópicos."
            ).replace("\n", "<br>")
        })

    # 3️⃣ Busca geral no conteúdo (apoio à IA)
    kb_content = search_knowledge_base(user_message)
    if not kb_content:
        return jsonify({
            "response": "❌ Não encontrei informações sobre esse assunto na base de conhecimento."
        })

    # 4️⃣ IA só organiza o que já existe
    prompt = f"""
    Use EXCLUSIVAMENTE as informações abaixo.
    Não invente nada.

    Base de conhecimento:
    {kb_content}

    Pergunta:
    {user_message}

    Responda de forma direta e técnica.
    """

    response = model.generate_content(prompt)

    try:
        text = response.candidates[0].content.parts[0].text
    except Exception:
        text = "Erro ao gerar resposta."

    return jsonify({"response": text.replace("\n", "<br>")})



# ===============================
# PDF (opcional)
# ===============================

PDF_FOLDER = "./assets/pdf/"

def extract_text_from_pdf(file_path):
    text = ""
    with fitz.open(file_path) as pdf:
        for page in pdf:
            text += page.get_text()
    return text

@app.route("/resumir_pdf", methods=["POST"])
def resumir_pdf():
    data = request.get_json()
    pdf_name = data.get("pdf_name")

    file_path = os.path.join(PDF_FOLDER, pdf_name)
    if not os.path.exists(file_path):
        return jsonify({"response": "PDF não encontrado."})

    pdf_text = extract_text_from_pdf(file_path)

    prompt = f"Resuma de forma clara e objetiva:\n\n{pdf_text}"

    response = model.generate_content(prompt)
    text = response.candidates[0].content.parts[0].text

    return jsonify({"response": text.replace("\n", "<br>")})

@app.route("/pdf/<path:filename>")
def serve_pdf(filename):
    return send_from_directory(PDF_FOLDER, filename)

# ===============================
# MAIN
# ===============================

if __name__ == "__main__":
    print("Servidor rodando em http://127.0.0.1:5000")
    app.run(debug=True)
