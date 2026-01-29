# Component Import Guide

Step-by-step guide to importing ECAD data (symbols, footprints, 3D models) from component distributors into your KiCad library.

---

## Overview

Most distributors provide free ECAD models through services like **Ultra Librarian**, **SnapEDA**, or **SamacSys**. This guide covers the workflow to download and import these into your library.

---

## Step 1: Find Your Component

### Option A: DigiKey
1. Go to [digikey.com](https://www.digikey.com) and search for your part
2. On the product page, scroll to **"EDA/CAD Models"**
3. Click **"Download"** → Select **"KiCad"** format
4. This downloads a `.zip` file from Ultra Librarian

### Option B: Mouser
1. Go to [mouser.com](https://www.mouser.com) and find your part
2. Look for **"CAD Models"** or **"3D Model"** links
3. Click the link (usually Ultra Librarian or SamacSys)
4. Select **KiCad** format and download

### Option C: SnapEDA (Direct)
1. Go to [snapeda.com](https://www.snapeda.com)
2. Search for your part number
3. Click **"Download"** → **"KiCad"**
4. Register/login if required, download the `.zip`

### Option D: SamacSys (Direct)
1. Go to [componentsearchengine.com](https://www.componentsearchengine.com)
2. Search for your part
3. Download the KiCad library files

---

## Step 2: Import Using lib_manager.py

### Basic Import
```bash
cd path/to/kicad-library
python lib_manager.py ~/Downloads/STM32F405RGT6.zip
```

### What Happens
1. The tool extracts the zip file
2. Shows an interactive menu to select the library category:
   ```
   ============================================================
   KiCad Library Manager - Library Selection
   ============================================================
   Select a library to add the component to:

    1. Connectors: Headers, sockets, terminals, USB, edge connectors
    2. Passives: Resistors, capacitors, inductors, ferrite beads
    3. Discretes: Diodes, transistors (BJT, MOSFET, JFET)
    4. Ics: Op-amps, comparators, logic, analog switches, ADC/DAC
    5. Power: LDOs, DC-DC, battery chargers, power switches, PD
    6. Microcontrollers: MCUs, SoCs, FPGAs, processors
    ...

   Enter your choice (0-15):
   ```
3. Adds the symbol to the appropriate `.kicad_sym` file
4. Copies the footprint to the `.pretty` directory
5. Copies any 3D models to `3d_models/`

### Import with Git Commit
```bash
python lib_manager.py STM32F405RGT6.zip --commit
```

### Import and Push to Remote
```bash
python lib_manager.py STM32F405RGT6.zip --commit --push
```

---

## Step 3: Use in Your Project

### If Library is a Submodule
Your project already has access via `${KIPRJMOD}/lib/...`

### If Library is Standalone
Add to your project's library tables:

**Symbol Library (sym-lib-table):**
```
(lib (name "lib_microcontrollers")(type "KiCad")(uri "C:/path/to/kicad-library/lib_sym/lib_microcontrollers.kicad_sym")(options "")(descr ""))
```

**Footprint Library (fp-lib-table):**
```
(lib (name "lib_microcontrollers")(type "KiCad")(uri "C:/path/to/kicad-library/lib_fp/lib_microcontrollers.pretty")(options "")(descr ""))
```

---

## Example: Complete Workflow

```bash
# 1. Download STM32F405RGT6 from DigiKey (saves to Downloads)

# 2. Navigate to library
cd c:\Users\aaron\Documents\repositories\kicad-library

# 3. Import the component
python lib_manager.py "C:\Users\aaron\Downloads\STM32F405RGT6.zip"
# Select: 6 (Microcontrollers)

# 4. Commit and push
python lib_manager.py --commit --push
# Or just: git add . && git commit -m "Add STM32F405RGT6" && git push

# 5. In your project, add the symbol from lib_microcontrollers
```

---

## Zip File Contents (What to Expect)

Typical vendor zip structure:
```
STM32F405RGT6.zip
├── STM32F405RGT6.kicad_sym     # Schematic symbol
├── STM32F405RGT6.kicad_mod     # Footprint (or in subfolder)
├── STM32F405RGT6.step          # 3D model (optional)
└── datasheet.pdf               # Sometimes included
```

The tool automatically:
- Detects `.kicad_sym` → adds to symbol library
- Detects `.kicad_mod` → copies to footprint directory
- Detects `.step/.stp/.stl` → copies to 3d_models/

---

## Tips

1. **Verify footprint paths** - After import, open the symbol in KiCad and check that the footprint field points to the correct library (e.g., `lib_microcontrollers:STM32F405RGT6`)

2. **3D model paths** - You may need to update the 3D model path in the footprint to use `${KIPRJMOD}/lib/3d_models/...` or configure `KICAD_3DMODEL_DIR`

3. **Batch import** - Run the tool multiple times for different components, selecting the appropriate category each time

4. **Check quality** - Vendor models vary in quality. Verify pin assignments and footprint dimensions before using in production designs

---

## Troubleshooting

| Issue                  | Solution                                            |
| ---------------------- | --------------------------------------------------- |
| "No KiCad files found" | Zip may contain nested folders or non-KiCad formats |
| Symbol not appearing   | Restart KiCad or refresh library tables             |
| Footprint link broken  | Edit symbol → Footprint field → select from library |
| 3D model not showing   | Update footprint's 3D model path                    |
