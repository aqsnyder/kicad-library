# KiCad Component Library

A structured component library for KiCad with 15 categorized libraries and a Python management tool for easy component organization.

## Features

- **15 Organized Categories** - Components sorted by type for easy discovery
- **Library Manager Tool** - Process manufacturer zip files automatically
- **Submodule Support** - Use as a shared library across multiple projects
- **Git Integration** - Built-in commit and push functionality

## Library Categories

| #   | Library                    | Contents                                              |
| --- | -------------------------- | ----------------------------------------------------- |
| 1   | `lib_connectors`           | Headers, sockets, terminals, USB, edge connectors     |
| 2   | `lib_passives`             | Resistors, capacitors, inductors, ferrite beads       |
| 3   | `lib_discretes`            | Diodes, transistors (BJT, MOSFET, JFET)               |
| 4   | `lib_ics`                  | Op-amps, comparators, logic, analog switches, ADC/DAC |
| 5   | `lib_power`                | LDOs, DC-DC, battery chargers, power switches         |
| 6   | `lib_microcontrollers`     | MCUs, SoCs, FPGAs, processors                         |
| 7   | `lib_memory`               | Flash, EEPROM, SRAM, SD card interfaces               |
| 8   | `lib_rf`                   | RF modules, antennas, BLE, WiFi, LoRa                 |
| 9   | `lib_sensors`              | Temperature, light, motion, pressure, IMU             |
| 10  | `lib_optoelectronics`      | LEDs, displays, optocouplers, photodiodes             |
| 11  | `lib_electromechanical`    | Switches, relays, buttons, encoders                   |
| 12  | `lib_protection`           | TVS, ESD, fuses, PTC, MOVs                            |
| 13  | `lib_audio`                | Speakers, buzzers, microphones, codecs                |
| 14  | `lib_crystals_oscillators` | Crystals, oscillators, resonators, TCXO               |
| 15  | `lib_mechanical`           | Standoffs, heatsinks, test points                     |

## Quick Start

### Clone the Repository

```bash
git clone https://github.com/aqsnyder/kicad-library.git
```

### Initialize Libraries

```bash
cd kicad-library
python lib_manager.py --init-libraries
```

## Using as a Submodule

Add to your KiCad project for shared component management:

```bash
# In your project root
git submodule add https://github.com/aqsnyder/kicad-library.git lib
git submodule update --init --recursive
```

### Configure KiCad Libraries

1. Open your project in KiCad
2. Go to **Preferences → Manage Symbol Libraries**
3. Add project libraries with paths like:
   - `${KIPRJMOD}/lib/lib_sym/lib_connectors.kicad_sym`
4. Repeat for **Preferences → Manage Footprint Libraries**:
   - `${KIPRJMOD}/lib/lib_fp/lib_connectors.pretty`

### Update Submodule

```bash
git submodule update --remote
```

## Library Manager Tool

### Add Components from Zip File

```bash
python lib_manager.py component.zip
```

The tool will:
1. Extract the zip file
2. Show an interactive menu to select the target library
3. Add symbols to `.kicad_sym` files
4. Add footprints to `.pretty` directories
5. Copy 3D models to `3d_models/`

### Options

```bash
python lib_manager.py component.zip --commit       # Commit changes
python lib_manager.py component.zip --push         # Commit and push
python lib_manager.py --add-to-project             # Add libs to project tables
python lib_manager.py --init-libraries             # Create empty libraries
```

### Full Workflow

```bash
# Download a component from SamacSys, SnapEDA, or manufacturer
python lib_manager.py STM32F405.zip --commit --push
```

## Repository Structure

```
kicad-library/
├── lib_manager.py       # Management tool
├── lib_sym/             # Symbol libraries (.kicad_sym)
├── lib_fp/              # Footprint libraries (.pretty dirs)
├── 3d_models/           # 3D models (STEP/STL)
├── README.md
└── LICENSE
```

## Requirements

- Python 3.6+
- Git (for commit/push features)
- KiCad 6.0+ (for library compatibility)

## License

MIT License - see [LICENSE](LICENSE)

---

**Author:** [aqsnyder](https://github.com/aqsnyder)
