const DOT_COLORS = {
    online: "#22c55e",
    offline: "#ef4444",
};

export default function Header({ theme, onToggleTheme, health }) {
    const isDark = theme === "dark";

    return (
        <header className="app-header">
            <div>
                <h1>FinSight AI</h1>
                <p>AI-powered financial document extraction and validation</p>
            </div>

            <div className="header-actions">
                <button
                    type="button"
                    className="theme-toggle"
                    onClick={onToggleTheme}
                    aria-label={
                        isDark ? "Switch to light mode" : "Switch to dark mode"
                    }
                >
                    <span aria-hidden="true">{isDark ? "☀️" : "🌙"}</span>
                </button>

                <div className="api-status">
                    <span
                        className="status-dot"
                        style={
                            DOT_COLORS[health.state]
                                ? { background: DOT_COLORS[health.state] }
                                : undefined
                        }
                    />
                    <span>{health.text}</span>
                </div>
            </div>
        </header>
    );
}
