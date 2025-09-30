from .chatbot import Chatbot

def iniciar_chat():
    bot = Chatbot()
    print("🤖 Chatbot Acadêmico iniciado! (digite 'sair' para encerrar)\n")

    while True:
        pergunta = input("Você: ")
        if pergunta.lower() in ["sair", "exit", "quit"]:
            print("👋 Até mais!")
            break

        resposta = bot.responder(pergunta)
        print(f"Bot: {resposta}\n")
