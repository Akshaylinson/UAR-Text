function resolveApiBase() {
  const override = window.UAR_API_BASE || localStorage.getItem("UAR_API_BASE");
  if (override) return override.replace(/\/$/, "");

  const isStaticDevServer = ["5500", "3000", "4173", "8080"].includes(window.location.port);
  if (isStaticDevServer) {
    return "http://127.0.0.1:8000";
  }

  return `${window.location.protocol}//${window.location.host}`;
}

const API_BASE = resolveApiBase();
const WS_BASE = API_BASE.startsWith("https:")
  ? API_BASE.replace(/^https:/, "wss:")
  : API_BASE.startsWith("http:")
    ? API_BASE.replace(/^http:/, "ws:")
    : `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}`;

function byId(id) {
  return document.getElementById(id);
}

function showOfflineNotice() {
  const box = byId("pageError");
  if (box) {
    box.textContent = `Backend unavailable at ${API_BASE}. Start FastAPI on port 8000 or set UAR_API_BASE.`;
    box.className = "status-pill error";
  }
}

async function fetchJson(path, options) {
  try {
    const response = await fetch(`${API_BASE}${path}`, options);
    if (!response.ok) {
      throw new Error(`${path} ${response.status}`);
    }
    return response.json();
  } catch (error) {
    const message = String(error?.message || error);
    if (message.includes("Failed to fetch") || message.includes("ERR_CONNECTION_REFUSED") || message.includes("Load failed")) {
      showOfflineNotice();
      return {};
    }
    throw error;
  }
}

async function postJson(path, body) {
  return fetchJson(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  });
}

function safeText(value, fallback = "-") {
  if (value === undefined || value === null || value === "") return fallback;
  return String(value);
}

function chip(text, className = "") {
  return `<span class="pill ${className}">${text}</span>`;
}

function renderPills(items, emptyLabel = "None", className = "") {
  if (!items || !items.length) {
    return `<span class="muted">${emptyLabel}</span>`;
  }
  return items.map((item) => chip(item, className)).join("");
}

function renderCards(target, cards) {
  if (!target) return;
  target.innerHTML = cards.map((card) => `
    <article class="metric-card">
      <span>${card.label}</span>
      <strong>${card.value}</strong>
      ${card.note ? `<small>${card.note}</small>` : ""}
    </article>
  `).join("");
}

function renderBars(target, bars) {
  if (!target) return;
  target.innerHTML = bars.map((bar) => `
    <div class="chart-row">
      <div class="chart-label">
        <span>${bar.label}</span>
        <strong>${bar.value}</strong>
      </div>
      <div class="chart-track"><div class="chart-fill" style="width:${Math.min(100, Math.max(0, bar.percent))}%"></div></div>
    </div>
  `).join("");
}

function renderTree(node) {
  const children = node.children || [];
  const title = node.model_name ? `${node.label} <span class="muted">${node.model_name}</span>` : node.label;
  if (!children.length) {
    return `<div class="tree-leaf"><span>${title}</span></div>`;
  }
  return `
    <details class="tree-card" ${node.type === "root" || node.type === "block" ? "open" : ""}>
      <summary>${title}</summary>
      <div class="tree-children">
        ${children.map((child) => renderTree(child)).join("")}
      </div>
    </details>
  `;
}

function modelControlsHtml() {
  return `
    <div class="control-bar">
      <select id="modelSelect" class="input select"></select>
      <div class="action-group">
        <button id="loadModelBtn" class="button primary" type="button">Load</button>
        <button id="switchModelBtn" class="button secondary" type="button">Switch</button>
        <button id="reloadModelBtn" class="button secondary" type="button">Reload</button>
        <button id="unloadModelBtn" class="button secondary" type="button">Unload</button>
        <button id="downloadModelBtn" class="button secondary" type="button">Download</button>
      </div>
    </div>
  `;
}

