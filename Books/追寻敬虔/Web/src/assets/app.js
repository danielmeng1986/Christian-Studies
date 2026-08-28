const STORAGE_KEYS = {
  theme: "qfg-reader-theme",
  leftPanel: "qfg-reader-left-panel",
  rightPanel: "qfg-reader-right-panel",
  notesPanelWidth: "qfg-reader-notes-panel-width",
  discussionPanelWidth: "qfg-reader-discussion-panel-width",
};

const THEMES = new Set(["light", "sepia", "dark"]);
const root = document.documentElement;
const shell = document.querySelector("#app-shell");
const article = document.querySelector("#chapter-article");
const themeButtons = [...document.querySelectorAll("[data-theme-choice]")];
const leftToggle = document.querySelector("#toggle-references");
const rightToggle = document.querySelector("#toggle-notes");
const footnotePanel = document.querySelector("#reference-panel");
const notesPanel = document.querySelector("#notes-panel");
const studyPanelResizer = document.querySelector("#study-panel-resizer");
const chapterNavigation = document.querySelector("#chapter-navigation");
const chapterMenu = document.querySelector("#chapter-menu-list");
const currentChapterLink = chapterMenu.querySelector('[aria-current="page"]');
const chapterId = article.dataset.chapterId;
const notesApiUrl = `/api/chapters/${encodeURIComponent(chapterId)}/notes`;
const discussionsApiUrl = `/api/chapters/${encodeURIComponent(chapterId)}/discussions`;

const referenceList = document.querySelector("#reference-list");
const referenceEmptyState = document.querySelector("#reference-empty-state");
const showAllReferences = document.querySelector("#show-all-references");
const clearReferences = document.querySelector("#clear-references");
const footnoteRefs = [...document.querySelectorAll(".footnote-ref[data-footnote-id]")];
const scriptureRefs = [...document.querySelectorAll(".scripture-ref[data-scripture-id]")];
const interactiveRefs = [...document.querySelectorAll(".footnote-ref[data-footnote-id], .scripture-ref[data-scripture-id]")];
const scriptureData = JSON.parse(document.querySelector("#scripture-data")?.textContent || "{}");
const referenceKey = (ref) =>
  ref.classList.contains("scripture-ref") ? `scripture:${ref.dataset.scriptureId}` : `footnote:${ref.dataset.footnoteId}`;
const allReferenceKeys = [...new Set(interactiveRefs.map(referenceKey))];
let openReferenceKeys = [];
const selectedScriptureVersions = new Map();

const saveStatus = document.querySelector("#save-status");
const notesMessage = document.querySelector("#notes-message");
const notesMessageText = document.querySelector("#notes-message-text");
const reloadNotesButton = document.querySelector("#reload-notes");
const notesListView = document.querySelector("#notes-list-view");
const notesList = document.querySelector("#notes-list");
const notesCount = document.querySelector("#notes-count");
const unresolvedCount = document.querySelector("#unresolved-count");
const toggleAllNotes = document.querySelector("#toggle-all-notes");
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
const selectionNoteAction = document.querySelector("#selection-note-action");
const selectionDiscussAction = document.querySelector("#selection-discuss-action");
const notesTab = document.querySelector("#notes-tab");
const discussionsTab = document.querySelector("#discussions-tab");
const notesView = document.querySelector("#notes-view");
const discussionsView = document.querySelector("#discussions-view");
const studyPanelTitle = document.querySelector("#study-panel-title");
const discussionMessage = document.querySelector("#discussion-message");
const discussionHome = document.querySelector("#discussion-home");
const discussionThread = document.querySelector("#discussion-thread");
const discussionSelectionCard = document.querySelector("#discussion-selection-card");
const discussionSelectionQuote = document.querySelector("#discussion-selection-quote");
const discussionContextSummary = document.querySelector("#discussion-context-summary");
const matchingDiscussions = document.querySelector("#matching-discussions");
const matchingDiscussionCount = document.querySelector("#matching-discussion-count");
const matchingDiscussionList = document.querySelector("#matching-discussion-list");
const startNewDiscussionButton = document.querySelector("#start-new-discussion");
const cancelNewDiscussionButton = document.querySelector("#cancel-new-discussion");
const discussionStartForm = document.querySelector("#discussion-start-form");
const discussionFirstMessage = document.querySelector("#discussion-first-message");
const sendFirstMessage = document.querySelector("#send-first-message");
const discussionList = document.querySelector("#discussion-list");
const discussionEmptyState = document.querySelector("#discussion-empty-state");
const reloadDiscussions = document.querySelector("#reload-discussions");
const backToDiscussions = document.querySelector("#back-to-discussions");
const deleteDiscussionButton = document.querySelector("#delete-discussion");
const newFromThread = document.querySelector("#new-from-thread");
const discussionThreadQuote = document.querySelector("#discussion-thread-quote");
const discussionMessages = document.querySelector("#discussion-messages");
const discussionReplyForm = document.querySelector("#discussion-reply-form");
const discussionReply = document.querySelector("#discussion-reply");
const sendReply = document.querySelector("#send-reply");
const discussionModel = document.querySelector("#discussion-model");

