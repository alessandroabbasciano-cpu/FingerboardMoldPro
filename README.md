# Fingerboard Mold Pro

A parametric Workbench for FreeCAD to design professional fingerboard molds.

## Features
* **Loft & Bezier Engine**: Creates organic shapes, not just simple arcs.
* **Parametric Design**: Adjust wheelbase, concave, kicks, and length in real-time.
* **Shaper Templates**: Generates matching cutting templates with "Organic" transitions.
* **Presets System**: Save and load your favorite shapes (JSON based).
* **Batch Export**: Export Male, Female, and Shaper STL files in one click.
![Mod preview](preview.png)

## Installation

### Method 1: Manual Installation (Recommended for now)
Since this workbench is not yet in the official Addon Manager registry, you need to install it manually:

1.  **Download** this repository (Click the green "Code" button -> "Download ZIP") and extract it.
2.  Locate your FreeCAD **Mod** directory:
    * **Windows**: `%APPDATA%\FreeCAD\Mod\`
    * **Linux**: `~/.local/share/FreeCAD/Mod/` (or `~/.FreeCAD/Mod/`)
    * **macOS**: `~/Library/Application Support/FreeCAD/Mod/`
3.  Copy the extracted `FingerboardMoldPro` folder into that **Mod** directory.
4.  **Restart FreeCAD**.

### Method 2: Addon Manager (Coming Soon)
*Once approved by the FreeCAD team:*
1. Open **Tools -> Addon Manager**.
2. Search for **Fingerboard Mold Pro**.
3. Click **Install**.

## How to Use
1. Select the **Fingerboard Mold Pro** workbench from the dropdown menu.
2. Click the **New Mold** icon.
3. Select the created object (`Board_Preview`) in the tree.
4. Adjust parameters in the **Data** tab (Length, Kicks, Concave, etc.).
5. Use **Batch Export** to generate all STL files at once.

## License
This workbench is licensed under the **LGPLv2.1** (same as FreeCAD).