/**
 * PromptForge Prompt Diff Engine
 * Computes line-by-line diff between Seed Prompt (v1.0) and Mutated System Prompt (v1.N).
 */

window.PromptForgeDiff = {
  computeLineDiff: function(oldText, newText) {
    const oldLines = (oldText || "").split("\n");
    const newLines = (newText || "").split("\n");

    const diffLines = [];
    const maxLines = Math.max(oldLines.length, newLines.length);

    const oldSet = new Set(oldLines.map(l => l.trim()));
    const newSet = new Set(newLines.map(l => l.trim()));

    // Analyze lines for additions, deletions, and modifications
    newLines.forEach((line, idx) => {
      const trimmed = line.trim();
      if (!trimmed) {
        diffLines.push({ type: "unchanged", text: "" });
        return;
      }

      if (!oldSet.has(trimmed)) {
        diffLines.push({ type: "added", text: line });
      } else {
        diffLines.push({ type: "unchanged", text: line });
      }
    });

    oldLines.forEach(line => {
      const trimmed = line.trim();
      if (trimmed && !newSet.has(trimmed)) {
        diffLines.unshift({ type: "removed", text: line });
      }
    });

    return diffLines;
  },

  renderDiffViewer: function(containerId, oldText, newText) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const diff = this.computeLineDiff(oldText, newText);

    let html = `<div style="font-family:'JetBrains Mono', monospace; font-size:0.84rem; line-height:1.6; background:var(--bg-input); padding:1rem; border-radius:8px; border:1px solid var(--border-hairline); max-height:420px; overflow-y:auto; white-space:pre-wrap;">`;

    diff.forEach((lineObj, idx) => {
      if (lineObj.type === "added") {
        html += `<div style="background:rgba(52, 211, 153, 0.15); color:var(--accent-emerald); padding:2px 8px; border-left:3px solid var(--accent-emerald); font-weight:600;">+ ${this.escapeHtml(lineObj.text)}</div>`;
      } else if (lineObj.type === "removed") {
        html += `<div style="background:rgba(239, 68, 68, 0.15); color:#ef4444; padding:2px 8px; border-left:3px solid #ef4444; text-decoration:line-through;">- ${this.escapeHtml(lineObj.text)}</div>`;
      } else {
        html += `<div style="color:var(--text-secondary); padding:2px 8px;">  ${this.escapeHtml(lineObj.text)}</div>`;
      }
    });

    html += `</div>`;
    container.innerHTML = html;
  },

  escapeHtml: function(str) {
    return (str || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }
};
