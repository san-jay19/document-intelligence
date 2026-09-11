// =========================================================
// Configuration
// =========================================================

// Replace this with your actual Render backend URL.
const API_BASE_URL =
    "https://document-intelligence-538o.onrender.com";


// =========================================================
// DOM Helpers
// =========================================================

const $ = (id) =>
    document.getElementById(id);


// =========================================================
// Theme
// =========================================================

const THEME_STORAGE_KEY = "docint-theme";
const themeToggleButton = $("themeToggleButton");

function applyTheme(theme) {

    document.documentElement.setAttribute(
        "data-theme",
        theme
    );

    if (!themeToggleButton) {
        return;
    }

    const isDark =
        theme === "dark";

    themeToggleButton.querySelector("span").textContent =
        isDark ? "☀️" : "🌙";

    themeToggleButton.setAttribute(
        "aria-label",
        isDark
            ? "Switch to light mode"
            : "Switch to dark mode"
    );
}

function setTheme(theme) {

    applyTheme(theme);

    try {

        localStorage.setItem(
            THEME_STORAGE_KEY,
            theme
        );

    } catch (error) {
        // Private browsing / storage disabled — theme just
        // won't persist across reloads.
    }
}

// The page already set data-theme before paint (see the
// inline script in index.html); just sync the toggle icon.
applyTheme(
    document.documentElement.getAttribute("data-theme")
    || "light"
);

if (themeToggleButton) {

    themeToggleButton.addEventListener(
        "click",
        () => {

            const current =
                document.documentElement.getAttribute("data-theme")
                === "dark"
                    ? "dark"
                    : "light";

            setTheme(
                current === "dark"
                    ? "light"
                    : "dark"
            );
        }
    );
}


// =========================================================
// Navigation
// =========================================================

document
    .querySelectorAll(".nav-button")
    .forEach((button) => {

        button.addEventListener(
            "click",
            () => {

                const view =
                    button.dataset.view;

                switchView(view);
            }
        );
    });


function switchView(viewName) {

    document
        .querySelectorAll(".view")
        .forEach((view) => {

            view.classList.remove(
                "active-view"
            );
        });

    document
        .querySelectorAll(".nav-button")
        .forEach((button) => {

            button.classList.remove(
                "active"
            );
        });

    if (viewName === "dashboard") {

        $("dashboardView")
            .classList.add(
                "active-view"
            );

        $("dashboardNavButton")
            .classList.add(
                "active"
            );

        loadDashboard();

    } else {

        $("processView")
            .classList.add(
                "active-view"
            );

        $("processNavButton")
            .classList.add(
                "active"
            );
    }
}


// =========================================================
// API Health
// =========================================================

async function checkApiHealth() {

    const statusDot =
        document.querySelector(
            ".status-dot"
        );

    try {

        const response =
            await fetch(
                `${API_BASE_URL}/api/v1/health`
            );

        if (!response.ok) {
            throw new Error(
                "API health check failed"
            );
        }

        const data =
            await response.json();

        statusDot.style.background =
            "#22c55e";

        $("apiStatusText").textContent =
            `${data.service} online`;

    } catch (error) {

        statusDot.style.background =
            "#ef4444";

        $("apiStatusText").textContent =
            "API unavailable";

        console.error(error);
    }
}


// =========================================================
// Dashboard
// =========================================================

$("refreshDashboardButton")
    .addEventListener(
        "click",
        loadDashboard
    );


async function loadDashboard() {

    const tbody =
        $("documentsTableBody");

    tbody.innerHTML = `
        <tr>
            <td
                colspan="6"
                class="empty-state"
            >
                Loading documents...
            </td>
        </tr>
    `;

    try {

        const response =
            await fetch(
                `${API_BASE_URL}/api/v1/documents`
            );

        if (!response.ok) {
            throw new Error(
                `HTTP ${response.status}`
            );
        }

        const data =
            await response.json();

        renderDashboard(
            data.documents || []
        );

    } catch (error) {

        console.error(error);

        tbody.innerHTML = `
            <tr>
                <td
                    colspan="6"
                    class="empty-state"
                >
                    Could not load documents.
                </td>
            </tr>
        `;
    }
}


