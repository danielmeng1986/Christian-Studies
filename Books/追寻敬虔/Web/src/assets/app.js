const STORAGE_KEYS = {
  theme: "qfg-reader-theme",
  leftPanel: "qfg-reader-left-panel",
  rightPanel: "qfg-reader-right-panel",
  notesPanelWidth: "qfg-reader-notes-panel-width",
  discussionPanelWidth: "qfg-reader-discussion-panel-width",
  libraryPanelWidth: "qfg-reader-library-panel-width",
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
const hideReferences = document.querySelector("#hide-references");
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
const libraryTab = document.querySelector("#library-tab");
const notesView = document.querySelector("#notes-view");
const discussionsView = document.querySelector("#discussions-view");
const libraryView = document.querySelector("#library-view");
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
const discussionContextPreview = document.querySelector("#discussion-context-preview");
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
const discussionReplyContextPreview = document.querySelector("#discussion-reply-context-preview");
const sendReply = document.querySelector("#send-reply");
const discussionModel = document.querySelector("#discussion-model");
const libraryMessage = document.querySelector("#library-message");
const libraryImportForm = document.querySelector("#library-import-form");
const libraryFile = document.querySelector("#library-file");
const libraryTitle = document.querySelector("#library-title");
const libraryAuthor = document.querySelector("#library-author");
const libraryLanguage = document.querySelector("#library-language");
const librarySourceType = document.querySelector("#library-source-type");
const libraryAuthority = document.querySelector("#library-authority");
const librarySensitivity = document.querySelector("#library-sensitivity");
const libraryTradition = document.querySelector("#library-tradition");
const libraryLicense = document.querySelector("#library-license");
const libraryImportPreview = document.querySelector("#library-import-preview");
const libraryPreviewButton = document.querySelector("#library-preview-button");
const libraryConfirmButton = document.querySelector("#library-confirm-button");
const libraryRebuild = document.querySelector("#library-rebuild");
const libraryList = document.querySelector("#library-list");
const libraryEmptyState = document.querySelector("#library-empty-state");

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
let librarySources = [];
let libraryPreviewId = null;
const discussionPreviewState = { start: null, reply: null };

const DESKTOP_STUDY_LAYOUT = window.matchMedia("(min-width: 68.01rem)");
const READING_MIN_WIDTH = 512;
const RESIZER_WIDTH = 8;
const STUDY_PANEL_WIDTHS = {
  notes: { min: 320, max: 520, storageKey: STORAGE_KEYS.notesPanelWidth },
  discussions: { min: 448, max: 720, storageKey: STORAGE_KEYS.discussionPanelWidth },
  library: { min: 448, max: 720, storageKey: STORAGE_KEYS.libraryPanelWidth },
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

function selectionHeadingPath(block) {
  const blocks = [...article.querySelectorAll("[data-block-id]")];
  const selectedIndex = blocks.indexOf(block);
  if (selectedIndex < 0) return [];
  let chapterHeading = "";
  let sectionHeading = "";
  for (let index = 0; index <= selectedIndex; index += 1) {
    const candidate = blocks[index];
    if (candidate.matches("h1")) {
      chapterHeading = canonicalText(candidate, true).trim();
      sectionHeading = "";
    } else if (candidate.matches("h2")) {
      sectionHeading = canonicalText(candidate, true).trim();
    }
  }
  return [chapterHeading, sectionHeading].filter(Boolean);
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
  switchStudyTab("notes");
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
  pendingSelectionContext = {
    ...selectionReferences(range),
    headingPath: selectionHeadingPath(closestBlock(range.startContainer)),
  };
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
  const showDiscussions = tab === "discussions";
  const nextMode = showNotes ? "notes" : showDiscussions ? "discussions" : "library";
  const previousMode = activeStudyMode;
  activeStudyMode = nextMode;
  shell.classList.toggle("discussion-focus", !showNotes);
  if (!showNotes && previousMode === "notes") {
    applyPanelState("left", false, false);
  } else if (showNotes && previousMode !== "notes") {
    applyPanelState("left", storedPanelState(STORAGE_KEYS.leftPanel), false);
  }
  notesTab.setAttribute("aria-selected", String(showNotes));
  discussionsTab.setAttribute("aria-selected", String(showDiscussions));
  libraryTab.setAttribute("aria-selected", String(nextMode === "library"));
  notesView.hidden = !showNotes;
  discussionsView.hidden = !showDiscussions;
  libraryView.hidden = nextMode !== "library";
  studyPanelTitle.textContent = showNotes ? "我的笔记" : showDiscussions ? "与 AI 讨论" : "本地资料库";
  saveStatus.hidden = !showNotes;
  applyPanelState("right", true);
  applyStoredStudyPanelWidth();
  if (nextMode === "library") loadLibrary();
}

function showLibraryMessage(message, state = "info") {
  libraryMessage.textContent = message;
  libraryMessage.dataset.state = state;
  libraryMessage.hidden = !message;
}

async function libraryWrite(path, payload, method = "POST") {
  const response = await fetch(path, {
    method,
    headers: { "Content-Type": "application/json", "X-QFG-Write-Token": writeToken },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(await responseError(response));
  return response.json();
}

function renderLibrary() {
  libraryEmptyState.hidden = librarySources.length > 0;
  const fragment = document.createDocumentFragment();
  librarySources.forEach((source) => {
    const card = document.createElement("article");
    card.className = "library-source-card";
    const title = document.createElement("strong");
    title.textContent = source.title;
    const meta = document.createElement("p");
    meta.textContent = [source.author, source.format.toUpperCase(), source.authorityClass].filter(Boolean).join(" · ");
    const status = document.createElement("p");
    status.className = "discussion-context-preview__muted";
    status.textContent = `${source.enabled ? "已启用" : "已停用"} · ${source.indexed ? "已索引" : "索引已移除"} · ${source.externalSharingApprovedAt ? "已允许外发节选" : "尚未允许外发"}`;
    const actions = document.createElement("div");
    actions.className = "library-source-actions";
    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.textContent = source.enabled ? "停用" : "启用";
    toggle.addEventListener("click", async () => {
      try {
        await libraryWrite(`/api/library/sources/${encodeURIComponent(source.sourceId)}`, { enabled: !source.enabled });
        await loadLibrary();
      } catch (error) { showLibraryMessage(error.message, "error"); }
    });
    actions.append(toggle);
    if (!source.externalSharingApprovedAt) {
      const approve = document.createElement("button");
      approve.type = "button";
      approve.textContent = "允许向 OpenAI 发送所选节选";
      approve.addEventListener("click", async () => {
        if (!window.confirm("以后只有你在发送预览中明确勾选的节选才会发给 OpenAI。是否授权此资料？")) return;
        try {
          await libraryWrite(`/api/library/sources/${encodeURIComponent(source.sourceId)}`, { approveExternalSharing: true });
          await loadLibrary();
        } catch (error) { showLibraryMessage(error.message, "error"); }
      });
      actions.append(approve);
    }
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "danger-button";
    remove.textContent = "移除派生索引";
    remove.addEventListener("click", async () => {
      if (!window.confirm("仅移除派生索引；原件与转换稿会保留，可通过重建恢复。继续吗？")) return;
      try {
        await libraryWrite(`/api/library/sources/${encodeURIComponent(source.sourceId)}/derived`, {}, "DELETE");
        await loadLibrary();
      } catch (error) { showLibraryMessage(error.message, "error"); }
    });
    actions.append(remove);
    card.append(title, meta, status, actions);
    fragment.append(card);
  });
  libraryList.replaceChildren(fragment);
}

async function loadLibrary() {
  try {
    const response = await fetch("/api/library");
    if (!response.ok) throw new Error(await responseError(response));
    librarySources = (await response.json()).sources;
    renderLibrary();
    showLibraryMessage("");
  } catch (error) { showLibraryMessage(`无法读取资料库：${error.message}`, "error"); }
}

function fileAsBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(",", 2)[1]);
    reader.onerror = () => reject(reader.error || new Error("无法读取文件"));
    reader.readAsDataURL(file);
  });
}

