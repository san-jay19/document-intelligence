import { useCallback, useEffect, useState } from "react";

const THEME_STORAGE_KEY = "docint-theme";

export function useTheme() {
    // index.html already set data-theme before first paint.
    const [theme, setTheme] = useState(
        () => document.documentElement.getAttribute("data-theme") || "light"
    );

    useEffect(() => {
        document.documentElement.setAttribute("data-theme", theme);
    }, [theme]);

    const toggleTheme = useCallback(() => {
        const next = theme === "dark" ? "light" : "dark";

        setTheme(next);

        try {
            localStorage.setItem(THEME_STORAGE_KEY, next);
        } catch (error) {
            // Storage disabled: theme just won't persist across reloads.
        }
    }, [theme]);

    return { theme, toggleTheme };
}
