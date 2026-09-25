# CollectBox for Houdini

**CollectBox** is a smart, automated asset collection tool for SideFX Houdini — built to work like After Effects' "Collect Files". 

It gathers external project dependencies, groups textures into dedicated folders named after their materials (with native support for Redshift & standard shader networks), bundles 3D models and LUTs, and safely exports a clean, self-contained `.hip` file without copying heavy simulation caches.

---

## Compatibility
* **Tested on:** Houdini 22 (Supports Houdini 20.x, 20.5, and 22+)
* **Platforms:** Windows, macOS, Linux

---

## Installation

### Step 1: Locate your Houdini preferences directory
* **Windows:** `Documents/houdini22.0/`
* **macOS:** `~/Library/Preferences/houdini/22.0/`
* **Linux:** `~/houdini22.0/`

### Step 2: Install via Packages
1. Inside your Houdini preferences directory, locate the **`packages`** folder. 
   > **Note:** If the `packages` folder does not exist, simply create a new folder named `packages`.
2. Copy the **`CollectBox.json`** file into the `packages` directory.
3. Place the main **`CollectBox`** folder (containing `python`, `toolbar`, and `config`) in any directory referenced by your `.json` (or directly inside `packages/CollectBox/`).

### Step 3: Launch
Open Houdini, enable the **CollectBox** shelf tab (or add the tool from your Shelf set), and click the CollectBox icon.

---

## Features
* **Smart Texture Grouping:** Automatically generates subfolders named after each material container.
* **Asset Support:** Collects textures, HDRI maps, geometries (`.fbx`, `.obj`, `.abc`, `.usd`), and LUTs (`.cube`, `.mtlx`).
* **Cache Exclusion:** Automatically skips heavy simulation files (`.bgeo.sc`, `.vdb`, particles, etc.) to keep archived projects lightweight.
* **Safe Repathing:** Repaths dependencies to relative `$HIP` paths without breaking your currently open work session.
* **Custom Dark PySide UI:** Clean console feedback with adjustable export options.

---

## License
Free for both **personal** and **commercial** use.

---

© 2026 [Saeid Yaghani](https://www.instagram.com/saeidyaghani). All rights reserved.