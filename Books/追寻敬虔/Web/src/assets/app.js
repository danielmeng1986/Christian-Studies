const STORAGE_KEYS = {
  theme: "qfg-reader-theme",
  leftPanel: "qfg-reader-left-panel",
  rightPanel: "qfg-reader-right-panel",
};

const THEMES = new Set(["light", "sepia", "dark"]);
const root = document.documentElement;
const shell = document.querySelector("#app-shell");
const article = document.querySelector("#chapter-article");
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

const saveStatus = document.querySelector("#save-status");
const notesMessage = document.querySelector("#notes-message");
const notesMessageText = document.querySelector("#notes-message-text");
const reloadNotesButton = document.querySelector("#reload-notes");
const notesListView = document.querySelector("#notes-list-view");
const notesList = document.querySelector("#notes-list");
const notesCount = document.querySelector("#notes-count");
const unresolvedCount = document.querySelector("#unresolved-count");
const notesEmptyState = document.querySelector("#notes-empty-state");
const noteEditor = document.querySelector("#note-editor");
const noteEditorMode = document.querySelector("#note-editor-mode");
const noteEditorTitle = document.querySelector("#note-editor-title");
const noteQuotation = document.querySelector("#note-quotation");
const noteBody = document.querySelector("#note-body");
const noteFieldMessage = document.querySelector("#note-field-message");
const saveNoteButton = document.querySelector("#save-note");
const cancelNoteButton = document.querySelector("#cancel-note");
const deleteNoteButton = document.querySelector("#delete-note");
const selectionAction = document.querySelector("#selection-action");

let notesDocument = null;
let notesEtag = null;
let writeToken = null;
let resolvedAnchors = new Map();
let activeNoteId = null;
let draftAnchor = null;
let editorDirty = false;
let pendingSelectionAnchor = null;

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

function setSaveStatus(label, state) {
  saveStatus.textContent = label;
  saveStatus.dataset.state = state;
}

function showNotesMessage(message, reloadable = false) {
  notesMessageText.textContent = message;
  reloadNotesButton.hidden = !reloadable;
  notesMessage.hidden = false;
}

function hideNotesMessage() {
  notesMessage.hidden = true;
  notesMessageText.textContent = "";
}

function canonicalTextNodes(container) {
  const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      if (!node.data) return NodeFilter.FILTER_REJECT;
      if (node.parentElement?.closest(".footnote-ref")) return NodeFilter.FILTER_REJECT;
      return NodeFilter.FILTER_ACCEPT;
    },
  });
  const nodes = [];
  while (walker.nextNode()) nodes.push(walker.currentNode);
  return nodes;
}

function canonicalText(container) {
  return canonicalTextNodes(container).map((node) => node.data).join("");
}

function canonicalOffset(block, container, offset) {
  const range = document.createRange();
  range.setStart(block, 0);
  range.setEnd(container, offset);
  return canonicalText(range.cloneContents()).length;
}

function closestBlock(node) {
  const element = node.nodeType === Node.ELEMENT_NODE ? node : node.parentElement;
  return element?.closest("[data-block-id]") ?? null;
}

function contextMatches(text, index, anchor) {
  const prefix = text.slice(Math.max(0, index - anchor.prefix.length), index);
  const suffix = text.slice(index + anchor.exact.length, index + anchor.exact.length + anchor.suffix.length);
  return prefix === anchor.prefix && suffix === anchor.suffix;
}

function matchingOffsets(text, anchor) {
  const matches = [];
  let start = 0;
  while (start <= text.length) {
    const index = text.indexOf(anchor.exact, start);
    if (index === -1) break;
    if (contextMatches(text, index, anchor)) {
      matches.push({ startOffset: index, endOffset: index + anchor.exact.length });
    }
    start = index + Math.max(1, anchor.exact.length);
  }
  return matches;
}

function resolveAnchor(anchor) {
  const originalBlock = article.querySelector(`[data-block-id="${CSS.escape(anchor.blockId)}"]`);
  if (originalBlock) {
    const text = canonicalText(originalBlock);
    if (text.slice(anchor.startOffset, anchor.endOffset) === anchor.exact) {
      return { ...anchor };
    }
    const matches = matchingOffsets(text, anchor);
    if (matches.length === 1) {
      return { ...anchor, ...matches[0] };
    }
  }

  const chapterMatches = [];
  article.querySelectorAll("[data-block-id]").forEach((block) => {
    const matches = matchingOffsets(canonicalText(block), anchor);
    matches.forEach((match) => chapterMatches.push({ ...anchor, ...match, blockId: block.dataset.blockId }));
  });
  return chapterMatches.length === 1 ? chapterMatches[0] : null;
}

function unwrapHighlights() {
  article.querySelectorAll("mark.annotation-highlight").forEach((mark) => {
    const parent = mark.parentNode;
    mark.replaceWith(...mark.childNodes);
    parent?.normalize();
  });
}

