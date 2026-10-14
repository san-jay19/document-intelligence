import { useEffect, useState } from "react";
import { fetchHealth } from "../api.js";

// state: "checking" | "online" | "offline"
export function useApiHealth() {
    const [health, setHealth] = useState({
        state: "checking",
        text: "Checking API...",
    });

    useEffect(() => {
        let cancelled = false;

        fetchHealth()
            .then((data) => {
                if (!cancelled) {
                    setHealth({
                        state: "online",
                        text: `${data.service} online`,
                    });
                }
            })
            .catch((error) => {
                console.error(error);

                if (!cancelled) {
                    setHealth({
                        state: "offline",
                        text: "API unavailable",
                    });
                }
            });

        return () => {
            cancelled = true;
        };
    }, []);

    return health;
}
