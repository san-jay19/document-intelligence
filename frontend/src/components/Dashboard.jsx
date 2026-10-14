import { useCallback, useEffect, useState } from "react";
import { fetchDocuments } from "../api.js";
import {
    formatConfidence,
    formatDate,
    formatDocumentType,
} from "../utils/format.js";
import StatusBadge from "./StatusBadge.jsx";

function countByStatus(documents, status) {
    return documents.filter(
        (doc) => doc.processing_status?.toUpperCase() === status
    ).length;
}

function averageConfidence(documents) {
    const values = documents
        .map((doc) => Number(doc.confidence))
        .filter((value) => Number.isFinite(value));

    if (values.length === 0) {
        return "—";
    }

    const average = values.reduce((sum, value) => sum + value, 0) / values.length;

    return formatConfidence(average);
}

function EmptyRow({ children }) {
    return (
        <tr>
            <td colSpan="6" className="empty-state">
                {children}
            </td>
        </tr>
    );
}

// Mounted only while the Dashboard tab is open, so it reloads
// the history every time the user switches back to it.
export default function Dashboard({ onView }) {
    const [documents, setDocuments] = useState([]);
    const [status, setStatus] = useState("loading"); // loading | ready | error

    const load = useCallback(async () => {
        setStatus("loading");

        try {
            setDocuments(await fetchDocuments());
            setStatus("ready");
        } catch (error) {
            console.error(error);
            setStatus("error");
        }
    }, []);

    useEffect(() => {
        load();
    }, [load]);

    let body;

    if (status === "loading") {
        body = <EmptyRow>Loading documents...</EmptyRow>;
    } else if (status === "error") {
        body = <EmptyRow>Could not load documents.</EmptyRow>;
    } else if (documents.length === 0) {
        body = <EmptyRow>No documents processed yet.</EmptyRow>;
    } else {
        body = documents.map((doc) => (
            <tr key={doc.id ?? doc.document_name}>
                <td data-label="Document">{doc.document_name}</td>
                <td data-label="Type">{formatDocumentType(doc.document_type)}</td>
                <td data-label="Status">
                    <StatusBadge status={doc.processing_status} />
                </td>
                <td data-label="Confidence">
                    {doc.confidence !== null && doc.confidence !== undefined
                        ? formatConfidence(doc.confidence)
                        : "—"}
                </td>
                <td data-label="Updated">{formatDate(doc.updated_at)}</td>
                <td>
                    <button
                        type="button"
                        className="secondary-button"
                        onClick={() => onView(doc.document_name)}
                    >
                        View
                    </button>
                </td>
            </tr>
        ));
    }

    const ready = status === "ready";

    return (
        <>
            <div className="page-header">
                <div>
                    <h2>Processed Documents</h2>
                    <p>Review previously processed documents and validation status.</p>
                </div>

                <button type="button" className="primary-button" onClick={load}>
                    Refresh
                </button>
            </div>

            <div className="summary-grid">
                <div className="summary-card">
                    <span className="summary-label">Total Documents</span>
                    <span className="summary-value">
                        {ready ? documents.length : 0}
                    </span>
                </div>

                <div className="summary-card">
                    <span className="summary-label">Passed</span>
                    <span className="summary-value success-text">
                        {ready ? countByStatus(documents, "PASS") : 0}
                    </span>
                </div>

                <div className="summary-card">
                    <span className="summary-label">Failed</span>
                    <span className="summary-value error-text">
                        {ready ? countByStatus(documents, "FAILED") : 0}
                    </span>
                </div>

                <div className="summary-card">
                    <span className="summary-label">Average Confidence</span>
                    <span className="summary-value">
                        {ready ? averageConfidence(documents) : "—"}
                    </span>
                </div>
            </div>

            <div className="panel">
                <div className="panel-header">
                    <h3>Document History</h3>
                </div>

                <div className="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>Document</th>
                                <th>Type</th>
                                <th>Status</th>
                                <th>Confidence</th>
                                <th>Updated</th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody>{body}</tbody>
                    </table>
                </div>
            </div>
        </>
    );
}
