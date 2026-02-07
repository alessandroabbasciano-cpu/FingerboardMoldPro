# Fingerboard Mold Pro

A professional parametric workbench for FreeCAD, designed to generate high-precision molds for **fingerboarding** (miniature skateboarding).

It allows makers to generate organic, customizable 3D-printable molds used to press and shape wooden veneers into finished fingerboard decks.

![Mod preview](./images/preview.png)

## 🚀 Key Features
* **Loft & Bezier Engine**: Generates organic shapes and fluid transitions (no simple geometric arcs).
* **Fully Parametric**: Every dimension (wheelbase, kick height, concave depth) is adjustable in real-time.
* **SideLocks System (New in v1.3)**: Integrated pentagonal guides allowing molds to be printed vertically without supports.
* **Concave Styles**: Choose between "Organic" (Classic Wavy) or "Flat" (Modern Tub/Pocket) geometry.
* **Batch Export**: Automatically exports all necessary STL files (Male, Female, Template) with a single click.

### v1.3 Release Notes: The "Vertical" Update
- **New: SideLocks System**: Added `SideLocks` (Bool). When enabled, it generates pentagonal guide rails on the sides of the mold. This allows you to print the Male and Female parts standing vertically on the print bed **without any supports**, ensuring the smoothest possible surface finish on the pressing face.
- **New: Concave Styles**: Added `ConcaveStyle` parameter.
    - **Organic**: The classic continuous curve (Wavy).
    - **Flat**: A modern "Tub" or "Pocket" concave with a flat central section and steep walls.
- **Improved**: The `AddFillet` logic is now fully compatible with SideLocks.
- **Fix**: Resolved topological issues in the "Belly" section of the loft.

---

## 📦 Installation

Since this workbench is not yet available in the official Addon Manager registry, please install it manually:

1. **Download** this repository as a ZIP file and extract it.

2. **Locate your FreeCAD Addon folder**:
    * Open FreeCAD and launch the **Addon Manager**
    * **Ensure your Addon Manager is up to date**.
    * Click on the **"Open Addon Folder"** option:![alt text](./images/am_oaf.png)

3. **Copy** the extracted `FingerboardMoldPro` folder into that directory you just opened.

4. **Restart FreeCAD** to load the new workbench.

---

## 📖 User Guide

### 1. Core Concept: The "Master" and the "Slaves"
When you create a new mold, **4 objects** will appear in the project tree:

1.  **`Board_Preview` (THE MASTER)**: This is the finished deck in the center. **This is the ONLY object you need to modify.** It holds all the parameters (dimensions, angles, etc.).
2.  `Male_Mold`: The positive mold block (blue).
3.  `Female_Mold`: The negative mold block (red).
4.  `Shaper_Template`: The cutting guide (green transparent).

**⚠️ Important:** The Male, Female, and Template objects are linked to the Master. If you want to change the length or wheelbase, **always modify `Board_Preview` only**. The others will update automatically.

### 2. Step-by-Step Workflow
1.  **Select the Workbench**: Choose "Fingerboard Mold Pro" from the dropdown menu.
2.  **Create**: Click the **New Mold** icon (Yellow Deck icon).
3.  **Edit Parameters**:
    * Select the **`Board_Preview`** object in the tree.
    * Go to the **Data** tab in the Property View.
    * Change values (e.g., `Wheelbase`, `NoseAngle`) and press **Enter**.
4.  **Visualize & Export**:
    * Use the **Batch Export STL** icon (Green arrow) to generate files for your 3D printer.

### 💡 Pro Tip: The Vertical Printing Strategy (The "Side-Print" Method)
To get the smoothest possible surface on your mold (the curved part touching the veneer), you should print the molds standing on their side.

1.  **Enable `SideLocks`**: This places the alignment keys on the **Nose and Tail ends** of the mold, keeping the long sides free of obstructions.
2.  **Disable `AddFillet`**: Set to `False` to remove the rounded bottom edge, creating a sharp 90° corner for stable adhesion.
3.  **Flatten the Sides**: Set **`MoldBaseWidth` equal to `MoldCoreWidth`**.
    * *Why?* If the Base is wider than the Core, you have a "step" on the side. By making them equal (e.g., both 45mm), you create a perfectly flush, flat side wall that sits solidly on the printer bed.