function renderDashboard(documents) {

    $("totalDocuments").textContent =
        documents.length;

    const passed =
        documents.filter(
            (document) =>
                document.processing_status
                    ?.toUpperCase()
                === "PASS"
        ).length;

    const failed =
        documents.filter(
            (document) =>
                document.processing_status
                    ?.toUpperCase()
                === "FAILED"
        ).length;

    $("passedDocuments").textContent =
        passed;

    $("failedDocuments").textContent =
        failed;


    const confidenceValues =
        documents
            .map(
                (document) =>
                    Number(document.confidence)
            )
            .filter(
                (value) =>
                    Number.isFinite(value)
            );

    if (confidenceValues.length > 0) {

        const average =
            confidenceValues.reduce(
                (sum, value) =>
                    sum + value,
                0
            ) / confidenceValues.length;

        $("averageConfidence")
            .textContent =
            formatConfidence(
                average
            );

    } else {

        $("averageConfidence")
            .textContent = "—";
    }


    const tbody =
        $("documentsTableBody");

    if (documents.length === 0) {

        tbody.innerHTML = `
            <tr>
                <td
                    colspan="6"
                    class="empty-state"
                >
                    No documents processed yet.
                </td>
            </tr>
        `;

        return;
    }


    tbody.innerHTML =
        documents
            .map(
                (document) => {

                    const encodedName =
                        encodeURIComponent(
                            document.document_name
                        );

                    return `
                        <tr>
                            <td data-label="Document">
                                ${escapeHtml(
                                    document.document_name
                                )}
                            </td>

                            <td data-label="Type">
                                ${formatDocumentType(
                                    document.document_type
                                )}
                            </td>

                            <td data-label="Status">
                                ${renderStatusBadge(
                                    document.processing_status
                                )}
                            </td>

                            <td data-label="Confidence">
                                ${
                                    document.confidence !== null
                                        ? formatConfidence(
                                            document.confidence
                                        )
                                        : "—"
                                }
                            </td>

                            <td data-label="Updated">
                                ${formatDate(
                                    document.updated_at
                                )}
                            </td>

                            <td>
                                <button
                                    class="secondary-button"
                                    onclick="viewDocument(
                                        '${encodedName}'
                                    )"
                                >
                                    View
                                </button>
                            </td>
                        </tr>
                    `;
                }
            )
            .join("");
}


// =========================================================
// Process Form
// =========================================================

$("processForm")
    .addEventListener(
        "submit",
        processDocument
    );


async function processDocument(event) {

    event.preventDefault();

    const file =
        $("documentFile").files[0];

    const documentType =
        $("documentType").value;

    if (!file) {

        showMessage(
            "Please select a file.",
            "error"
        );

        return;
    }

    if (!documentType) {

        showMessage(
            "Please select a document type.",
            "error"
        );

        return;
    }

    const formData =
        new FormData();

    formData.append(
        "file",
        file
    );

    formData.append(
        "document_type",
        documentType
    );

    const processButton =
        $("processButton");

    processButton.disabled = true;

    processButton.textContent =
        "Processing...";

    showMessage(
        "Document is being processed. This may take a little while for scanned PDFs.",
        "info"
    );

    try {

        const data = await new Promise(
            (resolve, reject) => {

                const xhr =
                    new XMLHttpRequest();

                xhr.open(
                    "POST",
                    `${API_BASE_URL}/api/v1/documents/process`,
                    true
                );

                xhr.setRequestHeader(
                    "Accept",
                    "application/json"
                );

                xhr.timeout =
                    180000;

                xhr.onload = () => {

                    let responseData = null;

                    try {
                        responseData =
                            xhr.responseText
                                ? JSON.parse(
                                    xhr.responseText
                                )
                                : null;
                    } catch (error) {
                        responseData = null;
                    }

                    if (
                        xhr.status >= 200
                        && xhr.status < 300
                    ) {
                        resolve(
                            responseData
                        );
                        return;
                    }

                    const message =
                        responseData?.detail?.message
                        || responseData?.detail
                        || `Request failed with HTTP ${xhr.status}`;

                    reject(
                        new Error(message)
                    );
                };

                xhr.onerror = () => {

                    reject(
                        new Error(
                            "Network error while uploading the document. This may be caused by CORS or the mobile network."
                        )
                    );
                };

                xhr.ontimeout = () => {

                    reject(
                        new Error(
                            "Document processing timed out. Please try a smaller document."
                        )
                    );
                };

                xhr.onabort = () => {

                    reject(
                        new Error(
                            "Document upload was cancelled."
                        )
                    );
                };

                xhr.send(
                    formData
                );
            }
        );

        renderResult(data);

        $("resultSection")
            .classList.remove(
                "hidden"
            );

        showMessage(
            "Document processing completed.",
            "success"
        );

    } catch (error) {

        console.error(
            "Document processing error:",
            error
        );

        showMessage(
            error.message
            || "An unexpected error occurred.",
            "error"
        );

    } finally {

        processButton.disabled = false;

        processButton.textContent =
            "Process Document";
    }
}