let notesDocument = null;
let notesEtag = null;
let writeToken = null;
let resolvedAnchors = new Map();
let activeNoteId = null;
let draftAnchor = null;
let editorDirty = false;
let pendingSelectionAnchor = null;
let pendingSelectionContext = null;
let notesExpanded = false;
let session = null;
let discussionSummaries = [];
let activeDiscussion = null;
let activeDiscussionEtag = null;
let discussionSelection = null;
let discussionBusy = false;
let activeStudyMode = "notes";

const DESKTOP_STUDY_LAYOUT = window.matchMedia("(min-width: 68.01rem)");
const READING_MIN_WIDTH = 512;
const RESIZER_WIDTH = 8;
const STUDY_PANEL_WIDTHS = {
  notes: { min: 320, max: 520, storageKey: STORAGE_KEYS.notesPanelWidth },
  discussions: { min: 448, max: 720, storageKey: STORAGE_KEYS.discussionPanelWidth },
};

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
  if (side === "left" && activeStudyMode === "notes") {
    window.requestAnimationFrame(() => applyStoredStudyPanelWidth());
  }
  updateStudyPanelResizer();
}

function currentStudyWidthConfig() {
  return STUDY_PANEL_WIDTHS[activeStudyMode];
}

function studyWidthLimits() {
  const config = currentStudyWidthConfig();
  const leftWidth =
    activeStudyMode === "notes" && leftToggle.getAttribute("aria-expanded") === "true"
      ? footnotePanel.getBoundingClientRect().width
      : 0;
  const available = Math.floor(shell.getBoundingClientRect().width - leftWidth - READING_MIN_WIDTH - RESIZER_WIDTH);
  const maximum = Math.max(config.min, Math.min(config.max, available));
  return { min: Math.min(config.min, maximum), max: maximum };
}

function clampStudyPanelWidth(width) {
  const limits = studyWidthLimits();
  return Math.round(Math.min(limits.max, Math.max(limits.min, width)));
}

function storedStudyPanelWidth() {
  const value = Number(localStorage.getItem(currentStudyWidthConfig().storageKey));
  return Number.isFinite(value) && value > 0 ? value : null;
}

function updateStudyPanelResizer() {
  if (!studyPanelResizer) return;
  const enabled = DESKTOP_STUDY_LAYOUT.matches && rightToggle.getAttribute("aria-expanded") === "true";
  studyPanelResizer.setAttribute("aria-disabled", String(!enabled));
  studyPanelResizer.tabIndex = enabled ? 0 : -1;
  const limits = studyWidthLimits();
  const width = Math.round(notesPanel.getBoundingClientRect().width);
  studyPanelResizer.setAttribute("aria-valuemin", String(limits.min));
  studyPanelResizer.setAttribute("aria-valuemax", String(limits.max));
  studyPanelResizer.setAttribute("aria-valuenow", String(width));
  studyPanelResizer.setAttribute("aria-valuetext", `${width} 像素`);
}

function applyStoredStudyPanelWidth() {
  if (!DESKTOP_STUDY_LAYOUT.matches) {
    shell.style.removeProperty("--study-panel-width");
    updateStudyPanelResizer();
    return;
  }
  const savedWidth = storedStudyPanelWidth();
  if (savedWidth === null) {
    shell.style.removeProperty("--study-panel-width");
  } else {
    shell.style.setProperty("--study-panel-width", `${clampStudyPanelWidth(savedWidth)}px`);
  }
  window.requestAnimationFrame(updateStudyPanelResizer);
}

function setStudyPanelWidth(width, persist = true) {
  const nextWidth = clampStudyPanelWidth(width);
  shell.style.setProperty("--study-panel-width", `${nextWidth}px`);
  if (persist) localStorage.setItem(currentStudyWidthConfig().storageKey, String(nextWidth));
  updateStudyPanelResizer();
}

function resetStudyPanelWidth() {
  localStorage.removeItem(currentStudyWidthConfig().storageKey);
  shell.style.removeProperty("--study-panel-width");
  window.requestAnimationFrame(updateStudyPanelResizer);
}

function setChapterMenuOpen(open) {
  chapterMenu.hidden = !open;
  chapterNavigation.setAttribute("aria-expanded", String(open));
  if (open) currentChapterLink?.scrollIntoView({ block: "nearest" });
}

function footnoteTemplate(footnoteId) {
  return document.getElementById(`footnote-template-${footnoteId}`);
}

function syncReferenceRefs() {
  const openSet = new Set(openReferenceKeys);
  interactiveRefs.forEach((ref) => {
    const isOpen = openSet.has(referenceKey(ref));
    ref.setAttribute("aria-expanded", String(isOpen));
    ref.classList.toggle("is-open", isOpen);
  });
}

