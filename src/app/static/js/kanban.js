// Kanban — drag-and-drop nativo (HTML5) + persistência via fetch na API JSON.
document.addEventListener("DOMContentLoaded", () => {
    let draggedCard = null;

    document.querySelectorAll(".kanban-card").forEach((card) => {
        card.addEventListener("dragstart", () => {
            draggedCard = card;
            card.classList.add("dragging");
        });
        card.addEventListener("dragend", () => card.classList.remove("dragging"));
    });

    document.querySelectorAll(".kanban-cards").forEach((container) => {
        container.addEventListener("dragover", (e) => {
            e.preventDefault();
            container.closest(".kanban-column").classList.add("drag-over");
        });
        container.addEventListener("dragleave", () => {
            container.closest(".kanban-column").classList.remove("drag-over");
        });
        container.addEventListener("drop", async (e) => {
            e.preventDefault();
            container.closest(".kanban-column").classList.remove("drag-over");
            if (!draggedCard) return;

            container.appendChild(draggedCard);
            const taskId = draggedCard.dataset.taskId;
            const columnId = container.dataset.columnId;
            const position = Array.from(container.children).indexOf(draggedCard);

            await fetch(`/api/v1/tasks/${taskId}/kanban-move`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ kanban_column_id: columnId, position }),
            });

            document.querySelectorAll(".kanban-column").forEach((col) => {
                const count = col.querySelector(".kanban-cards").children.length;
                col.querySelector(".text-muted.small").textContent = count;
            });
        });
    });

    // Kanban colaborativo: recarrega o quadro quando outra aba/sessão altera uma
    // tarefa. Não faz nada se o Supabase não estiver configurado (ex.: ambiente
    // local com SQLite) — a chave anônima é segura de expor no client, protegida
    // por RLS (ver scripts/supabase_schema.sql).
    const board = document.getElementById("kanban-board");
    const supabaseUrl = board && board.dataset.supabaseUrl;
    const supabaseAnonKey = board && board.dataset.supabaseAnonKey;
    if (board && supabaseUrl && supabaseAnonKey && window.supabase) {
        const client = window.supabase.createClient(supabaseUrl, supabaseAnonKey);
        client
            .channel("kanban-tasks")
            .on(
                "postgres_changes",
                { event: "*", schema: "public", table: "tasks", filter: `user_id=eq.${board.dataset.userId}` },
                () => window.location.reload()
            )
            .subscribe();
    }
});