// =========================================================
// Result Rendering
// =========================================================

function renderResult(data) {

    $("resultDocumentName")
        .textContent =
        data.document_name
        || "—";

    $("resultDocumentType")
        .textContent =
        formatDocumentType(
            data.document_type
        );

    $("resultProcessingStatus")
        .innerHTML =
        renderStatusBadge(
            data.processing_status
        );

    $("resultConfidence")
        .textContent =
        data.confidence !== null
            && data.confidence !== undefined
            ? formatConfidence(
                data.confidence
            )
            : "—";


    renderValidation(
        data.validation
    );

    renderFields(
        data.extracted_data?.fields
        || []
    );

    renderTables(
        data.extracted_data?.tables
        || []
    );

    $("rawJson").textContent =
        JSON.stringify(
            data,
            null,
            2
        );
}


// =========================================================
// Validation Rendering
// =========================================================

function renderValidation(validation) {

    const summary =
        validation?.summary
        || {};

    const overallStatus =
        validation?.overall_status
        || "NOT_APPLICABLE";


    $("validationSummary").innerHTML = `

        <div class="validation-stat">

            <div class="validation-stat-label">
                Overall Status
            </div>

            <div>
                ${renderStatusBadge(
                    overallStatus
                )}
            </div>

        </div>


        <div class="validation-stat">

            <div class="validation-stat-label">
                Passed Checks
            </div>

            <div class="validation-stat-value">
                ${summary.passed_checks ?? 0}
            </div>

        </div>


        <div class="validation-stat">

            <div class="validation-stat-label">
                Failed Checks
            </div>

            <div class="validation-stat-value">
                ${summary.failed_checks ?? 0}
            </div>

        </div>


        <div class="validation-stat">

            <div class="validation-stat-label">
                Not Applicable
            </div>

            <div class="validation-stat-value">
                ${summary.not_applicable_checks ?? 0}
            </div>

        </div>
    `;


    const checks =
        validation?.checks
        || [];

    const tbody =
        $("validationTableBody");


    if (checks.length === 0) {

        tbody.innerHTML = `
            <tr>
                <td
                    colspan="5"
                    class="empty-state"
                >
                    No financial validation checks available.
                </td>
            </tr>
        `;

        return;
    }


    tbody.innerHTML =
        checks
            .map(
                (check) => `

                    <tr>

                        <td data-label="Check">
                            ${
                                escapeHtml(
                                    check.check
                                    || check.name
                                    || "Validation check"
                                )
                            }
                        </td>

                        <td data-label="Status">
                            ${renderStatusBadge(
                                check.status
                                || "NOT_APPLICABLE"
                            )}
                        </td>

                        <td data-label="Calculated">
                            ${formatValue(
                                check.calculated
                            )}
                        </td>

                        <td data-label="Reported">
                            ${formatValue(
                                check.reported
                            )}
                        </td>

                        <td data-label="Variance">
                            ${formatValue(
                                check.variance
                            )}
                        </td>

                    </tr>
                `
            )
            .join("");
}


// =========================================================
// Field Rendering
// =========================================================