function closeReference(key) {
  openReferenceKeys = openReferenceKeys.filter((item) => item !== key);
  renderReferences();
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
  closeButton.addEventListener("click", () => closeReference(`footnote:${footnoteId}`));

  const content = document.createElement("div");
  content.className = "footnote-card__content";
  content.append(template.content.cloneNode(true));
  header.append(title, closeButton);
  card.append(header, content);
  return card;
}

function createScriptureCard(scriptureId) {
  const reference = scriptureData.references?.[scriptureId];
  if (!reference) return null;
  const selectedVersion = selectedScriptureVersions.get(scriptureId) || scriptureData.defaultTranslation;
  const passage = reference.versions[selectedVersion];
  if (!passage) return null;

  const card = document.createElement("article");
  card.className = "footnote-card scripture-card";
  card.id = `open-scripture-${scriptureId}`;
  card.dataset.scriptureId = scriptureId;

  const header = document.createElement("header");
  header.className = "footnote-card__header scripture-card__header";
  const title = document.createElement("h3");
  title.textContent = "经文";
  const controls = document.createElement("div");
  controls.className = "scripture-card__controls";
  const select = document.createElement("select");
  select.className = "scripture-card__translation";
  select.setAttribute("aria-label", "选择圣经译本");
  scriptureData.translationOrder.forEach((translationId) => {
    const option = document.createElement("option");
    option.value = translationId;
    option.textContent = scriptureData.translations[translationId].label;
    option.selected = translationId === selectedVersion;
    select.append(option);
  });
  select.addEventListener("change", () => {
    selectedScriptureVersions.set(scriptureId, select.value);
    renderReferences(`scripture:${scriptureId}`);
  });
  const closeButton = document.createElement("button");
  closeButton.type = "button";
  closeButton.className = "footnote-card__close";
  closeButton.setAttribute("aria-label", `关闭经文 ${scriptureId}`);
  closeButton.textContent = "×";
  closeButton.addEventListener("click", () => closeReference(`scripture:${scriptureId}`));
  controls.append(select, closeButton);
  header.append(title, controls);

  const content = document.createElement("div");
  content.className = "footnote-card__content scripture-card__content";
  const text = document.createElement("p");
  text.className = "scripture-card__text";
  text.textContent = passage.text;
  const citation = document.createElement("p");
  citation.className = "scripture-card__citation";
  citation.textContent = passage.citation;
  content.append(text, citation);
  card.append(header, content);
  return card;
}

function createReferenceCard(key) {
  const [type, id] = key.split(/:(.*)/s, 2);
  return type === "scripture" ? createScriptureCard(id) : createFootnoteCard(id);
}

function renderReferences(scrollToKey = null) {
  const cards = openReferenceKeys.map(createReferenceCard).filter(Boolean);
  referenceList.replaceChildren(...cards);
  referenceEmptyState.hidden = cards.length > 0;
  clearReferences.disabled = cards.length === 0;
  showAllReferences.disabled = allReferenceKeys.length === 0 || cards.length === allReferenceKeys.length;
  syncReferenceRefs();
  if (scrollToKey) {
    const [type, id] = scrollToKey.split(/:(.*)/s, 2);
    document.getElementById(`open-${type}-${id}`)?.scrollIntoView({ block: "nearest" });
  }
}

function toggleReference(key, initialVersion = null) {
  if (openReferenceKeys.includes(key)) {
    closeReference(key);
    return;
  }
  if (key.startsWith("scripture:") && initialVersion) {
    const scriptureId = key.slice("scripture:".length);
    if (!selectedScriptureVersions.has(scriptureId)) selectedScriptureVersions.set(scriptureId, initialVersion);
  }
  openReferenceKeys = [...openReferenceKeys, key];
  applyPanelState("left", true);
  renderReferences(key);
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

function canonicalTextNodes(container, includeReferences = false) {
  const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      if (!node.data) return NodeFilter.FILTER_REJECT;
      if (node.parentElement?.closest(".discussion-anchor-marker")) return NodeFilter.FILTER_REJECT;
      if (node.parentElement?.closest(".footnote-ref")) return NodeFilter.FILTER_REJECT;
      if (!includeReferences && node.parentElement?.closest(".scripture-ref")) {
        return NodeFilter.FILTER_REJECT;
      }
      return NodeFilter.FILTER_ACCEPT;
    },
  });
  const nodes = [];
  while (walker.nextNode()) nodes.push(walker.currentNode);
  return nodes;
}

function canonicalText(container, includeReferences = false) {
  return canonicalTextNodes(container, includeReferences).map((node) => node.data).join("");
}