4.  **Slicer Orientation**: Rotate the object **90°** so it stands on this flat long edge.
    * *Result:* Zero supports needed, and layer lines run along the length of the kick for a superior finish.

---

## 🎛️ Parameters Glossary (Data Tab)

### 1. Mold Structure & Printing
*These parameters control the physical block of the mold, not the shape of the deck.*

* **`SideLocks`** (Bool)
    * **Function:** If `True`, generates pentagonal rails on the sides of the Male/Female parts.
    * **Usage:** Enables **Vertical Printing**. The locks align the two halves perfectly, allowing the pressing surface to be printed vertically for maximum smoothness without supports.
* **`MoldBaseHeight`**
    * **Function:** Thickness of the base plate (the part that touches the clamp/press).
    * **Limits:** Max **20.0mm**.
* **`MoldCornerRadius`**
    * **Function:** Aesthetic radius on the vertical corners of the mold block.
    * **Limits:** Min **0.1mm** - Max **5.0mm**.
* **`AddFillet`** (Bool)
    * **Function:** Adds a rounded fillet at the base of the mold structure for reinforcement.
    * **Recommendation:** Keep `True` for strength. Set to `False` **ONLY** if printing horizontally without SideLocks (to get a flat bottom).

### 2. Board Geometry (The Core)
*Dimensions defining the main body of the fingerboard.*

* **`BoardWidth`**
    * **Function:** The maximum width of the deck (usually at the widest point).
    * **Limits:** Min **29.0mm**. Cannot exceed `MoldCoreWidth` (default 45mm).
* **`Wheelbase`**
    * **Function:** Distance between the *inner* truck holes. This is the primary driver for the mold's length.
    * **Limits:** Min **30.0mm** - Max **50.0mm**.
* **`ConcaveDrop`**
    * **Function:** The depth of the concave (height difference between the center and the edge).
    * **Limits:** Max **3.4mm** (Values higher than this cause veneer cracking).
* **`ConcaveLength`**
    * **Function:** The length of the central section where the concave profile is applied.
    * **Limits:** Cannot exceed the `Wheelbase`.
* **`ConcaveStyle`**
    * **`Organic`**: Generates a continuous, smooth curve from edge to edge (Classic style).
    * **`Flat`**: Generates a "Tub" or "Pocket" concave with a completely flat center and steep curved walls (Modern street style).
* **`TubWidth`**
    * **Function:** Defines the width of the flat central strip.
    * **Condition:** Active **ONLY** if `ConcaveStyle` is set to **"Flat"**.
    * **Limits:** Max is `BoardWidth - 2mm`.

### 3. Kicks (Nose & Tail)
*Parameters controlling the bends at the tips.*

* **`NoseAngle` / `TailAngle`**
    * **Function:** The steepness of the kicks in degrees.
    * **Limits:** Max **45°**.
* **`NoseLength` / `TailLength`**
    * **Function:** Total length of the kick measured from the *outer* truck holes to the tip.
    * **Limits:** Min **5.0mm** - Max **23.0mm**.
* **`TransitionLength`**
    * **Function:** The horizontal distance used to blend the flat wheelbase into the angled kick.
    * **Physics:** This mathematically defines the **Radius** of the kick bend.
        * *Larger Value* = Mellow, large radius curve.
        * *Smaller Value* = Sharp, tight kink.
    * **Limits:** Min **0.1mm** - Max **10.0mm** (or limited by available Kick Length).

### 4. Shaper Template (Cutout Guide)
*Parameters for the green transparent object used to trace the outline.*

* **`NoseShape` / `TailShape`**
    * **Function:** Selects a pre-defined tip shape (Popsicle, Boxy, Spade, etc.) from the library.
* **`NoseTaperStart` / `TailTaperStart`**
    * **Function:** The distance from the tip where the board starts to narrow (taper).
    * **Usage:** Lower values make the board parallel for longer (wider nose/tail).
* **`NoseFlatness` / `TailFlatness`**
    * **Function:** Controls the curvature of the very tip.
    * **Values:**
        * **0%**: Perfectly Pointy.
        * **100%**: Perfectly Square (Boxy).
        * **50-70%**: Standard Popsicle shape.

---
## License
This workbench is licensed under the **LGPLv2.1** (same as FreeCAD).  

---

## Warning: 
Using this software may cause an uncontrollable urge to sand tiny pieces of wood at 3 AM.