async function previewLibraryImport(event) {
  event.preventDefault();
  const file = libraryFile.files[0];
  if (!file) return;
  libraryPreviewButton.disabled = true;
  try {
    const optional = (input) => input.value.trim() || null;
    const result = await libraryWrite("/api/library/imports/preview", {
      filename: file.name,
      contentBase64: await fileAsBase64(file),
      metadata: {
        title: libraryTitle.value.trim(), author: optional(libraryAuthor), language: libraryLanguage.value.trim(),
        sourceType: librarySourceType.value, theologicalTradition: optional(libraryTradition),
        authorityClass: libraryAuthority.value, url: null, licenseNote: optional(libraryLicense),
        sensitivity: librarySensitivity.value,
      },
    });
    libraryPreviewId = result.previewId;
    const samples = result.sampleChunks.map((chunk) => `${chunk.locator}：${chunk.text.slice(0, 180)}`).join("\n\n");
    libraryImportPreview.textContent = `${result.format.toUpperCase()} · ${result.chunkCount} 个可定位片段 · SHA-256 ${result.sha256}\n\n${samples}`;
    libraryImportPreview.hidden = false;
    libraryConfirmButton.hidden = false;
    showLibraryMessage("请检查转换预览，确认后才会保存原件并建立索引。", "info");
  } catch (error) { showLibraryMessage(`无法预览：${error.message}`, "error"); }
  finally { libraryPreviewButton.disabled = false; }
}