function canonicalOffset(block, container, offset, includeReferences = false) {
  const range = document.createRange();
  range.setStart(block, 0);
  range.setEnd(container, offset);
  return canonicalText(range.cloneContents(), includeReferences).length;
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

function resolveAnchorInProjection(anchor, includeReferences) {
  const originalBlock = article.querySelector(`[data-block-id="${CSS.escape(anchor.blockId)}"]`);
  if (originalBlock) {
    const text = canonicalText(originalBlock, includeReferences);
    if (text.slice(anchor.startOffset, anchor.endOffset) === anchor.exact) {
      return { ...anchor, includeReferences };
    }
    const matches = matchingOffsets(text, anchor);
    if (matches.length === 1) {
      return { ...anchor, ...matches[0], includeReferences };
    }
  }

  const chapterMatches = [];
  article.querySelectorAll("[data-block-id]").forEach((block) => {
    const matches = matchingOffsets(canonicalText(block, includeReferences), anchor);
    matches.forEach((match) =>
      chapterMatches.push({ ...anchor, ...match, blockId: block.dataset.blockId, includeReferences }),
    );
  });
  return chapterMatches.length === 1 ? chapterMatches[0] : null;
}

function resolveAnchor(anchor) {
  return resolveAnchorInProjection(anchor, true) ?? resolveAnchorInProjection(anchor, false);
}

function unwrapHighlights() {
  article.querySelectorAll("mark.annotation-highlight").forEach((mark) => {
    const parent = mark.parentNode;
    mark.replaceWith(...mark.childNodes);
    parent?.normalize();
  });
}

function wrapTextRange(block, startOffset, endOffset, noteId, includeReferences) {
  const nodes = canonicalTextNodes(block, includeReferences);
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
      .forEach(({ note, anchor }) =>
        wrapTextRange(block, anchor.startOffset, anchor.endOffset, note.id, anchor.includeReferences),
      );
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

  const sortedNotes = [...notesDocument.notes].sort(
    (left, right) => new Date(right.updatedAt) - new Date(left.updatedAt) || right.id.localeCompare(left.id),
  );
  const visibleNotes = notesExpanded ? sortedNotes : sortedNotes.slice(0, 3);
  toggleAllNotes.hidden = count <= 3;
  toggleAllNotes.setAttribute("aria-expanded", String(notesExpanded));
  toggleAllNotes.textContent = notesExpanded ? "收起" : `展开全部（${count}）`;

  const items = visibleNotes.map((note) => {
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
      fetch(notesApiUrl, { cache: "no-store" }),
    ]);
    if (!sessionResponse.ok) throw new Error(await responseError(sessionResponse));
    if (!notesResponse.ok) throw new Error(await responseError(notesResponse));
    session = await sessionResponse.json();
    writeToken = session.writeToken;
    notesDocument = await notesResponse.json();
    notesEtag = notesResponse.headers.get("ETag");
    setSaveStatus("已载入", "saved");
    renderNotes();
    await loadDiscussions();
  } catch (error) {
    setSaveStatus("载入失败", "error");
    showNotesMessage(`无法读取笔记：${error.message}`, true);
  }
}

