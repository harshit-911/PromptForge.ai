/**
 * PromptForge Baseline vs Optimized Comparison Engine
 * Renders BEFORE vs AFTER metric cards (Accuracy, Precision, Recall, F1, Latency, Tokens).
 */

window.PromptForgeComparison = {
  renderComparison: function(containerId, baseline, final) {
    const container = document.getElementById(containerId);
    if (!container) return;

    if (!baseline || !final) {
      container.innerHTML = `<p style="color:var(--text-muted); font-size:0.9rem;">Run an optimization to view Baseline vs. Optimized comparison.</p>`;
      return;
    }

    const metrics = [
      { label: "Accuracy", base: baseline.accuracy || 0, opt: final.accuracy || 0, unit: "%" },
      { label: "Precision", base: baseline.precision || baseline.accuracy || 0, opt: final.precision || final.accuracy || 0, unit: "%" },
      { label: "Recall", base: baseline.recall || baseline.accuracy || 0, opt: final.recall || final.accuracy || 0, unit: "%" },
      { label: "F1 Score", base: baseline.f1 || baseline.accuracy || 0, opt: final.f1 || final.accuracy || 0, unit: "%" },
      { label: "Passed Tests", base: baseline.passed || 0, opt: final.passed || 0, unit: "" }
    ];

    let html = `
      <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:1.25rem; margin-bottom:1.5rem;">
    `;

    metrics.forEach(m => {
      const delta = (m.opt - m.base).toFixed(1);
      const isUp = parseFloat(delta) >= 0;
      html += `
        <div style="background:var(--bg-card); border:1px solid var(--border-hairline); border-radius:12px; padding:1.25rem;">
          <div style="font-family:var(--font-display); font-size:0.75rem; font-weight:700; color:var(--text-muted); text-transform:uppercase;">${m.label}</div>
          <div style="display:flex; align-items:baseline; gap:8px; margin-top:8px;">
            <span style="font-family:var(--font-display); font-size:1.4rem; color:var(--text-muted); text-decoration:line-through;">${m.base}${m.unit}</span>
            <span style="font-size:1rem; color:var(--text-muted);">➔</span>
            <span style="font-family:var(--font-display); font-size:1.8rem; font-weight:700; color:var(--accent-emerald);">${m.opt}${m.unit}</span>
          </div>
          <div style="margin-top:6px; font-size:0.78rem; font-weight:700; color:${isUp ? 'var(--accent-emerald)' : '#ef4444'};">
            ${isUp ? '▲' : '▼'} ${isUp ? '+' : ''}${delta}${m.unit} Delta
          </div>
        </div>
      `;
    });

    html += `</div>`;
    container.innerHTML = html;
  }
};
