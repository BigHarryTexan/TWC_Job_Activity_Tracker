// report.js

document.getElementById("generateReportBtn").addEventListener("click", async () => {
    const status = document.getElementById("reportStatus");
    status.textContent = "Generating report…";

    try {
        const response = await fetch(`${WORKER_URL}/generate-report`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ trigger: "generate_report" })
        });

        if (response.ok) {
            status.textContent = "Report generation triggered! Check the reports folder shortly.";
        } else {
            status.textContent = "Error triggering report.";
        }
    } catch (err) {
        status.textContent = "Network error triggering report.";
    }
});
