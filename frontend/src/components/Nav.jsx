const TABS = [
    { id: "dashboard", label: "Dashboard" },
    { id: "process", label: "Process Document" },
];

export default function Nav({ view, onChange }) {
    return (
        <nav className="top-nav">
            {TABS.map((tab) => (
                <button
                    key={tab.id}
                    type="button"
                    className={`nav-button${view === tab.id ? " active" : ""}`}
                    onClick={() => onChange(tab.id)}
                >
                    {tab.label}
                </button>
            ))}
        </nav>
    );
}
