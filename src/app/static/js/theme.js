// Tema Claro / Escuro / Automático — aplicado antes do primeiro paint quando possível.
(function () {
    const STORAGE_KEY = "triade-theme";

    function resolve(pref) {
        if (pref === "auto") {
            return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
        }
        return pref;
    }

    function apply(pref) {
        document.documentElement.setAttribute("data-bs-theme", resolve(pref));
    }

    window.triadeTheme = {
        get: () => localStorage.getItem(STORAGE_KEY) || "auto",
        set: (pref) => {
            localStorage.setItem(STORAGE_KEY, pref);
            apply(pref);
        },
    };

    apply(window.triadeTheme.get());

    window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
        if (window.triadeTheme.get() === "auto") apply("auto");
    });

    document.addEventListener("DOMContentLoaded", () => {
        const btn = document.getElementById("theme-toggle");
        if (btn) {
            btn.addEventListener("click", () => {
                const order = ["light", "dark", "auto"];
                const next = order[(order.indexOf(window.triadeTheme.get()) + 1) % order.length];
                window.triadeTheme.set(next);
            });
        }
    });
})();