function bindModelControls(onRefresh) {
  const select = byId("modelSelect");
  const handlers = [
    ["loadModelBtn", "/api/model/load"],
    ["switchModelBtn", "/api/model/switch"],
    ["downloadModelBtn", "/api/model/download"],
  ];

  handlers.forEach(([id, path]) => {
    const button = byId(id);
    if (!button || button.dataset.bound) return;
    button.dataset.bound = "1";
    button.addEventListener("click", async () => {
      if (!select || !select.value) return;
      button.disabled = true;
      try {
        await postJson(path, { model_name: select.value });
        await onRefresh();
      } catch (error) {
        console.error(error);
      } finally {
        button.disabled = false;
      }
    });
  });

  const reloadBtn = byId("reloadModelBtn");
  if (reloadBtn && !reloadBtn.dataset.bound) {
    reloadBtn.dataset.bound = "1";
    reloadBtn.addEventListener("click", async () => {
      reloadBtn.disabled = true;
      try {
        await postJson("/api/model/reload");
        await onRefresh();
      } catch (error) {
        console.error(error);
      } finally {
        reloadBtn.disabled = false;
      }
    });
  }

  const unloadBtn = byId("unloadModelBtn");
  if (unloadBtn && !unloadBtn.dataset.bound) {
    unloadBtn.dataset.bound = "1";
    unloadBtn.addEventListener("click", async () => {
      unloadBtn.disabled = true;
      try {
        await postJson("/api/model/unload");
        await onRefresh();
      } catch (error) {
        console.error(error);
      } finally {
        unloadBtn.disabled = false;
      }
    });
  }
}

async function loadModelExplorer() {
  const infoTarget = byId("modelInfo");
  const treeTarget = byId("architectureTree");
  const listTarget = byId("supportedModels");
  const statusTarget = byId("modelStatus");
  let select = null;

  const refresh = async () => {
    const [info, architecture, list] = await Promise.all([
      fetchJson("/api/model/info"),
      fetchJson("/api/model/architecture"),
      fetchJson("/api/model/list"),
    ]);

    const models = list.models || [];

    const controlsTarget = byId("modelControls");
    if (controlsTarget) {
      controlsTarget.innerHTML = modelControlsHtml();
    }

    select = byId("modelSelect");
    if (select) {
      const current = info.model_name || models[0]?.model_name || "";
      select.innerHTML = models.map((model) => {
        const selected = model.model_name === current ? "selected" : "";
        return `<option value="${model.model_name}" ${selected}>${model.model_family} - ${model.model_name}</option>`;
      }).join("");
    }

    renderCards(infoTarget, [
      { label: "Model Name", value: safeText(info.model_name) },
      { label: "Model Family", value: safeText(info.model_family) },
      { label: "Model Type", value: safeText(info.model_type) },
      { label: "Architecture", value: safeText(info.architecture) },
      { label: "Parameter Count", value: safeText(info.parameter_count?.toLocaleString?.() || info.parameter_count) },
      { label: "Model Size", value: `${safeText(info.size_gb)} GB` },
      { label: "Context Window", value: safeText(info.context_window) },
      { label: "Hidden Size", value: safeText(info.hidden_size) },
      { label: "Vocabulary Size", value: safeText(info.vocab_size) },
      { label: "Layers", value: safeText(info.layer_count) },
    ]);

    if (treeTarget) {
      treeTarget.innerHTML = renderTree(architecture);
    }

    if (listTarget) {
      listTarget.innerHTML = models.map((model) => `
        <article class="model-row">
          <strong>${model.model_family}</strong>
          <span>${model.model_name}</span>
          <small>${model.parameter_count?.toLocaleString?.() || model.parameter_count} params · ${model.size_gb} GB · ${model.context_window} ctx</small>
        </article>
      `).join("");
    }

    if (statusTarget) {
      statusTarget.textContent = info.loaded ? `Loaded: ${info.model_name}` : "No model loaded";
      statusTarget.className = info.loaded ? "status-pill good" : "status-pill muted";
    }

    bindModelControls(refresh);
  };

  await refresh();
}