async function persistNotes(nextDocument) {
  setSaveStatus("保存中", "saving");
  hideNotesMessage();
  const response = await fetch(notesApiUrl, {
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

function selectionAnchor() {
  const selection = window.getSelection();
  if (!selection || selection.rangeCount !== 1 || selection.isCollapsed) return null;
  const range = selection.getRangeAt(0);
  const startBlock = closestBlock(range.startContainer);
  const endBlock = closestBlock(range.endContainer);
  if (!startBlock || startBlock !== endBlock || !article.contains(startBlock)) return null;

  const startOffset = canonicalOffset(startBlock, range.startContainer, range.startOffset, true);
  const endOffset = canonicalOffset(startBlock, range.endContainer, range.endOffset, true);
  if (endOffset <= startOffset) return null;
  const text = canonicalText(startBlock, true);
  const exact = text.slice(startOffset, endOffset);
  if (!exact.trim()) return null;

  return {
    blockId: startBlock.dataset.blockId,
    startOffset,
    endOffset,
    exact,
    prefix: text.slice(Math.max(0, startOffset - 32), startOffset),
    suffix: text.slice(endOffset, endOffset + 32),
  };
}

function selectionReferences(range) {
  const refs = interactiveRefs.filter((ref) => {
    try {
      return range.intersectsNode(ref);
    } catch {
      return false;
    }
  });
  const scriptures = [];
  const footnotes = [];
  const seen = new Set();
  refs.forEach((ref) => {
    const key = referenceKey(ref);
    if (seen.has(key)) return;
    seen.add(key);
    if (ref.classList.contains("scripture-ref")) {
      const id = ref.dataset.scriptureId;
      const translationId = selectedScriptureVersions.get(id) || ref.dataset.initialVersion || scriptureData.defaultTranslation;
      const passage = scriptureData.references?.[id]?.versions?.[translationId];
      const translation = scriptureData.translations?.[translationId];
      if (passage && translation) {
        scriptures.push({
          id,
          translationId,
          translationLabel: translation.label,
          citation: passage.citation,
          text: passage.text,
        });
      }
    } else {
      const id = ref.dataset.footnoteId;
      const template = footnoteTemplate(id);
      const text = template?.content?.textContent?.trim();
      if (text) footnotes.push({ id, text });
    }
  });
  return { scriptures, footnotes };
}

function updateSelectionAction() {
  const anchor = selectionAnchor();
  if (!anchor || !notesDocument) {
    pendingSelectionAnchor = null;
    pendingSelectionContext = null;
    selectionAction.hidden = true;
    return;
  }
  const selection = window.getSelection();
  const range = selection.getRangeAt(0);
  const rects = range.getClientRects();
  const rect = rects[rects.length - 1] ?? range.getBoundingClientRect();
  pendingSelectionAnchor = anchor;
  pendingSelectionContext = selectionReferences(range);
  selectionAction.hidden = false;
  selectionAction.style.left = `${Math.min(window.innerWidth - 236, Math.max(8, rect.left + rect.width / 2 - 112))}px`;
  selectionAction.style.top = `${Math.min(window.innerHeight - 50, rect.bottom + 8)}px`;
}

function beginSelectedNote(anchor) {
  pendingSelectionAnchor = null;
  pendingSelectionContext = null;
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

function switchStudyTab(tab) {
  const showNotes = tab === "notes";
  const nextMode = showNotes ? "notes" : "discussions";
  const previousMode = activeStudyMode;
  activeStudyMode = nextMode;
  shell.classList.toggle("discussion-focus", !showNotes);
  if (!showNotes && previousMode !== "discussions") {
    applyPanelState("left", false, false);
  } else if (showNotes && previousMode === "discussions") {
    applyPanelState("left", storedPanelState(STORAGE_KEYS.leftPanel), false);
  }
  notesTab.setAttribute("aria-selected", String(showNotes));
  discussionsTab.setAttribute("aria-selected", String(!showNotes));
  notesView.hidden = !showNotes;
  discussionsView.hidden = showNotes;
  studyPanelTitle.textContent = showNotes ? "我的笔记" : "与 AI 讨论";
  saveStatus.hidden = !showNotes;
  applyPanelState("right", true);
  applyStoredStudyPanelWidth();
}

function showDiscussionMessage(message, state = "info") {
  discussionMessage.textContent = message;
  discussionMessage.dataset.state = state;
  discussionMessage.hidden = !message;
}

function sameAnchor(left, right) {
  return (
    left.blockId === right.blockId &&
    left.startOffset === right.startOffset &&
    left.endOffset === right.endOffset &&
    left.exact === right.exact
  );
}

function createDiscussionListItem(summary) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "discussion-list-item";
  const title = document.createElement("strong");
  title.textContent = summary.title;
  const preview = document.createElement("span");
  preview.textContent = summary.preview || "等待 AI 回复";
  const meta = document.createElement("small");
  meta.textContent = `${summary.messageCount} 条消息 · ${formatDate(summary.updatedAt)}${summary.hasFailedResponse ? " · 回复失败" : ""}`;
  button.append(title, preview, meta);
  button.addEventListener("click", () => openDiscussion(summary.id));
  return button;
}

function renderDiscussionMarkers() {
  article.querySelectorAll(".discussion-anchor-marker").forEach((marker) => marker.remove());
  const byBlock = new Map();
  discussionSummaries.forEach((summary) => {
    const entries = byBlock.get(summary.anchor.blockId) || [];
    entries.push(summary);
    byBlock.set(summary.anchor.blockId, entries);
  });
  byBlock.forEach((entries, blockId) => {
    const block = article.querySelector(`[data-block-id="${CSS.escape(blockId)}"]`);
    if (!block) return;
    const marker = document.createElement("button");
    marker.type = "button";
    marker.className = "discussion-anchor-marker";
    marker.textContent = entries.length === 1 ? "AI" : `AI ${entries.length}`;
    marker.title = entries.map((entry) => entry.title).join("\n");
    marker.setAttribute("aria-label", `打开这段文字的 ${entries.length} 个 AI 讨论`);
    marker.addEventListener("click", () => openDiscussion(entries[0].id));
    block.append(marker);
  });
}

function renderDiscussionLists() {
  renderDiscussionMarkers();
  const allItems = discussionSummaries.map(createDiscussionListItem);
  discussionList.replaceChildren(...allItems);
  discussionEmptyState.hidden = allItems.length > 0;

  if (!discussionSelection) {
    discussionSelectionCard.hidden = true;
    matchingDiscussions.hidden = true;
    discussionStartForm.hidden = true;
    return;
  }
  discussionSelectionCard.hidden = false;
  discussionSelectionQuote.textContent = discussionSelection.anchor.exact;
  const scriptureCount = discussionSelection.scriptures.length;
  const footnoteCount = discussionSelection.footnotes.length;
  discussionContextSummary.textContent = `将加入完整章节、${scriptureCount} 处经文和 ${footnoteCount} 条脚注。`;
  const matches = discussionSummaries.filter((summary) => sameAnchor(summary.anchor, discussionSelection.anchor));
  matchingDiscussionList.replaceChildren(...matches.map(createDiscussionListItem));
  matchingDiscussionCount.textContent = matches.length ? `${matches.length} 个` : "";
  matchingDiscussions.hidden = matches.length === 0;
  discussionStartForm.hidden = matches.length > 0;
  if (matches.length === 0) discussionFirstMessage.focus();
}

async function loadDiscussions() {
  try {
    const response = await fetch(discussionsApiUrl, { cache: "no-store" });
    if (!response.ok) throw new Error(await responseError(response));
    discussionSummaries = (await response.json()).discussions;
    showDiscussionMessage("");
    renderDiscussionLists();
  } catch (error) {
    showDiscussionMessage(`无法读取讨论：${error.message}`, "error");
  }
}

function renderDiscussionThread() {
  if (!activeDiscussion) return;
  discussionHome.hidden = true;
  discussionThread.hidden = false;
  discussionThreadQuote.textContent = activeDiscussion.anchor.exact;
  discussionModel.textContent = session?.model ? `模型：${session.model}` : "";
  const items = activeDiscussion.messages.map((message) => {
    const item = document.createElement("article");
    item.className = `discussion-message-card discussion-message-card--${message.role}`;
    const label = document.createElement("p");
    label.className = "discussion-message-card__label";
    label.textContent = message.role === "user" ? "你" : "AI";
    const content = document.createElement("div");
    content.className = "discussion-message-card__content";
    if (message.status === "pending" && !message.content) {
      content.textContent = "正在思考……";
      item.classList.add("is-pending");
    } else if (message.status === "failed") {
      content.textContent = message.error?.message || "这次回复失败了。";
      item.classList.add("is-failed");
      if (message.error?.retryable) {
        const retry = document.createElement("button");
        retry.type = "button";
        retry.className = "secondary-button";
        retry.textContent = "重试";
        retry.disabled = discussionBusy;
        retry.addEventListener("click", retryDiscussion);
        content.append(document.createElement("br"), retry);
      }
    } else {
      if (message.role === "assistant" && typeof message.renderedContent === "string") {
        content.classList.add("markdown-content");
        content.innerHTML = message.renderedContent;
      } else {
        content.textContent = message.content;
      }
    }
    item.append(label, content);
    return item;
  });
  discussionMessages.replaceChildren(...items);
  discussionReply.disabled = discussionBusy;
  sendReply.disabled = discussionBusy;
  discussionMessages.lastElementChild?.scrollIntoView({ block: "end" });
}

async function openDiscussion(id) {
  try {
    const response = await fetch(`/api/discussions/${encodeURIComponent(id)}`, { cache: "no-store" });
    if (!response.ok) throw new Error(await responseError(response));
    activeDiscussion = await response.json();
    activeDiscussionEtag = response.headers.get("ETag");
    discussionSelection = {
      anchor: activeDiscussion.anchor,
      scriptures: activeDiscussion.context.scriptures,
      footnotes: activeDiscussion.context.footnotes,
    };
    showDiscussionMessage(
      activeDiscussion.sourceRevision === article.dataset.sourceRevision ? "" : "正文自创建此讨论后已变更；讨论保留，本轮会使用当前完整章节。",
      "info",
    );
    switchStudyTab("discussions");
    renderDiscussionThread();
  } catch (error) {
    showDiscussionMessage(`无法打开讨论：${error.message}`, "error");
  }
}

async function consumeNdjson(response) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";
    for (const line of lines) {
      if (!line.trim()) continue;
      const event = JSON.parse(line);
      if (event.type === "response.started") {
        activeDiscussion = event.discussion;
        activeDiscussionEtag = event.etag;
        renderDiscussionThread();
      } else if (event.type === "response.delta") {
        const pending = activeDiscussion?.messages.at(-1);
        if (pending?.status === "pending") pending.content += event.delta;
        renderDiscussionThread();
      } else if (event.type === "response.completed" || event.type === "response.error") {
        activeDiscussion = event.discussion;
        activeDiscussionEtag = event.etag;
        if (event.error) showDiscussionMessage(event.error.message, "error");
        renderDiscussionThread();
      }
    }
    if (done) break;
  }
}

async function postDiscussion(url, payload, etag = null) {
  discussionBusy = true;
  showDiscussionMessage("");
  renderDiscussionThread();
  const headers = {
    "Content-Type": "application/json",
    "X-QFG-Write-Token": writeToken,
  };
  if (etag) headers["If-Match"] = etag;
  try {
    const response = await fetch(url, { method: "POST", headers, body: JSON.stringify(payload) });
    if (!response.ok) {
      const error = new Error(await responseError(response));
      error.status = response.status;
      throw error;
    }
    discussionHome.hidden = true;
    discussionThread.hidden = false;
    await consumeNdjson(response);
    await loadDiscussions();
  } finally {
    discussionBusy = false;
    renderDiscussionThread();
  }
}

function beginSelectedDiscussion(anchor, context) {
  pendingSelectionAnchor = null;
  pendingSelectionContext = null;
  selectionAction.hidden = true;
  window.getSelection()?.removeAllRanges();
  discussionSelection = { anchor, ...context };
  activeDiscussion = null;
  activeDiscussionEtag = null;
  discussionHome.hidden = false;
  discussionThread.hidden = true;
  switchStudyTab("discussions");
  renderDiscussionLists();
}

async function createDiscussion(event) {
  event.preventDefault();
  if (!discussionSelection || !discussionFirstMessage.value.trim()) return;
  if (!session?.aiConfigured) {
    showDiscussionMessage("尚未安全注入 OPENAI_API_KEY，请先从已配置密钥的终端启动阅读器。", "error");
    return;
  }
  const payload = {
    sourceRevision: article.dataset.sourceRevision,
    anchor: discussionSelection.anchor,
    scriptures: discussionSelection.scriptures,
    footnotes: discussionSelection.footnotes,
    message: discussionFirstMessage.value,
  };
  sendFirstMessage.disabled = true;
  try {
    await postDiscussion(discussionsApiUrl, payload);
    discussionFirstMessage.value = "";
  } catch (error) {
    showDiscussionMessage(`无法发起讨论：${error.message}`, "error");
  } finally {
    sendFirstMessage.disabled = false;
  }
}

async function continueDiscussion(event) {
  event.preventDefault();
  const message = discussionReply.value;
  if (!activeDiscussion || !message.trim()) return;
  try {
    discussionReply.value = "";
    await postDiscussion(
      `/api/discussions/${encodeURIComponent(activeDiscussion.id)}/messages`,
      { message },
      activeDiscussionEtag,
    );
  } catch (error) {
    discussionReply.value = message;
    showDiscussionMessage(`无法继续讨论：${error.message}`, "error");
  }
}

async function retryDiscussion() {
  if (!activeDiscussion || discussionBusy) return;
  try {
    await postDiscussion(
      `/api/discussions/${encodeURIComponent(activeDiscussion.id)}/messages`,
      { retry: true },
      activeDiscussionEtag,
    );
  } catch (error) {
    showDiscussionMessage(`重试失败：${error.message}`, "error");
  }
}

async function deleteDiscussion() {
  if (!activeDiscussion || discussionBusy) return;
  if (!window.confirm("确定删除这个讨论及其全部消息吗？此操作不可在阅读器中撤销。")) return;
  discussionBusy = true;
  try {
    const response = await fetch(`/api/discussions/${encodeURIComponent(activeDiscussion.id)}`, {
      method: "DELETE",
      headers: {
        "If-Match": activeDiscussionEtag,
        "X-QFG-Write-Token": writeToken,
      },
    });
    if (!response.ok) throw new Error(await responseError(response));
    activeDiscussion = null;
    activeDiscussionEtag = null;
    discussionSelection = null;
    discussionThread.hidden = true;
    discussionHome.hidden = false;
    await loadDiscussions();
    showDiscussionMessage("讨论已删除。");
  } catch (error) {
    showDiscussionMessage(`无法删除讨论：${error.message}`, "error");
  } finally {
    discussionBusy = false;
  }
}

themeButtons.forEach((button) => button.addEventListener("click", () => applyTheme(button.dataset.themeChoice)));
chapterNavigation.addEventListener("click", () => {
  setChapterMenuOpen(chapterNavigation.getAttribute("aria-expanded") !== "true");
});
chapterMenu.addEventListener("click", (event) => {
  const link = event.target.closest("a[href]");
  if (!link) return;
  if (!confirmDiscard()) event.preventDefault();
  setChapterMenuOpen(false);
});
document.addEventListener("click", (event) => {
  if (!event.target.closest(".chapter-menu")) setChapterMenuOpen(false);
});
document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape" || chapterMenu.hidden) return;
  setChapterMenuOpen(false);
  chapterNavigation.focus();
});
leftToggle.addEventListener("click", () => applyPanelState("left", leftToggle.getAttribute("aria-expanded") !== "true"));
rightToggle.addEventListener("click", () => applyPanelState("right", rightToggle.getAttribute("aria-expanded") !== "true"));

