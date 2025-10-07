import subprocess
import os
import sys
import re

def run_error_checker(file_path):
    base_dir = os.path.dirname(os.path.dirname(__file__))
    exe_path = os.path.join(base_dir, "tools", "error_checker.exe")
    full_file_path = os.path.join(base_dir, file_path)
    
    if not os.path.exists(exe_path):
        return f"❌ Erro: o executável '{exe_path}' não foi encontrado."
    if not os.path.exists(full_file_path):
        return f"❌ Erro: o arquivo '{full_file_path}' não existe."

    try:
        result = subprocess.run(
            [exe_path, full_file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False
        )

        output = result.stdout or ""
        error = result.stderr or ""

        if not output.strip() and not error.strip():
            return "⚠️ O verificador não retornou nenhuma saída."
        if error.strip():
            return f"❌ Erro durante a execução:\n{error.strip()}"

        # <<< Aqui chamamos a função de tradução
        friendly_output = translate_gcc_errors(output)
        return friendly_output

    except Exception as e:
        return f"Erro ao executar verificador: {e}"


def translate_gcc_errors(gcc_output: str) -> str:
    """
    Recebe a saída do GCC e traduz para mensagens amigáveis.
    """
    lines = gcc_output.splitlines()
    friendly_messages = []

    for line in lines:
        # Detecta falta de ';'
        m = re.search(r'error: expected .+ before', line)
        if m:
            # Extrai a linha do arquivo
            line_num_match = re.search(r':(\d+):', line)
            if line_num_match:
                line_num = line_num_match.group(1)
                friendly_messages.append(f"⚠️ Possível falta de ';' na linha {line_num}.")

        # Detecta chaves desbalanceadas
        if "expected '}'" in line:
            line_num_match = re.search(r':(\d+):', line)
            line_num = line_num_match.group(1) if line_num_match else "?"
            friendly_messages.append(f"⚠️ Chave de fechamento ausente na linha {line_num}.")

        # Outros erros podem ser adicionados aqui
        if "error:" in line and "expected" not in line:
            friendly_messages.append(f"⚠️ GCC: {line.strip()}")

    if not friendly_messages:
        return "✅ Nenhum erro detectado."

    return "\n".join(friendly_messages)