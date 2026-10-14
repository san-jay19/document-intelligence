import { useEffect, useRef, useState } from "react";
import {
    formatConfidence,
    formatDocumentType,
    formatValue,
} from "../utils/format.js";
import StatusBadge from "./StatusBadge.jsx";

const LOW_CONFIDENCE_THRESHOLD = 0.7;

function ValidationPanel({ validation }) {
    const summary = validation?.summary || {};
    const overallStatus = validation?.overall_status || "NOT_APPLICABLE";
    const checks = validation?.checks || [];

    return (
        <div className="panel">
            <div className="panel-header">
                <h3>Financial Validation</h3>
            </div>

            <div className="validation-summary">
                <div className="validation-stat">
                    <div className="validation-stat-label">Overall Status</div>
                    <div>
                        <StatusBadge status={overallStatus} />
                    </div>
                </div>

                <div className="validation-stat">
                    <div className="validation-stat-label">Passed Checks</div>
                    <div className="validation-stat-value">
                        {summary.passed_checks ?? 0}
                    </div>
                </div>

                <div className="validation-stat">
                    <div className="validation-stat-label">Failed Checks</div>
                    <div className="validation-stat-value">
                        {summary.failed_checks ?? 0}
                    </div>
                </div>

                <div className="validation-stat">
                    <div className="validation-stat-label">Not Applicable</div>
                    <div className="validation-stat-value">
                        {summary.not_applicable_checks ?? 0}
                    </div>
                </div>
            </div>

            <div className="table-wrapper">
                <table>
                    <thead>
                        <tr>
                            <th>Check</th>
                            <th>Status</th>
                            <th>Calculated</th>
                            <th>Reported</th>
                            <th>Variance</th>
                        </tr>
                    </thead>

                    <tbody>
                        {checks.length === 0 ? (
                            <tr>
                                <td colSpan="5" className="empty-state">
                                    No financial validation checks available.
                                </td>
                            </tr>
                        ) : (
                            checks.map((check, index) => (
                                <tr key={index}>
                                    <td data-label="Check">
                                        {check.check || check.name || "Validation check"}
                                    </td>
                                    <td data-label="Status">
                                        <StatusBadge
                                            status={check.status || "NOT_APPLICABLE"}
                                        />
                                    </td>
                                    <td data-label="Calculated">
                                        {formatValue(check.calculated)}
                                    </td>
                                    <td data-label="Reported">
                                        {formatValue(check.reported)}
                                    </td>
                                    <td data-label="Variance">
                                        {formatValue(check.variance)}
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

function FieldCard({ field }) {
    const value = field.value;
    const missing = value === null || value === undefined || value === "";

    const confidence = Number(field.confidence);
    const lowConfidence =
        Number.isFinite(confidence) && confidence < LOW_CONFIDENCE_THRESHOLD;

    let className = "field-card";

    if (missing) {
        className += " missing";
    } else if (lowConfidence) {
        className += " low-confidence";
    }

    return (
        <div className={className}>
            <div className="field-name">{field.name}</div>

            <div className="field-value">
                {missing ? "Missing / unavailable" : formatValue(value)}
            </div>

            <div className="field-meta">
                {field.confidence !== null && field.confidence !== undefined && (
                    <span>Confidence: {formatConfidence(field.confidence)}</span>
                )}
            </div>

            {field.evidence && (
                <div className="evidence">
                    <strong>Evidence:</strong> {field.evidence}
                </div>
            )}
        </div>
    );
}

function FieldsPanel({ fields }) {
    return (
        <div className="panel">
            <div className="panel-header">
                <h3>Extracted Fields</h3>
            </div>

            <div className="fields-grid">
                {fields.length === 0 ? (
                    <div className="empty-state">No fields were extracted.</div>
                ) : (
                    fields.map((field, index) => (
                        <FieldCard key={index} field={field} />
                    ))
                )}
            </div>
        </div>
    );
}

function TablesPanel({ tables }) {
    return (
        <div className="panel">
            <div className="panel-header">
                <h3>Extracted Tables</h3>
            </div>

            <div>
                {tables.length === 0 ? (
                    <div className="empty-state">
                        No structured tables were extracted.
                    </div>
                ) : (
                    tables.map((table, tableIndex) => {
                        const headers = table.headers || [];
                        const rows = table.rows || [];

                        return (
                            <div className="extracted-table" key={tableIndex}>
                                <h4>{table.table_name || "Table"}</h4>

                                <div className="table-container">
                                    <table>
                                        <thead>
                                            <tr>
                                                {headers.map((header, index) => (
                                                    <th key={index}>{String(header)}</th>
                                                ))}
                                            </tr>
                                        </thead>

                                        <tbody>
                                            {rows.map((row, rowIndex) => (
                                                <tr key={rowIndex}>
                                                    {row.map((cell, cellIndex) => (
                                                        <td
                                                            key={cellIndex}
                                                            data-label={
                                                                headers[cellIndex] !== undefined
                                                                    ? String(headers[cellIndex])
                                                                    : ""
                                                            }
                                                        >
                                                            {formatValue(cell)}
                                                        </td>
                                                    ))}
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        );
                    })
                )}
            </div>
        </div>
    );
}

function RawJsonPanel({ data }) {
    const [copied, setCopied] = useState(false);
    const timerRef = useRef(null);

    const json = JSON.stringify(data, null, 2);

    useEffect(() => () => clearTimeout(timerRef.current), []);

    async function handleCopy() {
        try {
            await navigator.clipboard.writeText(json);

            setCopied(true);
            clearTimeout(timerRef.current);
            timerRef.current = setTimeout(() => setCopied(false), 1500);
        } catch (error) {
            console.error(error);
        }
    }

    return (
        <div className="panel">
            <div className="panel-header">
                <h3>Raw JSON</h3>

                <button
                    type="button"
                    className="secondary-button"
                    onClick={handleCopy}
                >
                    {copied ? "Copied" : "Copy"}
                </button>
            </div>

            <pre className="json-viewer">{json}</pre>
        </div>
    );
}

export default function ResultView({ data }) {
    const hasConfidence =
        data.confidence !== null && data.confidence !== undefined;

    return (
        <div>
            <div className="page-header">
                <div>
                    <h2>Processing Result</h2>
                </div>
            </div>

            <div className="summary-grid">
                <div className="summary-card">
                    <span className="summary-label">Document</span>
                    <span className="summary-value small-value">
                        {data.document_name || "—"}
                    </span>
                </div>

                <div className="summary-card">
                    <span className="summary-label">Type</span>
                    <span className="summary-value small-value">
                        {formatDocumentType(data.document_type)}
                    </span>
                </div>

                <div className="summary-card">
                    <span className="summary-label">Processing Status</span>
                    <span>
                        <StatusBadge status={data.processing_status} />
                    </span>
                </div>

                <div className="summary-card">
                    <span className="summary-label">Confidence</span>
                    <span className="summary-value">
                        {hasConfidence ? formatConfidence(data.confidence) : "—"}
                    </span>
                </div>
            </div>

            <ValidationPanel validation={data.validation} />
            <FieldsPanel fields={data.extracted_data?.fields || []} />
            <TablesPanel tables={data.extracted_data?.tables || []} />
            <RawJsonPanel data={data} />
        </div>
    );
}
