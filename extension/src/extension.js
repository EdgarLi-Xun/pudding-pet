const vscode = require("vscode");
const path = require("path");

const STATES = [
  { id: "idle", label: "待机", row: 0, frames: 6, fps: 6 },
  { id: "running-right", label: "向右跑", row: 1, frames: 8, fps: 10 },
  { id: "running-left", label: "向左跑", row: 2, frames: 8, fps: 10 },
  { id: "waving", label: "挥手", row: 3, frames: 4, fps: 6 },
  { id: "jumping", label: "跳跃", row: 4, frames: 5, fps: 8 },
  { id: "failed", label: "失败", row: 5, frames: 8, fps: 6 },
  { id: "waiting", label: "等待", row: 6, frames: 6, fps: 5 },
  { id: "running", label: "工作", row: 7, frames: 6, fps: 6 },
  { id: "review", label: "检查", row: 8, frames: 6, fps: 5 },
];

/** @type {vscode.WebviewView | undefined} */
let currentView;

function activate(context) {
  const provider = new BudingPetViewProvider(context.extensionUri);

  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider("budingPet.view", provider, {
      webviewOptions: { retainContextWhenHidden: true },
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("budingPet.show", async () => {
      await vscode.commands.executeCommand("budingPet.view.focus");
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("budingPet.setState", async () => {
      const picked = await vscode.window.showQuickPick(
        STATES.map((s) => ({ label: s.label, description: s.id, state: s.id })),
        { placeHolder: "选择布丁的动作" }
      );
      if (picked) postState(picked.state);
    })
  );

  for (const [command, state] of [
    ["budingPet.wave", "waving"],
    ["budingPet.work", "running"],
    ["budingPet.idle", "idle"],
  ]) {
    context.subscriptions.push(
      vscode.commands.registerCommand(command, () => postState(state))
    );
  }
}

function postState(stateId) {
  if (!currentView) {
    vscode.window.showInformationMessage("请先打开侧边栏「布丁」视图");
    vscode.commands.executeCommand("budingPet.view.focus");
    return;
  }
  currentView.webview.postMessage({ type: "setState", state: stateId });
}

class BudingPetViewProvider {
  /** @param {vscode.Uri} extensionUri */
  constructor(extensionUri) {
    this.extensionUri = extensionUri;
  }

  /** @param {vscode.WebviewView} webviewView */
  resolveWebviewView(webviewView) {
    currentView = webviewView;
    const { webview } = webviewView;
    webview.options = {
      enableScripts: true,
      localResourceRoots: [vscode.Uri.joinPath(this.extensionUri, "media")],
    };

    const sheetUri = webview.asWebviewUri(
      vscode.Uri.joinPath(this.extensionUri, "media", "spritesheet.webp")
    );
    const scriptUri = webview.asWebviewUri(
      vscode.Uri.joinPath(this.extensionUri, "media", "pet.js")
    );
    const styleUri = webview.asWebviewUri(
      vscode.Uri.joinPath(this.extensionUri, "media", "pet.css")
    );

    webview.html = getHtml(webview, sheetUri, scriptUri, styleUri, STATES);

    webview.onDidReceiveMessage((msg) => {
      if (msg?.type === "ready") {
        webview.postMessage({ type: "setState", state: "idle" });
      }
    });
  }
}

function getHtml(webview, sheetUri, scriptUri, styleUri, states) {
  const csp = [
    `default-src 'none'`,
    `img-src ${webview.cspSource} data: blob:`,
    `style-src ${webview.cspSource}`,
    `script-src ${webview.cspSource}`,
  ].join("; ");

  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta http-equiv="Content-Security-Policy" content="${csp}" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <link rel="stylesheet" href="${styleUri}" />
  <title>布丁</title>
</head>
<body>
  <div class="stage">
    <canvas id="pet" width="192" height="208" aria-label="布丁桌宠"></canvas>
    <div class="hint">移动鼠标，布丁会看向你</div>
  </div>
  <div class="controls" id="controls"></div>
  <script>
    window.BUDING_CONFIG = {
      sheetUrl: ${JSON.stringify(String(sheetUri))},
      states: ${JSON.stringify(states)},
      cellWidth: 192,
      cellHeight: 208,
      columns: 8
    };
  </script>
  <script src="${scriptUri}"></script>
</body>
</html>`;
}

function deactivate() {}

module.exports = { activate, deactivate };
