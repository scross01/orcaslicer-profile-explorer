# OrcaSlicer Filament Profile Visualizer

A command-line tool to analyze and visualize the inheritance relationships between OrcaSlicer filament profiles, showing how profiles inherit from each other in a directed graph format.

## Features

- **Graph Visualization**: Generate Graphviz .dot files showing inheritance relationships between filament profiles
- **Parameter Comparison**: Compare settings across the inheritance chain in a table format
- **Flexible Filtering**: Visualize all profiles or focus on a specific profile's inheritance chain

## Installation

This project uses `uv` for package management. Install the dependencies with:

```bash
uv sync
```

## Usage

### Graph Visualization

Generate a complete graph of all filament profiles:

```bash
uv run orcaslicer-visualizer
```

Visualize only the inheritance chain for a specific profile:

```bash
uv run orcaslicer-visualizer --target "Spool Fuel Generic PETG"
```

Specify a custom output file:

```bash
uv run orcaslicer-visualizer --output my_graph.dot --target "Bambu PLA Basic @base"
```

### Parameter Comparison

Compare settings across the inheritance chain:

```bash
uv run orcaslicer-visualizer --compare "Spool Fuel Generic PETG"
```

This outputs a table showing how settings are defined across the inheritance chain, from base to specific profile.

### Complete Command Options

```bash
Usage: orcaslicer-visualizer [OPTIONS]

  OrcaSlicer Filament Profile Visualizer

Options:
  -t, --target TEXT     Target profile to visualize (shows parents and children)
  -o, --output TEXT     Output file for the graphviz dot file
  -i, --input-dir TEXT  Input directory containing OrcaSlicer profiles (default: OrcaSlicer)
  -c, --compare TEXT    Compare settings for a specific profile and its inheritance chain
  --help                Show this message and exit.
```

## Example Output

### Graph Visualization
The tool generates Graphviz .dot files that can be converted to images:

```bash
# Generate the dot file
uv run orcaslicer-visualizer --output graph.dot

# Convert to PNG image (requires graphviz installed)
dot -Tpng graph.dot -o graph.png
```

### Parameter Comparison Table
Example output showing settings inheritance from base to specific profile:

```
| Setting Name | fdm_filament_common | fdm_filament_pet | Creality Generic PETG | Spool Fuel Generic PETG |
| --- | --- | --- | --- | --- |
| filament_vendor | Generic | N/A | N/A | Spool Fuel |
| filament_density | 0 | 1.27 | N/A | N/A |
| hot_plate_temp | 60 | 80 | N/A | 70 |
| ...
```

## Directory Structure

The tool expects OrcaSlicer profiles to be organized as follows:

```
OrcaSlicer/
├── system/
│   ├── BBL/
│   ├── Creality/
│   └── ...
└── user/
    └── default/
        └── filament/
```

You can specify a different input directory with the `--input-dir` option.

## Development

To add the tool to your Python environment:

```bash
uv sync
uv run pip install -e .
```

The package entry point is `orcaslicer-visualizer` which can be run after installation.