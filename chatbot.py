import os
from flask import Flask, render_template, request, jsonify,send_from_directory
import google.generativeai as genai
from dotenv import load_dotenv
import fitz

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


app = Flask(
    __name__,
    template_folder="web/templates",
    static_folder="web/static"
)


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


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/send", methods=["POST"])
def send():
    data = request.get_json()
    user_message = data.get("message", "").lower().strip()

   
    forbidden_keywords = ["futebol", "celebridade", "notícia", "filme"]

    # Lista de exceções 
    #greetings = ["oi","oi,chat","olá","ola,chat","bom dia","bom dia chat","boa tarde","boa tarde chat","boa noite","boa noite chat"]
    thanks = ["obrigado", "obg","obrigada", "valeu","vlw","agradecido","vlw chat","obrigado chat","obrigada chat"]

    # saudação
    #if any(word in user_message for word in greetings):
        #return jsonify({"response": "Olá! 👋 Seja bem-vindo ao ChatBot Unip. Como posso ajudar em seus estudos hoje?"})

    #  agradecimento
    if any(word in user_message for word in thanks):
        return jsonify({"response": "De nada! Estou sempre à disposição para ajudar em suas pesquisas acadêmicas. 📚"})

    
    if any(keyword in user_message for keyword in forbidden_keywords):
        return jsonify({
            "response": "⚠️ Sua pergunta não está relacionada ao meu propósito acadêmico. Por favor, faça uma pergunta sobre pesquisa, bibliografia ou a universidade."
        })

    if not user_message:
        return jsonify({"response": "Mensagem vazia!"})

  
    response = chat.send_message(user_message)
    formatted = getattr(response, "text", str(response)).replace("\n", "<br>")

    return jsonify({"response": formatted})

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
    