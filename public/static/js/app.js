// Comportamentos globais: CSRF em requisições HTMX, confirmação de exclusão,
// auto-abertura do painel de Notas (offcanvas), fechamento automático de
// modais (Projetos/Metas/Categorias/Papéis) após salvar, e seletor de ícones.
(function () {
    document.body.addEventListener("htmx:configRequest", (event) => {
        const meta = document.querySelector('meta[name="csrf-token"]');
        if (meta) {
            event.detail.headers["X-CSRF-Token"] = meta.content;
        }
    });

    document.body.addEventListener("htmx:confirm", (event) => {
        if (event.detail.elt.hasAttribute("data-confirm")) {
            event.preventDefault();
            const message = event.detail.elt.getAttribute("data-confirm");
            if (confirm(message)) {
                event.detail.issueRequest(true);
            }
        }
    });

    document.body.addEventListener("htmx:afterSwap", (event) => {
        if (event.detail.target && event.detail.target.id === "notes-panel-container") {
            const panelEl = event.detail.target.querySelector(".offcanvas");
            if (panelEl) {
                bootstrap.Offcanvas.getOrCreateInstance(panelEl).show();
            }
        }
    });

    // Modais de criar/editar (Projetos, Metas, Categorias, Papéis, ...) ficam
    // sempre no DOM e são abertos via data-bs-toggle="modal" — não dependem de
    // HTMX para abrir, então também não fechavam sozinhos ao salvar (o usuário
    // não via feedback de que salvou e clicava de novo, criando registros
    // duplicados). Os modais de edição (um por card/linha) ficam DENTRO do
    // elemento que a resposta troca — fecha em beforeSwap, enquanto o nó
    // antigo (com .show) ainda existe, para o Bootstrap limpar corretamente
    // o backdrop antes de ele ser substituído pelo HTML novo.
    document.body.addEventListener("htmx:beforeSwap", (event) => {
        if (!event.detail.shouldSwap || event.detail.requestConfig.verb === "get") return;
        const openModal = document.querySelector(".modal.show");
        if (openModal) {
            bootstrap.Modal.getOrCreateInstance(openModal).hide();
        }
    });

    // Rede de segurança: se por algum motivo o backdrop/travamento de scroll
    // ficar órfão (ex.: o nó do modal foi substituído no meio da animação de
    // fechamento), remove qualquer resíduo assim que não houver mais modal
    // aberto — evita a tela ficar "presa" atrás de um overlay escuro.
    document.body.addEventListener("htmx:afterSettle", () => {
        if (document.querySelector(".modal.show")) return;
        document.querySelectorAll(".modal-backdrop").forEach((el) => el.remove());
        document.body.classList.remove("modal-open");
        document.body.style.removeProperty("overflow");
        document.body.style.removeProperty("padding-right");
    });

    // Limpa o formulário ao fechar (Cancelar, X, ou fechamento automático
    // acima) para a próxima abertura não reaproveitar valores antigos, e
    // resincroniza o destaque visual do seletor de ícones com o valor
    // restaurado pelo form.reset().
    document.body.addEventListener("hidden.bs.modal", (event) => {
        const form = event.target.querySelector("form");
        if (!form) return;
        form.reset();
        form.querySelectorAll(".icon-picker").forEach((picker) => {
            const input = picker.querySelector('input[type="hidden"]');
            picker.querySelectorAll(".icon-picker-option").forEach((btn) => {
                btn.classList.toggle("active", btn.dataset.icon === input.value);
            });
        });
    });

    // Seletor de ícones: clicar numa opção define o input escondido e destaca
    // a opção selecionada. Delegado em document.body para funcionar também
    // nos modais de edição (um por linha, renderizados dinamicamente).
    document.body.addEventListener("click", (event) => {
        const option = event.target.closest(".icon-picker-option");
        if (!option) return;
        event.preventDefault();
        const picker = option.closest(".icon-picker");
        const input = picker.querySelector('input[type="hidden"]');
        input.value = option.dataset.icon;
        picker.querySelectorAll(".icon-picker-option").forEach((btn) => btn.classList.remove("active"));
        option.classList.add("active");
    });
})();
