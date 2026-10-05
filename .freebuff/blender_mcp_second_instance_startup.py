# Startup script for a SECOND Blender instance: starts the blender-mcp
# socket server on port 9877 (the first instance/Codex owns 9876).
# Run:  blender --background|--windowed --python <this file> [-- other args]
import bpy

PORT = 9877

# Ensure the addon is enabled (shared user prefs should already have it).
mod = "blender_mcp"
if mod not in bpy.context.preferences.addons:
    bpy.ops.preferences.addon_enable(module=mod)

# Persist the port on the current scene so the panel shows the same value.
bpy.context.scene.blendermcp_port = PORT

# Start the server unless something already listens on the port.
already = any(
    getattr(s, "port", None) == PORT
    for s in [getattr(bpy.types, "blendermcp_server", None)]
    if s is not None
)
if not already:
    bpy.ops.blendermcp.start_server()
    print(f"[freebuff] blender-mcp server started on port {PORT}")
else:
    print(f"[freebuff] blender-mcp server already running on port {PORT}")
