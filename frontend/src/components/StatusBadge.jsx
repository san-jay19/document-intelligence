export default function StatusBadge({ status }) {
    const normalized = String(status || "NOT_APPLICABLE").toUpperCase();

    let variant = "status-na";

    if (normalized === "PASS") {
        variant = "status-pass";
    } else if (normalized === "FAIL" || normalized === "FAILED") {
        variant = "status-fail";
    } else if (normalized === "WARNING") {
        variant = "status-warning";
    }

    return <span className={`status-badge ${variant}`}>{normalized}</span>;
}
