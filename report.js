document.getElementById("generateReport").addEventListener("click", async () => {
  const status = document.getElementById("reportStatus");
  status.textContent = "Generating report...";

  try {
    const response = await fetch("https://twc-job-worker.clayharryman.workers.dev/view-raw");
    const data = await response.json();

    if (!response.ok) {
      status.textContent = "Error generating report.";
      return;
    }

    // Build a simple HTML table
    let html = `<h3>Work Search Report (Last 14 Days)</h3>`;
    html += `<p>Total entries: ${data.count}</p>`;
    html += `<table border="1" cellpadding="6" style="border-collapse: collapse;">`;
    html += `
      <tr>
        <th>Date</th>
        <th>Employer</th>
        <th>Position</th>
        <th>Method</th>
        <th>Notes</th>
      </tr>
    `;

    for (const e of data.entries) {
      html += `
        <tr>
          <td>${e.date}</td>
          <td>${e.employer}</td>
          <td>${e.position}</td>
          <td>${e.method}</td>
          <td>${e.notes}</td>
        </tr>
      `;
    }

    html += `</table>`;

    // Replace the status div with the report
    status.innerHTML = html;

  } catch (err) {
    console.error(err);
    status.textContent = "Failed to generate report.";
  }
});
