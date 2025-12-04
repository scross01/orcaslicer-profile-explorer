import click
import os
from pathlib import Path
from typing import Optional

from .profile_analyzer import ProfileAnalyzer
from .visualizer import GraphVisualizer


@click.command()
@click.option('--target', '-t', default=None, help='Target profile to visualize (shows parents and children)')
@click.option('--output', '-o', default='orcaslicer_graph.dot', help='Output file for the graphviz dot file')
@click.option('--input-dir', '-i', default='OrcaSlicer', help='Input directory containing OrcaSlicer profiles')
@click.option('--show-profile', '-s', default=None, help='Show settings for a specific profile and its inheritance chain')
@click.option('--show-effective-profile', default=None, multiple=True, help='Show effective settings for specific profiles with all values inherited from parents. Can be used multiple times to compare multiple profiles of the same type.')
@click.option('--user', '-u', is_flag=True, help='Only show branches that include user-defined profiles')
@click.option('--filament', '-f', 'profile_types', flag_value='filament', help='Show only filament profiles')
@click.option('--machine', '-m', 'profile_types', flag_value='machine', help='Show only machine profiles')
@click.option('--process', '-p', 'profile_types', flag_value='process', help='Show only process profiles')
@click.option('--group', is_flag=True, help='Group nodes by directory hierarchy')
@click.option('--simple', is_flag=True, help='Show only profile names without additional attributes')
def main(target: Optional[str], output: str, input_dir: str, show_profile: Optional[str], show_effective_profile: tuple, user: bool, profile_types: str, group: bool, simple: bool):
    """OrcaSlicer Profile Visualizer - supports filament, machine, and process profiles"""

    # Check if input directory exists
    if not os.path.exists(input_dir):
        click.echo(f"Error: Input directory {input_dir} does not exist")
        return

    # Determine which profile types to load
    profile_type_list = [profile_types] if profile_types else ["filament", "machine", "process"]

    # Create analyzer
    analyzer = ProfileAnalyzer(input_dir)
    # Clear the default loading and load only requested profile types
    analyzer.profiles = {}
    analyzer.load_profiles_by_type(profile_type_list)

    # If show-effective-profile option is used, show effective settings table for multiple profiles
    if show_effective_profile:  # nargs creates an empty tuple when not used, which is falsy
        table = analyzer.get_effective_profile_settings_multiple(show_effective_profile)
        click.echo(table)
        return

    # If show-profile option is used, show parameter comparison table
    if show_profile:
        table = analyzer.format_settings_comparison_table(show_profile)
        click.echo(table)
        return

    # Otherwise, generate the graph visualization
    try:
        visualizer = GraphVisualizer(analyzer)
        dot = visualizer.generate_graph(target, user_only=user, profile_types=profile_type_list, group=group, simple=simple)
        
        # Write to output file
        output_path = Path(output)
        if output_path.suffix != '.dot':
            # If no .dot extension, add it
            output_file = str(output_path) + '.dot'
        else:
            output_file = str(output_path)

        # Save the dot file - graphviz save() will handle the file creation properly
        dot.save(filename=output_file)

        # Print the actual file that was created
        actual_output_path = Path(output_file)
        click.echo(f"Graph saved to {actual_output_path}")
        click.echo(f"View the graph using: cat {actual_output_path}")
        click.echo(f"Or convert to image: dot -Tpng {actual_output_path} -o {actual_output_path.with_suffix('.png')}")
        
    except ValueError as e:
        click.echo(f"Error: {e}")


if __name__ == "__main__":
    main()