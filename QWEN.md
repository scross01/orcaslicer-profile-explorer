# OrcaSlicer Filament Profile Visualizer

## Project Overview

The `orcaslicer-filament-profile-visualizer` project is a Python command-line tool designed to analyze and visualize the inheritance relationships between OrcaSlicer profiles (filament, machine, and process). The tool reads OrcaSlicer's system and user profile files and creates a visual graph representation using Graphviz, showing how profiles inherit from each other in a directed graph.

The project supports:
- Generating graph visualizations of profile inheritance chains
- Comparing parameter settings across inheritance chains
- Grouping nodes by directory hierarchy
- Filtering profiles by type (filament, machine, process)
- Displaying profiles with different levels of detail (simple vs. detailed)
- Distinguishing between system and user-defined profiles with different visual styling

## Project Structure

```
orcaslicer-filament-profile-visualizer/
├── pyproject.toml            # Project dependencies and build config
├── README.md                 # Usage documentation
├── GOAL.md                   # Project goals and requirements
├── OrcaSlicer/               # Sample OrcaSlicer profile files
│   ├── system/               # System-provided profiles
│   └── user/                 # User-defined profiles
├── orcaslice_profile_explorer/    # Source code for the visualizer
│   ├── __init__.py
│   ├── cli.py                # Command-line interface
│   ├── profile_analyzer.py   # Profile loading and analysis
│   └── visualizer.py         # Graphviz visualization
└── QWEN.md                   # This file
```

## Dependencies

The project uses:
- `graphviz`: For generating graph visualizations
- `click`: For command-line interface
- Python 3.12+ with uv for package management

## Building and Running

### Setup
```bash
# Install dependencies
uv sync

# Run the visualizer
uv run orcaslicer-profile-explorer [OPTIONS]
```

### Commands

Generate a complete graph of all profiles:
```bash
uv run orcaslicer-profile-explorer
```

Visualize only filament profiles:
```bash
uv run orcaslicer-profile-explorer --filament
```

Visualize only machine profiles:
```bash
uv run orcaslicer-profile-explorer --machine
```

Visualize only process profiles:
```bash
uv run orcaslicer-profile-explorer --process
```

Show only profiles with thick borders indicating user-defined profiles:
```bash
uv run orcaslicer-profile-explorer --user
```

Show only profile names without additional attributes (simple view):
```bash
uv run orcaslicer-profile-explorer --simple
```

Group nodes by directory hierarchy:
```bash
uv run orcaslicer-profile-explorer --group
```

Compare settings for a specific profile across its inheritance chain:
```bash
uv run orcaslicer-profile-explorer --show-profile "Profile Name"
```

Show effective settings (with inherited values) for a profile:
```bash
uv run orcaslicer-profile-explorer --show-effective-profile "Profile Name"
```

Combine options:
```bash
uv run orcaslicer-profile-explorer --machine --user --simple --group
```

## Development Conventions

- Code is organized into modules: CLI, profile analysis, and visualization components
- Profile types are distinguished by color: blue for filament, green for machine, purple for process
- System vs user profiles are distinguished by border thickness and fill transparency
- Directory hierarchy grouping starts from 'system' and 'user' levels
- The code follows Python typing conventions
- Command-line interface uses Click decorators for option parsing
- File paths and directory names are normalized to handle special characters
- Profile type is inferred from JSON file data or directory structure when not explicitly defined

## Key Features

1. **Multi-type profile support**: Handles filament, machine, and process profiles
2. **Visual distinction**: Different colors and border thicknesses for profile types and sources
3. **Directory grouping**: Nested subgraphs organized by directory structure
4. **Inheritance visualization**: Shows parent-child relationships between profiles
5. **Effective settings**: Compares settings across inheritance chains with inherited values
6. **Simple mode**: Displays only profile names without additional attributes
7. **User filtering**: Shows only profiles that include user-defined profiles in their branches
8. **Path information**: Shows file location relative to input directory (unless using `--simple`)