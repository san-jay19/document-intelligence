import { useCallback, useState } from "react";
import { fetchDocument } from "./api.js";
import { useApiHealth } from "./hooks/useApiHealth.js";
import { useTheme } from "./hooks/useTheme.js";
import Dashboard from "./components/Dashboard.jsx";
import Header from "./components/Header.jsx";
import Nav from "./components/Nav.jsx";
import ProcessForm from "./components/ProcessForm.jsx";
import ResultView from "./components/ResultView.jsx";

export default function App() {
    const { theme, toggleTheme } = useTheme();
    const health = useApiHealth();

    const [view, setView] = useState("dashboard"); // dashboard | process
    const [result, setResult] = useState(null);

    // "View" button on the dashboard: load the stored result and
    // show it on the Process Document tab.
    const openStoredDocument = useCallback(async (documentName) => {
        try {
            const data = await fetchDocument(documentName);

            setResult(data);
            setView("process");
        } catch (error) {
            console.error(error);
            alert(error.message || "Could not retrieve document.");
        }
    }, []);

    return (
        <>
            <Header theme={theme} onToggleTheme={toggleTheme} health={health} />
            <Nav view={view} onChange={setView} />

            <main className="container">
                {/* Dashboard remounts each time it opens, so it refetches. */}
                {view === "dashboard" && (
                    <section className="view active-view">
                        <Dashboard onView={openStoredDocument} />
                    </section>
                )}

                {/* Always mounted so the form and its message survive tab switches. */}
                <section
                    className={`view${view === "process" ? " active-view" : ""}`}
                >
                    <div className="page-header">
                        <div>
                            <h2>Process Document</h2>
                            <p>
                                Upload a supported financial document for AI
                                extraction and validation.
                            </p>
                        </div>
                    </div>

                    <ProcessForm onResult={setResult} />

                    {result && <ResultView data={result} />}
                </section>
            </main>
        </>
    );
}
