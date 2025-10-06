document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("userInput");
    const sendBtn = document.getElementById("sendBtn");
    const chatBox = document.getElementById("chat-box");

    sendBtn.addEventListener("click", enviar);
    input.addEventListener("keydown", (e) => { if (e.key === "Enter") enviar(); });

    adicionarMensagem("bot", "Olá! 👋 Sou o assistente acadêmico da UNIP. Estou aqui para ajudar com suas dúvidas e pesquisas. 📚<br><br>➡️ À sua direita, você encontra materiais em PDF que podem ser resumidos para facilitar seu estudo.");
    // ----------------------------
    // Parte nova: selects dinâmicos
    // ----------------------------
    const materiaSelect = document.getElementById("materiaSelect");
    const moduloSelect = document.getElementById("moduloSelect");
    const resumirBtn = document.getElementById("resumirBtn");
    const abrirBtn = document.getElementById("abrirBtn");

    const modulos = {
        "fundamentos_de_infraestrutura_computacional": [
            { nome: "Infraestrutura Computacional - 1", arquivo: "infraestrutura_computacional_modulo_1.pdf" },
            { nome: "Infraestrutura Computacional - 2", arquivo: "infraestrutura_computacional_modulo_2.pdf" },
            { nome: "Infraestrutura Computacional - 3", arquivo: "infraestrutura_computacional_modulo_3.pdf" },
            { nome: "Infraestrutura Computacional - 4", arquivo: "infraestrutura_computacional_modulo_4.pdf" },
        ],
        "fundamentos_de_math": [
            { nome: "Matemática e Estatística - 1", arquivo: "matematica_estatistica_modulo_1.pdf" },
            { nome: "Matemática e Estatística - 2", arquivo: "matematica_estatistica_modulo_2.pdf" },
            { nome: "Matemática e Estatística - 3", arquivo: "matematica_estatistica_modulo_3.pdf" }
        ],
        "fundamentos_de_python": [
            { nome: "Python - 1", arquivo: "fundamentos_de_python_modulo_1.pdf" },
            { nome: "Python - 2", arquivo: "fundamentos_de_python_modulo_2.pdf" },
            { nome: "Python - 3", arquivo: "fundamentos_de_python_modulo_3.pdf" },
            { nome: "Python - 4", arquivo: "fundamentos_de_python_modulo_4.pdf" },
            { nome: "Python - 5", arquivo: "fundamentos_de_python_modulo_5.pdf" },
            { nome: "Python - 6", arquivo: "fundamentos_de_python_modulo_6.pdf" }
        ],
        "fundamentos_de_tic": [
            { nome: "Tecnologia da informação - 1", arquivo: "tecnologia_da_informacao_modulo_1.pdf" },
            { nome: "Tecnologia da informação - 2", arquivo: "tecnologia_da_informacao_modulo_2.pdf" },
            { nome: "Tecnologia da informação - 3", arquivo: "tecnologia_da_informacao_modulo_3.pdf" },
            { nome: "Tecnologia da informação - 4", arquivo: "tecnologia_da_informacao_modulo_4.pdf" }
        ]
    };

    materiaSelect.addEventListener("change", () => {
        const materia = materiaSelect.value;
        moduloSelect.innerHTML = "";

        if (materia && modulos[materia]) {
            moduloSelect.disabled = false;
            resumirBtn.disabled = false;
            abrirBtn.disabled = false;

            modulos[materia].forEach(m => {
                const opt = document.createElement("option");
                opt.value = materia + "/" + m.arquivo;
                opt.textContent = m.nome;
                moduloSelect.appendChild(opt);
            });
        } else {
            moduloSelect.disabled = true;
            resumirBtn.disabled = true;
            const opt = document.createElement("option");
            opt.textContent = "-- Primeiro escolha uma matéria --";
            moduloSelect.appendChild(opt);
        }
    });

    resumirBtn.addEventListener("click", async () => {
        const pdfName = moduloSelect.value;

        adicionarMensagem("user", `Resumir o PDF: ${pdfName}`);
        const digitandoElem = adicionarMensagem("bot", "", true);

        try {
            const resp = await fetch("/resumir_pdf", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ pdf_name: pdfName })
            });

            const data = await resp.json();
            digitandoElem.querySelector(".bubble").classList.remove("typing");
            digitandoElem.querySelector(".bubble").innerHTML = data.response ?? "Sem resposta.";
        } catch (err) {
            digitandoElem.querySelector(".bubble").classList.remove("typing");
            digitandoElem.querySelector(".bubble").innerHTML = "⚠️ Erro ao resumir PDF.";
        }
    });

    async function enviar() {
        const mensagem = input.value.trim();
        if (!mensagem) return;


        adicionarMensagem("user", mensagem);
        const digitandoElem = adicionarMensagem("bot", "", true);

        input.value = "";
        input.disabled = true;
        sendBtn.disabled = true;

        try {
            const resp = await fetch("/send_message", {
                method: "POST",
                headers: { "Content-Type": "application/json", "Accept": "application/json" },
                body: JSON.stringify({ message: mensagem })
            });

            if (!resp.ok) {
                const text = await resp.text();
                console.error("Erro do servidor:", resp.status, text);
                digitandoElem.querySelector(".bubble").classList.remove("typing");
                digitandoElem.querySelector(".bubble").innerHTML = "⚠️ Erro do servidor.";
            } else {
                const data = await resp.json();
                digitandoElem.querySelector(".bubble").classList.remove("typing");
                digitandoElem.querySelector(".bubble").innerHTML = data.response ?? "Sem resposta.";
            }
        } catch (err) {
            console.error("Erro no fetch:", err);
            digitandoElem.querySelector(".bubble").classList.remove("typing");
            digitandoElem.querySelector(".bubble").innerHTML = "⚠️ Erro: não foi possível conectar ao servidor.";
        } finally {
            input.disabled = false;
            sendBtn.disabled = false;
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    }

    function adicionarMensagem(tipo, texto, isTyping = false) {
        const msg = document.createElement("div");
        msg.classList.add("message", tipo);

        const avatar = document.createElement("div");
        avatar.classList.add("avatar");
        avatar.innerText = tipo === "user" ? "🧑" : "🤖";

        const content = document.createElement("div");
        content.classList.add("content");

        const label = document.createElement("div");
        label.classList.add("label");
        label.textContent = tipo === "user" ? "Você" : "Assistente UNIP";

        const bubble = document.createElement("div");
        bubble.classList.add("bubble");
        if (isTyping) {
            bubble.classList.add("typing");
            bubble.innerHTML = `<span></span><span></span><span></span>`;
        } else {
            bubble.innerHTML = texto;
        }

        content.appendChild(label);
        content.appendChild(bubble);

        if (tipo === "user") {
            msg.appendChild(content);
            msg.appendChild(avatar);
        } else {
            msg.appendChild(avatar);
            msg.appendChild(content);
        }

        chatBox.appendChild(msg);
        chatBox.scrollTo({ top: chatBox.scrollHeight, behavior: "smooth" });

        return msg;
    }

});
const abrirBtn = document.getElementById("abrirBtn");

