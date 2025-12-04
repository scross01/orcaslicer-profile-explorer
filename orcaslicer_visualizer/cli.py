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
@click.option('--compare', '-c', default=None, help='Compare settings for a specific profile and its inheritance chain')
@click.option('--user', '-u', is_flag=True, help='Only show branches that include user-defined profiles')
def main(target: Optional[str], output: str, input_dir: str, compare: Optional[str], user: bool):
    """OrcaSlicer Filament Profile Visualizer"""

    # Check if input directory exists
    if not os.path.exists(input_dir):
        click.echo(f"Error: Input directory {input_dir} does not exist")
        return

    # Create analyzer
    analyzer = ProfileAnalyzer(input_dir)

    # If compare option is used, show parameter comparison table
    if compare:
        table = analyzer.format_settings_comparison_table(compare)
        click.echo(table)
        return

    # Otherwise, generate the graph visualization
    try:
        visualizer = GraphVisualizer(analyzer)
        dot = visualizer.generate_graph(target, user_only=user)
        
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