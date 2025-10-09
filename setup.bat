@echo off
echo ==========================================
echo 🚀 Configurando ambiente do projeto Flask
echo ==========================================

REM Criar ambiente virtual
if not exist venv (
    echo 📦 Criando ambiente virtual...
    python -m venv venv
) else (
    echo ⚙️ Ambiente virtual ja existe.
)

REM Ativar ambiente virtual
call venv\Scripts\activate

REM Instalar dependências
echo 📚 Instalando dependências...
pip install --upgrade pip
pip install Flask python-dotenv google-generativeai PyMuPDF requests

REM Verificar instalação do GCC
echo 🔍 Verificando instalação do GCC...
where gcc >nul 2>nul
if %errorlevel%==0 (
    echo ✅ GCC encontrado!
    gcc --version
) else (
    echo ⚠️ GCC nao encontrado.
    echo ➜ Instale o compilador C MinGW-w64:
    echo    https://sourceforge.net/projects/mingw-w64/
)

echo ==========================================
echo ✅ Configuração concluída!
echo Para iniciar o servidor:
echo.
echo     call venv\Scripts\activate
echo     python app.py
echo ==========================================
pause
