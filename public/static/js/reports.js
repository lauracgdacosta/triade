// Página de Relatórios: busca os dados prontos (labels/values) nos endpoints de
// API e instancia os gráficos Chart.js — nenhuma lógica de agregação aqui.
(function () {
    const charts = {};

    function renderChart(id, labels, values, label) {
        const canvas = document.getElementById(id);
        if (!canvas) return;
        if (charts[id]) charts[id].destroy();
        charts[id] = new Chart(canvas, {
            type: "bar",
            data: { labels, datasets: [{ label, data: values, backgroundColor: "#6366f1" }] },
            options: { responsive: true, plugins: { legend: { display: false } } },
        });
    }

    async function fetchJson(url) {
        const response = await fetch(url);
        return response.json();
    }

    async function loadAll() {
        const from = document.getElementById("report-date-from").value;
        const to = document.getElementById("report-date-to").value;
        const qs = from && to ? `?date_from=${from}&date_to=${to}` : "";

        const [byProject, byCategory, byRole, byWeek, efficiency, stats] = await Promise.all([
            fetchJson(`/api/v1/reports/time-by-project${qs}`),
            fetchJson(`/api/v1/reports/time-by-category${qs}`),
            fetchJson(`/api/v1/reports/time-by-role${qs}`),
            fetchJson("/api/v1/reports/time-by-week"),
            fetchJson(`/api/v1/reports/efficiency${qs}`),
            fetchJson(`/api/v1/reports/stats${qs}`),
        ]);

        renderChart("chart-project", byProject.labels, byProject.values, "Minutos");
        renderChart("chart-category", byCategory.labels, byCategory.values, "Minutos");
        renderChart("chart-role", byRole.labels, byRole.values, "Minutos");
        renderChart("chart-week", byWeek.labels, byWeek.values, "Minutos");

        document.getElementById("eff-completed").textContent = efficiency.tasks_completed;
        document.getElementById("eff-planned").textContent = efficiency.planned_minutes;
        document.getElementById("eff-actual").textContent = efficiency.actual_minutes;
        document.getElementById("eff-percent").textContent = efficiency.efficiency_percent;
        document.getElementById("eff-avg").textContent = efficiency.avg_minutes_per_task;

        document.getElementById("stat-streak").textContent = stats.streak_days;
        document.getElementById("stat-completion").textContent = `${stats.completion_rate_percent}%`;
        document.getElementById("stat-lost").textContent = stats.lost_minutes;
        document.getElementById("stat-overdue").textContent = stats.overdue_tasks;
    }

    document.addEventListener("DOMContentLoaded", () => {
        const refreshBtn = document.getElementById("report-refresh");
        if (!refreshBtn) return;
        refreshBtn.addEventListener("click", loadAll);
        loadAll();
    });
})();
