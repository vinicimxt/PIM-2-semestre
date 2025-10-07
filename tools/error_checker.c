#include <stdio.h>
#include <string.h>
#include <stdbool.h>

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Uso: %s <arquivo_para_verificar>\n", argv[0]);
        return 1;
    }

    FILE *file = fopen(argv[1], "r");
    if (!file) {
        printf("❌ Erro: não foi possível abrir o arquivo %s\n", argv[1]);
        return 1;
    }

    printf("🔍 Verificando código: %s\n\n", argv[1]);

    char line[512];
    int line_number = 1;
    int error_count = 0;
    int open_braces = 0;  // Contador de '{'
    int close_braces = 0; // Contador de '}'

    while (fgets(line, sizeof(line), file)) {
        // Remover quebra de linha
        line[strcspn(line, "\n")] = 0;

        // Ignorar linhas vazias e comentários
        if (strlen(line) == 0 || strstr(line, "//") == line) {
            line_number++;
            continue;
        }

        // Verificar presença de chaves
        if (strchr(line, '{')) open_braces++;
        if (strchr(line, '}')) close_braces++;

        // Verificar falta de ';' em linhas comuns (não if, while, for, etc.)
        if (
            strstr(line, "if") == NULL &&
            strstr(line, "for") == NULL &&
            strstr(line, "while") == NULL &&
            strstr(line, "else") == NULL &&
            strstr(line, "do") == NULL &&
            strchr(line, '{') == NULL &&
            strchr(line, '}') == NULL &&
            strstr(line, "#include") == NULL &&
            strstr(line, "return") == NULL
        ) {
            if (line[strlen(line) - 1] != ';') {
                printf("⚠️  Linha %d: possível falta de ';' no final.\n", line_number);
                error_count++;
            }
        }

        line_number++;
    }

    fclose(file);

    // Verificar se chaves estão desbalanceadas
    if (open_braces != close_braces) {
        printf("⚠️  Chaves desbalanceadas: '{' = %d, '}' = %d\n", open_braces, close_braces);
        error_count++;
    }

    if (error_count == 0) {
        printf("\n✅ Nenhum erro detectado.\n");
    } else {
        printf("\n⚠️  Total de possíveis erros: %d\n", error_count);
    }

    return 0;
}
