const scheme = window.matchMedia("(prefers-color-scheme: dark)");
const root = document.documentElement;
const theme = document.querySelector("#theme-toggle");
try {
  const stored = localStorage.getItem("ydd-skills-theme");
  if (stored === "light" || stored === "dark") root.dataset.theme = stored;
} catch {
  // The toggle still works for this page when storage is unavailable.
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
  const cards = [...document.querySelectorAll(".skill-card")];
  const count = document.querySelector("#skill-count");
  const empty = document.querySelector("#no-results");
  const chinese = root.lang === "zh-CN";
  function filterCatalog() {
    const terms = search.value.toLocaleLowerCase().trim().split(/\s+/);
    let visible = 0;
    for (const card of cards) {
      const text = card.textContent.toLocaleLowerCase();
      card.hidden = !terms.every((term) => text.includes(term));
      if (!card.hidden) visible++;
    }
    count.textContent = chinese ? `${visible} 项 Skills` : `${visible} ${visible === 1 ? "skill" : "skills"}`;
    empty.hidden = visible > 0;
  }
  search.closest("label").hidden = false;
  search.addEventListener("input", filterCatalog);
  filterCatalog();
}

const status = document.querySelector("#copy-status");
for (const button of document.querySelectorAll("[data-copy]")) {
  button.hidden = false;
  button.addEventListener("click", async () => {
    const target = document.getElementById(button.dataset.copy);
    try {
      await navigator.clipboard.writeText(target.textContent);
      status.textContent = document.body.dataset.copied;
    } catch {
      if (!target.hidden) {
        const selection = window.getSelection();
        const range = document.createRange();
        range.selectNodeContents(target);
        selection.removeAllRanges();
        selection.addRange(range);
      }
      status.textContent = target.hidden ? document.body.dataset.linkFailed : document.body.dataset.copyFailed;
    }
  });
}