function renderFields(fields) {

    const container =
        $("fieldsContainer");


    if (fields.length === 0) {

        container.innerHTML = `
            <div class="empty-state">
                No fields were extracted.
            </div>
        `;

        return;
    }


    container.innerHTML =
        fields
            .map(
                (field) => {

                    const value =
                        field.value;

                    const missing =
                        value === null
                        || value === undefined
                        || value === "";

                    const confidence =
                        Number(
                            field.confidence
                        );

                    const lowConfidence =
                        Number.isFinite(
                            confidence
                        )
                        && confidence < 0.70;


                    let className =
                        "field-card";

                    if (missing) {
                        className +=
                            " missing";
                    }

                    else if (lowConfidence) {
                        className +=
                            " low-confidence";
                    }


                    return `

                        <div
                            class="${className}"
                        >

                            <div class="field-name">
                                ${escapeHtml(
                                    field.name
                                )}
                            </div>

                            <div class="field-value">
                                ${
                                    missing
                                        ? "Missing / unavailable"
                                        : escapeHtml(
                                            formatValue(
                                                value
                                            )
                                        )
                                }
                            </div>

                            <div class="field-meta">

                                ${
                                    field.confidence !== null
                                    && field.confidence !== undefined
                                        ? `
                                            <span>
                                                Confidence:
                                                ${
                                                    formatConfidence(
                                                        field.confidence
                                                    )
                                                }
                                            </span>
                                          `
                                        : ""
                                }

                            </div>


                            ${
                                field.evidence
                                    ? `
                                        <div class="evidence">
                                            <strong>
                                                Evidence:
                                            </strong>

                                            ${escapeHtml(
                                                field.evidence
                                            )}
                                        </div>
                                      `
                                    : ""
                            }

                        </div>
                    `;
                }
            )
            .join("");
}


// =========================================================
// Table Rendering
// =========================================================

function renderTables(tables) {

    const container =
        $("tablesContainer");


    if (tables.length === 0) {

        container.innerHTML = `
            <div class="empty-state">
                No structured tables were extracted.
            </div>
        `;

        return;
    }


    container.innerHTML =
        tables
            .map(
                (table) => {

                    const headers =
                        table.headers
                        || [];

                    const rows =
                        table.rows
                        || [];


                    const headerHtml =
                        headers
                            .map(
                                (header) =>
                                    `<th>${escapeHtml(
                                        String(header)
                                    )}</th>`
                            )
                            .join("");


                    const rowsHtml =
                        rows
                            .map(
                                (row) => {

                                    const cells =
                                        row
                                            .map(
                                                (cell, cellIndex) => {

                                                    const label =
                                                        headers[cellIndex] !== undefined
                                                            ? escapeHtml(
                                                                String(
                                                                    headers[cellIndex]
                                                                )
                                                            )
                                                            : "";

                                                    return `<td data-label="${label}">${escapeHtml(
                                                        formatValue(
                                                            cell
                                                        )
                                                    )}</td>`;
                                                }
                                            )
                                            .join("");

                                    return `<tr>${cells}</tr>`;
                                }
                            )
                            .join("");


                    return `

                        <div class="extracted-table">

                            <h4>
                                ${escapeHtml(
                                    table.table_name
                                    || "Table"
                                )}
                            </h4>

                            <div class="table-container">

                                <table>

                                    <thead>
                                        <tr>
                                            ${headerHtml}
                                        </tr>
                                    </thead>

                                    <tbody>
                                        ${rowsHtml}
                                    </tbody>

                                </table>

                            </div>

                        </div>
                    `;
                }
            )
            .join("");
}


// =========================================================
// Get One Document
// =========================================================

async function viewDocument(
    encodedName
) {

    const documentName =
        decodeURIComponent(
            encodedName
        );


    try {

        const response =
            await fetch(
                `${API_BASE_URL}/api/v1/documents/${encodedName}`
            );


        if (!response.ok) {

            const data =
                await response.json();

            throw new Error(
                data?.detail?.message
                || "Could not retrieve document."
            );
        }


        const data =
            await response.json();


        // Switch to processing/result view.
        switchView(
            "process"
        );


        renderResult(
            data
        );


        $("resultSection")
            .classList.remove(
                "hidden"
            );


    } catch (error) {

        console.error(error);

        alert(
            error.message
            || "Could not retrieve document."
        );
    }
}


// =========================================================
// Copy Raw JSON
// =========================================================

