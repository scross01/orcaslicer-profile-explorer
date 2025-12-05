# OrcaSlicer Profile Explorer

A command-line tool to analyze and review the inheritance relationships and setting of OrcaSlicer filament, machine and process profiles, including showing how profiles inherit from each other in a directed graph format.

The `OrcaSlicer` settings directory contains system and user profile settings for different filaments settings and customizations. The blog post ["OrcaSlicer Profile Management: The Ultimate Guide"](https://www.obico.io/blog/orcaslicer-comprehensive-profile-management-guide/) by Kenneth Jiang provides an excellent overview of OrcaSlicer's profile management system.

> The underlying file structure and the inheritance model of profiles are often not intuitive, making it challenging to understand how settings are stored, linked, and affected by software updates or account interactions.

This utility aims to aid in unravelling some of that complexity. 

## Features

- **Heirarchy Graph Visualization**: Generate Graphviz .dot files showing inheritance relationships between filament, machine, and process profiles
- **View Parameter Inheritence**: View the settings across the inheritance chain in a table format
- **Compare Profiles**: Compare the effective parameters across multiple profiles
- **Flexible Filtering**: Visualize all profiles or focus on a specific profile's inheritance chain

## Installation

This project uses `uv` for package management. Install the dependencies with:

```bash
git clone https://github.com/scross01/orcaslicer-profile-explorer
cd orcaslicer-profile-explorer
uv sync
source .venv/bin/activate
```

## Usage

### Graph Visualization

The the graph generation createa a [Graphviz](https://graphviz.org/) .dot file that can be rendered to different display formats using the graphviz `dot` command. 

Generate a complete graph of all profiles:

```bash
uv run orcaslicer-profile-explorer
```

Generate a complete graph of all profiles, convert to pdf

```bash
uv run orcaslicer-profile-explorer && dot -Tpdf orcaslicer-graph.dot -o orcaslicer_graph.png
```

Generate a graph showing only filament profiles:

```bash
uv run orcaslicer-profile-explorer --filament
```

Generate a graph showing only machine profiles:

```bash
uv run orcaslicer-profile-explorer --machine
```

Generate a graph showing only process profiles:

```bash
uv run orcaslicer-profile-explorer --process
```

Visualize only the inheritance chain for a specific profile:

```bash
uv run orcaslicer-profile-explorer --target "Spool Fuel Generic PETG"
```

Only show branches that include user-defined profiles:

```bash
uv run orcaslicer-profile-explorer --user
```

Specify a custom output file:

```bash
uv run orcaslicer-profile-explorer --output my_graph.dot --target "Bambu PLA Basic @base"
```

Combine options to show user branches for a specific target profile:

```bash
uv run orcaslicer-profile-explorer --target "Spool Fuel Generic PETG" --user
```

Combine profile type selection with other options:

```bash
uv run orcaslicer-profile-explorer --machine --user --output machine_user_only.dot
```

Group nodes by directory hierarchy:

```bash
uv run orcaslicer-profile-explorer --group --output grouped_graph.dot
```

Combine grouping with other options:

```bash
uv run orcaslicer-profile-explorer --filament --group --output grouped_filament_graph.dot
```

Show profiles with only names (simple view):

```bash
uv run orcaslicer-profile-explorer --simple
```

Combine simple view with profile type selection:

```bash
uv run orcaslicer-profile-explorer --machine --simple
```

Combine simple view with grouping:

```bash
uv run orcaslicer-profile-explorer --process --simple --group
```

### Profile Parameter Comparison

Compare settings across the inheritance chain:

```bash
uv run orcaslicer-profile-explorer --show-profile "Spool Fuel Generic PETG"
```

This outputs a table showing how settings are defined across the inheritance chain, from base to specific profile.

Show effective settings for a profile (using inherited values where not set):

```bash
uv run orcaslicer-profile-explorer --show-effective-profile "Spool Fuel Generic PETG"
```

This outputs a table showing the effective settings for the profile, taking values from parent profiles where not explicitly set.

Compare effective settings for multiple profiles of the same type:

```bash
uv run orcaslicer-profile-explorer --show-effective-profile "HiPi.io Generic PLA" --show-effective-profile "HiPi.io Transparent PLA"
```

This outputs a table comparing the effective settings of multiple profiles of the same type (filament, machine, or process).

### Complete Command Options

```bash
Usage: orcaslicer-profile-explorer [OPTIONS]

  OrcaSlicer Profile Explorer - supports filament, machine, and process
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
  --simple              Show only profile names without additional attributes
  --help                Show this message and exit.
```

## Example Output

### Graph Visualization
The tool generates Graphviz .dot files that can be converted to images:

```bash
# Generate the dot file
uv run orcaslicer-profile-explorer --output graph.dot

# Convert to PNG image (requires graphviz installed)
dot -Tpng graph.dot -o graph.png
```

### Parameter Comparison Table
Example output showing settings inheritance from base to specific profile:

```
| Setting Name | fdm_filament_common | fdm_filament_pet | Creality Generic PETG | Spool Fuel Generic PETG |
| --- | --- | --- | --- | --- |
| filament_vendor | Generic | - | - | Spool Fuel |
| filament_density | 0 | 1.27 | - | - |
| hot_plate_temp | 60 | 80 | - | 70 |
| ... | ... | ... | ... | ... |
```

## Directory Structure

The tool expects OrcaSlicer profiles in teh standard location for the operating system:

| Operating System |	Default Settings Path |
| Windows	| C:\Users\<username>\AppData\Roaming\OrcaSlicer\ |
| macOS	| ~/Library/Application Support/OrcaSlicer/ |
| Linux	| ~/.config/OrcaSlicer/ | 

You can specify a different input directory with the `--input-dir` option.