interactiveRefs.forEach((ref) => {
  ref.addEventListener("click", (event) => {
    event.preventDefault();
    if (event.target.closest("mark.annotation-highlight")) return;
    toggleReference(referenceKey(ref), ref.dataset.initialVersion);
  });
});
showAllReferences.addEventListener("click", () => {
  scriptureRefs.forEach((ref) => {
    if (!selectedScriptureVersions.has(ref.dataset.scriptureId)) {
      selectedScriptureVersions.set(ref.dataset.scriptureId, ref.dataset.initialVersion);
    }
  });
  openReferenceKeys = [...allReferenceKeys];
  applyPanelState("left", true);
  renderReferences();
});
clearReferences.addEventListener("click", () => {
  openReferenceKeys = [];
  renderReferences();
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
selectionNoteAction.addEventListener("click", () => {
  if (pendingSelectionAnchor) beginSelectedNote(pendingSelectionAnchor);
});
selectionDiscussAction.addEventListener("click", () => {
  if (pendingSelectionAnchor && pendingSelectionContext) {
    beginSelectedDiscussion(pendingSelectionAnchor, pendingSelectionContext);
  }
});

notesTab.addEventListener("click", () => switchStudyTab("notes"));
discussionsTab.addEventListener("click", () => switchStudyTab("discussions"));
studyPanelResizer.addEventListener("pointerdown", (event) => {
  if (!DESKTOP_STUDY_LAYOUT.matches || rightToggle.getAttribute("aria-expanded") !== "true") return;
  event.preventDefault();
  const startX = event.clientX;
  const startWidth = notesPanel.getBoundingClientRect().width;
  studyPanelResizer.setPointerCapture(event.pointerId);
  studyPanelResizer.classList.add("is-resizing");
  document.body.classList.add("is-resizing-study-panel");

  const move = (moveEvent) => setStudyPanelWidth(startWidth + startX - moveEvent.clientX);
  const finish = () => {
    studyPanelResizer.classList.remove("is-resizing");
    document.body.classList.remove("is-resizing-study-panel");
    studyPanelResizer.removeEventListener("pointermove", move);
    studyPanelResizer.removeEventListener("pointerup", finish);
    studyPanelResizer.removeEventListener("pointercancel", finish);
  };
  studyPanelResizer.addEventListener("pointermove", move);
  studyPanelResizer.addEventListener("pointerup", finish);
  studyPanelResizer.addEventListener("pointercancel", finish);
});
studyPanelResizer.addEventListener("keydown", (event) => {
  if (!DESKTOP_STUDY_LAYOUT.matches || rightToggle.getAttribute("aria-expanded") !== "true") return;
  const currentWidth = notesPanel.getBoundingClientRect().width;
  const step = event.shiftKey ? 48 : 16;
  if (event.key === "ArrowLeft") setStudyPanelWidth(currentWidth + step);
  else if (event.key === "ArrowRight") setStudyPanelWidth(currentWidth - step);
  else if (event.key === "Home") setStudyPanelWidth(studyWidthLimits().min);
  else if (event.key === "End") setStudyPanelWidth(studyWidthLimits().max);
  else return;
  event.preventDefault();
});
studyPanelResizer.addEventListener("dblclick", resetStudyPanelWidth);
reloadDiscussions.addEventListener("click", loadDiscussions);
startNewDiscussionButton.addEventListener("click", () => {
  matchingDiscussions.hidden = true;
  discussionStartForm.hidden = false;
  discussionFirstMessage.focus();
});
cancelNewDiscussionButton.addEventListener("click", () => {
  const hasMatches = discussionSelection
    ? discussionSummaries.some((summary) => sameAnchor(summary.anchor, discussionSelection.anchor))
    : false;
  discussionStartForm.hidden = true;
  matchingDiscussions.hidden = !hasMatches;
});
discussionStartForm.addEventListener("submit", createDiscussion);
discussionReplyForm.addEventListener("submit", continueDiscussion);
backToDiscussions.addEventListener("click", () => {
  activeDiscussion = null;
  activeDiscussionEtag = null;
  discussionThread.hidden = true;
  discussionHome.hidden = false;
  renderDiscussionLists();
});
deleteDiscussionButton.addEventListener("click", deleteDiscussion);
newFromThread.addEventListener("click", () => {
  if (!discussionSelection) return;
  activeDiscussion = null;
  activeDiscussionEtag = null;
  discussionThread.hidden = true;
  discussionHome.hidden = false;
  matchingDiscussions.hidden = true;
  discussionStartForm.hidden = false;
  renderDiscussionLists();
  matchingDiscussions.hidden = true;
  discussionStartForm.hidden = false;
  discussionFirstMessage.focus();
});

noteBody.addEventListener("input", () => {
  editorDirty = true;
  noteFieldMessage.textContent = "";
  setSaveStatus("未保存", "dirty");
});
noteEditor.addEventListener("submit", saveEditor);
cancelNoteButton.addEventListener("click", () => closeEditor());
deleteNoteButton.addEventListener("click", deleteActiveNote);
toggleAllNotes.addEventListener("click", () => {
  notesExpanded = !notesExpanded;
  renderNoteList();
});
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
window.addEventListener("resize", applyStoredStudyPanelWidth);

applyTheme(preferredTheme(), false);
applyPanelState("left", storedPanelState(STORAGE_KEYS.leftPanel), false);
applyPanelState("right", storedPanelState(STORAGE_KEYS.rightPanel), false);
applyStoredStudyPanelWidth();
renderReferences();
loadNotes();