function wrapTextRange(block, startOffset, endOffset, noteId) {
  const nodes = canonicalTextNodes(block);
  const segments = [];
  let position = 0;
  nodes.forEach((node) => {
    const nodeStart = position;
    const nodeEnd = position + node.data.length;
    const start = Math.max(startOffset, nodeStart);
    const end = Math.min(endOffset, nodeEnd);
    if (start < end) {
      segments.push({ node, start: start - nodeStart, end: end - nodeStart });
    }
    position = nodeEnd;
  });

  segments.reverse().forEach(({ node, start, end }) => {
    let selected = node;
    if (end < selected.data.length) selected.splitText(end);
    if (start > 0) selected = selected.splitText(start);
    const mark = document.createElement("mark");
    mark.className = "annotation-highlight";
    mark.dataset.noteId = noteId;
    mark.tabIndex = 0;
    mark.title = "打开笔记";
    selected.replaceWith(mark);
    mark.append(selected);
  });
}

function restoreAndRenderHighlights() {
  unwrapHighlights();
  resolvedAnchors = new Map();
  if (!notesDocument) return;

  const byBlock = new Map();
  notesDocument.notes.forEach((note) => {
    const resolved = resolveAnchor(note.anchor);
    if (!resolved) return;
    resolvedAnchors.set(note.id, resolved);
    const notes = byBlock.get(resolved.blockId) ?? [];
    notes.push({ note, anchor: resolved });
    byBlock.set(resolved.blockId, notes);
  });

  byBlock.forEach((entries, blockId) => {
    const block = article.querySelector(`[data-block-id="${CSS.escape(blockId)}"]`);
    if (!block) return;
    entries
      .sort((left, right) => right.anchor.startOffset - left.anchor.startOffset)
      .forEach(({ note, anchor }) => wrapTextRange(block, anchor.startOffset, anchor.endOffset, note.id));
  });
}

function formatDate(value) {
  return new Intl.DateTimeFormat("zh-CN", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

function renderNoteList() {
  if (!notesDocument) return;
  const count = notesDocument.notes.length;
  const unresolved = notesDocument.notes.filter((note) => !resolvedAnchors.has(note.id)).length;
  notesCount.textContent = `${count} 条笔记`;
  unresolvedCount.textContent = unresolved ? `${unresolved} 条需重新定位` : "";

  const items = notesDocument.notes.map((note) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "note-list-item";
    button.dataset.noteId = note.id;
    if (!resolvedAnchors.has(note.id)) button.classList.add("is-unresolved");

    const quote = document.createElement("span");
    quote.className = "note-list-item__quote";
    quote.textContent = `“${note.anchor.exact}”`;
    const preview = document.createElement("span");
    preview.className = "note-list-item__preview";
    preview.textContent = note.body;
    const meta = document.createElement("span");
    meta.className = "note-list-item__meta";
    meta.textContent = resolvedAnchors.has(note.id) ? formatDate(note.updatedAt) : `需重新定位 · ${formatDate(note.updatedAt)}`;
    button.append(quote, preview, meta);
    button.addEventListener("click", () => openExistingNote(note.id, true));
    return button;
  });
  notesList.replaceChildren(...items);

  const editorOpen = !noteEditor.hidden;
  notesListView.hidden = editorOpen || count === 0;
  notesEmptyState.hidden = editorOpen || count > 0;
}

function renderNotes() {
  restoreAndRenderHighlights();
  renderNoteList();
}

function cloneDocument() {
  return JSON.parse(JSON.stringify(notesDocument));
}

async function responseError(response) {
  try {
    const payload = await response.json();
    return payload.error?.message || `请求失败（${response.status}）`;
  } catch {
    return `请求失败（${response.status}）`;
  }
}

async function loadNotes() {
  setSaveStatus("载入中", "loading");
  hideNotesMessage();
  try {
    const [sessionResponse, notesResponse] = await Promise.all([
      fetch("/api/session", { cache: "no-store" }),
      fetch("/api/chapters/05/notes", { cache: "no-store" }),
    ]);
    if (!sessionResponse.ok) throw new Error(await responseError(sessionResponse));
    if (!notesResponse.ok) throw new Error(await responseError(notesResponse));
    writeToken = (await sessionResponse.json()).writeToken;
    notesDocument = await notesResponse.json();
    notesEtag = notesResponse.headers.get("ETag");
    setSaveStatus("已载入", "saved");
    renderNotes();
  } catch (error) {
    setSaveStatus("载入失败", "error");
    showNotesMessage(`无法读取笔记：${error.message}`, true);
  }
}

async function persistNotes(nextDocument) {
  setSaveStatus("保存中", "saving");
  hideNotesMessage();
  const response = await fetch("/api/chapters/05/notes", {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      "If-Match": notesEtag,
      "X-QFG-Write-Token": writeToken,
    },
    body: JSON.stringify(nextDocument),
  });
  if (!response.ok) {
    const message = await responseError(response);
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }
  notesDocument = await response.json();
  notesEtag = response.headers.get("ETag");
  setSaveStatus("已保存", "saved");
}

