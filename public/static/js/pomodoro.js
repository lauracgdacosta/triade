// Cronômetro Pomodoro — roda no cliente; registra tempo no servidor a cada ciclo concluído.
document.addEventListener("DOMContentLoaded", () => {
    const modeSelect = document.getElementById("pomodoro-mode");
    const customFields = document.getElementById("pomodoro-custom-fields");
    const ring = document.getElementById("pomodoro-ring");
    const phaseLabel = document.getElementById("pomodoro-phase");
    const timeLabel = document.getElementById("pomodoro-time");
    const cycleLabel = document.getElementById("pomodoro-cycle");
    const startBtn = document.getElementById("btn-start-pomodoro");
    const cancelBtn = document.getElementById("btn-cancel-pomodoro");
    const configCard = document.getElementById("pomodoro-config");

    let sessionId = null;
    let workMinutes = 25;
    let breakMinutes = 5;
    let cyclesPlanned = 1;
    let cyclesDone = 0;
    let phase = "work"; // work | break
    let secondsLeft = 0;
    let totalSeconds = 0;
    let timerHandle = null;

    modeSelect.addEventListener("change", () => {
        customFields.style.display = modeSelect.value === "custom" ? "flex" : "none";
    });

    function formatTime(seconds) {
        const m = Math.floor(seconds / 60).toString().padStart(2, "0");
        const s = Math.floor(seconds % 60).toString().padStart(2, "0");
        return `${m}:${s}`;
    }

    function tick() {
        secondsLeft -= 1;
        const progress = Math.round(((totalSeconds - secondsLeft) / totalSeconds) * 100);
        ring.style.setProperty("--progress", progress);
        timeLabel.textContent = formatTime(Math.max(0, secondsLeft));
        if (secondsLeft <= 0) {
            clearInterval(timerHandle);
            onPhaseEnd();
        }
    }

    function startPhase(newPhase) {
        phase = newPhase;
        totalSeconds = (phase === "work" ? workMinutes : breakMinutes) * 60;
        secondsLeft = totalSeconds;
        phaseLabel.textContent = phase === "work" ? "Foco" : "Pausa";
        ring.style.setProperty("--progress", 0);
        timeLabel.textContent = formatTime(secondsLeft);
        timerHandle = setInterval(tick, 1000);
    }

    async function onPhaseEnd() {
        if (phase === "work") {
            startPhase("break");
            return;
        }
        // fim do ciclo (foco + pausa)
        const res = await fetch(`/api/v1/pomodoro/${sessionId}/complete-cycle`, { method: "POST" });
        const data = await res.json();
        cyclesDone = data.cycles_completed;
        cycleLabel.textContent = `Ciclo ${cyclesDone}/${cyclesPlanned}`;
        if (data.status === "completed") {
            finish("Sessão concluída! 🎉");
        } else {
            startPhase("work");
        }
    }

    function finish(message) {
        clearInterval(timerHandle);
        phaseLabel.textContent = message;
        timeLabel.textContent = "--:--";
        ring.style.setProperty("--progress", 0);
        startBtn.classList.remove("d-none");
        cancelBtn.classList.add("d-none");
        configCard.classList.remove("d-none");
        sessionId = null;
    }

    startBtn.addEventListener("click", async () => {
        const mode = modeSelect.value;
        if (mode === "25_5") { workMinutes = 25; breakMinutes = 5; }
        else if (mode === "50_10") { workMinutes = 50; breakMinutes = 10; }
        else {
            workMinutes = Number(document.getElementById("pomodoro-work").value) || 25;
            breakMinutes = Number(document.getElementById("pomodoro-break").value) || 5;
        }
        cyclesPlanned = Number(document.getElementById("pomodoro-cycles").value) || 1;
        cyclesDone = 0;
        const taskId = document.getElementById("pomodoro-task").value || null;

        const res = await fetch("/api/v1/pomodoro/start", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                mode, work_minutes: workMinutes, break_minutes: breakMinutes,
                cycles_planned: cyclesPlanned, task_id: taskId,
            }),
        });
        if (!res.ok) { alert("Não foi possível iniciar o Pomodoro."); return; }
        const data = await res.json();
        sessionId = data.id;
        cycleLabel.textContent = `Ciclo 0/${cyclesPlanned}`;
        startBtn.classList.add("d-none");
        cancelBtn.classList.remove("d-none");
        configCard.classList.add("d-none");
        startPhase("work");
    });

    cancelBtn.addEventListener("click", async () => {
        clearInterval(timerHandle);
        if (sessionId) {
            await fetch(`/api/v1/pomodoro/${sessionId}/cancel`, { method: "POST" });
        }
        finish("Cancelado");
    });
});
