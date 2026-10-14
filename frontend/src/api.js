// =========================================================
// API client
// =========================================================

// Set VITE_API_BASE_URL in .env (local) or in the Render
// Static Site environment settings. Falls back to the
// currently deployed backend.
export const API_BASE_URL = (
    import.meta.env.VITE_API_BASE_URL ||
    "https://document-intelligence-538o.onrender.com"
).replace(/\/$/, "");

const API = `${API_BASE_URL}/api/v1`;

// FastAPI errors look like { detail: "text" } or
// { detail: { message: "text", ... } }.
function extractMessage(data, fallback) {
    const detail = data?.detail;

    if (typeof detail === "string") {
        return detail;
    }

    if (detail?.message) {
        return detail.message;
    }

    return fallback;
}

export async function fetchHealth() {
    const response = await fetch(`${API}/health`, { cache: "no-store" });

    if (!response.ok) {
        throw new Error("API health check failed");
    }

    return response.json();
}

export async function fetchDocuments() {
    const response = await fetch(`${API}/documents`);

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();

    return data.documents || [];
}

export async function fetchDocument(documentName) {
    const response = await fetch(
        `${API}/documents/${encodeURIComponent(documentName)}`
    );

    if (!response.ok) {
        let data = null;

        try {
            data = await response.json();
        } catch (error) {
            // Non-JSON error body; use the fallback below.
        }

        throw new Error(
            extractMessage(data, "Could not retrieve document.")
        );
    }

    return response.json();
}

// XMLHttpRequest is kept on purpose (as in the original app):
// it gives a reliable long timeout and clear network errors
// for large scanned uploads on slow or mobile connections.
export function processDocument(file, documentType) {
    return new Promise((resolve, reject) => {
        const formData = new FormData();

        formData.append("file", file);
        formData.append("document_type", documentType);

        const xhr = new XMLHttpRequest();

        xhr.open("POST", `${API}/documents/process`, true);
        xhr.setRequestHeader("Accept", "application/json");
        xhr.timeout = 180000;

        xhr.onload = () => {
            let responseData = null;

            try {
                responseData = xhr.responseText
                    ? JSON.parse(xhr.responseText)
                    : null;
            } catch (error) {
                responseData = null;
            }

            if (xhr.status >= 200 && xhr.status < 300) {
                resolve(responseData);
                return;
            }

            reject(
                new Error(
                    extractMessage(
                        responseData,
                        `Request failed with HTTP ${xhr.status}`
                    )
                )
            );
        };

        xhr.onerror = () =>
            reject(
                new Error(
                    "Network error while uploading the document. This may be caused by CORS or the mobile network."
                )
            );

        xhr.ontimeout = () =>
            reject(
                new Error(
                    "Document processing timed out. Please try a smaller document."
                )
            );

        xhr.onabort = () =>
            reject(new Error("Document upload was cancelled."));

        xhr.send(formData);
    });
}