async function loadLayersPage() {
  const summaryTarget = byId("layerSummary");
  const tableTarget = byId("layerTable");

  const refresh = async () => {
    const data = await fetchJson("/api/model/layers");
    const layers = data.layers || [];
    const loaded = layers.filter((layer) => layer.status === "Loaded").length;
    const executing = layers.filter((layer) => layer.status === "Executing").length;
    const cached = layers.filter((layer) => layer.status === "Cached").length;
    const unloaded = layers.filter((layer) => layer.status === "Unloaded").length;

    renderCards(summaryTarget, [
      { label: "Total", value: safeText(data.total) },
      { label: "Loaded", value: safeText(loaded) },
      { label: "Executing", value: safeText(executing) },
      { label: "Cached", value: safeText(cached) },
      { label: "Unloaded", value: safeText(unloaded) },
      { label: "Max Active", value: safeText(data.max_active) },
    ]);

    if (tableTarget) {
      tableTarget.innerHTML = `
        <table class="table">
          <thead>
            <tr>
              <th>Layer</th>
              <th>Type</th>
              <th>Parameters</th>
              <th>Status</th>
              <th>Device</th>
            </tr>
          </thead>
          <tbody>
            ${layers.map((layer) => `
              <tr>
                <td>${layer.id}</td>
                <td>${layer.type}</td>
                <td>${layer.parameters}</td>
                <td><span class="status-pill ${layer.status.toLowerCase()}">${layer.status}</span></td>
                <td>${layer.device}</td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      `;
    }
  };

  await refresh();
  setInterval(refresh, 2000);
}

function pipelineMarkup(activeStage) {
  const stages = [
    "prompt",
    "tokenizer",
    "scheduler",
    "layer_loader",
    "layer_executor",
    "token_generator",
    "output",
  ];
  return stages.map((stage, index) => `
    <div class="pipeline-step ${stage === activeStage ? "active" : ""}">
      <span>${stage.replace(/_/g, " ")}</span>
      ${index < stages.length - 1 ? '<div class="pipeline-arrow">↓</div>' : ''}
    </div>
  `).join("");
}

async function loadRuntimePage() {
  const summaryTarget = byId("runtimeSummary");
  const pipelineTarget = byId("pipelineViz");
  const logsTarget = byId("runtimeLogList");

  const refresh = async () => {
    const [stats, tokens, scheduler, logs] = await Promise.all([
      fetchJson("/api/runtime/stats"),
      fetchJson("/api/runtime/tokens"),
      fetchJson("/api/scheduler"),
      fetchJson("/api/runtime/logs"),
    ]);

    renderCards(summaryTarget, [
      { label: "Current Prompt", value: safeText(tokens.prompt || stats.current_prompt) },
      { label: "Current Token", value: safeText(stats.current_token || tokens.generated_tokens?.[0]) },
      { label: "Tokens Generated", value: safeText(stats.tokens_generated || tokens.generated_tokens?.length || 0) },
      { label: "Tokens/sec", value: safeText(stats.tokens_per_second) },
      { label: "Latency", value: `${safeText(stats.latency_ms)} ms` },
      { label: "Inference Time", value: `${safeText(stats.inference_time_ms)} ms` },
      { label: "Active Layers", value: safeText(stats.active_layers_count) },
      { label: "Cache Hits", value: safeText(stats.cache_hits) },
      { label: "Cache Misses", value: safeText(stats.cache_misses) },
      { label: "Memory Usage", value: `${safeText(stats.memory_usage_percent)}%` },
      { label: "CPU Usage", value: `${safeText(stats.cpu_usage_percent)}%` },
      { label: "Stage", value: safeText(stats.active_stage || scheduler.stage) },
    ]);

    if (pipelineTarget) {
      pipelineTarget.innerHTML = pipelineMarkup(stats.active_stage || scheduler.stage);
    }

    if (logsTarget) {
      logsTarget.innerHTML = (logs.logs || []).slice(-8).map((entry) => `
        <div class="log-item">
          <span class="log-ts">${new Date(entry.ts).toLocaleTimeString()}</span>
          <span class="log-msg ${entry.event}">${entry.event}</span>
          <span class="log-detail">${JSON.stringify(entry)}</span>
        </div>
      `).join("");
    }
  };

  await refresh();
  setInterval(refresh, 2000);
}

async function loadHardwarePage() {
  const summaryTarget = byId("hardwareSummary");
  const chartsTarget = byId("hardwareCharts");

  const refresh = async () => {
    const [hardware, runtime] = await Promise.all([
      fetchJson("/api/hardware"),
      fetchJson("/api/runtime/stats"),
    ]);

    renderCards(summaryTarget, [
      { label: "CPU Model", value: safeText(hardware.cpu) },
      { label: "CPU Cores", value: safeText(hardware.cpu_cores) },
      { label: "CPU Threads", value: safeText(hardware.cpu_threads) },
      { label: "RAM Total", value: `${safeText(hardware.ram_total_gb)} GB` },
      { label: "RAM Used", value: `${safeText(hardware.ram_used_gb)} GB` },
      { label: "RAM Free", value: `${safeText(hardware.ram_free_gb)} GB` },
      { label: "Disk Size", value: `${safeText(hardware.disk_total_gb)} GB` },
      { label: "Disk Usage", value: `${safeText(hardware.disk_usage_percent)}%` },
      { label: "GPU Available", value: hardware.gpu_available ? "Yes" : "No" },
      { label: "GPU Memory", value: `${safeText(hardware.gpu_memory_gb)} GB` },
    ]);

    renderBars(chartsTarget, [
      { label: "CPU Usage %", value: `${safeText(hardware.cpu_usage_percent)}%`, percent: hardware.cpu_usage_percent || 0 },
      { label: "RAM Usage %", value: `${safeText(hardware.ram_usage_percent)}%`, percent: hardware.ram_usage_percent || 0 },
      { label: "Disk Usage %", value: `${safeText(hardware.disk_usage_percent)}%`, percent: hardware.disk_usage_percent || 0 },
      { label: "Tokens/sec", value: safeText(runtime.tokens_per_second), percent: Math.min(100, (runtime.tokens_per_second || 0) * 5) },
    ]);
  };

  await refresh();
  setInterval(refresh, 2000);
}

async function loadSchedulerPage() {
  const summaryTarget = byId("schedulerSummary");
  const planTarget = byId("executionPlan");
  const selectedTarget = byId("selectedLayers");
  const skippedTarget = byId("skippedLayers");
  const strategyTarget = byId("strategyChip");

  const refresh = async () => {
    const data = await fetchJson("/api/scheduler");
    renderCards(summaryTarget, [
      { label: "Prompt", value: safeText(data.prompt || "Waiting for prompt") },
      { label: "Execution Strategy", value: safeText(data.execution_strategy) },
      { label: "Active Stage", value: safeText(data.stage) },
      { label: "Active Layers", value: safeText((data.active_layers || []).length) },
    ]);

    if (planTarget) planTarget.innerHTML = renderPills((data.execution_plan || []).map(String), "None", "plan");
    if (selectedTarget) selectedTarget.innerHTML = renderPills((data.selected_layers || []).map(String), "None", "selected");
    if (skippedTarget) skippedTarget.innerHTML = renderPills((data.skipped_layers || []).map(String), "None", "skipped");
    if (strategyTarget) strategyTarget.textContent = data.execution_strategy || "Unknown";
  };

  await refresh();
  setInterval(refresh, 2000);
}

async function loadMemoryPage() {
  const summaryTarget = byId("memorySummary");
  const allocationTarget = byId("memoryAllocation");

  const refresh = async () => {
    const data = await fetchJson("/api/memory");
    renderCards(summaryTarget, [
      { label: "Layer Cache Size", value: safeText(data.layer_cache_size) },
      { label: "Active Layers", value: safeText((data.active_layers || []).length) },
      { label: "RAM Allocation", value: safeText((data.ram_allocation || []).length) },
      { label: "SSD Allocation", value: safeText((data.ssd_allocation || []).length) },
      { label: "Cache Hit Ratio", value: `${safeText(data.cache_hit_ratio)}%` },
      { label: "Cache Miss Ratio", value: `${safeText(data.cache_miss_ratio)}%` },
    ]);

    if (allocationTarget) {
      const renderAllocation = (title, list, className) => `
        <section class="allocation-group">
          <h3>${title}</h3>
          <div class="pill-list">
            ${(list || []).map((item) => chip(`Layer ${item.layer_id}`, className)).join("") || `<span class="muted">None</span>`}
          </div>
        </section>
      `;
      allocationTarget.innerHTML = `
        ${renderAllocation("RAM", data.ram_allocation, "ram")}
        ${renderAllocation("SSD", data.ssd_allocation, "ssd")}
        ${renderAllocation("Cache", data.cache_allocation, "cache")}
      `;
    }
  };

  await refresh();
  setInterval(refresh, 2000);
}

async function loadTokensPage() {
  const summaryTarget = byId("tokenSummary");
  const inputTarget = byId("inputTokens");
  const generatedTarget = byId("generatedTokens");
  const predictionsTarget = byId("topPredictions");

  const refresh = async () => {
    const data = await fetchJson("/api/runtime/tokens");
    renderCards(summaryTarget, [
      { label: "Token Probability", value: `${safeText(data.token_probability)}%` },
      { label: "Token IDs", value: safeText((data.token_ids || []).length) },
      { label: "Input Tokens", value: safeText((data.input_tokens || []).length) },
      { label: "Generated Tokens", value: safeText((data.generated_tokens || []).length) },
    ]);

    if (inputTarget) inputTarget.innerHTML = renderPills(data.input_tokens, "None", "input");
    if (generatedTarget) generatedTarget.innerHTML = renderPills(data.generated_tokens, "None", "generated");
    if (predictionsTarget) {
      predictionsTarget.innerHTML = (data.top_k_predictions || []).map((prediction) => `
        <div class="prediction-row">
          <span>${prediction.token}</span>
          <strong>${prediction.probability}%</strong>
        </div>
      `).join("");
    }
  };

  await refresh();
  setInterval(refresh, 2000);
}

function renderHeatmap(values) {
  return `<div class="heatmap-grid">${values.map((value) => {
    const intensity = Math.max(0.12, Math.min(1, value / 100));
    return `<div class="heatmap-cell" style="background-color: rgba(124, 196, 255, ${intensity})">${value}</div>`;
  }).join("")}</div>`;
}

async function loadAttentionPage() {
  const summaryTarget = byId("attentionSummary");
  const mapsTarget = byId("attentionMaps");

  const refresh = async () => {
    const data = await fetchJson("/api/model/attention");
    renderCards(summaryTarget, [
      { label: "Model", value: safeText(data.model_name) },
      { label: "Attention Heads", value: safeText(data.attention_heads) },
      { label: "Visible Layers", value: safeText((data.layers || []).length) },
    ]);

    if (mapsTarget) {
      mapsTarget.innerHTML = (data.layers || []).map((layer) => `
        <article class="heatmap-card">
          <header>
            <h3>Layer ${layer.layer_id}</h3>
          </header>
          <div class="heatmap-list">
            ${(layer.heads || []).map((head) => `
              <section>
                <h4>Head ${head.head_id}</h4>
                ${renderHeatmap((head.heatmap || []).map((value) => Math.round(value)))}
              </section>
            `).join("")}
          </div>
        </article>
      `).join("");
    }
  };

  await refresh();
  setInterval(refresh, 2000);
}

function appendLog(target, entry) {
  if (!target) return;
  const row = document.createElement("div");
  row.className = "log-item";
  row.innerHTML = `
    <span class="log-ts">${new Date(entry.ts).toLocaleTimeString()}</span>
    <span class="log-msg ${entry.event}">${entry.event}</span>
    <span class="log-detail">${JSON.stringify(entry)}</span>
  `;
  target.appendChild(row);
  target.scrollTop = target.scrollHeight;
  while (target.children.length > 300) {
    target.removeChild(target.firstChild);
  }
}

async function loadLogsPage() {
  const target = byId("logStream");
  if (!target) return;
  const seen = new Set();
  const appendUnique = (entry) => {
    const key = `${entry.ts}|${entry.event}|${JSON.stringify(entry)}`;
    if (seen.has(key)) return;
    seen.add(key);
    appendLog(target, entry);
  };

  const initial = await fetchJson("/api/runtime/logs");
  (initial.logs || []).forEach((entry) => appendUnique(entry));

  const connect = () => {
    const ws = new WebSocket(`${WS_BASE}/ws/logs`);
    ws.onmessage = (event) => appendUnique(JSON.parse(event.data));
    ws.onclose = () => setTimeout(connect, 2000);
  };

  connect();
}

async function loadMetricsPage() {
  const summaryTarget = byId("metricsSummary");
  const chartTarget = byId("metricsCharts");

  const refresh = async () => {
    const [runtime, hardware, memory, logs] = await Promise.all([
      fetchJson("/api/runtime/stats"),
      fetchJson("/api/hardware"),
      fetchJson("/api/memory"),
      fetchJson("/api/runtime/logs"),
    ]);

    const layerLoadEvents = (logs.logs || []).filter((entry) => entry.event === "layer_load").length;
    renderCards(summaryTarget, [
      { label: "Inference Latency", value: `${safeText(runtime.latency_ms)} ms` },
      { label: "Tokens/sec", value: safeText(runtime.tokens_per_second) },
      { label: "Memory Usage", value: `${safeText(runtime.memory_usage_percent)}%` },
      { label: "CPU Usage", value: `${safeText(runtime.cpu_usage_percent)}%` },
      { label: "Layer Loading Time", value: `${safeText(Math.round((runtime.latency_ms || 0) / Math.max(1, runtime.active_layers_count || 1)))} ms` },
      { label: "Response Time", value: `${safeText(runtime.inference_time_ms)} ms` },
      { label: "Layer Load Events", value: safeText(layerLoadEvents) },
      { label: "Cache Hit Ratio", value: `${safeText(memory.cache_hit_ratio)}%` },
    ]);

    renderBars(chartTarget, [
      { label: "Inference Latency", value: `${safeText(runtime.latency_ms)} ms`, percent: Math.min(100, (runtime.latency_ms || 0) / 20) },
      { label: "Tokens/sec", value: safeText(runtime.tokens_per_second), percent: Math.min(100, (runtime.tokens_per_second || 0) * 4) },
      { label: "Memory Usage", value: `${safeText(runtime.memory_usage_percent)}%`, percent: runtime.memory_usage_percent || 0 },
      { label: "CPU Usage", value: `${safeText(hardware.cpu_usage_percent)}%`, percent: hardware.cpu_usage_percent || 0 },
      { label: "Layer Loading Time", value: `${safeText(Math.round((runtime.latency_ms || 0) / Math.max(1, runtime.active_layers_count || 1)))} ms`, percent: Math.min(100, (runtime.latency_ms || 0) / 15) },
      { label: "Response Time", value: `${safeText(runtime.inference_time_ms)} ms`, percent: Math.min(100, (runtime.inference_time_ms || 0) / 20) },
    ]);
  };

  await refresh();
  setInterval(refresh, 2000);
}

const pageHandlers = {
  "model-explorer": loadModelExplorer,
  layers: loadLayersPage,
  runtime: loadRuntimePage,
  hardware: loadHardwarePage,
  scheduler: loadSchedulerPage,
  memory: loadMemoryPage,
  tokens: loadTokensPage,
  attention: loadAttentionPage,
  logs: loadLogsPage,
  metrics: loadMetricsPage,
};

window.addEventListener("DOMContentLoaded", () => {
  const page = document.body.dataset.page;
  const handler = pageHandlers[page];
  if (handler) {
    handler().catch((error) => {
      console.error(error);
      const errorBox = byId("pageError");
      if (errorBox) {
        errorBox.textContent = error.message;
      }
    });
  }
});
