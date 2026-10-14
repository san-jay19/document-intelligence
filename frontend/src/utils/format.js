export const DOCUMENT_TYPES = [
    { value: "invoice", label: "Invoice" },
    { value: "balance_sheet", label: "Balance Sheet" },
    { value: "profit_and_loss", label: "Profit & Loss" },
    { value: "cash_flow_statement", label: "Cash Flow Statement" },
];

export function formatDocumentType(type) {
    if (!type) {
        return "—";
    }

    const match = DOCUMENT_TYPES.find((item) => item.value === type);

    return match ? match.label : type;
}

// Handles both decimal (0.92) and percentage (92) confidence.
export function formatConfidence(value) {
    const number = Number(value);

    if (value === null || value === undefined || !Number.isFinite(number)) {
        return "—";
    }

    const percentage = number <= 1 ? number * 100 : number;

    return `${percentage.toFixed(1)}%`;
}

export function formatDate(value) {
    if (!value) {
        return "—";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return value;
    }

    return date.toLocaleString();
}

export function formatValue(value) {
    if (value === null || value === undefined) {
        return "—";
    }

    if (typeof value === "object") {
        return JSON.stringify(value);
    }

    return String(value);
}