materiaSelect.addEventListener("change", () => {
    const materia = materiaSelect.value;
    moduloSelect.innerHTML = "";

    if (materia && modulos[materia]) {
        moduloSelect.disabled = false;

        modulos[materia].forEach(m => {
            const opt = document.createElement("option");
            opt.value = materia + "/" + m.arquivo;
            opt.textContent = m.nome;
            moduloSelect.appendChild(opt);
        });

        // Desabilitado até escolhas
        resumirBtn.disabled = true;
        abrirBtn.disabled = true;
    } else {
        moduloSelect.disabled = true;
        resumirBtn.disabled = true;
        abrirBtn.disabled = true;
        const opt = document.createElement("option");
        opt.textContent = "-- Primeiro escolha uma matéria --";
        moduloSelect.appendChild(opt);
    }
});

// Habilita ao escolher
moduloSelect.addEventListener("change", () => {
    if (moduloSelect.value) {
        resumirBtn.disabled = false;
        abrirBtn.disabled = false;
    } else {
        resumirBtn.disabled = true;
        abrirBtn.disabled = true;
    }
});

abrirBtn.addEventListener("click", () => {
    const pdfName = moduloSelect.value;
    if (pdfName) {
        window.open(`/pdf/${pdfName}`, "_blank");
    }
});
document.getElementById("logoutBtn").addEventListener("click", async () => {
    try {
        await fetch("/logout");
        // Redireciona para a página de login
        window.location.href = "/login_page";
    } catch (err) {
        console.error("Erro ao fazer logout:", err);
    }
});

document.addEventListener("DOMContentLoaded", async () => {
    const chatBox = document.getElementById("chat-box");

    // Função para adicionar mensagem no chat
    function adicionarMensagem(tipo, texto, isTyping = false) {
        const chatBox = document.getElementById("chat-box");
        const msg = document.createElement("div");
        msg.classList.add("message", tipo);

        const avatar = document.createElement("div");
        avatar.classList.add("avatar");
        avatar.innerText = tipo === "user" ? "🧑" : "🤖";

        const content = document.createElement("div");
        content.classList.add("flex", "flex-col", "items-start", "max-w-[80%]");

        const label = document.createElement("div");
        label.classList.add("label");
        label.textContent = tipo === "user" ? "Você" : "Assistente UNIP";

        const bubble = document.createElement("pre");
        bubble.classList.add("bubble");
        if (isTyping) {
            bubble.innerHTML = `<span class="animate-pulse">Digitando...</span>`;
        } else {
            bubble.innerHTML = texto;
        }

        content.appendChild(label);
        content.appendChild(bubble);

        msg.appendChild(avatar);
        msg.appendChild(content);
        chatBox.appendChild(msg);

        chatBox.scrollTop = chatBox.scrollHeight;
        return msg;
    }


    // --- BUSCAR HISTÓRICO ---
    try {
        const resp = await fetch("/history");
        const data = await resp.json();

        data.forEach(msg => {
            adicionarMensagem("user", msg[0]);      // msg[0] = message
            adicionarMensagem("bot", msg[1]);       // msg[1] = response
        });
    } catch (err) {
        console.error("Erro ao carregar histórico:", err);
    }
});