function confirmDiscard() {
  return !editorDirty || window.confirm("这条笔记还有未保存的修改。要放弃这些修改吗？");
}

function closeEditor({ force = false } = {}) {
  if (!force && !confirmDiscard()) return false;
  activeNoteId = null;
  draftAnchor = null;
  editorDirty = false;
  noteEditor.hidden = true;
  noteBody.value = "";
  noteFieldMessage.textContent = "";
  renderNoteList();
  return true;
}

function openEditor({ note = null, anchor }) {
  if (!confirmDiscard()) return;
  activeNoteId = note?.id ?? null;
  draftAnchor = anchor;
  editorDirty = false;
  noteEditor.hidden = false;
  notesListView.hidden = true;
  notesEmptyState.hidden = true;
  noteEditorMode.textContent = note ? "EDIT NOTE" : "NEW NOTE";
  noteEditorTitle.textContent = note ? "编辑笔记" : "写笔记";
  noteQuotation.textContent = anchor.exact;
  noteBody.value = note?.body ?? "";
  noteFieldMessage.textContent = note && !resolvedAnchors.has(note.id) ? "这条笔记目前无法在正文中定位，但内容仍可编辑。" : "";
  deleteNoteButton.hidden = !note;
  saveNoteButton.textContent = note ? "保存修改" : "保存笔记";
  applyPanelState("right", true);
  noteBody.focus();
}

function openExistingNote(noteId, scrollToHighlight = false) {
  const note = notesDocument?.notes.find((item) => item.id === noteId);
  if (!note) return;
  const anchor = resolvedAnchors.get(noteId) ?? note.anchor;
  openEditor({ note, anchor });
  if (scrollToHighlight && resolvedAnchors.has(noteId)) {
    article.querySelector(`mark[data-note-id="${CSS.escape(noteId)}"]`)?.scrollIntoView({ block: "center", behavior: "smooth" });
  }
}

function rangeIncludesFootnote(range) {
  return Boolean(range.cloneContents().querySelector?.(".footnote-ref"));
}

function selectionAnchor() {
  const selection = window.getSelection();
  if (!selection || selection.rangeCount !== 1 || selection.isCollapsed) return null;
  const range = selection.getRangeAt(0);
  const startBlock = closestBlock(range.startContainer);
  const endBlock = closestBlock(range.endContainer);
  if (!startBlock || startBlock !== endBlock || !article.contains(startBlock)) return null;
  if (rangeIncludesFootnote(range)) return null;

  const startOffset = canonicalOffset(startBlock, range.startContainer, range.startOffset);
  const endOffset = canonicalOffset(startBlock, range.endContainer, range.endOffset);
  if (endOffset <= startOffset) return null;
  const text = canonicalText(startBlock);
  const exact = text.slice(startOffset, endOffset);
  if (!exact.trim()) return null;

  const overlaps = [...resolvedAnchors.values()].some(
    (anchor) => anchor.blockId === startBlock.dataset.blockId && startOffset < anchor.endOffset && endOffset > anchor.startOffset,
  );
  if (overlaps) return null;

  return {
    blockId: startBlock.dataset.blockId,
    startOffset,
    endOffset,
    exact,
    prefix: text.slice(Math.max(0, startOffset - 32), startOffset),
    suffix: text.slice(endOffset, endOffset + 32),
  };
}

function updateSelectionAction() {
  const anchor = selectionAnchor();
  if (!anchor || !notesDocument) {
    pendingSelectionAnchor = null;
    selectionAction.hidden = true;
    return;
  }
  const selection = window.getSelection();
  const range = selection.getRangeAt(0);
  const rects = range.getClientRects();
  const rect = rects[rects.length - 1] ?? range.getBoundingClientRect();
  pendingSelectionAnchor = anchor;
  selectionAction.hidden = false;
  selectionAction.style.left = `${Math.min(window.innerWidth - 100, Math.max(8, rect.left + rect.width / 2 - 42))}px`;
  selectionAction.style.top = `${Math.min(window.innerHeight - 50, rect.bottom + 8)}px`;
}

function beginSelectedNote(anchor) {
  pendingSelectionAnchor = null;
  selectionAction.hidden = true;
  window.getSelection()?.removeAllRanges();
  openEditor({ anchor });
}

