const STORAGE_KEYS = {
  theme: "qfg-reader-theme",
  leftPanel: "qfg-reader-left-panel",
  rightPanel: "qfg-reader-right-panel",
};

const THEMES = new Set(["light", "sepia", "dark"]);
const root = document.documentElement;
const shell = document.querySelector("#app-shell");
const themeButtons = [...document.querySelectorAll("[data-theme-choice]")];
const leftToggle = document.querySelector("#toggle-footnotes");
const rightToggle = document.querySelector("#toggle-notes");

function preferredTheme() {
  const saved = localStorage.getItem(STORAGE_KEYS.theme);
  if (saved && THEMES.has(saved)) return saved;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function applyTheme(theme, persist = true) {
  const nextTheme = THEMES.has(theme) ? theme : "light";
  root.dataset.theme = nextTheme;
  themeButtons.forEach((button) => {
    button.setAttribute("aria-pressed", String(button.dataset.themeChoice === nextTheme));
  });
  if (persist) localStorage.setItem(STORAGE_KEYS.theme, nextTheme);
}

function storedPanelState(key) {
  return localStorage.getItem(key) !== "closed";
}

function applyPanelState(side, open, persist = true) {
  const isLeft = side === "left";
  const className = isLeft ? "left-collapsed" : "right-collapsed";
  const toggle = isLeft ? leftToggle : rightToggle;
  const storageKey = isLeft ? STORAGE_KEYS.leftPanel : STORAGE_KEYS.rightPanel;

  shell.classList.toggle(className, !open);
  toggle.setAttribute("aria-expanded", String(open));
  if (persist) localStorage.setItem(storageKey, open ? "open" : "closed");
}

themeButtons.forEach((button) => {
  button.addEventListener("click", () => applyTheme(button.dataset.themeChoice));
});

leftToggle.addEventListener("click", () => {
  applyPanelState("left", leftToggle.getAttribute("aria-expanded") !== "true");
});

rightToggle.addEventListener("click", () => {
  applyPanelState("right", rightToggle.getAttribute("aria-expanded") !== "true");
});

applyTheme(preferredTheme(), false);
applyPanelState("left", storedPanelState(STORAGE_KEYS.leftPanel), false);
applyPanelState("right", storedPanelState(STORAGE_KEYS.rightPanel), false);
