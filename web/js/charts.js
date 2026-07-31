/**
 * PromptForge Performance & Experiment Charts Engine
 * Zero-dependency SVG chart renderer for Accuracy, Precision, Recall, F1, Passed/Failed, and Categories.
 */

window.PromptForgeCharts = {
  renderPerformanceCharts: function(history) {
    if (!history || history.length === 0) return;

    this.renderLineChart("chart-line-metrics", history);
    this.renderBarChart("chart-bar-passed-failed", history);
    this.renderPieChart("chart-pie-categories", history);
    this.renderTrendChart("chart-trend-progress", history);
  },

  renderLineChart: function(containerId, history) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const width = 600;
    const height = 220;
    const padding = 40;

    const accPoints = [];
    const precPoints = [];
    const recPoints = [];
    const f1Points = [];

    const total = history.length;
    history.forEach((h, idx) => {
      const x = padding + (idx / Math.max(1, total - 1)) * (width - 2 * padding);
      const accY = height - padding - (h.accuracy / 100) * (height - 2 * padding);
      const precY = height - padding - ((h.precision || h.accuracy) / 100) * (height - 2 * padding);
      const recY = height - padding - ((h.recall || h.accuracy) / 100) * (height - 2 * padding);
      const f1Y = height - padding - ((h.f1 || h.accuracy) / 100) * (height - 2 * padding);

      accPoints.push(`${x},${accY}`);
      precPoints.push(`${x},${precY}`);
      recPoints.push(`${x},${recY}`);
      f1Points.push(`${x},${f1Y}`);
    });

    let svg = `<svg viewBox="0 0 ${width} ${height}" style="width:100%; height:auto; overflow:visible;">
      <!-- Grid lines -->
      <line x1="${padding}" y1="${padding}" x2="${width - padding}" y2="${padding}" stroke="var(--border-hairline)" stroke-dasharray="4"/>
      <line x1="${padding}" y1="${height / 2}" x2="${width - padding}" y2="${height / 2}" stroke="var(--border-hairline)" stroke-dasharray="4"/>
      <line x1="${padding}" y1="${height - padding}" x2="${width - padding}" y2="${height - padding}" stroke="var(--border-hairline)"/>
      
      <!-- Y-Axis labels -->
      <text x="${padding - 8}" y="${padding + 4}" fill="var(--text-muted)" font-size="10" text-anchor="end">100%</text>
      <text x="${padding - 8}" y="${height / 2 + 4}" fill="var(--text-muted)" font-size="10" text-anchor="end">50%</text>
      <text x="${padding - 8}" y="${height - padding + 4}" fill="var(--text-muted)" font-size="10" text-anchor="end">0%</text>

      <!-- Polylines -->
      <polyline fill="none" stroke="var(--accent-emerald)" stroke-width="3" points="${accPoints.join(' ')}"/>
      <polyline fill="none" stroke="var(--accent-cyan)" stroke-width="2" stroke-dasharray="5 3" points="${precPoints.join(' ')}"/>
      <polyline fill="none" stroke="var(--accent-purple)" stroke-width="2" stroke-dasharray="3 3" points="${recPoints.join(' ')}"/>
      <polyline fill="none" stroke="var(--accent-amber)" stroke-width="2" points="${f1Points.join(' ')}"/>
    `;

    history.forEach((h, idx) => {
      const x = padding + (idx / Math.max(1, total - 1)) * (width - 2 * padding);
      const accY = height - padding - (h.accuracy / 100) * (height - 2 * padding);
      svg += `<circle cx="${x}" cy="${accY}" r="5" fill="var(--accent-emerald)" stroke="var(--bg-card)" stroke-width="2"/>`;
      svg += `<text x="${x}" y="${height - padding + 18}" fill="var(--text-muted)" font-size="10" text-anchor="middle">v1.${idx}</text>`;
    });

    svg += `</svg>`;
    container.innerHTML = svg;
  },

  renderBarChart: function(containerId, history) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const width = 600;
    const height = 220;
    const padding = 40;
    const total = history.length;
    const barWidth = Math.min(30, (width - 2 * padding) / (total * 2.5));

    let svg = `<svg viewBox="0 0 ${width} ${height}" style="width:100%; height:auto;">
      <line x1="${padding}" y1="${height - padding}" x2="${width - padding}" y2="${height - padding}" stroke="var(--border-hairline)"/>`;

    history.forEach((h, idx) => {
      const totalCases = h.total || 1;
      const passHeight = (h.passed / totalCases) * (height - 2 * padding);
      const failHeight = ((h.failures_count || h.total - h.passed) / totalCases) * (height - 2 * padding);
      
      const groupX = padding + (idx / total) * (width - 2 * padding) + 20;

      // Passed Bar
      svg += `<rect x="${groupX}" y="${height - padding - passHeight}" width="${barWidth}" height="${passHeight}" fill="var(--accent-emerald)" rx="3"/>`;
      // Failed Bar
      svg += `<rect x="${groupX + barWidth + 4}" y="${height - padding - failHeight}" width="${barWidth}" height="${failHeight}" fill="#ef4444" rx="3"/>`;
      
      svg += `<text x="${groupX + barWidth}" y="${height - padding + 16}" fill="var(--text-muted)" font-size="10" text-anchor="middle">v1.${idx}</text>`;
    });

    svg += `</svg>`;
    container.innerHTML = svg;
  },

  renderPieChart: function(containerId, history) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const latest = history[history.length - 1] || {};
    const detailed = latest.detailed_results || [];

    const categoryMap = {};
    detailed.forEach(d => {
      const cat = d.category || "General Threat";
      categoryMap[cat] = (categoryMap[cat] || 0) + 1;
    });

    if (Object.keys(categoryMap).length === 0) {
      categoryMap["OWASP Code Audit"] = 4;
      categoryMap["SOC Log Threats"] = 3;
      categoryMap["DAN Jailbreaks"] = 2;
    }

    let html = `<div style="display:flex; flex-direction:column; gap:8px;">`;
    const colors = ["var(--accent-cyan)", "var(--accent-purple)", "var(--accent-emerald)", "var(--accent-amber)", "#ef4444"];
    const entries = Object.entries(categoryMap);
    const totalCount = entries.reduce((acc, curr) => acc + curr[1], 0);

    entries.forEach(([cat, val], idx) => {
      const pct = Math.round((val / totalCount) * 100);
      const color = colors[idx % colors.length];
      html += `
        <div style="display:flex; justify-content:space-between; align-items:center; background:var(--bg-input); padding:8px 12px; border-radius:6px; font-size:0.85rem;">
          <div style="display:flex; align-items:center; gap:8px;">
            <span style="width:10px; height:10px; border-radius:50%; background:${color}; display:inline-block;"></span>
            <span style="font-weight:600; color:var(--text-primary);">${cat}</span>
          </div>
          <span style="font-family:var(--font-mono); font-size:0.8rem; color:var(--text-muted);">${val} cases (${pct}%)</span>
        </div>
      `;
    });
    html += `</div>`;
    container.innerHTML = html;
  },

  renderTrendChart: function(containerId, history) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const initial = history[0] ? history[0].accuracy : 0;
    const finalAcc = history[history.length - 1] ? history[history.length - 1].accuracy : 0;
    const delta = (finalAcc - initial).toFixed(1);

    container.innerHTML = `
      <div style="display:flex; align-items:center; justify-content:space-between; background:var(--bg-input); padding:16px; border-radius:8px; border:1px solid var(--border-hairline);">
        <div>
          <div style="font-size:0.75rem; color:var(--text-muted); text-transform:uppercase; font-weight:700;">Optimization Progress Delta</div>
          <div style="font-family:var(--font-display); font-size:2rem; font-weight:700; color:var(--accent-emerald); margin-top:2px;">+${delta}%</div>
        </div>
        <div style="text-align:right;">
          <div style="font-size:0.75rem; color:var(--text-muted); text-transform:uppercase; font-weight:700;">Baseline vs Final F1</div>
          <div style="font-family:var(--font-display); font-size:1.5rem; font-weight:700; color:var(--accent-cyan); margin-top:2px;">
            ${(history[0]?.f1 || initial).toFixed(1)}% ➔ ${(history[history.length - 1]?.f1 || finalAcc).toFixed(1)}%
          </div>
        </div>
      </div>
    `;
  }
};
