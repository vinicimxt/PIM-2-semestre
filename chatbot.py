import os
from functools import wraps
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
import google.generativeai as genai
from dotenv import load_dotenv
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import fitz

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


app = Flask(
    __name__,
    template_folder="web/templates",
    static_folder="web/static"
)
app.secret_key = "supersecretkey" 
DB_FILE = "chat.db"

system_instruction = {
    "role": "user",
    "parts": ["Você é um assistente de pesquisa e orientação acadêmica da Unip. Sua principal função é fornecer informações confiáveis e baseadas em evidências para estudantes, professores e pesquisadores. Mantenha um tom formal e profissional. Responda apenas sobre temas acadêmicos, evitando gírias, opiniões pessoais ou conversas informais. Se não puder responder de forma acadêmica, diga educadamente que não pode ajudar."],
}

model_response_ack = {
    "role": "model",
    "parts": ["Entendido. Como assistente acadêmico, estou pronto para ajudar com suas perguntas."],
}


model = genai.GenerativeModel("gemini-2.5-flash-lite")


chat = model.start_chat(history=[system_instruction, model_response_ack])

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message TEXT,
            response TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Registro
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    
    hashed = generate_password_hash(password)
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
        conn.commit()
        conn.close()
        return jsonify({"status": "ok", "message": "Usuário registrado com sucesso!"})
    except sqlite3.IntegrityError:
        return jsonify({"status": "error", "message": "Usuário já existe!"})

# Login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated_function


@app.route("/login_page")
def login_page():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():
    
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, password FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()

    if user and check_password_hash(user[1], password):
        session["user_id"] = user[0]
        session["username"] = username 
        return jsonify({"status": "ok", "message": "Login realizado!"})
    return jsonify({"status": "error", "message": "Usuário ou senha incorretos."})


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("login_page"))

# Enviar mensagem (com histórico)



@app.route("/send", methods=["POST"])
def send_message():
    if "user_id" not in session:
        return jsonify({"response": "Você precisa estar logado."})

    data = request.get_json()
    user_message = data.get("message", "").strip().lower()

    if not user_message:
        return jsonify({"response": "Mensagem vazia!"})

    username = session.get("username", "usuário(a)")

    # Listas de palavras-chave
    greetings = ["oi", "olá", "ola", "bom dia", "boa tarde", "boa noite"]
    thanks = ["obrigado", "obg","obrigada","valeu","vlw","agradecido","vlw chat","obrigado chat","obrigada chat"]
    forbidden_keywords = ["futebol", "celebridade", "notícia", "filme"]

    # --- CHECAGENS ANTES DO GEMINI ---
    response_text = None

    # 1️⃣ Saudação
    if any(greet in user_message for greet in greetings):
        response_text = f"""
Olá {username},em que posso te ajudar hoje?
"""
    # 2️⃣ Agradecimento
    elif any(word in user_message for word in thanks):
        response_text = "De nada! Estou sempre à disposição para ajudar em suas pesquisas acadêmicas. 📚"
    # 3️⃣ Palavras proibidas
    elif any(keyword in user_message for keyword in forbidden_keywords):
        response_text = "⚠️ Sua pergunta não está relacionada ao meu propósito acadêmico. Por favor, faça uma pergunta sobre pesquisa, bibliografia ou a universidade."
    
    # 4️⃣ Mensagem acadêmica → chama Gemini
    else:
        response = chat.send_message(user_message)
        response_text = getattr(response, "text", str(response)).replace("\n", "<br>")

    # --- SALVAR NO BANCO ---
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO messages (user_id, message, response) VALUES (?, ?, ?)",
              (session["user_id"], user_message, response_text))
    conn.commit()
    conn.close()

    return jsonify({"response": response_text})



# Recuperar histórico
@app.route("/history")
def history():
    if "user_id" not in session:
        return jsonify([])

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        SELECT message, response, timestamp 
        FROM messages 
        WHERE user_id=? 
        ORDER BY timestamp
    """, (session["user_id"],))
    msgs = c.fetchall()
    conn.close()
    return jsonify(msgs)

@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/send", methods=["POST"])


# Função para extrair texto do PDF
def extract_text_from_pdf(file_path):
    text = ""
    with fitz.open(file_path) as pdf:
        for page in pdf:
            text += page.get_text()
    return text

PDF_FOLDER = "./assets/pdf/"

@app.route("/resumir_pdf", methods=["POST"])
def resumir_pdf():
    data = request.get_json()
    pdf_name = data.get("pdf_name")

    file_path = os.path.join(PDF_FOLDER, pdf_name)
    if not os.path.exists(file_path):
        return jsonify({"response": "⚠️ PDF não encontrado no servidor."})

    pdf_text = extract_text_from_pdf(file_path)

    # Criar prompt de resumo
    prompt = f"Resuma de forma clara e objetiva o seguinte conteúdo:\n\n{pdf_text}"

    response = chat.send_message(prompt)
    formatted = getattr(response, "text", str(response)).replace("\n", "<br>")

    return jsonify({"response": formatted})

@app.route("/pdf/<path:filename>")
def serve_pdf(filename):
    return send_from_directory(PDF_FOLDER, filename)

# Flask
if __name__ == "__main__":
    print("Servidor rodando em http://127.0.0.1:5000")
    app.run(debug=True)
    