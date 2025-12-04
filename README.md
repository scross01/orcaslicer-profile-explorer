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

Generate a complete graph of all profiles:

```bash
uv run orcaslicer-visualizer
```

Show settings comparison for a profile and its inheritance chain:

```bash
uv run orcaslicer-visualizer --show-profile "Spool Fuel Generic PETG"
```

Generate a graph showing only filament profiles:

```bash
uv run orcaslicer-visualizer --filament
```

Generate a graph showing only machine profiles:

```bash
uv run orcaslicer-visualizer --machine
```

Generate a graph showing only process profiles:

```bash
uv run orcaslicer-visualizer --process
```

Visualize only the inheritance chain for a specific profile:

```bash
uv run orcaslicer-visualizer --target "Spool Fuel Generic PETG"
```

Only show branches that include user-defined profiles:

```bash
uv run orcaslicer-visualizer --user
```

Specify a custom output file:

```bash
uv run orcaslicer-visualizer --output my_graph.dot --target "Bambu PLA Basic @base"
```

Combine options to show user branches for a specific target profile:

```bash
uv run orcaslicer-visualizer --target "Spool Fuel Generic PETG" --user
```

Combine profile type selection with other options:

```bash
uv run orcaslicer-visualizer --machine --user --output machine_user_only.dot
```

Group nodes by directory hierarchy:

```bash
uv run orcaslicer-visualizer --group --output grouped_graph.dot
```

Combine grouping with other options:

```bash
uv run orcaslicer-visualizer --filament --group --output grouped_filament_graph.dot
```
```

### Parameter Comparison

Compare settings across the inheritance chain:

```bash
uv run orcaslicer-visualizer --show-profile "Spool Fuel Generic PETG"
```

This outputs a table showing how settings are defined across the inheritance chain, from base to specific profile.

Show effective settings for a profile (using inherited values where not set):

```bash
uv run orcaslicer-visualizer --show-effective-profile "Spool Fuel Generic PETG"
```

This outputs a table showing the effective settings for the profile, taking values from parent profiles where not explicitly set.

### Complete Command Options

```bash
Usage: orcaslicer-visualizer [OPTIONS]

  OrcaSlicer Profile Visualizer - supports filament, machine, and process
  profiles

Options:
  -t, --target TEXT     Target profile to visualize (shows parents and children)
  -o, --output TEXT     Output file for the graphviz dot file
  -i, --input-dir TEXT  Input directory containing OrcaSlicer profiles (default: OrcaSlicer)
  -s, --show-profile TEXT          Show settings for a specific profile and its inheritance chain
  --show-effective-profile TEXT    Show effective settings for a specific profile with all values inherited from parents
  -u, --user                       Only show branches that include user-defined profiles
  -f, --filament        Show only filament profiles
  -m, --machine         Show only machine profiles
  -p, --process         Show only process profiles
  --group               Group nodes by directory hierarchy
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