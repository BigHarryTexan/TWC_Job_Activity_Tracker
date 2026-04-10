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

    if (!response.ok) {
      throw new Error("Worker returned an error");
    }

    alert("Entry saved!");
  } catch (err) {
    console.error(err);
    alert("Failed to save entry.");
  }
});
