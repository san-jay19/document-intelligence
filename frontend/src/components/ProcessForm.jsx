import { useRef, useState } from "react";
import { processDocument } from "../api.js";
import { DOCUMENT_TYPES } from "../utils/format.js";

export default function ProcessForm({ onResult }) {
    const fileInputRef = useRef(null);

    const [documentType, setDocumentType] = useState("");
    const [processing, setProcessing] = useState(false);
    const [message, setMessage] = useState(null); // { text, type }

    async function handleSubmit(event) {
        event.preventDefault();

        const file = fileInputRef.current?.files?.[0];

        if (!file) {
            setMessage({ text: "Please select a file.", type: "error" });
            return;
        }

        if (!documentType) {
            setMessage({ text: "Please select a document type.", type: "error" });
            return;
        }

        setProcessing(true);
        setMessage({
            text: "Document is being processed. This may take a little while for scanned PDFs.",
            type: "info",
        });

        try {
            const data = await processDocument(file, documentType);

            onResult(data);
            setMessage({ text: "Document processing completed.", type: "success" });
        } catch (error) {
            console.error("Document processing error:", error);
            setMessage({
                text: error.message || "An unexpected error occurred.",
                type: "error",
            });
        } finally {
            setProcessing(false);
        }
    }

    const messageClass = message
        ? `message${
              message.type === "error"
                  ? " message-error"
                  : message.type === "success"
                  ? " message-success"
                  : ""
          }`
        : "";

    return (
        <div className="panel">
            <form id="processForm" onSubmit={handleSubmit}>
                <div className="form-group">
                    <label htmlFor="documentType">Document Type</label>

                    <select
                        id="documentType"
                        name="document_type"
                        value={documentType}
                        onChange={(event) => setDocumentType(event.target.value)}
                        required
                    >
                        <option value="">Select document type</option>
                        {DOCUMENT_TYPES.map((type) => (
                            <option key={type.value} value={type.value}>
                                {type.label}
                            </option>
                        ))}
                    </select>
                </div>

                <div className="form-group">
                    <label htmlFor="documentFile">Document File</label>

                    <input
                        type="file"
                        id="documentFile"
                        name="file"
                        ref={fileInputRef}
                        accept=".pdf,.jpg,.jpeg,.png"
                        required
                    />

                    <small>Supported: PDF, JPG, PNG</small>
                </div>

                <button
                    type="submit"
                    className="primary-button"
                    disabled={processing}
                >
                    {processing ? "Processing..." : "Process Document"}
                </button>
            </form>

            {message && <div className={messageClass}>{message.text}</div>}
        </div>
    );
}
