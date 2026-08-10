# 布丁 (Buding) — Codex v2 宠物

赤柴布丁的 Codex 兼容精灵图包（spriteVersionNumber 2）。

## 快速安装（Codex Desktop）

1. 复制 `package/buding/` 整个文件夹到：
   - Windows: `%USERPROFILE%\.codex\pets\buding\`
   - macOS / Linux: `~/.codex/pets/buding/`
2. 打开 Codex → Settings → Pets → Refresh
3. 选择「布丁」后使用 `/pet`

## 仓库内容

| 路径 | 说明 |
|------|------|
| `package/buding/` | 可直接安装的宠物包（`pet.json` + `spritesheet.webp`） |
| `runs/buding/final/` | 组装产物与校验结果 |
| `runs/buding/frames/` | 分行动画帧 |
| `runs/buding/prompts/` | 生成用提示词 |
| `extension/` | Cursor 侧栏预览扩展（实验性） |

## 规格

- Atlas: 8×11 格，每格 192×208
- 格式: RGBA WebP
- 行序: idle / running-right / running-left / waving / jumping / failed / waiting / working(laptop) / review / look×2
