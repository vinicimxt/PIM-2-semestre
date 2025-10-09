import os
import sqlite3
import subprocess
import platform
import tkinter as tk
from tkinter import messagebox
import webbrowser

# === Funções principais ===
def open_gemini_page():
    webbrowser.open("https://aistudio.google.com/app/apikey", new=2)

def create_env(api_key):
    with open(".env", "w", encoding="utf-8") as f:
        f.write(f"GEMINI_API_KEY={api_key}\n")

def install_dependencies():
    try:
        subprocess.check_call(["pip", "install", "-r", "requirements.txt"])
        return True
    except subprocess.CalledProcessError:
        return False

def init_database():
    db_file = "chat.db"
    if not os.path.exists(db_file):
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            );
        """)
        conn.commit()
        conn.close()

def check_gcc():
    try:
        subprocess.check_output(["gcc", "--version"])
        return True
    except FileNotFoundError:
        return False

# === Função para rodar o setup ===
def run_setup():
    def start_installation():
        api_key = api_entry.get().strip()
        if not api_key:
            messagebox.showwarning(
                "Chave necessária",
                "Você precisa inserir sua chave da API do Gemini para continuar.\n\n"
                "Se ainda não tiver uma, clique no botão 'Obter chave do Gemini'."
            )
            return

        create_env(api_key)
        status_label.config(text="🔧 Instalando dependências...")
        root.update()

        if not install_dependencies():
            messagebox.showerror(
                "Erro",
                "Falha ao instalar dependências.\n"
                "Tente rodar manualmente: pip install -r requirements.txt"
            )
            return

        status_label.config(text="💾 Criando banco de dados...")
        root.update()
        init_database()

        status_label.config(text="🧰 Verificando GCC...")
        root.update()
        if not check_gcc():
            system = platform.system()
            if system == "Windows":
                messagebox.showinfo(
                    "GCC não encontrado",
                    "O compilador GCC é necessário para rodar o verificador de código em C.\n\n"
                    "Baixe o MinGW ou TDM-GCC:\nhttps://jmeubank.github.io/tdm-gcc/"
                )
            elif system == "Linux":
                messagebox.showinfo(
                    "GCC não encontrado",
                    "O GCC não foi encontrado.\n\nInstale com:\n  sudo apt install build-essential"
                )
            else:
                messagebox.showinfo(
                    "GCC não encontrado",
                    "O GCC não foi encontrado.\nInstale-o manualmente conforme seu sistema."
                )

        status_label.config(text="✅ Instalação concluída com sucesso!")
        messagebox.showinfo(
            "Instalação concluída",
            "Tudo pronto! Agora você pode iniciar o ChatBot com:\n\npython chatbot.py"
        )
        root.destroy()  # fecha a janela após o setup

    # === Interface gráfica ===
    global root, api_entry, status_label
    root = tk.Tk()
    root.title("Instalador do ChatBot UNIP")
    root.geometry("520x400")
    root.resizable(False, False)

    tk.Label(root, text="🤖 Instalador do ChatBot UNIP", font=("Segoe UI", 16, "bold")).pack(pady=20)
    tk.Label(root,
             text="Cole abaixo sua chave da API Gemini (necessária para usar o chatbot):",
             font=("Segoe UI", 11), wraplength=450, justify="center").pack(pady=5)

    api_entry = tk.Entry(root, width=45, font=("Segoe UI", 11))
    api_entry.pack(pady=5)

    tk.Button(root, text="🔗 Obter chave do Gemini", font=("Segoe UI", 10, "bold"), bg="#f1f1f1",
              command=open_gemini_page).pack(pady=5)

    tk.Button(root, text="🚀 Instalar", font=("Segoe UI", 12, "bold"), bg="#0078D7", fg="white", padx=20, pady=8,
              command=start_installation).pack(pady=20)

    status_label = tk.Label(root, text="Aguardando ação...", font=("Segoe UI", 10), fg="gray")
    status_label.pack(pady=10)

    root.mainloop()
