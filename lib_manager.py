#!/usr/bin/env python
"""
KiCad Library Manager

A comprehensive script for managing KiCad component libraries with automated 
organization and git integration.

Features:
- Organized Libraries: 15 categorized libraries for different component types
- Zip File Processing: Automatically extracts and processes KiCad components
- Interactive Library Selection: User-friendly menu for selecting target library
- File Type Detection: Automatically categorizes symbols, footprints, and 3D models
- Duplicate Detection: Warns if a symbol already exists in the library
- 3D Model Path Fixing: Automatically updates footprint 3D model references
- Project Integration: Optional integration with project-specific library settings
- Git Integration: Automated commit and push functionality

Usage:
    python lib_manager.py <zip_file> [options]

Options:
    --library <name>    Target library (skip interactive menu)
    --add-to-project    Add libraries to project-specific settings
    --init-libraries    Initialize empty library files
    --commit            Commit changes with automated message
    --push              Push changes to remote repository
    --help              Show this help message

Author: aqsnyder (https://github.com/aqsnyder)
License: MIT
"""

import os
import sys
import zipfile
import shutil
import argparse
import subprocess
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set
import tempfile


class LibraryManager:
    """Main class for managing KiCad libraries"""
    
    def __init__(self, base_path: str = None):
        """Initialize the library manager with base path"""
        self.base_path = Path(base_path) if base_path else Path(__file__).parent
        self.lib_sym_path = self.base_path / "lib_sym"
        self.lib_fp_path = self.base_path / "lib_fp"
        self.models_3d_path = self.base_path / "3d_models"
        
        # Define library categories (15 categories)
        self.libraries = {
            "connectors": {
                "sym_file": "lib_connectors.kicad_sym",
                "fp_dir": "lib_connectors.pretty",
                "description": "Headers, sockets, terminals, USB, edge connectors"
            },
            "passives": {
                "sym_file": "lib_passives.kicad_sym",
                "fp_dir": "lib_passives.pretty",
                "description": "Resistors, capacitors, inductors, ferrite beads"
            },
            "discretes": {
                "sym_file": "lib_discretes.kicad_sym",
                "fp_dir": "lib_discretes.pretty",
                "description": "Diodes, transistors (BJT, MOSFET, JFET)"
            },
            "ics": {
                "sym_file": "lib_ics.kicad_sym",
                "fp_dir": "lib_ics.pretty",
                "description": "Op-amps, comparators, logic, analog switches, ADC/DAC"
            },
            "power": {
                "sym_file": "lib_power.kicad_sym",
                "fp_dir": "lib_power.pretty",
                "description": "LDOs, DC-DC, battery chargers, power switches, PD"
            },
            "microcontrollers": {
                "sym_file": "lib_microcontrollers.kicad_sym",
                "fp_dir": "lib_microcontrollers.pretty",
                "description": "MCUs, SoCs, FPGAs, processors"
            },
            "memory": {
                "sym_file": "lib_memory.kicad_sym",
                "fp_dir": "lib_memory.pretty",
                "description": "Flash, EEPROM, SRAM, SD card interfaces"
            },
            "rf": {
                "sym_file": "lib_rf.kicad_sym",
                "fp_dir": "lib_rf.pretty",
                "description": "RF modules, antennas, BLE, WiFi, LoRa"
            },
            "sensors": {
                "sym_file": "lib_sensors.kicad_sym",
                "fp_dir": "lib_sensors.pretty",
                "description": "Temperature, light, motion, pressure, IMU"
            },
            "optoelectronics": {
                "sym_file": "lib_optoelectronics.kicad_sym",
                "fp_dir": "lib_optoelectronics.pretty",
                "description": "LEDs, displays, optocouplers, photodiodes, IR"
            },
            "electromechanical": {
                "sym_file": "lib_electromechanical.kicad_sym",
                "fp_dir": "lib_electromechanical.pretty",
                "description": "Switches, relays, buttons, encoders, motors"
            },
            "protection": {
                "sym_file": "lib_protection.kicad_sym",
                "fp_dir": "lib_protection.pretty",
                "description": "TVS, ESD, fuses, PTC, MOVs"
            },
            "audio": {
                "sym_file": "lib_audio.kicad_sym",
                "fp_dir": "lib_audio.pretty",
                "description": "Speakers, buzzers, microphones, audio codecs"
            },
            "crystals_oscillators": {
                "sym_file": "lib_crystals_oscillators.kicad_sym",
                "fp_dir": "lib_crystals_oscillators.pretty",
                "description": "Crystals, oscillators, resonators, TCXO"
            },
            "mechanical": {
                "sym_file": "lib_mechanical.kicad_sym",
                "fp_dir": "lib_mechanical.pretty",
                "description": "Standoffs, heatsinks, mounting hardware, test points"
            }
        }
    
    def display_library_menu(self, component_name: str = None, datasheet: str = None, footprint: str = None) -> None:
        """Display the library selection menu"""
        print("\n" + "="*60)
        print("KiCad Library Manager - Library Selection")
        print("="*60)
        print("Select a library to add the component to:")
        print()
        
        for i, (key, lib_info) in enumerate(self.libraries.items(), 1):
            print(f"{i:2d}. {key.replace('_', ' ').title()}: {lib_info['description']}")
        
        print()
        print(" 0. Skip (don't add to any library)")
        print("="*60)
        
        if component_name:
            print(f"\nComponent: {component_name}")
            if datasheet:
                print(f"Datasheet: {datasheet}")
            if footprint:
                print(f"Footprint: {footprint}")
            print()
    
    def get_library_selection(self) -> Optional[str]:
        """Get library selection from user"""
        while True:
            try:
                choice = input(f"\nEnter your choice (0-{len(self.libraries)}): ").strip()
                choice_num = int(choice)
                
                if choice_num == 0:
                    return None
                elif 1 <= choice_num <= len(self.libraries):
                    return list(self.libraries.keys())[choice_num - 1]
                else:
                    print(f"Invalid choice. Please enter a number between 0 and {len(self.libraries)}")
            except ValueError:
                print("Invalid input. Please enter a number.")
            except KeyboardInterrupt:
                print("\n⚠ Operation cancelled by user.")
                return None
    
    def extract_zip_contents(self, zip_path: str) -> Tuple[Path, List[str]]:
        """Extract zip file and return temporary directory and file list"""
        temp_dir = Path(tempfile.mkdtemp())
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Get list of extracted files
            extracted_files = []
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    extracted_files.append(Path(root) / file)
            
            return temp_dir, extracted_files
        except zipfile.BadZipFile:
            print(f"Error: {zip_path} is not a valid zip file")
            sys.exit(1)
        except Exception as e:
            print(f"Error extracting zip file: {e}")
            sys.exit(1)
    
    def categorize_files(self, files: List[Path]) -> Dict[str, List[Path]]:
        """Categorize files by type (symbols, footprints, 3d_models)"""
        categorized = {
            'symbols': [],
            'footprints': [],
            '3d_models': []
        }
        
        for file_path in files:
            file_ext = file_path.suffix.lower()
            file_name = file_path.name.lower()
            
            if file_ext == '.kicad_sym':
                categorized['symbols'].append(file_path)
            elif file_ext == '.kicad_mod':
                categorized['footprints'].append(file_path)
            elif file_ext in ['.step', '.stp', '.stl', '.3d'] or '3d' in file_name:
                categorized['3d_models'].append(file_path)
        
        return categorized
    
    def get_existing_symbols(self, library_key: str) -> Set[str]:
        """Get set of symbol names that already exist in a library"""
        existing_symbols = set()
        target_sym_file = self.lib_sym_path / self.libraries[library_key]['sym_file']
        
        if target_sym_file.exists():
            try:
                with open(target_sym_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                # Find all symbol names using regex
                matches = re.findall(r'\(symbol "([^"]+)"', content)
                # Filter out sub-symbols (contain underscore followed by number at end)
                for match in matches:
                    if not re.match(r'.+_\d+_\d+$', match):
                        existing_symbols.add(match)
            except Exception:
                pass
        
        return existing_symbols
    
    def extract_symbol_names(self, symbol_content: str) -> List[str]:
        """Extract symbol names from symbol file content"""
        names = []
        matches = re.findall(r'\(symbol "([^"]+)"', symbol_content)
        for match in matches:
            # Skip sub-symbols (e.g., "PartName_1_1")
            if not re.match(r'.+_\d+_\d+$', match):
                names.append(match)
        return names
    
    def add_symbol_to_library(self, symbol_file: Path, library_key: str) -> bool:
        """Add symbol to the specified library with duplicate detection"""
        try:
            target_sym_file = self.lib_sym_path / self.libraries[library_key]['sym_file']
            
            # Read the symbol file content
            with open(symbol_file, 'r', encoding='utf-8') as f:
                symbol_content = f.read().strip()
            
            # Check for duplicates
            existing_symbols = self.get_existing_symbols(library_key)
            new_symbol_names = self.extract_symbol_names(symbol_content)
            
            duplicates = [name for name in new_symbol_names if name in existing_symbols]
            if duplicates:
                print(f"⚠ Symbol(s) already exist in {library_key}: {', '.join(duplicates)}")
                while True:
                    choice = input("  Overwrite? (y/n): ").strip().lower()
                    if choice in ['n', 'no']:
                        print(f"  - Skipped {symbol_file.name}")
                        return True
                    elif choice in ['y', 'yes']:
                        break
                    else:
                        print("  Please enter 'y' or 'n'")
            
            # Extract symbols
            symbols_to_add = ""
            
            if symbol_content.startswith('(kicad_symbol_lib'):
                first_paren = symbol_content.find('(symbol "')
                if first_paren == -1:
                    return True
                
                last_paren = symbol_content.rfind(')')
                if last_paren == -1:
                    return True
                
                symbols_to_add = symbol_content[first_paren:last_paren]
            else:
                symbols_to_add = symbol_content
            
            # Read existing library content
            existing_content = ""
            if target_sym_file.exists():
                with open(target_sym_file, 'r', encoding='utf-8') as f:
                    existing_content = f.read().strip()
            
            # Prepare the updated library content
            if existing_content and existing_content != '(kicad_symbol_lib (version 20211014) (generator kicad_symbol_editor)\n)':
                if existing_content.endswith(')'):
                    content_without_close = existing_content[:-1]
                    updated_content = f"{content_without_close}\n{symbols_to_add}\n)"
                else:
                    updated_content = f"{existing_content}\n{symbols_to_add}"
            else:
                updated_content = f"""(kicad_symbol_lib (version 20211014) (generator kicad_symbol_editor)
{symbols_to_add}
)"""
            
            # Write the updated content
            with open(target_sym_file, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            print(f"✓ Added symbol(s) from {symbol_file.name} to {library_key}")
            return True
            
        except Exception as e:
            print(f"✗ Error adding symbol {symbol_file.name}: {e}")
            return False
    
    def update_footprint_3d_path(self, footprint_file: Path) -> None:
        """Update 3D model path in footprint to use library's 3d_models folder"""
        try:
            with open(footprint_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find and update 3D model paths
            # Pattern: (model "path/to/model.step"
            def replace_model_path(match):
                original_path = match.group(1)
                model_name = Path(original_path).name
                # Use ${KIPRJMOD}/lib/3d_models/ or relative path
                new_path = f"${{KICAD_3DMODEL_DIR}}/{model_name}"
                return f'(model "{new_path}"'
            
            updated_content = re.sub(
                r'\(model "([^"]+)"',
                replace_model_path,
                content
            )
            
            if updated_content != content:
                with open(footprint_file, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                print(f"  → Updated 3D model path in {footprint_file.name}")
                
        except Exception as e:
            # Non-fatal error, just skip
            pass
    
    def add_footprint_to_library(self, footprint_file: Path, library_key: str) -> bool:
        """Add footprint to the specified library"""
        try:
            target_fp_dir = self.lib_fp_path / self.libraries[library_key]['fp_dir']
            target_fp_dir.mkdir(parents=True, exist_ok=True)
            
            target_file = target_fp_dir / footprint_file.name
            
            # Check for duplicate
            if target_file.exists():
                print(f"⚠ Footprint already exists: {footprint_file.name}")
                while True:
                    choice = input("  Overwrite? (y/n): ").strip().lower()
                    if choice in ['n', 'no']:
                        print(f"  - Skipped {footprint_file.name}")
                        return True
                    elif choice in ['y', 'yes']:
                        break
                    else:
                        print("  Please enter 'y' or 'n'")
            
            shutil.copy2(footprint_file, target_file)
            
            # Update 3D model path in the copied footprint
            self.update_footprint_3d_path(target_file)
            
            print(f"✓ Added footprint {footprint_file.name} to {library_key}")
            return True
            
        except Exception as e:
            print(f"✗ Error adding footprint {footprint_file.name}: {e}")
            return False
    
    def add_3d_model(self, model_file: Path) -> bool:
        """Add 3D model to the 3d_models directory"""
        try:
            target_file = self.models_3d_path / model_file.name
            shutil.copy2(model_file, target_file)
            
            print(f"✓ Added 3D model {model_file.name}")
            return True
            
        except Exception as e:
            print(f"✗ Error adding 3D model {model_file.name}: {e}")
            return False
    
    def display_project_library_menu(self) -> None:
        """Display the project library selection menu"""
        print("\n" + "="*60)
        print("Project Library Integration")
        print("="*60)
        print("Select libraries to add to project settings:")
        print()
        
        for i, (key, lib_info) in enumerate(self.libraries.items(), 1):
            print(f"{i:2d}. {key.replace('_', ' ').title()}: {lib_info['description']}")
        
        print()
        print(" 0. Add all libraries")
        print("="*60)
    
    def get_project_library_selection(self) -> List[str]:
        """Get project library selection from user"""
        while True:
            try:
                choice = input(f"\nEnter your choice (0-{len(self.libraries)}, comma-separated for multiple): ").strip()
                
                if choice == "0":
                    return list(self.libraries.keys())
                
                choices = [c.strip() for c in choice.split(',')]
                valid_choices = []
                
                for choice_str in choices:
                    choice_num = int(choice_str)
                    if 1 <= choice_num <= len(self.libraries):
                        valid_choices.append(list(self.libraries.keys())[choice_num - 1])
                    else:
                        print(f"Invalid choice: {choice_str}")
                        break
                else:
                    return valid_choices
                    
            except ValueError:
                print("Invalid input. Please enter numbers separated by commas.")
            except KeyboardInterrupt:
                print("\n⚠ Operation cancelled by user.")
                return []

    def update_project_settings(self) -> bool:
        """Update project-specific library settings"""
        try:
            parent_dir = self.base_path.parent
            sym_lib_table = parent_dir / "sym-lib-table"
            fp_lib_table = parent_dir / "fp-lib-table"
            
            if not sym_lib_table.exists() or not fp_lib_table.exists():
                print("⚠ Project library tables not found. Skipping project integration.")
                return False
            
            self.display_project_library_menu()
            selected_libraries = self.get_project_library_selection()
            
            if not selected_libraries:
                print("No libraries selected. Skipping project integration.")
                return False
            
            print(f"\nSelected libraries: {', '.join(selected_libraries)}")
            
            self._update_sym_lib_table(sym_lib_table, selected_libraries)
            self._update_fp_lib_table(fp_lib_table, selected_libraries)
            
            print("✓ Updated project library settings")
            return True
            
        except Exception as e:
            print(f"✗ Error updating project settings: {e}")
            return False
    
    def _update_sym_lib_table(self, sym_lib_table: Path, selected_libraries: List[str]) -> None:
        """Update symbol library table"""
        try:
            existing_entries = set()
            table_content = ""
            if sym_lib_table.exists():
                with open(sym_lib_table, 'r', encoding='utf-8') as f:
                    table_content = f.read()
                    for line in table_content.split('\n'):
                        if 'name=' in line and 'uri=' in line:
                            try:
                                name_start = line.find('name="') + 6
                                name_end = line.find('"', name_start)
                                if name_start > 5 and name_end > name_start:
                                    lib_name = line[name_start:name_end]
                                    existing_entries.add(lib_name)
                            except:
                                pass
            
            new_entries = []
            for lib_key in selected_libraries:
                lib_info = self.libraries[lib_key]
                lib_name = lib_info['sym_file'].replace('.kicad_sym', '')
                
                if lib_name not in existing_entries:
                    lib_path = self.lib_sym_path / lib_info['sym_file']
                    relative_path = os.path.relpath(lib_path, sym_lib_table.parent)
                    relative_path = relative_path.replace('\\', '/')
                    
                    entry = f'  (lib (name "{lib_name}")(type "KiCad")(uri "${{KIPRJMOD}}/{relative_path}")(options "")(descr ""))'
                    new_entries.append(entry)
                    print(f"    + Adding symbol library: {lib_name}")
                else:
                    print(f"    - Symbol library already exists: {lib_name}")
            
            if new_entries:
                if table_content.strip():
                    lines = table_content.split('\n')
                    last_closing_idx = -1
                    for i in range(len(lines) - 1, -1, -1):
                        if ')' in lines[i] and not lines[i].strip().startswith('('):
                            last_closing_idx = i
                            break
                    
                    if last_closing_idx >= 0:
                        lines.insert(last_closing_idx, '\n'.join(new_entries))
                    else:
                        lines.extend([''] + new_entries)
                    
                    with open(sym_lib_table, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(lines))
                else:
                    table_structure = f"""(sym_lib_table
  (version 7)
{chr(10).join(new_entries)}
)"""
                    with open(sym_lib_table, 'w', encoding='utf-8') as f:
                        f.write(table_structure)
                
                print(f"  ✓ Added {len(new_entries)} symbol libraries to project")
            else:
                print("  - No new symbol libraries to add")
                
        except Exception as e:
            print(f"  ✗ Error updating symbol library table: {e}")
    
    def _update_fp_lib_table(self, fp_lib_table: Path, selected_libraries: List[str]) -> None:
        """Update footprint library table"""
        try:
            existing_entries = set()
            table_content = ""
            if fp_lib_table.exists():
                with open(fp_lib_table, 'r', encoding='utf-8') as f:
                    table_content = f.read()
                    for line in table_content.split('\n'):
                        if 'name=' in line and 'uri=' in line:
                            try:
                                name_start = line.find('name="') + 6
                                name_end = line.find('"', name_start)
                                if name_start > 5 and name_end > name_start:
                                    lib_name = line[name_start:name_end]
                                    existing_entries.add(lib_name)
                            except:
                                pass
            
            new_entries = []
            for lib_key in selected_libraries:
                lib_info = self.libraries[lib_key]
                lib_name = lib_info['fp_dir'].replace('.pretty', '')
                
                if lib_name not in existing_entries:
                    lib_path = self.lib_fp_path / lib_info['fp_dir']
                    relative_path = os.path.relpath(lib_path, fp_lib_table.parent)
                    relative_path = relative_path.replace('\\', '/')
                    
                    entry = f'  (lib (name "{lib_name}")(type "KiCad")(uri "${{KIPRJMOD}}/{relative_path}")(options "")(descr ""))'
                    new_entries.append(entry)
                    print(f"    + Adding footprint library: {lib_name}")
                else:
                    print(f"    - Footprint library already exists: {lib_name}")
            
            if new_entries:
                if table_content.strip():
                    lines = table_content.split('\n')
                    last_closing_idx = -1
                    for i in range(len(lines) - 1, -1, -1):
                        if ')' in lines[i] and not lines[i].strip().startswith('('):
                            last_closing_idx = i
                            break
                    
                    if last_closing_idx >= 0:
                        lines.insert(last_closing_idx, '\n'.join(new_entries))
                    else:
                        lines.extend([''] + new_entries)
                    
                    with open(fp_lib_table, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(lines))
                else:
                    table_structure = f"""(fp_lib_table
  (version 7)
{chr(10).join(new_entries)}
)"""
                    with open(fp_lib_table, 'w', encoding='utf-8') as f:
                        f.write(table_structure)
                
                print(f"  ✓ Added {len(new_entries)} footprint libraries to project")
            else:
                print("  - No new footprint libraries to add")
                
        except Exception as e:
            print(f"  ✗ Error updating footprint library table: {e}")
    
    def commit_changes(self, zip_filename: str) -> bool:
        """Commit changes with automated message"""
        try:
            subprocess.run(['git', 'add', '.'], cwd=self.base_path, check=True)
            commit_msg = f"Add components from {zip_filename}"
            subprocess.run(['git', 'commit', '-m', commit_msg], cwd=self.base_path, check=True)
            print(f"✓ Committed changes: {commit_msg}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ Error committing changes: {e}")
            return False
        except FileNotFoundError:
            print("✗ Git not found. Please ensure git is installed.")
            return False
    
    def push_changes(self) -> bool:
        """Push changes to remote repository"""
        try:
            subprocess.run(['git', 'push'], cwd=self.base_path, check=True)
            print("✓ Pushed changes to remote repository")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ Error pushing changes: {e}")
            return False
        except FileNotFoundError:
            print("✗ Git not found.")
            return False
    
    def initialize_libraries(self) -> bool:
        """Initialize empty library files if they don't exist"""
        try:
            print("Initializing library files...")
            
            # Create directories if needed
            self.lib_sym_path.mkdir(parents=True, exist_ok=True)
            self.lib_fp_path.mkdir(parents=True, exist_ok=True)
            self.models_3d_path.mkdir(parents=True, exist_ok=True)
            
            # Initialize symbol libraries
            for lib_key, lib_info in self.libraries.items():
                sym_file = self.lib_sym_path / lib_info['sym_file']
                if not sym_file.exists():
                    empty_lib_content = """(kicad_symbol_lib (version 20211014) (generator kicad_symbol_editor)
)"""
                    with open(sym_file, 'w', encoding='utf-8') as f:
                        f.write(empty_lib_content)
                    print(f"  ✓ Created symbol library: {lib_info['sym_file']}")
                else:
                    print(f"  - Symbol library already exists: {lib_info['sym_file']}")
            
            # Initialize footprint library directories
            for lib_key, lib_info in self.libraries.items():
                fp_dir = self.lib_fp_path / lib_info['fp_dir']
                if not fp_dir.exists():
                    fp_dir.mkdir(parents=True, exist_ok=True)
                    print(f"  ✓ Created footprint directory: {lib_info['fp_dir']}")
                else:
                    print(f"  - Footprint directory already exists: {lib_info['fp_dir']}")
            
            print("✓ Library initialization complete")
            return True
            
        except Exception as e:
            print(f"✗ Error initializing libraries: {e}")
            return False
    
    def ask_delete_zip_file(self, zip_path: str) -> None:
        """Ask user if they want to delete the zip file after processing"""
        try:
            zip_file = Path(zip_path)
            if not zip_file.exists():
                return
            
            print(f"\n" + "="*60)
            print("Cleanup")
            print("="*60)
            print(f"Zip file: {zip_file.name}")
            
            while True:
                try:
                    choice = input("Delete the zip file? (y/n): ").strip().lower()
                    if choice in ['y', 'yes']:
                        zip_file.unlink()
                        print(f"✓ Deleted {zip_file.name}")
                        break
                    elif choice in ['n', 'no']:
                        print(f"✓ Kept {zip_file.name}")
                        break
                    else:
                        print("Please enter 'y' or 'n'")
                except KeyboardInterrupt:
                    print(f"\n✓ Kept {zip_file.name}")
                    break
                    
        except Exception as e:
            print(f"✗ Error handling zip file deletion: {e}")
    
    def extract_symbol_info(self, symbol_content: str) -> Dict[str, str]:
        """Extract symbol information including datasheet and footprint"""
        info = {
            'name': '',
            'datasheet': '',
            'footprint': '',
            'content': symbol_content
        }
        
        lines = symbol_content.split('\n')
        for line in lines:
            if line.strip().startswith('(symbol "'):
                name_start = line.find('"') + 1
                name_end = line.find('"', name_start)
                if name_start > 0 and name_end > name_start:
                    info['name'] = line[name_start:name_end]
            
            elif 'property "Datasheet"' in line and 'http' in line:
                url_start = line.find('http')
                if url_start != -1:
                    url_end = line.find('"', url_start)
                    if url_end == -1:
                        url_end = line.find(')', url_start)
                    if url_end != -1:
                        info['datasheet'] = line[url_start:url_end]
            
            elif 'property "Footprint"' in line:
                quotes = [i for i, c in enumerate(line) if c == '"']
                if len(quotes) >= 4:
                    info['footprint'] = line[quotes[2]+1:quotes[3]]
        
        return info
    
    def process_zip_file(self, zip_path: str, add_to_project: bool = False, 
                         commit: bool = False, push: bool = False,
                         library: str = None) -> bool:
        """Main method to process a zip file"""
        print(f"\nProcessing: {zip_path}")
        
        # Extract zip contents
        temp_dir, files = self.extract_zip_contents(zip_path)
        
        try:
            # Categorize files
            categorized = self.categorize_files(files)
            
            print(f"\nFound:")
            print(f"  - {len(categorized['symbols'])} symbol file(s)")
            print(f"  - {len(categorized['footprints'])} footprint file(s)")
            print(f"  - {len(categorized['3d_models'])} 3D model file(s)")
            
            if not any(categorized.values()):
                print("\n⚠ No KiCad files found in zip")
                return False
            
            # Get library selection (from CLI or interactively)
            if library:
                if library not in self.libraries:
                    print(f"Error: Unknown library '{library}'")
                    print(f"Valid libraries: {', '.join(self.libraries.keys())}")
                    return False
                selected_library = library
                print(f"\nUsing library: {selected_library}")
            else:
                self.display_library_menu()
                selected_library = self.get_library_selection()
                
                if selected_library is None:
                    print("No library selected. Operation cancelled.")
                    return False
            
            print(f"\nAdding to library: {selected_library}")
            
            # Process symbols
            for symbol_file in categorized['symbols']:
                self.add_symbol_to_library(symbol_file, selected_library)
            
            # Process footprints
            for footprint_file in categorized['footprints']:
                self.add_footprint_to_library(footprint_file, selected_library)
            
            # Process 3D models
            for model_file in categorized['3d_models']:
                self.add_3d_model(model_file)
            
            # Update project settings if requested
            if add_to_project:
                self.update_project_settings()
            
            # Git operations
            if commit:
                self.commit_changes(Path(zip_path).name)
            if push:
                self.push_changes()
            
            # Cleanup
            self.ask_delete_zip_file(zip_path)
            
            print("\n✓ Processing complete!")
            return True
            
        finally:
            # Clean up temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='KiCad Library Manager - Organize and manage component libraries',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python lib_manager.py component.zip              Process a zip file
  python lib_manager.py --init-libraries           Initialize empty libraries
  python lib_manager.py component.zip --commit     Process and commit changes
  python lib_manager.py --add-to-project           Add libraries to project settings

Library Categories:
  1. Connectors         8. RF                    15. Mechanical
  2. Passives           9. Sensors
  3. Discretes         10. Optoelectronics
  4. ICs               11. Electromechanical
  5. Power             12. Protection
  6. Microcontrollers  13. Audio
  7. Memory            14. Crystals/Oscillators
"""
    )
    
    parser.add_argument('zip_file', nargs='?', help='Path to component zip file')
    parser.add_argument('--library', '-l', type=str,
                        choices=['connectors', 'passives', 'discretes', 'ics', 'power',
                                'microcontrollers', 'memory', 'rf', 'sensors', 
                                'optoelectronics', 'electromechanical', 'protection',
                                'audio', 'crystals_oscillators', 'mechanical'],
                        help='Target library (skip interactive menu)')
    parser.add_argument('--add-to-project', action='store_true', 
                        help='Add libraries to project-specific settings')
    parser.add_argument('--init-libraries', action='store_true',
                        help='Initialize empty library files')
    parser.add_argument('--commit', action='store_true',
                        help='Commit changes with automated message')
    parser.add_argument('--push', action='store_true',
                        help='Push changes to remote repository')
    
    args = parser.parse_args()
    
    manager = LibraryManager()
    
    # Initialize libraries if requested
    if args.init_libraries:
        manager.initialize_libraries()
        if args.commit:
            manager.commit_changes("library initialization")
        if args.push:
            manager.push_changes()
        return
    
    # Add to project only (no zip file)
    if args.add_to_project and not args.zip_file:
        manager.update_project_settings()
        return
    
    # Process zip file
    if args.zip_file:
        if not Path(args.zip_file).exists():
            print(f"Error: File not found: {args.zip_file}")
            sys.exit(1)
        
        manager.process_zip_file(
            args.zip_file,
            add_to_project=args.add_to_project,
            commit=args.commit,
            push=args.push,
            library=args.library
        )
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
