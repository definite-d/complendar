// Wait for the DOM to be fully loaded before running script
document.addEventListener("DOMContentLoaded", () => {
  // --- 1. Cache DOM Elements ---
  const logs = document.getElementById("logs");
  const dlLink = document.getElementById("download-link");
  const linkInput = document.getElementById("link");
  const convertButton = document.getElementById("convert-btn");
  const themeToggle = document.getElementById("theme-toggle");

  // --- 2. Define Functions ---

  /**
   * Logs a message to the log box.
   * @param {string} msg - The message to display.
   * @param {string} [level='info'] - The log level ('info', 'warn', 'error', 'success').
   */
  function log(msg, level = "info") {
    const div = document.createElement("div");
    div.className = `log-entry log-${level}`;

    let prefix = "";
    if (level === "warn") prefix = "⚠️ ";
    else if (level === "error") prefix = "❌ ";
    else if (level === "success") prefix = "✅ ";

    const ts = new Date().toLocaleTimeString();

    div.textContent = `[${ts}] ${prefix}${msg}`;
    logs.appendChild(div);
    logs.scrollTop = logs.scrollHeight; // Auto-scroll to bottom
  }

  /**
   * Handles the conversion process when the button is clicked.
   */
  async function convert() {
    const link = linkInput.value.trim();

    if (!link) {
      log("No link provided.", "warn"); // Will get ⚠️ emoji and 'warn' style
      return;
    }
    dlLink.style.display = "none";
    logs.innerHTML = ""; // Clear previous logs
    log("Fetching and converting...", "info"); // Will get 'info' style

    try {
      const res = await fetch("/api/convert", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ link }),
      });
      const data = await res.json();

      if (res.ok) {
        if (data.guessed_headers) {
          log(
            `Guessed headers\n→ Name: "${data.guessed_headers.name}"\n→ Birthday: "${data.guessed_headers.birthday}"`,
            "info"
          );
        }
        dlLink.href = data.file;
        dlLink.style.display = "block";
        log("Conversion successful. You can now download the file.", "success");
      } else {
        log(`Error: ${data.error}`, "error");
      }
    } catch (e) {
      log(`Network or server error: ${e.message}`, "error");
    }
  }

  /**
   * Toggles the data-theme attribute on the <html> element.
   */
  function toggleTheme() {
    const theme = document.documentElement.getAttribute("data-theme");
    document.documentElement.setAttribute(
      "data-theme",
      theme === "dark" ? "light" : "dark"
    );
  }

  /**
   * Sets the initial theme based on user's system preference.
   */
  function setInitialTheme() {
    if (
      window.matchMedia &&
      window.matchMedia("(prefers-color-scheme: dark)").matches
    ) {
      document.documentElement.setAttribute("data-theme", "dark");
    }
  }

  // --- 3. Attach Event Listeners ---
  convertButton.addEventListener("click", convert);
  themeToggle.addEventListener("click", toggleTheme);

  // --- 4. Run Initial Setup ---
  setInitialTheme();
  log("Ready. Paste a link and click convert.", "info");
});
  