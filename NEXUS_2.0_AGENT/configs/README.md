# NEXUS 2.0 Custom HTML Tabs

This directory is for your custom HTML files that will be integrated as tabs in NEXUS.

## Required Files

1. **stage_management.html** - Your stage management interface
2. **desktop_prototype.html** - Your desktop prototype interface

## How to Add Your Files

### Option 1: Command Line
```bash
# From your downloads folder
cp ~/Downloads/stage_management.html /workspaces/nexus-mind-repository/NEXUS_2.0_AGENT/configs/
cp ~/Downloads/desktop_prototype.html /workspaces/nexus-mind-repository/NEXUS_2.0_AGENT/configs/
```

### Option 2: Drag & Drop
- Open VS Code
- Navigate to `NEXUS_2.0_AGENT/configs/`
- Drag your HTML files from your file manager into this folder

### Option 3: Upload Through VS Code
- Right-click on the `configs` folder in VS Code
- Select "Upload..."
- Choose your HTML files

## File Naming

Make sure your files are named exactly:
- `stage_management.html`
- `desktop_prototype.html`

If your files have different names, rename them before copying.

## After Adding Files

Run the launcher:
```bash
cd /workspaces/nexus-mind-repository/NEXUS_2.0_AGENT
python launch_with_custom_tabs.py
```

The launcher will:
1. Detect your HTML files
2. Create a unified interface with your content as tabs
3. Give you options to launch in web or terminal mode

## HTML Requirements

Your HTML files should be self-contained with:
- All styles in `<style>` tags
- All scripts in `<script>` tags  
- Content in the `<body>` section

The integrator will extract and merge these sections automatically.