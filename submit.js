const WORKER_URL = "https://twc-job-worker.clayharryman.workers.dev";

document.getElementById("entry-form").addEventListener("submit", async (e) => {
  e.preventDefault();

  const entry = {
    timestamp: Date.now(),
    date: document.getElementById("date").value,
    employer: document.getElementById("employer").value,
    position: document.getElementById("position").value,
    method: document.getElementById("method").value,
    notes: document.getElementById("notes").value
  };

  try {
    const response = await fetch(WORKER_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(entry)
    });

    const msg = document.getElementById("message");

    if (response.ok) {
      msg.textContent = "Entry saved successfully.";
      msg.className = "success";
      e.target.reset();
    } else {
      msg.textContent = "Error saving entry.";
      msg.className = "error";
    }
  } catch (err) {
    console.error(err);
    const msg = document.getElementById("message");
    msg.textContent = "Failed to save entry.";
    msg.className = "error";
  }
});