$("copyJsonButton")
    .addEventListener(
        "click",
        async () => {

            try {

                await navigator.clipboard.writeText(
                    $("rawJson").textContent
                );

                $("copyJsonButton")
                    .textContent =
                    "Copied";

                setTimeout(
                    () => {

                        $("copyJsonButton")
                            .textContent =
                            "Copy";

                    },
                    1500
                );

            } catch (error) {

                console.error(error);

            }
        }
    );


// =========================================================
// Message
// =========================================================

function showMessage(
    message,
    type = "info"
) {

    const element =
        $("processingMessage");

    element.textContent =
        message;

    element.classList.remove(
        "hidden"
    );

    element.classList.remove(
        "message-success",
        "message-error"
    );

    if (type === "error") {

        element.classList.add(
            "message-error"
        );

    } else if (type === "success") {

        element.classList.add(
            "message-success"
        );
    }

    // "info" uses the base .message styling, no extra class.
}


// =========================================================
// Formatting
// =========================================================

function formatDocumentType(
    type
) {

    if (!type) {
        return "—";
    }

    const labels = {
        invoice: "Invoice",

        balance_sheet:
            "Balance Sheet",

        profit_and_loss:
            "Profit & Loss",

        cash_flow_statement:
            "Cash Flow Statement",
    };

    return (
        labels[type]
        || type
    );
}


function formatConfidence(
    value
) {

    const number =
        Number(value);

    if (!Number.isFinite(number)) {
        return "—";
    }

    // Handle both decimal confidence
    // and percentage confidence.
    const percentage =
        number <= 1
            ? number * 100
            : number;

    return `${percentage.toFixed(1)}%`;
}


function formatDate(
    value
) {

    if (!value) {
        return "—";
    }

    const date =
        new Date(value);

    if (Number.isNaN(
        date.getTime()
    )) {
        return value;
    }

    return date.toLocaleString();
}


function formatValue(
    value
) {

    if (
        value === null
        || value === undefined
    ) {
        return "—";
    }

    if (
        typeof value === "object"
    ) {
        return JSON.stringify(
            value
        );
    }

    return String(
        value
    );
}


// =========================================================
// Status Badge
// =========================================================

function renderStatusBadge(
    status
) {

    const normalized =
        String(
            status
            || "NOT_APPLICABLE"
        )
        .toUpperCase();


    let className =
        "status-badge ";


    if (
        normalized === "PASS"
    ) {

        className +=
            "status-pass";

    } else if (
        normalized === "FAIL"
        || normalized === "FAILED"
    ) {

        className +=
            "status-fail";

    } else if (
        normalized === "WARNING"
    ) {

        className +=
            "status-warning";

    } else {

        className +=
            "status-na";
    }


    return `
        <span class="${className}">
            ${escapeHtml(
                normalized
            )}
        </span>
    `;
}


// =========================================================
// HTML Escape
// =========================================================

function escapeHtml(
    value
) {

    return String(
        value
        ?? ""
    )
    .replace(
        /&/g,
        "&amp;"
    )
    .replace(
        /</g,
        "&lt;"
    )
    .replace(
        />/g,
        "&gt;"
    )
    .replace(
        /"/g,
        "&quot;"
    )
    .replace(
        /'/g,
        "&#039;"
    );
}


// =========================================================
// Backend Connection Test
// =========================================================

async function testBackendConnection() {

    try {

        showMessage(
            "Testing backend connection...",
            "info"
        );

        const response =
            await fetch(
                `${API_BASE_URL}/api/v1/health`,
                {
                    method: "GET",
                    cache: "no-store",
                }
            );

        const data =
            await response.json();

        if (!response.ok) {

            throw new Error(
                `Backend returned HTTP ${response.status}`
            );
        }

        showMessage(
            `Backend connected: ${data.service}`,
            "success"
        );

        console.log(
            "Backend health:",
            data
        );

    } catch (error) {

        console.error(
            "Backend connection error:",
            error
        );

        showMessage(
            `Backend connection failed: ${error.message}`,
            "error"
        );
    }
}


// =========================================================
// Initial Load
// =========================================================

document.addEventListener(
    "DOMContentLoaded",
    () => {

        checkApiHealth();

        loadDashboard();

        testBackendConnection();

    }
);