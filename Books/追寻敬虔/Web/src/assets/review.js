const endpoint = "/api/edition-reviews/chatgpt-zh-cn/05";
const list = document.querySelector("#review-list");
const template = document.querySelector("#review-row-template");
const counts = document.querySelector("#review-counts");
const chapterState = document.querySelector("#chapter-state");
const saveStatus = document.querySelector("#save-status");
const approveChapter = document.querySelector("#approve-chapter");
const toggleEnglish = document.querySelector("#toggle-english");
const englishReference = document.querySelector("#english-reference");

let writeToken = "";
let revision = "";
let review = null;

const labels = { draft: "草稿", reviewed: "已复核", approved: "已批准" };
const kindLabels = { h1: "章标题", h2: "小标题", paragraph: "正文", blockquote: "引文" };

function render() {
  list.replaceChildren();
  counts.textContent = `草稿 ${review.counts.draft} · 已复核 ${review.counts.reviewed} · 已批准 ${review.counts.approved} · 待处理意见 ${review.counts.openComments} · 共 ${review.pairs.length} 段`;
  chapterState.textContent = `整章状态：${labels[review.chapterStatus]}`;
  approveChapter.disabled = !review.canApproveChapter || review.chapterStatus === "approved";
  approveChapter.textContent = review.chapterStatus === "approved" ? "整章已批准" : "批准整章";

  for (const pair of review.pairs) {
    const row = template.content.firstElementChild.cloneNode(true);
    row.dataset.pairId = pair.pairId;
    row.dataset.status = pair.status;
    row.querySelector(".review-row__number").textContent = `第 ${pair.ordinal} 段`;
    row.querySelector(".review-row__kind").textContent = kindLabels[pair.kind] || pair.kind;
    row.querySelector(".review-copy--source p").textContent = pair.sourceText;
    row.querySelector(".review-copy--target p").textContent = pair.targetText;
    const openComments = pair.comments.filter((comment) => comment.status === "open");
    row.dataset.hasOpenComments = String(openComments.length > 0);
    row.querySelector(".review-comments__summary").textContent = openComments.length
      ? `${openComments.length} 条待处理`
      : pair.comments.length ? "全部已处理" : "尚无意见";
    const commentList = row.querySelector(".review-comments__list");
    for (const comment of pair.comments) {
      const item = document.createElement("article");
      item.className = "review-comment";
      item.dataset.status = comment.status;
      const text = document.createElement("p");
      text.textContent = comment.text;
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = comment.status === "open" ? "标记已处理" : "重新打开";
      button.addEventListener("click", () => mutate({
        action: "set-comment-status",
        pairId: pair.pairId,
        commentId: comment.commentId,
        status: comment.status === "open" ? "resolved" : "open",
      }));
      item.append(text, button);
      commentList.append(item);
    }
    const form = row.querySelector(".review-comments__form");
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const textarea = form.elements.comment;
      const text = textarea.value.trim();
      if (!text || document.body.dataset.saving === "true") return;
      mutate({ action: "add-comment", pairId: pair.pairId, text });
    });
    for (const button of row.querySelectorAll("[data-status]")) {
      button.setAttribute("aria-pressed", String(button.dataset.status === pair.status));
      if (button.dataset.status === "approved" && openComments.length) {
        button.disabled = true;
        button.title = "请先处理这一段的全部修改意见";
      }
      button.addEventListener("click", () => updateBlock(pair.pairId, button.dataset.status));
    }
    list.append(row);
  }
}

async function request(path, options = {}) {
  const response = await fetch(path, options);
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.error?.message || `请求失败（${response.status}）`);
  }
  revision = response.headers.get("ETag") || revision;
  return response.json();
}

async function load() {
  try {
    const session = await request("/api/session");
    writeToken = session.writeToken;
    review = await request(endpoint);
    render();
    saveStatus.textContent = "已载入";
  } catch (error) {
    saveStatus.textContent = error.message;
  }
}

async function mutate(payload) {
  saveStatus.textContent = "保存中…";
  document.body.dataset.saving = "true";
  try {
    review = await request(endpoint, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        "X-QFG-Write-Token": writeToken,
        "If-Match": revision,
      },
      body: JSON.stringify(payload),
    });
    render();
    saveStatus.textContent = "已保存";
  } catch (error) {
    saveStatus.textContent = error.message;
    if (error.message.includes("changed") || error.message.includes("变更")) await load();
  } finally {
    delete document.body.dataset.saving;
  }
}

function updateBlock(pairId, status) {
  if (document.body.dataset.saving === "true") return;
  mutate({ action: "set-block-status", pairId, status });
}

approveChapter.addEventListener("click", () => {
  if (confirm("确认批准整章？批准后，仍需完成正式阅读器的版本发布迁移才会对普通读者开放。")) {
    mutate({ action: "approve-chapter" });
  }
});

toggleEnglish.addEventListener("click", () => {
  const open = !document.body.classList.contains("english-hidden");
  document.body.classList.toggle("english-hidden", open);
  englishReference.hidden = open;
  toggleEnglish.setAttribute("aria-expanded", String(!open));
  toggleEnglish.textContent = open ? "显示英文原稿" : "隐藏英文原稿";
});

load();
