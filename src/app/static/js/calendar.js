// Agenda — FullCalendar (vanilla JS) alimentado pela API JSON /api/v1/events.
// Criar e editar compromisso são páginas próprias (/agenda/new, /agenda/{id}/edit).
document.addEventListener("DOMContentLoaded", () => {
    const calendarEl = document.getElementById("calendar");
    if (!calendarEl) return;

    const calendar = new FullCalendar.Calendar(calendarEl, {
        // As build globais do @fullcalendar/{daygrid,timegrid,interaction,rrule} se
        // auto-registram em FullCalendar.globalPlugins ao carregar o <script> — não
        // exportam FullCalendar.dayGridPlugin/etc. Passar isso aqui deixava o array
        // cheio de `undefined` e quebrava o FullCalendar ao processar as opções.
        initialView: "timeGridWeek",
        locale: "pt-br",
        firstDay: 1,
        headerToolbar: { left: "prev,next today", center: "title", right: "dayGridMonth,timeGridWeek,timeGridDay" },
        buttonText: { today: "Hoje", month: "Mês", week: "Semana", day: "Dia" },
        selectable: true,
        editable: true,
        height: "auto",
        events: async (info, successCallback, failureCallback) => {
            try {
                const res = await fetch(`/api/v1/events?start=${info.startStr}&end=${info.endStr}`);
                if (!res.ok) throw new Error("Falha ao carregar eventos");
                const data = await res.json();
                successCallback(
                    data.map((e) => ({
                        id: e.id,
                        title: e.title,
                        start: e.start_at,
                        end: e.end_at,
                        allDay: e.all_day,
                        backgroundColor: e.color || undefined,
                        borderColor: e.color || undefined,
                        classNames: e.has_conflict ? ["has-conflict"] : [],
                        extendedProps: e,
                    }))
                );
            } catch (err) {
                failureCallback(err);
            }
        },
        select: (info) => {
            window.location.href = `/agenda/new?start=${encodeURIComponent(info.start.toISOString())}&end=${encodeURIComponent(info.end.toISOString())}`;
        },
        eventClick: (info) => {
            window.location.href = `/agenda/${info.event.id}/edit`;
        },
        eventDidMount: (info) => {
            const link = info.event.extendedProps.meeting_link;
            if (!link || !link.startsWith("http")) return;
            const icon = document.createElement("i");
            icon.className = "fa-solid fa-video ms-1";
            icon.title = "Tem link de reunião";
            (info.el.querySelector(".fc-event-title") || info.el).appendChild(icon);
        },
        eventDrop: (info) => updateEventTimes(info.event, info.revert),
        eventResize: (info) => updateEventTimes(info.event, info.revert),
    });
    calendar.render();

    async function updateEventTimes(event, revert) {
        try {
            const res = await fetch(`/api/v1/events/${event.id}`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ start_at: event.start.toISOString(), end_at: (event.end || event.start).toISOString() }),
            });
            if (!res.ok) throw new Error();
            const data = await res.json();
            if (data.has_conflict) {
                event.setProp("classNames", ["has-conflict"]);
            }
        } catch {
            revert();
        }
    }
});
