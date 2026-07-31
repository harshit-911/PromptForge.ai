/**
 * PromptForge Multi-Format Report Exporter
 * Triggers PDF (printable HTML), Markdown, JSON, and CSV exports.
 */

window.PromptForgeExport = {
  exportExperiment: function(expId, format) {
    if (!expId) {
      if (window.lastOptimizationData && window.lastOptimizationData.experiment_id) {
        expId = window.lastOptimizationData.experiment_id;
      } else {
        alert("Please select or run an experiment first before exporting.");
        return;
      }
    }
    const url = `/api/experiments/${expId}/export?format=${format}`;
    window.open(url, "_blank");
  },

  exportCurrentReportMarkdown: function() {
    if (!window.lastOptimizationData) {
      alert("Please run an optimization first!");
      return;
    }
    const expId = window.lastOptimizationData.experiment_id;
    if (expId) {
      this.exportExperiment(expId, "markdown");
    } else {
      window.exportReport();
    }
  },

  exportCurrentReportPDF: function() {
    if (!window.lastOptimizationData) {
      alert("Please run an optimization first!");
      return;
    }
    const expId = window.lastOptimizationData.experiment_id;
    if (expId) {
      this.exportExperiment(expId, "pdf");
    }
  }
};
