# 🎨 Blender MCP Server v2

> **AI-Powered 3D Creation for Antigravity IDE**

A production-ready MCP (Model Context Protocol) server that enables **Google Gemini 3 Pro** to control Blender directly through natural language. Create 3D models, apply materials, sculpt meshes, and more - all from text prompts.

---

## ✨ Features

- 🤖 **AI-First Design** - Optimized for Antigravity IDE + Gemini 3 Pro
- 🔧 **17 Powerful Tools** - From primitives to AI-assisted sculpting
- 📐 **Blueprint System** - Structural model generation (buildings, weapons, vehicles, characters)
- 🎨 **AI Texturing** - Generate and apply textures via AI
- 👁️ **Vision Feedback** - AI can "see" renders and revise models
- ⚡ **Token Optimized** - Compact responses for efficient LLM usage
- 🖥️ **Windows Native** - Works perfectly on Windows 10/11

---

## 🛠️ Available Tools (17 Total)

| # | Tool | Description |
|---|------|-------------|
| 1 | `status` | Check Blender connection |
| 2 | `scene` | List objects in scene |
| 3 | `prim` | Create primitives (cube, sphere, cylinder, etc.) |
| 4 | `export` | Export models (GLB, FBX, OBJ) |
| 5 | `tex` | Apply textures from file |
| 6 | `mat` | Set materials (METAL, GLASS, WOOD, GLOW, etc.) |
| 7 | `proc` | Procedural generation (tree, rock, terrain) |
| 8 | `opt` | Optimize/decimate mesh |
| 9 | `render` | Full quality render |
| 10 | `bake` | Bake textures (normal, AO, diffuse) |
| 11 | `gentex` | AI texture generation + application |
| 12 | `pipe` | Step-by-step workflow orchestrator |
| 13 | `parse` | Analyze prompts structurally |
| 14 | `blueprint` | Generate complex models from structure |
| 15 | `sculpt` | AI-assisted mesh modification |
| 16 | `preview` | Quick render for AI vision feedback |
| 17 | `run` | Execute custom Python/bpy code |

---

## 📋 Requirements

- **Blender** 4.0+ (tested on 4.2+)
- **Node.js** 18+ 
- **Antigravity IDE** with **Gemini 3 Pro (High)** model
- **Windows** 10/11 (macOS/Linux should work but not tested)

> ⚠️ **Important:** This MCP is optimized for **Gemini 3 Pro (High)** model only. Other models may not work properly due to the complexity of 3D generation tasks and tool calling requirements.

---

## 🚀 Installation

### Step 1: Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/blender-mcp-v2.git
cd blender-mcp-v2
```

### Step 2: Install Node Dependencies

```bash
cd src/mcp-server
npm install
npm run build
```

### Step 3: Install Blender Addon

1. Open **Blender 4.0+**
2. Go to **Edit → Preferences → Add-ons**
3. Click **Install...**
4. Navigate to `blender-mcp-v2/mcp_connector_v2.py`
5. Select the file and click **Install Add-on**
6. ✅ Enable checkbox for **"Interface: MCP Connector v2"**
7. Click **Save Preferences**

### Step 4: Start Blender Server

1. In Blender, press `N` to open sidebar
2. Find the **MCP** tab
3. Click **Start Server**
4. ✅ Status should show: `Running on ws://127.0.0.1:9876`

### Step 5: Configure Antigravity IDE

Edit your MCP config file:
- **Windows:** `C:\Users\{username}\.gemini\antigravity\mcp_config.json`
- **macOS/Linux:** `~/.gemini/antigravity/mcp_config.json`

Add the following configuration:

```json
{
  "mcpServers": {
    "blender-mcp": {
      "command": "node",
      "args": ["C:/FULL/PATH/TO/blender-mcp-v2/src/mcp-server/dist/index.js"],
      "env": {
        "BLENDER_HOST": "127.0.0.1",
        "BLENDER_PORT": "9876"
      }
    }
  }
}
```

⚠️ **Important:** Replace `C:/FULL/PATH/TO/` with your actual path. Use forward slashes `/` even on Windows.

### Step 6: Restart Antigravity IDE

Restart the IDE to load the new MCP server.

### Step 7: Verify Connection

In Antigravity IDE, try this prompt:
```
Check Blender connection status
```

You should see a response like:
```json
{"ok":1,"v":"4.2.0","objs":3}
```

---

## 💡 Usage Examples

### Basic Object Creation
```
Create a red metallic cube in Blender
```

### Complex Model with Blueprint
```
Create a cyberpunk building with neon signs
```

### AI-Assisted Sculpting
```
Take that sphere and add horns, make it look like a demon head
```

### Procedural Generation
```
Generate a low-poly tree for my game scene
```

### Full Workflow
```
Create an AWP sniper rifle, low poly style, optimize for mobile, export as GLB
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│  Antigravity IDE (Gemini 3 Pro)                                │
│         │                                                        │
│         │ stdio (MCP Protocol)                                  │
│         ▼                                                        │
│  TypeScript MCP Server (17 tools)                               │
│         │                                                        │
│         │ WebSocket (ws://127.0.0.1:9876)                       │
│         ▼                                                        │
│  Python Addon (mcp_connector_v2.py)                             │
│         │                                                        │
│         │ bpy (Blender Python API)                              │
│         ▼                                                        │
│  Blender 4.x                                                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
blender-mcp-v2/
├── mcp_connector_v2.py          # Blender addon (install this)
├── src/
│   ├── mcp-server/              # TypeScript MCP server
│   │   ├── src/
│   │   │   ├── index.ts         # Entry point
│   │   │   ├── server.ts        # MCP server + tool registration
│   │   │   ├── bridge/          # WebSocket client to Blender
│   │   │   ├── tools/           # All 17 tools
│   │   │   └── utils/           # Logger, config
│   │   ├── dist/                # Compiled JS (after build)
│   │   └── package.json
│   └── blender-addon/           # Addon source (reference)
└── README.md
```

---

## 🔧 Development

### Build

```bash
cd src/mcp-server
npm run build
```

### Watch Mode

```bash
npm run dev
```

### Test Connection

```bash
# In a new terminal
node dist/index.js
```

---

## ❓ Troubleshooting

### "Connection Failed" Error

1. Make sure Blender is running
2. Check MCP addon is enabled in Blender preferences
3. Click **Start Server** in MCP panel
4. Verify status shows "Running"

### "No Response" from Tools

1. Check Blender system console for errors
2. Verify WebSocket port is 9876
3. Try restarting both Blender and Antigravity IDE

### "Invalid Path" Error

- Use forward slashes `/` in mcp_config.json even on Windows
- Use full absolute paths, not relative

### Addon Not Showing in Blender

1. Make sure you installed `mcp_connector_v2.py` (not the folder)
2. Check Blender version is 4.0+
3. Look in **Edit → Preferences → Add-ons** and search "MCP"

---

## 🎯 Designed For

This project is specifically designed for:

- **Antigravity IDE** - The AI-powered development environment
- **Google Gemini 3 Pro** - As the LLM brain for understanding 3D concepts
- **Rapid 3D Prototyping** - Create game assets, architectural concepts, and more

---

## 📜 License

MIT License - Feel free to use, modify, and distribute.

---

## 🙏 Credits

Developed for the Antigravity IDE ecosystem.

Special thanks to the Blender and MCP communities.

---

**Made with ❤️ for AI-powered 3D creation**