async function saveEditor(event) {
  event.preventDefault();
  const body = noteBody.value;
  if (!body.trim()) {
    noteFieldMessage.textContent = "笔记内容不能为空。";
    noteBody.focus();
    return;
  }
  if (!notesDocument || !draftAnchor) return;

  saveNoteButton.disabled = true;
  deleteNoteButton.disabled = true;
  const nextDocument = cloneDocument();
  const timestamp = new Date().toISOString();
  const normalizedAnchor = { ...draftAnchor };

  if (activeNoteId) {
    const index = nextDocument.notes.findIndex((note) => note.id === activeNoteId);
    if (index === -1) return;
    nextDocument.notes[index] = {
      ...nextDocument.notes[index],
      sourceRevision: article.dataset.sourceRevision,
      anchor: normalizedAnchor,
      body,
      updatedAt: timestamp,
    };
  } else {
    nextDocument.notes.push({
      id: crypto.randomUUID(),
      sourceRevision: article.dataset.sourceRevision,
      anchor: normalizedAnchor,
      body,
      format: "plain-text",
      createdAt: timestamp,
      updatedAt: timestamp,
    });
  }

  try {
    await persistNotes(nextDocument);
    editorDirty = false;
    closeEditor({ force: true });
    renderNotes();
  } catch (error) {
    setSaveStatus(error.status === 409 ? "版本冲突" : "保存失败", "error");
    showNotesMessage(error.status === 409 ? "磁盘中的笔记已经改变。请保留当前内容并重新载入。" : `保存失败：${error.message}`, true);
  } finally {
    saveNoteButton.disabled = false;
    deleteNoteButton.disabled = false;
  }
}

async function deleteActiveNote() {
  if (!activeNoteId || !notesDocument) return;
  if (!window.confirm("确定删除这条笔记吗？删除后正文高亮也会移除。")) return;
  const nextDocument = cloneDocument();
  nextDocument.notes = nextDocument.notes.filter((note) => note.id !== activeNoteId);
  saveNoteButton.disabled = true;
  deleteNoteButton.disabled = true;
  try {
    await persistNotes(nextDocument);
    editorDirty = false;
    closeEditor({ force: true });
    renderNotes();
  } catch (error) {
    setSaveStatus(error.status === 409 ? "版本冲突" : "删除失败", "error");
    showNotesMessage(error.status === 409 ? "磁盘中的笔记已经改变，请重新载入。" : `删除失败：${error.message}`, true);
  } finally {
    saveNoteButton.disabled = false;
    deleteNoteButton.disabled = false;
  }
}

themeButtons.forEach((button) => button.addEventListener("click", () => applyTheme(button.dataset.themeChoice)));
leftToggle.addEventListener("click", () => applyPanelState("left", leftToggle.getAttribute("aria-expanded") !== "true"));
rightToggle.addEventListener("click", () => applyPanelState("right", rightToggle.getAttribute("aria-expanded") !== "true"));

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

article.addEventListener("click", (event) => {
  const highlight = event.target.closest("mark.annotation-highlight");
  if (highlight) openExistingNote(highlight.dataset.noteId);
});
article.addEventListener("keydown", (event) => {
  const highlight = event.target.closest("mark.annotation-highlight");
  if (highlight && (event.key === "Enter" || event.key === " ")) {
    event.preventDefault();
    openExistingNote(highlight.dataset.noteId);
  }
});
article.addEventListener("mouseup", () => window.setTimeout(updateSelectionAction, 0));
article.addEventListener("keyup", () => window.setTimeout(updateSelectionAction, 0));
article.addEventListener("contextmenu", (event) => {
  if (event.shiftKey) return;
  const anchor = selectionAnchor();
  if (!anchor) return;
  event.preventDefault();
  beginSelectedNote(anchor);
});
document.addEventListener("selectionchange", () => window.setTimeout(updateSelectionAction, 0));

selectionAction.addEventListener("mousedown", (event) => event.preventDefault());
selectionAction.addEventListener("click", () => {
  if (pendingSelectionAnchor) beginSelectedNote(pendingSelectionAnchor);
});

noteBody.addEventListener("input", () => {
  editorDirty = true;
  noteFieldMessage.textContent = "";
  setSaveStatus("未保存", "dirty");
});
noteEditor.addEventListener("submit", saveEditor);
cancelNoteButton.addEventListener("click", () => closeEditor());
deleteNoteButton.addEventListener("click", deleteActiveNote);
reloadNotesButton.addEventListener("click", () => {
  if (!confirmDiscard()) return;
  closeEditor({ force: true });
  loadNotes();
});
window.addEventListener("beforeunload", (event) => {
  if (!editorDirty) return;
  event.preventDefault();
  event.returnValue = "";
});

applyTheme(preferredTheme(), false);
applyPanelState("left", storedPanelState(STORAGE_KEYS.leftPanel), false);
applyPanelState("right", storedPanelState(STORAGE_KEYS.rightPanel), false);
renderFootnotes();
loadNotes();
