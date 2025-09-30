from flask import Flask, render_template, request, jsonify
from src.chatbot import Chatbot

app = Flask(__name__, template_folder="web/templates", static_folder="web/static")
bot = Chatbot()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/perguntar", methods=["POST"])
def perguntar():
    pergunta = request.json.get("pergunta", "")
    return jsonify({"resposta": bot.responder(pergunta)})

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
