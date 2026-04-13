document.getElementById("generateReport").addEventListener("click", async () => {
  const status = document.getElementById("reportStatus");
  status.textContent = "Generating report… this may take a few seconds.";
  status.style.color = "black";

  // Show spinner
  const spinner = document.createElement("div");
  spinner.id = "spinner";
  spinner.style.marginTop = "10px";
  spinner.innerHTML = `
    <div style="
      border: 4px solid #f3f3f3;
      border-top: 4px solid #3498db;
      border-radius: 50%;
      width: 28px;
      height: 28px;
      animation: spin 1s linear infinite;
      margin: auto;
    "></div>
  `;
  status.appendChild(spinner);

  // Add spinner animation
  const style = document.createElement("style");
  style.innerHTML = `
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
  `;
  document.head.appendChild(style);

  try {
    // Trigger the Worker
    const response = await fetch(
      "https://twc-job-worker.clayharryman.workers.dev/generate-report",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" }
      }
    );

    if (!response.ok) {
      throw new Error("Worker returned an error");
    }

    status.textContent = "Report is generating… waiting for GitHub Pages to deploy.";
    status.appendChild(spinner);

    // Build expected report URL
    const today = new Date();
    const yyyy = today.getFullYear();
    const mm = String(today.getMonth() + 1).padStart(2, "0");
    const dd = String(today.getDate()).padStart(2, "0");

    const reportUrl = `https://bigharrytexan.github.io/TWC_Job_Activity_Tracker/reports/twc_report_${yyyy}_${mm}_${dd}.html`;

    // Poll GitHub Pages until the file exists
    const maxAttempts = 20; // ~20 seconds
    let attempts = 0;

    const poll = setInterval(async () => {
      attempts++;

      try {
        const check = await fetch(reportUrl, { method: "GET", cache: "no-store" });

        if (check.ok) {
          clearInterval(poll);
          status.textContent = "Report ready! Opening…";
          window.open(reportUrl, "_blank");
        }
      } catch (err) {
        // Ignore fetch errors during polling
      }

      if (attempts >= maxAttempts) {
        clearInterval(poll);
        status.textContent =
          "Report generation took too long. Refresh the page and try again.";
        status.style.color = "red";
      }
    }, 1000);
  } catch (err) {
    status.textContent = "Error generating report.";
    status.style.color = "red";
  }
});
