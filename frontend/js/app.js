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

async function loadDashboard() {
  const el = document.getElementById("stats");
  if (!el) return;
  const render = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/runtime/stats`);
      if (!res.ok) {
        throw new Error(`${res.status}`);
      }
      const data = await res.json();
      el.innerHTML = `
        <article class="stat"><span>Active Model</span><strong>${data.active_model}</strong></article>
        <article class="stat"><span>CPU Usage</span><strong>${data.cpu_usage_percent}%</strong></article>
        <article class="stat"><span>RAM Usage</span><strong>${data.ram_usage_percent}%</strong></article>
        <article class="stat"><span>Tokens / sec</span><strong>${data.tokens_per_second}</strong></article>
        <article class="stat"><span>Loaded Layers</span><strong>${(data.loaded_layers || []).join(", ") || "none"}</strong></article>
        <article class="stat"><span>Active Layer Count</span><strong>${data.active_layers_count}</strong></article>
      `;
    } catch (error) {
      const message = String(error?.message || error);
      el.innerHTML = `<article class="stat"><span>Status</span><strong>${message.includes("Failed to fetch") || message.includes("ERR_CONNECTION_REFUSED") ? "Backend offline" : message}</strong></article>`;
    }
  };
  await render();
  setInterval(render, 3000);
}

async function loadRuntimeViewer() {
  const el = document.getElementById("layers");
  if (!el) return;
  const res = await fetch(`${API_BASE}/api/runtime/stats`);
  const data = await res.json();
  const layers = data.loaded_layers || [];
  const cards = [];
  for (let index = 0; index < Math.max(8, layers.length + 2); index += 1) {
    const id = index + 1;
    const state = layers.includes(index) ? "Loaded" : (index === 0 ? "Executing" : "Unloaded");
    cards.push(`<article class="layer-card"><span>Layer ${id}</span><strong>${state}</strong></article>`);
  }
  el.innerHTML = cards.join("");
}

function setupChat() {
  const form = document.getElementById("chatForm");
  const input = document.getElementById("promptInput");
  const log = document.getElementById("chatLog");
  if (!form || !input || !log) return;

  const socket = new WebSocket(`${WS_BASE}/ws/chat`);

  const addBubble = (role, text) => {
    const bubble = document.createElement("div");
    bubble.className = `bubble ${role}`;
    bubble.textContent = text;
    log.appendChild(bubble);
    log.scrollTop = log.scrollHeight;
    return bubble;
  };

  let activeBubble = null;

  socket.addEventListener("message", (event) => {
    const message = JSON.parse(event.data);
    if (message.type === "token") {
      if (!activeBubble) activeBubble = addBubble("assistant", "");
      activeBubble.textContent = `${activeBubble.textContent} ${message.value}`.trim();
    }
    if (message.type === "done") {
      activeBubble = null;
    }
  });

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const prompt = input.value.trim();
    if (!prompt || socket.readyState !== WebSocket.OPEN) return;
    addBubble("user", prompt);
    socket.send(JSON.stringify({ prompt }));
    input.value = "";
  });
}

loadDashboard();
loadRuntimeViewer();
setupChat();
