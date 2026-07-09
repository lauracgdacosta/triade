// Página de criar/editar compromisso (/agenda/new e /agenda/{id}/edit) — POST ou
// PATCH em /api/v1/events e volta pra Agenda.
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("event-form");
    if (!form) return;

    const conflictAlert = document.getElementById("event-conflict-alert");
    const deleteBtn = document.getElementById("btn-delete-event");
    const eventId = form.dataset.eventId;

    function toLocalInput(date) {
        const pad = (n) => String(n).padStart(2, "0");
        return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
    }

    const prefillStart = form.dataset.prefillStart;
    const prefillEnd = form.dataset.prefillEnd;
    document.getElementById("event-start").value = prefillStart ? toLocalInput(new Date(prefillStart)) : toLocalInput(new Date());
    document.getElementById("event-end").value = prefillEnd ? toLocalInput(new Date(prefillEnd)) : toLocalInput(new Date(Date.now() + 3600000));

    // Compromissos recorrentes não sincronizam com o Google (ver
    // EventService._assert_recurrence_google_compatible) — reflete a regra
    // no client antes do 422 do backend, desabilitando um campo quando o
    // outro está preenchido.
    const recurrenceInput = document.getElementById("event-recurrence");
    const googleAccountSelect = document.getElementById("event-google-account");
    function syncRecurrenceGoogleToggle() {
        googleAccountSelect.disabled = recurrenceInput.value.trim() !== "";
        recurrenceInput.disabled = googleAccountSelect.value !== "";
    }
    recurrenceInput.addEventListener("input", syncRecurrenceGoogleToggle);
    googleAccountSelect.addEventListener("change", syncRecurrenceGoogleToggle);
    syncRecurrenceGoogleToggle();

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        conflictAlert.classList.add("d-none");
        const payload = {
            title: document.getElementById("event-title").value,
            description: document.getElementById("event-description").value || null,
            start_at: new Date(document.getElementById("event-start").value).toISOString(),
            end_at: new Date(document.getElementById("event-end").value).toISOString(),
            category_id: document.getElementById("event-category").value || null,
            project_id: document.getElementById("event-project").value || null,
            location: document.getElementById("event-location").value || null,
            color: document.getElementById("event-color").value,
            recurrence_rule: recurrenceInput.disabled ? null : (recurrenceInput.value || null),
            google_account_id: googleAccountSelect.disabled ? null : (googleAccountSelect.value || null),
        };
        const res = await fetch(eventId ? `/api/v1/events/${eventId}` : "/api/v1/events", {
            method: eventId ? "PATCH" : "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        if (!res.ok) {
            alert("Não foi possível salvar o compromisso.");
            return;
        }
        const data = await res.json();
        window.location.href = data.has_conflict ? "/agenda?conflict=1" : "/agenda";
    });

    if (deleteBtn) {
        deleteBtn.addEventListener("click", async () => {
            if (!confirm("Excluir este compromisso?")) return;
            await fetch(`/api/v1/events/${eventId}`, { method: "DELETE" });
            window.location.href = "/agenda";
        });
    }
});
