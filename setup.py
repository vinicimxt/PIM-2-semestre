import os
import sqlite3
import subprocess

def create_env():
    """Cria o arquivo .env com a chave da API"""
    print("\n=== Configuração da API Gemini ===")
    api_key = input("➡️  Cole aqui sua chave da API do Gemini: ").strip()

    if not api_key:
        print("❌ Nenhuma chave informada. Abortando configuração.")
        return False

    with open(".env", "w", encoding="utf-8") as f:
        f.write(f"GEMINI_API_KEY={api_key}\n")
    
    print("✅ Arquivo .env criado com sucesso!")
    return True


def install_dependencies():
    """Instala dependências do projeto"""
    print("\n📦 Instalando dependências (isso pode levar alguns minutos)...\n")
    try:
        subprocess.check_call(["pip", "install", "-r", "requirements.txt"])
        print("✅ Dependências instaladas com sucesso!")
    except subprocess.CalledProcessError:
        print("⚠️ Erro ao instalar dependências. Tente rodar manualmente: pip install -r requirements.txt")


def init_database():
    """Cria o banco SQLite se não existir"""
    db_file = "chat.db"
    if os.path.exists(db_file):
        print("💾 Banco de dados já existe, pulando criação.")
        return
    
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
    print("✅ Banco de dados criado com sucesso!")


if __name__ == "__main__":
    print("🚀 Iniciando configuração do ChatBot UNIP...\n")
    
    if create_env():
        install_dependencies()
        init_database()
        print("\n🎉 Instalação concluída com sucesso!")
        print("Agora você pode iniciar o app com: python app.py")
    else:
        print("❌ Instalação cancelada.")
