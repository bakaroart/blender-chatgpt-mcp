# Install Blender Add-On

This add-on targets Blender 5.1 or newer.

1. Build the zip:

   ```bash
   npm run package:addon
   ```

2. Open Blender.
3. Open `Edit > Preferences > Add-ons`.
4. Use Blender's install-from-disk control and choose `dist/blender_chatgpt_bridge.zip`.
5. Enable "Blender MCP Bridge".
6. Open the add-on preferences.
7. Set a project root directory.
8. Click "Generate Token".
9. Put the same token in `.env` as `BLENDER_BRIDGE_TOKEN`.
10. In the 3D View sidebar, open `MCP Bridge`.
11. Click "Start MCP Bridge".
12. Verify non-secret health locally:

    ```bash
    curl http://127.0.0.1:8765/healthz
    ```

Do not expose the Blender bridge port publicly.
