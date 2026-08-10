(() => {
  const vscode = acquireVsCodeApi();
  const cfg = window.BUDING_CONFIG;
  const canvas = document.getElementById("pet");
  const ctx = canvas.getContext("2d");
  const controls = document.getElementById("controls");

  const CELL_W = cfg.cellWidth;
  const CELL_H = cfg.cellHeight;
  const COLS = cfg.columns;

  /** Look rows: row 9 = 000..157.5, row 10 = 180..337.5 */
  const LOOK_ORDER = [
    0, 22.5, 45, 67.5, 90, 112.5, 135, 157.5, 180, 202.5, 225, 247.5, 270, 292.5, 315, 337.5,
  ];

  const sheet = new Image();
  sheet.src = cfg.sheetUrl;

  let stateId = "idle";
  let frame = 0;
  let lastTs = 0;
  let lookMode = false;
  let lookIndex = -1;
  let pointerAngle = null;

  const stateMap = Object.fromEntries(cfg.states.map((s) => [s.id, s]));

  function currentState() {
    return stateMap[stateId] || stateMap.idle;
  }

  function drawFrame(row, col) {
    ctx.clearRect(0, 0, CELL_W, CELL_H);
    if (!sheet.complete) return;
    ctx.drawImage(
      sheet,
      col * CELL_W,
      row * CELL_H,
      CELL_W,
      CELL_H,
      0,
      0,
      CELL_W,
      CELL_H
    );
  }

  function angleToLookIndex(deg) {
    // Normalize to [0, 360)
    let a = ((deg % 360) + 360) % 360;
    // Map CSS-like atan2 (0=right, 90=down) to pet look (0=up, 90=right)
    // Our pointer uses: 0 = up, clockwise
    let best = 0;
    let bestDiff = Infinity;
    for (let i = 0; i < LOOK_ORDER.length; i++) {
      let d = Math.abs(LOOK_ORDER[i] - a);
      d = Math.min(d, 360 - d);
      if (d < bestDiff) {
        bestDiff = d;
        best = i;
      }
    }
    // Deadzone near front/neutral: keep idle if almost no offset
    return best;
  }

  function tick(ts) {
    const st = currentState();
    const interval = 1000 / (st.fps || 6);

    if (!lookMode) {
      if (ts - lastTs >= interval) {
        frame = (frame + 1) % st.frames;
        lastTs = ts;
      }
      drawFrame(st.row, frame);
    } else if (lookIndex >= 0) {
      const row = lookIndex < 8 ? 9 : 10;
      const col = lookIndex % 8;
      drawFrame(row, col);
    } else {
      drawFrame(stateMap.idle.row, 0);
    }

    requestAnimationFrame(tick);
  }

  function setState(id) {
    if (!stateMap[id]) return;
    stateId = id;
    frame = 0;
    lookMode = false;
    lookIndex = -1;
    for (const btn of controls.querySelectorAll("button")) {
      btn.classList.toggle("active", btn.dataset.state === id);
    }
  }

  function buildControls() {
    controls.innerHTML = "";
    for (const st of cfg.states) {
      const btn = document.createElement("button");
      btn.textContent = st.label;
      btn.dataset.state = st.id;
      btn.addEventListener("click", () => setState(st.id));
      controls.appendChild(btn);
    }
  }

  const stage = document.querySelector(".stage");
  stage.addEventListener("pointermove", (e) => {
    if (stateId !== "idle") return;
    const rect = canvas.getBoundingClientRect();
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height * 0.35; // near head
    const dx = e.clientX - cx;
    const dy = e.clientY - cy;
    // Convert to pet look degrees: 0=up, 90=right, clockwise
    const rad = Math.atan2(dx, -dy); // 0 when up
    let deg = (rad * 180) / Math.PI;
    if (deg < 0) deg += 360;
    pointerAngle = deg;
    lookMode = true;
    lookIndex = angleToLookIndex(deg);
  });

  stage.addEventListener("pointerleave", () => {
    lookMode = false;
    lookIndex = -1;
  });

  window.addEventListener("message", (event) => {
    const msg = event.data;
    if (msg?.type === "setState") setState(msg.state);
  });

  sheet.onload = () => {
    buildControls();
    setState("idle");
    vscode.postMessage({ type: "ready" });
    requestAnimationFrame(tick);
  };
  sheet.onerror = () => {
    ctx.fillStyle = "#c44";
    ctx.font = "12px sans-serif";
    ctx.fillText("图集加载失败", 40, 104);
  };
})();
