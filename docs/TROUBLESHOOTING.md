# Troubleshooting

- Blender bridge not running: open the 3D View sidebar, check status, token, project root, and click Start.
- Token mismatch: generate a new token in Blender and copy it to `.env` as `BLENDER_BRIDGE_TOKEN`.
- Wrong port: verify `BLENDER_BRIDGE_URL` and Blender preferences both use port `8765` unless you intentionally changed both.
- Add-on registration failure: install the zip root folder `blender_chatgpt_bridge`, not a parent directory.
- Timers not processing commands: ensure Blender is responsive; long modal operations can delay timers.
- Blender busy during render: render preview can block the command queue until Blender finishes.
- MCP cannot reach Blender: run `curl http://127.0.0.1:8765/healthz`.
- ChatGPT tunnel not connected: run the official tunnel diagnostic command.
- ChatGPT connector does not refresh: refresh connector metadata or start a new ChatGPT conversation.
- Preview too large: lower width, height, samples, or use JPEG.
- Unsupported Blender version: use Blender 5.1 or newer. Older Blender 3.x and 4.x releases are not supported.
- Windows firewall or antivirus: allow localhost connections for Blender and Node.
- macOS permissions: allow Blender and Terminal/Node local network access if prompted.
- Linux headless rendering: ensure graphics/EGL/OSMesa support is available for your Blender build.
