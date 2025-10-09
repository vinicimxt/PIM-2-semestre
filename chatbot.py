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
from setup import run_setup


load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    # Chave não existe, abre setup visual
    run_setup()
    # Após o setup, recarrega a chave
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")

import google.generativeai as genai

genai.configure(api_key=api_key)
print("✅ Chatbot iniciado com sucesso!")

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

@app.route("/")
@login_required
def index():
    return render_template("index.html")


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
@login_required
def send_message():
    try:
        data = request.get_json()
        user_message = data.get("message", "").strip()
        username = session.get("username", "usuário")

        # Detecta se o usuário enviou código C (heurística simples)
        if re.search(r'#include|int\s+main\s*\(|printf\s*\(', user_message):
            # Salva o código
            temp_path = "temp_user_code.c"
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(user_message)

            # Roda o verificador de erros em C
            gcc_output = run_error_checker(temp_path)

            # Monta a análise em Python
            analysis = []
            if "expected" in gcc_output:
                analysis.append("🔹 Parece haver um erro de sintaxe, possivelmente falta um ponto e vírgula ou parêntese.")
            if "return" not in user_message:
                analysis.append("🔹 O código não possui uma instrução de retorno em `main()`. Considere adicionar `return 0;`.")
            if "printf" not in user_message:
                analysis.append("🔹 Não encontrei nenhum `printf`. Está certo disso? Talvez queira imprimir algo para depurar o programa.")
            if "{" not in user_message or "}" not in user_message:
                analysis.append("🔹 As chaves `{}` parecem desbalanceadas. Verifique se todas estão abrindo e fechando corretamente.")

            python_feedback = "\n".join(analysis) if analysis else "✅ Nenhum problema estrutural detectado."

            # Gera explicação do Gemini com base no resultado
            prompt = f"""
            Analise o seguinte código C e os erros detectados.

            Código:
            {user_message}

            Saída do compilador:
            {gcc_output}

            Sugestões do analisador Python:
            {python_feedback}

            Dê um parecer técnico:
            - Explique de forma clara o que o compilador quis dizer.
            - Mostre o que corrigir.
            - Dê boas práticas de C (organização, comentários, clareza).
            """

            local_chat = model.start_chat(history=[system_instruction, model_response_ack])
            response = local_chat.send_message(prompt)

            try:
                response_text = response.candidates[0].content.parts[0].text
            except Exception:
                response_text = str(response)

            response_text = response_text.replace("\n", "<br>")
        
        else:
            # Conversa normal
            local_chat = model.start_chat(history=[system_instruction, model_response_ack])
            response = local_chat.send_message(user_message)

            try:
                response_text = response.candidates[0].content.parts[0].text
            except Exception:
                response_text = str(response)

            response_text = response_text.replace("\n", "<br>")

        return jsonify({"response": response_text})

    except Exception as e:
        print("Erro no send_message:", e)
        return jsonify({"response": "⚠️ Ocorreu um erro ao processar sua mensagem."}), 500




@app.route("/check_code_page", methods=["GET"])
@login_required
def check_code_page():
    
    return render_template("check_code.html")

# Rota para processar a verificação (executa o C)
@app.route("/check_code", methods=["POST"])

def check_code():
    data = request.get_json()
    file_to_check = data.get("file", "pim_code.c")
    result = run_error_checker(file_to_check)
    return jsonify({"response": result})

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




def extract_text_from_pdf(file_path):
    text = ""
    with fitz.open(file_path) as pdf:
        for page in pdf:
            text += page.get_text()
    return text

PDF_FOLDER = "./assets/pdf/"

@app.route("/resumir_pdf", methods=["POST"])
@login_required
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
    