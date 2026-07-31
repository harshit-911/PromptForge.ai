/**
 * PromptForge Experiment Tracker & History Engine
 * Manages experiment persistence, history table, and experiment drawer details.
 */

window.PromptForgeExperiments = {
  fetchExperimentsList: async function() {
    try {
      const res = await fetch("/api/experiments");
      const data = await res.json();
      return data.experiments || [];
    } catch (e) {
      console.error("Failed to fetch experiments:", e);
      return [];
    }
  },

  renderExperimentsTable: async function(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const experiments = await this.fetchExperimentsList();

    if (experiments.length === 0) {
      container.innerHTML = `
        <div style="background:var(--bg-input); padding:2rem; text-align:center; border-radius:8px; border:1px dashed var(--border-hairline);">
          <p style="color:var(--text-muted); font-size:0.9rem;">No saved experiment runs yet. Run a prompt optimization to automatically track experiments.</p>
        </div>
      `;
      return;
    }

    let html = `
      <div class="table-container">
        <table class="trajectory-table">
          <thead>
            <tr>
              <th style="width:170px;">Experiment ID</th>
              <th style="width:140px;">Benchmark</th>
              <th style="width:90px;">Model</th>
              <th style="width:80px;">Versions</th>
              <th style="width:110px;">Baseline Acc</th>
              <th style="width:110px;">Final Acc</th>
              <th style="width:100px;">Gain Delta</th>
              <th style="width:130px;">Actions</th>
            </tr>
          </thead>
          <tbody>
    `;

    experiments.forEach(exp => {
      const timeStr = new Date(exp.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      const isUp = exp.delta_accuracy >= 0;

      html += `
        <tr style="cursor:pointer;" onclick="PromptForgeExperiments.openExperimentDetail('${exp.experiment_id}')">
          <td>
            <span style="font-family:'JetBrains Mono', monospace; font-size:0.82rem; font-weight:700; color:var(--accent-cyan);">${exp.experiment_id}</span>
            <div style="font-size:0.75rem; color:var(--text-muted);">${timeStr}</div>
          </td>
          <td><strong style="color:var(--text-primary); font-size:0.86rem;">${exp.benchmark_name}</strong></td>
          <td><span class="model-chip">${exp.model || 'Gemini'}</span></td>
          <td><span style="font-size:0.82rem; font-weight:600;">v1.0 - v1.${Math.max(0, exp.iterations - 1)}</span></td>
          <td><span style="color:var(--text-secondary);">${exp.baseline_accuracy.toFixed(1)}%</span></td>
          <td><span style="color:var(--accent-emerald); font-weight:700;">${exp.final_accuracy.toFixed(1)}%</span></td>
          <td><span style="color:${isUp ? 'var(--accent-emerald)' : '#ef4444'}; font-weight:700;">+${exp.delta_accuracy.toFixed(1)}%</span></td>
          <td>
            <div style="display:flex; gap:6px;">
              <button class="copy-btn" style="padding:2px 8px;" onclick="event.stopPropagation(); PromptForgeExperiments.openExperimentDetail('${exp.experiment_id}')">View</button>
              <button class="copy-btn" style="padding:2px 8px; color:#ef4444;" onclick="event.stopPropagation(); PromptForgeExperiments.deleteExperiment('${exp.experiment_id}')">✕</button>
            </div>
          </td>
        </tr>
      `;
    });

    html += `</tbody></table></div>`;
    container.innerHTML = html;
  },

  openExperimentDetail: async function(expId) {
    try {
      const res = await fetch(`/api/experiments/${expId}`);
      const exp = await res.json();
      if (!exp) return;

      const titleEl = document.getElementById("exp-drawer-id");
      if (titleEl) titleEl.textContent = exp.experiment_id;

      if (window.PromptForgeComparison) {
        window.PromptForgeComparison.renderComparison("exp-comparison-container", exp.baseline_metrics, exp.final_metrics);
      }

      if (window.PromptForgeCharts) {
        window.PromptForgeCharts.renderPerformanceCharts(exp.history);
      }

      if (window.PromptForgeDiff) {
        window.PromptForgeDiff.renderDiffViewer("exp-diff-container", exp.seed_prompt, exp.optimized_prompt);
      }

      const modal = document.getElementById("experiment-detail-modal");
      if (modal) modal.classList.add("active");
    } catch (e) {
      alert("Failed to load experiment detail: " + e.message);
    }
  },

  closeExperimentDetail: function() {
    const modal = document.getElementById("experiment-detail-modal");
    if (modal) modal.classList.remove("active");
  },

  deleteExperiment: async function(expId) {
    if (!confirm(`Delete experiment record '${expId}'?`)) return;
    try {
      await fetch(`/api/experiments/${expId}`, { method: "DELETE" });
      this.renderExperimentsTable("experiments-history-container");
    } catch (e) {
      alert("Delete failed: " + e.message);
    }
  }
};
