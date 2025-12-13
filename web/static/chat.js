document.addEventListener("DOMContentLoaded", () => {

    // ======================
    // ELEMENTOS PRINCIPAIS
    // ======================
    const input = document.getElementById("userInput");
    const sendBtn = document.getElementById("sendBtn");
    const chatBox = document.getElementById("chat-box");

    const materiaSelect = document.getElementById("materiaSelect");
    const moduloSelect = document.getElementById("moduloSelect");
    const resumirBtn = document.getElementById("resumirBtn");
    const abrirBtn = document.getElementById("abrirBtn");

    // ======================
    // DADOS DOS PDFs
    // ======================
    const modulos = {
        fundamentos_de_infraestrutura_computacional: [
            { nome: "Infraestrutura Computacional - 1", arquivo: "infraestrutura_computacional_modulo_1.pdf" },
            { nome: "Infraestrutura Computacional - 2", arquivo: "infraestrutura_computacional_modulo_2.pdf" },
            { nome: "Infraestrutura Computacional - 3", arquivo: "infraestrutura_computacional_modulo_3.pdf" },
            { nome: "Infraestrutura Computacional - 4", arquivo: "infraestrutura_computacional_modulo_4.pdf" }
        ],
        fundamentos_de_math: [
            { nome: "Matemática e Estatística - 1", arquivo: "matematica_estatistica_modulo_1.pdf" },
            { nome: "Matemática e Estatística - 2", arquivo: "matematica_estatistica_modulo_2.pdf" },
            { nome: "Matemática e Estatística - 3", arquivo: "matematica_estatistica_modulo_3.pdf" }
        ],
        fundamentos_de_python: [
            { nome: "Python - 1", arquivo: "fundamentos_de_python_modulo_1.pdf" },
            { nome: "Python - 2", arquivo: "fundamentos_de_python_modulo_2.pdf" },
            { nome: "Python - 3", arquivo: "fundamentos_de_python_modulo_3.pdf" },
            { nome: "Python - 4", arquivo: "fundamentos_de_python_modulo_4.pdf" }
        ]
    };

    // ======================
    // MENSAGEM INICIAL
    // ======================
    adicionarMensagem(
        "bot",
        "Olá! 👋 Sou o assistente de TI"
    );

    // ======================
    // EVENTOS CHAT
    // ======================
    sendBtn.addEventListener("click", enviarMensagem);
    input.addEventListener("keydown", e => {
        if (e.key === "Enter") enviarMensagem();
    });

    async function enviarMensagem() {
        const mensagem = input.value.trim();
        if (!mensagem) return;

        adicionarMensagem("user", mensagem);
        const typing = adicionarMensagem("bot", "", true);

        input.value = "";
        input.disabled = true;
        sendBtn.disabled = true;

        try {
            const resp = await fetch("/send_message", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: mensagem })
            });

            const data = await resp.json();
            typing.querySelector(".bubble").classList.remove("typing");
            typing.querySelector(".bubble").innerHTML = data.response ?? "Sem resposta.";
        } catch (err) {
            typing.querySelector(".bubble").classList.remove("typing");
            typing.querySelector(".bubble").innerHTML = "⚠️ Erro ao conectar com o servidor.";
        } finally {
            input.disabled = false;
            sendBtn.disabled = false;
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    }

    // ======================
    // EVENTOS PDF
    // ======================
    materiaSelect.addEventListener("change", () => {
        const materia = materiaSelect.value;
        moduloSelect.innerHTML = "";

        if (!materia || !modulos[materia]) {
            moduloSelect.disabled = true;
            resumirBtn.disabled = true;
            abrirBtn.disabled = true;
            return;
        }

        moduloSelect.disabled = false;
        resumirBtn.disabled = true;
        abrirBtn.disabled = true;

        modulos[materia].forEach(m => {
            const opt = document.createElement("option");
            opt.value = `${materia}/${m.arquivo}`;
            opt.textContent = m.nome;
            moduloSelect.appendChild(opt);
        });
    });

    moduloSelect.addEventListener("change", () => {
        const ativo = Boolean(moduloSelect.value);
        resumirBtn.disabled = !ativo;
        abrirBtn.disabled = !ativo;
    });

    abrirBtn.addEventListener("click", () => {
        if (moduloSelect.value) {
            window.open(`/pdf/${moduloSelect.value}`, "_blank");
        }
    });

    resumirBtn.addEventListener("click", async () => {
        const pdf = moduloSelect.value;
        if (!pdf) return;

        adicionarMensagem("user", `Resumir PDF: ${pdf}`);
        const typing = adicionarMensagem("bot", "", true);

        try {
            const resp = await fetch("/resumir_pdf", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ pdf_name: pdf })
            });

            const data = await resp.json();
            typing.querySelector(".bubble").classList.remove("typing");
            typing.querySelector(".bubble").innerHTML = data.response ?? "Sem resposta.";
        } catch {
            typing.querySelector(".bubble").classList.remove("typing");
            typing.querySelector(".bubble").innerHTML = "⚠️ Erro ao resumir o PDF.";
        }
    });

    // ======================
    // FUNÇÃO DE MENSAGEM
    // ======================
    function adicionarMensagem(tipo, texto, typing = false) {
        const msg = document.createElement("div");
        msg.className = `message ${tipo}`;

        const avatar = document.createElement("div");
        avatar.className = "avatar";
        avatar.textContent = tipo === "user" ? "🧑" : "🤖";

        const content = document.createElement("div");
        content.className = "content";

        const label = document.createElement("div");
        label.className = "label";
        label.textContent = tipo === "user" ? "Você" : "Assistente UNIP";

        const bubble = document.createElement("div");
        bubble.className = "bubble";

        if (typing) {
            bubble.classList.add("typing");
            bubble.innerHTML = `<span></span><span></span><span></span>`;
        } else {
            bubble.innerHTML = texto;
        }

        content.append(label, bubble);

        tipo === "user"
            ? msg.append(content, avatar)
            : msg.append(avatar, content);

        chatBox.appendChild(msg);
        chatBox.scrollTo({ top: chatBox.scrollHeight, behavior: "smooth" });

        return msg;
    }

});
