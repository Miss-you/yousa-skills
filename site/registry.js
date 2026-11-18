const scheme = window.matchMedia("(prefers-color-scheme: dark)");
const root = document.documentElement;
const theme = document.querySelector("#theme-toggle");
try {
  const stored = localStorage.getItem("ydd-skills-theme");
  if (stored === "light" || stored === "dark") root.dataset.theme = stored;
} catch {
  // Theme controls also work without storage.
}
const isDark = () => root.dataset.theme ? root.dataset.theme === "dark" : scheme.matches;
const syncTheme = () => theme.setAttribute("aria-pressed", String(isDark()));
syncTheme();
theme.hidden = false;
scheme.addEventListener("change", syncTheme);
theme.addEventListener("click", () => {
  root.dataset.theme = isDark() ? "light" : "dark";
  syncTheme();
  try {
    localStorage.setItem("ydd-skills-theme", root.dataset.theme);
  } catch {
    // The page theme was already applied.
  }
});

const search = document.querySelector("#skill-search");
if (search) {
  const rows = Array.from(document.querySelectorAll(".skill-row"), (row) => ({
    row,
    text: row.dataset.search.toLocaleLowerCase(),
  }));
  const count = document.querySelector("#skill-count");
  const empty = document.querySelector("#no-results");
  const form = search.form;
  const clear = form.querySelector(".clear-search");
  const chinese = root.lang === "zh-CN";
  const initialCount = count.textContent;
  function filterCatalog() {
    const query = search.value.toLocaleLowerCase().trim();
    const terms = query.split(/\s+/);
    let visible = 0;
    for (const { row, text } of rows) {
      row.hidden = !terms.every((term) => text.includes(term));
      if (!row.hidden) visible++;
    }
    count.textContent = !query ? initialCount : chinese
      ? `${visible} / ${rows.length} 项`
      : `${visible} of ${rows.length} skills`;
    empty.hidden = visible > 0;
    clear.hidden = !search.value;
  }
  form.hidden = false;
  form.addEventListener("submit", (event) => event.preventDefault());
  form.addEventListener("reset", (event) => {
    event.preventDefault();
    search.value = "";
    filterCatalog();
    search.focus();
  });
  search.addEventListener("input", filterCatalog);
  window.addEventListener("pageshow", filterCatalog);
  filterCatalog();
}

const status = document.querySelector("#copy-status");
const dialog = document.querySelector("#copy-fallback");
const fallback = dialog.querySelector("textarea");
let resetCopyLabel;
let previousButton;
let previousLabel;
for (const button of document.querySelectorAll("[data-copy]")) {
  button.hidden = false;
  button.addEventListener("click", async () => {
    const text = button.dataset.copy;
    status.textContent = "";
    try {
      await navigator.clipboard.writeText(text);
      if (previousButton) previousButton.textContent = previousLabel;
      clearTimeout(resetCopyLabel);
      previousButton = button;
      previousLabel = button.textContent;
      button.textContent = document.body.dataset.copied;
      status.textContent = `${button.getAttribute("aria-label")} · ${document.body.dataset.copied}`;
      resetCopyLabel = setTimeout(() => {
        button.textContent = previousLabel;
        previousButton = undefined;
      }, 2000);
    } catch {
      fallback.value = text;
      dialog.showModal();
      fallback.focus();
      fallback.select();
    }
  });
}
