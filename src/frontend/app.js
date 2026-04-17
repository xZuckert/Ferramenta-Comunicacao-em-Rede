const state = {
  username: "",
  events: null,
};

const views = {
  welcome: document.querySelector("#welcome-view"),
  connecting: document.querySelector("#connecting-view"),
  chat: document.querySelector("#chat-view"),
};

const elements = {
  joinForm: document.querySelector("#join-form"),
  username: document.querySelector("#username"),
  messages: document.querySelector("#messages"),
  messageForm: document.querySelector("#message-form"),
  messageInput: document.querySelector("#message-input"),
  fileButton: document.querySelector("#file-button"),
  fileInput: document.querySelector("#file-input"),
  leaveButton: document.querySelector("#leave-button"),
  roomStatus: document.querySelector("#room-status"),
  steps: {
    discover: document.querySelector("#step-discover"),
    connect: document.querySelector("#step-connect"),
    ready: document.querySelector("#step-ready"),
  },
};

elements.joinForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const username = elements.username.value.trim();
  if (!username) {
    elements.username.focus();
    return;
  }

  state.username = username;
  showView("connecting");
  setStep("discover");

  try {
    const result = await postJson("/api/start", { username });
    setStep("connect");
    openEventStream();
    setStep("ready");
    elements.roomStatus.textContent = result.hosting
      ? `Hosting on TCP ${result.port}`
      : `Connected to ${result.host}:${result.port}`;
    showView("chat");
    elements.messageInput.focus();
  } catch (error) {
    showView("welcome");
    appendMessage({ type: "error", message: error.message || "Unable to connect." });
  }
});

elements.messageForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = elements.messageInput.value.trim();
  if (!text) {
    return;
  }

  elements.messageInput.value = "";
  try {
    await postJson("/api/message", { text });
  } catch (error) {
    appendMessage({ type: "error", message: error.message || "Message not sent." });
  }
});

elements.fileButton.addEventListener("click", () => {
  elements.fileInput.click();
});

elements.fileInput.addEventListener("change", async () => {
  const file = elements.fileInput.files[0];
  elements.fileInput.value = "";
  if (!file) {
    return;
  }

  try {
    const data = await readFileAsBase64(file);
    await postJson("/api/file", { filename: file.name, data });
  } catch (error) {
    appendMessage({ type: "error", message: error.message || "File not sent." });
  }
});

elements.leaveButton.addEventListener("click", async () => {
  try {
    await postJson("/api/stop", {});
  } finally {
    if (state.events) {
      state.events.close();
      state.events = null;
    }
    elements.messages.replaceChildren();
    showView("welcome");
  }
});

function showView(name) {
  Object.entries(views).forEach(([viewName, node]) => {
    node.classList.toggle("hidden", viewName !== name);
  });
}

function setStep(activeName) {
  let reachedActive = false;
  Object.entries(elements.steps).forEach(([name, node]) => {
    if (name === activeName) {
      reachedActive = true;
      node.classList.add("active");
      node.classList.remove("done");
      return;
    }
    node.classList.remove("active");
    node.classList.toggle("done", !reachedActive);
  });
}

function openEventStream() {
  if (state.events) {
    state.events.close();
  }
  state.events = new EventSource("/events");
  state.events.onmessage = (event) => {
    appendMessage(JSON.parse(event.data));
  };
  state.events.onerror = () => {
    appendMessage({ type: "error", message: "Event stream disconnected." });
  };
}

function appendMessage(packet) {
  const type = packet.type || "system";
  const row = document.createElement("article");
  row.className = `message ${messageClass(packet)}`;

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  if (type === "file" && packet.data) {
    const link = document.createElement("a");
    link.href = `data:application/octet-stream;base64,${packet.data}`;
    link.download = packet.filename || "file";
    link.textContent = messageText(packet);
    bubble.appendChild(link);
  } else {
    bubble.textContent = messageText(packet);
  }
  row.appendChild(bubble);

  const metaText = messageMeta(packet);
  if (metaText) {
    const meta = document.createElement("div");
    meta.className = "meta";
    meta.textContent = metaText;
    row.appendChild(meta);
  }

  elements.messages.appendChild(row);
  elements.messages.scrollTop = elements.messages.scrollHeight;
}

function messageClass(packet) {
  if (packet.type === "message" && packet.from === state.username) {
    return "mine";
  }
  if (packet.type === "error") {
    return "error";
  }
  if (packet.type === "status") {
    return "status";
  }
  if (packet.type === "system" || packet.type === "file") {
    return "system";
  }
  return "";
}

function messageText(packet) {
  if (packet.type === "message") {
    return packet.text || "";
  }
  if (packet.type === "file") {
    return `${packet.from || "Someone"} sent a file: ${packet.filename || "file"}`;
  }
  return packet.message || "";
}

function messageMeta(packet) {
  if (packet.type === "message") {
    const sender = packet.from === state.username ? "You" : packet.from || "Unknown";
    return `${sender} · ${formatTime(packet.timestamp)}`;
  }
  if (packet.timestamp) {
    return formatTime(packet.timestamp);
  }
  return "";
}

function formatTime(timestamp) {
  if (!timestamp) {
    return "";
  }
  const parts = String(timestamp).split(" ");
  return parts[1] || timestamp;
}

async function postJson(url, body) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const payload = await response.json();
  if (!response.ok || payload.ok === false) {
    throw new Error(payload.error || "Request failed.");
  }
  return payload;
}

function readFileAsBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error("Unable to read file."));
    reader.onload = () => {
      const result = String(reader.result || "");
      resolve(result.includes(",") ? result.split(",", 2)[1] : result);
    };
    reader.readAsDataURL(file);
  });
}