async function confirmLibraryImport() {
  if (!libraryPreviewId) return;
  libraryConfirmButton.disabled = true;
  try {
    await libraryWrite(`/api/library/imports/${encodeURIComponent(libraryPreviewId)}/confirm`, { confirm: true });
    libraryImportForm.reset();
    libraryLanguage.value = "zh";
    libraryPreviewId = null;
    libraryImportPreview.hidden = true;
    libraryConfirmButton.hidden = true;
    showLibraryMessage("资料已导入；原件、转换稿和索引均保存在本地。", "success");
    await loadLibrary();
  } catch (error) { showLibraryMessage(`导入失败：${error.message}`, "error"); }
  finally { libraryConfirmButton.disabled = false; }
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
  const headingLabel = discussionSelection.headingPath?.length
    ? `所属小节“${discussionSelection.headingPath.at(-1)}”、`
    : "";
  discussionContextSummary.textContent = `将加入${headingLabel}选区所在段落及前后语境、完整章节、${scriptureCount} 处经文和 ${footnoteCount} 条脚注。`;
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
    discussionPreviewState.reply = null;
    discussionReplyContextPreview.hidden = true;
    sendReply.textContent = "预览上下文";
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

function previewFingerprint(selection, message) {
  return JSON.stringify([selection.anchor, message.trim()]);
}

function invalidateContextPreview(state) {
  state.contextBuildId = null;
  state.expiresAt = null;
  state.estimates = null;
  state.budgetStatus = null;
  (state.kind === "start" ? sendFirstMessage : sendReply).textContent = "重新预览";
}

function markContextPreviewReady(state) {
  (state.kind === "start" ? sendFirstMessage : sendReply).textContent =
    state.budgetStatus === "over_budget" ? "调整后重新预览" : "确认发送";
}

function renderContextPreview(container, preview, state) {
  const title = document.createElement("strong");
  title.textContent = "本轮上下文预览";
  const summary = document.createElement("p");
  summary.textContent = `将发送完整章节、${preview.scriptureCount} 处经文、${preview.footnoteCount} 条脚注。`;
  const fragment = document.createDocumentFragment();
  fragment.append(title, summary);
  if (state.estimates) {
    const budget = document.createElement("p");
    budget.className = state.estimates.status === "over_budget"
      ? "discussion-context-preview__warning"
      : "discussion-context-preview__muted";
    budget.textContent = state.estimates.status === "over_budget"
      ? `保守估算超出输入预算约 ${state.estimates.overByTokens.toLocaleString()} tokens；请先排除可选证据并重新预览。`
      : `保守估算：约 ${state.estimates.estimatedInputTokens.toLocaleString()} 输入 tokens（上限 ${state.estimates.inputTokenLimit.toLocaleString()}）。`;
    fragment.append(budget);
  }

  if (preview.notes.length) {
    const heading = document.createElement("p");
    heading.className = "discussion-context-preview__heading";
    heading.textContent = "你的相关笔记（可排除）";
    fragment.append(heading);
    preview.notes.forEach((note) => {
      const label = document.createElement("label");
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.checked = !state.excludedNoteIds.has(note.noteId);
      checkbox.addEventListener("change", () => {
        if (checkbox.checked) state.excludedNoteIds.delete(note.noteId);
        else state.excludedNoteIds.add(note.noteId);
        invalidateContextPreview(state);
      });
      const text = document.createElement("span");
      text.textContent = `${note.relation === "exact" ? "同一选区" : "重叠选区"}：${note.body}`;
      label.append(checkbox, text);
      fragment.append(label);
    });
  }
  if (preview.noteCandidates.length) {
    const candidate = document.createElement("p");
    candidate.className = "discussion-context-preview__muted";
    candidate.textContent = `另有 ${preview.noteCandidates.length} 条同段但不重叠的笔记，本轮不发送。`;
    fragment.append(candidate);
  }
  const translations = [...preview.translationEntities, ...preview.translationCandidates];
  if (translations.length) {
    const heading = document.createElement("p");
    heading.className = "discussion-context-preview__heading";
    heading.textContent = "译名命中（仅用于身份解析）";
    fragment.append(heading);
    translations.forEach((entity) => {
      const label = document.createElement("label");
      if (entity.matchType === "candidate") label.className = "discussion-context-preview__muted";
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.checked = entity.matchType === "candidate"
        ? state.includedTranslationSourceLines.has(entity.sourceLine)
        : !state.excludedTranslationSourceLines.has(entity.sourceLine);
      checkbox.addEventListener("change", () => {
        if (entity.matchType === "candidate") {
          if (checkbox.checked) state.includedTranslationSourceLines.add(entity.sourceLine);
          else state.includedTranslationSourceLines.delete(entity.sourceLine);
        } else if (checkbox.checked) {
          state.excludedTranslationSourceLines.delete(entity.sourceLine);
        } else {
          state.excludedTranslationSourceLines.add(entity.sourceLine);
        }
        invalidateContextPreview(state);
      });
      const text = document.createElement("span");
      text.textContent = `${entity.chinese} ↔ ${entity.english}${entity.matchType === "candidate" ? "（候选，需确认）" : ""}`;
      label.append(checkbox, text);
      fragment.append(label);
    });
  }
  if (preview.bookPassages.length) {
    const heading = document.createElement("p");
    heading.className = "discussion-context-preview__heading";
    heading.textContent = "本书其他章节（可排除）";
    fragment.append(heading);
    preview.bookPassages.forEach((passage) => {
      const item = document.createElement("div");
      item.className = "discussion-context-preview__passage";
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.setAttribute("aria-label", `纳入${passage.chapterTitle}的相关段落`);
      checkbox.checked = !state.excludedBookPassageIds.has(passage.passageId);
      checkbox.addEventListener("change", () => {
        if (checkbox.checked) state.excludedBookPassageIds.delete(passage.passageId);
        else state.excludedBookPassageIds.add(passage.passageId);
        invalidateContextPreview(state);
      });
      const details = document.createElement("details");
      const summary = document.createElement("summary");
      summary.textContent = `${passage.chapterTitle} · ${passage.headingPath.at(-1) || passage.blockId}`;
      const excerpt = document.createElement("blockquote");
      excerpt.textContent = passage.excerpt;
      const locator = document.createElement("a");
      locator.href = passage.href;
      locator.textContent = `打开 ${passage.chapterId} 章 · ${passage.blockId}`;
      details.append(summary, excerpt);
      passage.relatedFootnotes
        .filter((footnote) => passage.matchedFootnoteIds.includes(footnote.id))
        .forEach((footnote) => {
          const footnoteExcerpt = document.createElement("blockquote");
          footnoteExcerpt.textContent = `脚注 ${footnote.id}：${footnote.text}`;
          details.append(footnoteExcerpt);
        });
      details.append(locator);
      item.append(checkbox, details);
      fragment.append(item);
    });
  } else {
    const empty = document.createElement("p");
    empty.className = "discussion-context-preview__muted";
    empty.textContent = "本书其他章节未找到足够强的相关段落。";
    fragment.append(empty);
  }
  if (preview.hasMoreBookPassages && state.bookPassageLimit === 5) {
    const more = document.createElement("button");
    more.type = "button";
    more.className = "secondary-button discussion-context-preview__more";
    more.textContent = "查找更多本书内容";
    more.addEventListener("click", async () => {
      more.disabled = true;
      try {
        state.bookPassageLimit = 10;
        await state.refresh();
      } catch (error) {
        state.bookPassageLimit = 5;
        showDiscussionMessage(`无法扩展本书检索：${error.message}`, "error");
      } finally {
        more.disabled = false;
      }
    });
    fragment.append(more);
  }
  if (preview.localSourceCandidates.length) {
    const heading = document.createElement("p");
    heading.className = "discussion-context-preview__heading";
    heading.textContent = "本地资料库命中（默认不发送）";
    fragment.append(heading);
    preview.localSourceCandidates.forEach((chunk) => {
      const item = document.createElement("div");
      item.className = "discussion-context-preview__passage";
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.checked = state.includedLocalChunkIds.has(chunk.chunkId);
      checkbox.setAttribute("aria-label", `纳入${chunk.sourceTitle}的资料片段`);
      if (!chunk.externalSharingApproved) {
        checkbox.title = "勾选后会先请求此资料的外发授权";
      }
      checkbox.addEventListener("change", async () => {
        if (!checkbox.checked) {
          state.includedLocalChunkIds.delete(chunk.chunkId);
          invalidateContextPreview(state);
          return;
        }
        if (chunk.externalSharingApproved) {
          state.includedLocalChunkIds.add(chunk.chunkId);
          invalidateContextPreview(state);
          return;
        }

        checkbox.checked = false;
        const approved = window.confirm(
          `“${chunk.sourceTitle}”尚未授权将节选发送给 OpenAI。` +
          "授权后，仍只有你在每轮上下文预览中明确勾选的片段才会发送。是否授权此资料并选择当前片段？",
        );
        if (!approved) return;

        checkbox.disabled = true;
        try {
          await libraryWrite(`/api/library/sources/${encodeURIComponent(chunk.sourceId)}`, {
            approveExternalSharing: true,
          });
        } catch (error) {
          checkbox.disabled = false;
          showDiscussionMessage(`无法授权资料：${error.message}`, "error");
          return;
        }

        chunk.externalSharingApproved = true;
        checkbox.title = "";
        checkbox.checked = true;
        checkbox.disabled = false;
        state.includedLocalChunkIds.add(chunk.chunkId);
        try {
          await state.refresh();
          showDiscussionMessage(`已授权“${chunk.sourceTitle}”并选择当前资料片段。`, "success");
        } catch (error) {
          invalidateContextPreview(state);
          showDiscussionMessage(`资料已授权，但无法刷新上下文：${error.message}`, "error");
        }
      });
      const details = document.createElement("details");
      const summary = document.createElement("summary");
      summary.textContent = `${chunk.sourceTitle} · ${chunk.locator}${chunk.externalSharingApproved ? "" : "（勾选时授权）"}`;
      const excerpt = document.createElement("blockquote");
      excerpt.textContent = chunk.text;
      details.append(summary, excerpt);
      if (!chunk.externalSharingApproved) {
        const warning = document.createElement("p");
        warning.className = "discussion-context-preview__warning";
        warning.textContent = "尚未授权外发。勾选后可授权此资料，并将当前片段加入本轮上下文。";
        details.append(warning);
      }
      item.append(checkbox, details);
      fragment.append(item);
    });
  }
  container.replaceChildren(fragment);
  container.hidden = false;
}

async function refreshDiscussionContextPreview(kind, selection, message, state) {
  invalidateContextPreview(state);
  const payload = {
    sourceRevision: article.dataset.sourceRevision,
    anchor: selection.anchor,
    scriptures: selection.scriptures,
    footnotes: selection.footnotes,
    message,
    excludedNoteIds: [...state.excludedNoteIds],
    includedTranslationSourceLines: [...state.includedTranslationSourceLines],
    excludedTranslationSourceLines: [...state.excludedTranslationSourceLines],
    excludedBookPassageIds: [...state.excludedBookPassageIds],
    bookPassageLimit: state.bookPassageLimit,
    includedLocalChunkIds: [...state.includedLocalChunkIds],
  };
  if (kind === "reply") {
    payload.discussionId = activeDiscussion.id;
    payload.discussionEtag = activeDiscussionEtag;
  }
  const response = await fetch(`${discussionsApiUrl}/context-preview`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-QFG-Write-Token": writeToken },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(await responseError(response));
  const result = await response.json();
  state.contextBuildId = result.contextBuildId;
  state.expiresAt = result.expiresAt;
  state.estimates = result.estimates;
  state.budgetStatus = result.estimates.status;
  renderContextPreview(kind === "start" ? discussionContextPreview : discussionReplyContextPreview, result.preview, state);
  markContextPreviewReady(state);
  return state;
}

async function previewDiscussionContext(kind, selection, message) {
  const fingerprint = previewFingerprint(selection, message);
  let state = discussionPreviewState[kind];
  if (state?.fingerprint !== fingerprint) {
    state = {
      kind,
      fingerprint,
      excludedNoteIds: new Set(),
      includedTranslationSourceLines: new Set(),
      excludedTranslationSourceLines: new Set(),
      excludedBookPassageIds: new Set(),
      includedLocalChunkIds: new Set(),
      bookPassageLimit: 5,
      contextBuildId: null,
      budgetStatus: null,
    };
    state.refresh = () => refreshDiscussionContextPreview(kind, selection, message, state);
    discussionPreviewState[kind] = state;
  }
  return state.refresh();
}

function beginSelectedDiscussion(anchor, context) {
  pendingSelectionAnchor = null;
  pendingSelectionContext = null;
  selectionAction.hidden = true;
  window.getSelection()?.removeAllRanges();
  discussionSelection = { anchor, ...context };
  activeDiscussion = null;
  activeDiscussionEtag = null;
  discussionPreviewState.start = null;
  discussionContextPreview.hidden = true;
  sendFirstMessage.textContent = "预览上下文";
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
  const message = discussionFirstMessage.value;
  const fingerprint = previewFingerprint(discussionSelection, message);
  if (discussionPreviewState.start?.fingerprint !== fingerprint || !discussionPreviewState.start?.contextBuildId) {
    sendFirstMessage.disabled = true;
    try {
      await previewDiscussionContext("start", discussionSelection, message);
    } catch (error) {
      showDiscussionMessage(`无法预览上下文：${error.message}`, "error");
    } finally {
      sendFirstMessage.disabled = false;
    }
    return;
  }
  if (discussionPreviewState.start.budgetStatus === "over_budget") {
    showDiscussionMessage("本轮上下文超过预算，请排除可选证据后重新预览。", "error");
    return;
  }
  const payload = {
    sourceRevision: article.dataset.sourceRevision,
    anchor: discussionSelection.anchor,
    scriptures: discussionSelection.scriptures,
    footnotes: discussionSelection.footnotes,
    message,
    excludedNoteIds: [...discussionPreviewState.start.excludedNoteIds],
    includedTranslationSourceLines: [...discussionPreviewState.start.includedTranslationSourceLines],
    excludedTranslationSourceLines: [...discussionPreviewState.start.excludedTranslationSourceLines],
    excludedBookPassageIds: [...discussionPreviewState.start.excludedBookPassageIds],
    bookPassageLimit: discussionPreviewState.start.bookPassageLimit,
    includedLocalChunkIds: [...discussionPreviewState.start.includedLocalChunkIds],
    contextBuildId: discussionPreviewState.start.contextBuildId,
  };
  sendFirstMessage.disabled = true;
  try {
    await postDiscussion(discussionsApiUrl, payload);
    discussionFirstMessage.value = "";
    discussionPreviewState.start = null;
    discussionContextPreview.hidden = true;
    sendFirstMessage.textContent = "预览上下文";
  } catch (error) {
    if (discussionPreviewState.start && (error.status === 409 || error.status === 422)) {
      invalidateContextPreview(discussionPreviewState.start);
      showDiscussionMessage(`无法发起讨论：${error.message} 已保留你的上下文选择，请重新预览。`, "error");
    } else {
      showDiscussionMessage(`无法发起讨论：${error.message}`, "error");
    }
  } finally {
    sendFirstMessage.disabled = false;
  }
}

async function continueDiscussion(event) {
  event.preventDefault();
  const message = discussionReply.value;
  if (!activeDiscussion || !message.trim()) return;
  const selection = {
    anchor: activeDiscussion.anchor,
    scriptures: activeDiscussion.context.scriptures,
    footnotes: activeDiscussion.context.footnotes,
  };
  const fingerprint = previewFingerprint(selection, message);
  if (discussionPreviewState.reply?.fingerprint !== fingerprint || !discussionPreviewState.reply?.contextBuildId) {
    sendReply.disabled = true;
    try {
      await previewDiscussionContext("reply", selection, message);
    } catch (error) {
      showDiscussionMessage(`无法预览上下文：${error.message}`, "error");
    } finally {
      sendReply.disabled = false;
    }
    return;
  }
  if (discussionPreviewState.reply.budgetStatus === "over_budget") {
    showDiscussionMessage("本轮上下文超过预算，请排除可选证据或新建讨论。", "error");
    return;
  }
  try {
    discussionReply.value = "";
    await postDiscussion(
      `/api/discussions/${encodeURIComponent(activeDiscussion.id)}/messages`,
      {
        message,
        excludedNoteIds: [...discussionPreviewState.reply.excludedNoteIds],
        includedTranslationSourceLines: [...discussionPreviewState.reply.includedTranslationSourceLines],
        excludedTranslationSourceLines: [...discussionPreviewState.reply.excludedTranslationSourceLines],
        excludedBookPassageIds: [...discussionPreviewState.reply.excludedBookPassageIds],
        bookPassageLimit: discussionPreviewState.reply.bookPassageLimit,
        includedLocalChunkIds: [...discussionPreviewState.reply.includedLocalChunkIds],
        contextBuildId: discussionPreviewState.reply.contextBuildId,
      },
      activeDiscussionEtag,
    );
    discussionPreviewState.reply = null;
    discussionReplyContextPreview.hidden = true;
    sendReply.textContent = "预览上下文";
  } catch (error) {
    discussionReply.value = message;
    if (discussionPreviewState.reply && (error.status === 409 || error.status === 422)) {
      invalidateContextPreview(discussionPreviewState.reply);
      showDiscussionMessage(`无法继续讨论：${error.message} 已保留你的上下文选择，请重新预览。`, "error");
    } else {
      showDiscussionMessage(`无法继续讨论：${error.message}`, "error");
    }
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
hideReferences.addEventListener("click", () => applyPanelState("left", false));

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
libraryTab.addEventListener("click", () => switchStudyTab("library"));
libraryImportForm.addEventListener("submit", previewLibraryImport);
libraryConfirmButton.addEventListener("click", confirmLibraryImport);
libraryFile.addEventListener("change", () => {
  if (!libraryTitle.value.trim() && libraryFile.files[0]) {
    libraryTitle.value = libraryFile.files[0].name.replace(/\.[^.]+$/, "");
  }
  libraryPreviewId = null;
  libraryImportPreview.hidden = true;
  libraryConfirmButton.hidden = true;
});
libraryRebuild.addEventListener("click", async () => {
  libraryRebuild.disabled = true;
  try {
    const result = await libraryWrite("/api/library/index/rebuild", { confirm: true });
    showLibraryMessage(`索引已由转换稿重建：${result.sourceCount} 份资料，${result.chunkCount} 个片段。`, "success");
    await loadLibrary();
  } catch (error) { showLibraryMessage(`重建失败：${error.message}`, "error"); }
  finally { libraryRebuild.disabled = false; }
});
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
discussionFirstMessage.addEventListener("input", () => {
  discussionPreviewState.start = null;
  discussionContextPreview.hidden = true;
  sendFirstMessage.textContent = "预览上下文";
});
discussionReply.addEventListener("input", () => {
  discussionPreviewState.reply = null;
  discussionReplyContextPreview.hidden = true;
  sendReply.textContent = "预览上下文";
});
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
