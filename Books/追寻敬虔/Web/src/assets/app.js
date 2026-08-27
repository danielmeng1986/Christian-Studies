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
const footnoteList = document.querySelector("#footnote-list");
const footnoteEmptyState = document.querySelector("#footnote-empty-state");
const showAllFootnotes = document.querySelector("#show-all-footnotes");
const clearFootnotes = document.querySelector("#clear-footnotes");
const footnoteRefs = [...document.querySelectorAll(".footnote-ref[data-footnote-id]")];
const allFootnoteIds = [...new Set(footnoteRefs.map((ref) => ref.dataset.footnoteId))];
let openFootnoteIds = [];

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

function footnoteTemplate(footnoteId) {
  return document.getElementById(`footnote-template-${footnoteId}`);
}

function syncFootnoteRefs() {
  const openSet = new Set(openFootnoteIds);
  footnoteRefs.forEach((ref) => {
    const isOpen = openSet.has(ref.dataset.footnoteId);
    ref.setAttribute("aria-expanded", String(isOpen));
    ref.classList.toggle("is-open", isOpen);
  });
}

function closeFootnote(footnoteId) {
  openFootnoteIds = openFootnoteIds.filter((id) => id !== footnoteId);
  renderFootnotes();
}

function createFootnoteCard(footnoteId) {
  const template = footnoteTemplate(footnoteId);
  if (!template) return null;

  const card = document.createElement("article");
  card.className = "footnote-card";
  card.id = `open-footnote-${footnoteId}`;
  card.dataset.footnoteId = footnoteId;

  const header = document.createElement("header");
  header.className = "footnote-card__header";

  const title = document.createElement("h3");
  title.textContent = /^\d+$/.test(footnoteId) ? `脚注 ${footnoteId}` : footnoteId;

  const closeButton = document.createElement("button");
  closeButton.type = "button";
  closeButton.className = "footnote-card__close";
  closeButton.setAttribute("aria-label", `关闭${title.textContent}`);
  closeButton.textContent = "×";
  closeButton.addEventListener("click", () => closeFootnote(footnoteId));

  const content = document.createElement("div");
  content.className = "footnote-card__content";
  content.append(template.content.cloneNode(true));

  header.append(title, closeButton);
  card.append(header, content);
  return card;
}

function renderFootnotes(scrollToId = null) {
  const cards = openFootnoteIds.map(createFootnoteCard).filter(Boolean);
  footnoteList.replaceChildren(...cards);
  footnoteEmptyState.hidden = cards.length > 0;
  clearFootnotes.disabled = cards.length === 0;
  showAllFootnotes.disabled = allFootnoteIds.length === 0 || cards.length === allFootnoteIds.length;
  syncFootnoteRefs();

  if (scrollToId) {
    document.getElementById(`open-footnote-${scrollToId}`)?.scrollIntoView({ block: "nearest" });
  }
}

function toggleFootnote(footnoteId) {
  if (openFootnoteIds.includes(footnoteId)) {
    closeFootnote(footnoteId);
    return;
  }

  openFootnoteIds = [...openFootnoteIds, footnoteId];
  applyPanelState("left", true);
  renderFootnotes(footnoteId);
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

footnoteRefs.forEach((ref) => {
  ref.addEventListener("click", (event) => {
    event.preventDefault();
    toggleFootnote(ref.dataset.footnoteId);
  });
});

showAllFootnotes.addEventListener("click", () => {
  openFootnoteIds = [...allFootnoteIds];
  applyPanelState("left", true);
  renderFootnotes();
});

clearFootnotes.addEventListener("click", () => {
  openFootnoteIds = [];
  renderFootnotes();
});

applyTheme(preferredTheme(), false);
applyPanelState("left", storedPanelState(STORAGE_KEYS.leftPanel), false);
applyPanelState("right", storedPanelState(STORAGE_KEYS.rightPanel), false);
renderFootnotes();
