import os
from functools import wraps
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
import google.generativeai as genai
from dotenv import load_dotenv
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import fitz
import re
from tools.error_checker_runner import run_error_checker
import string

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


app = Flask(
    __name__,
    template_folder="web/templates",
    static_folder="web/static",
    
)
app.secret_key = "supersecretkey" 
DB_FILE = "chat.db"

system_instruction = {
    "role": "user",
    "parts": ["Você é um assistente de pesquisa e orientação acadêmica da Unip. Sua principal função é fornecer informações confiáveis e baseadas em evidências para estudantes, professores e pesquisadores. Mantenha um tom formal e profissional. Responda apenas sobre temas acadêmicos, evitando gírias, opiniões pessoais ou conversas informais. Se não puder responder de forma acadêmica, diga educadamente que não pode ajudar."
    "Só responda com saudações ou agradecimentos se a mensagem do usuário realmente for uma saudação ou agradecimento. "
    "Se não for, responda educadamente que não pode ajudar fora do contexto acadêmico."],
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



@app.route("/check_code_page", methods=["GET"])
def check_code_page():
    return render_template("check_code.html")

# Rota para processar a verificação (executa o C)
@app.route("/check_code", methods=["POST"])
def check_code():
    data = request.get_json()
    file_to_check = data.get("file", "pim_code.c")
    result = run_error_checker(file_to_check)
    return jsonify({"response": result})

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



@app.route("/send_message", methods=["POST"])
def send_message():
    try:
        data = request.get_json()
        user_message = data.get("message", "").strip()
        username = session.get("username", "usuário")

        greetings = ["oi", "olá", "ola", "bom dia", "boa tarde", "boa noite"]
        thanks = ["obrigado", "valeu", "agradeço", "obg"]
        forbidden_keywords = ["sexo", "piada", "bobagem", "xingar"]
        question_words = ["quem", "o que", "onde", "quando", "como", "qual", "quais"]

        # Função para verificar palavras isoladas
        def contains_whole_word(word_list, text):
            words = re.findall(r'\b\w+\b', text.lower())
            return any(word in words for word in word_list)

        # Função para detectar se a mensagem é uma pergunta
        def is_question(text):
            if "?" in text:
                return True
            words = re.findall(r'\b\w+\b', text.lower())
            return any(qw in words for qw in question_words)

        # Prioridade: perguntas ou código não devem cair em greetings
        if is_question(user_message):
            # Pergunta, envia para o modelo
            local_chat = model.start_chat(history=[system_instruction, model_response_ack])
            response = local_chat.send_message(user_message)
            try:
                response_text = response.candidates[0].content.parts[0].text
            except Exception:
                response_text = str(response)
            response_text = response_text.replace("\n", "<br>")

        # Regras rápidas: greetings, thanks, forbidden_keywords
        elif contains_whole_word(greetings, user_message):
            response_text = f"Olá {username}, em que posso te ajudar hoje?"
        elif contains_whole_word(thanks, user_message):
            response_text = "De nada! Estou sempre à disposição para ajudar em suas pesquisas acadêmicas. 📚"
        elif contains_whole_word(forbidden_keywords, user_message):
            response_text = "⚠️ Sua pergunta não está relacionada ao meu propósito acadêmico. Por favor, faça uma pergunta sobre pesquisa, bibliografia ou a universidade."
        else:
            # Mensagem comum, envia para o modelo
            local_chat = model.start_chat(history=[system_instruction, model_response_ack])
            response = local_chat.send_message(user_message)
            try:
                response_text = response.candidates[0].content.parts[0].text
            except Exception:
                response_text = str(response)
            response_text = response_text.replace("\n", "<br>")

        # Salva mensagem no banco
        user_id = session.get("user_id")
        if user_id:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute(
                "INSERT INTO messages (user_id, message, response) VALUES (?, ?, ?)",
                (user_id, user_message, response_text)
            )
            conn.commit()
            conn.close()

        return jsonify({"response": response_text})

    except Exception as e:
        print("Erro no send_message:", e)
        return jsonify({"response": "⚠️ Ocorreu um erro ao processar sua mensagem."}), 500






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
    