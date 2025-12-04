import graphviz
import os
from typing import List, Optional
from .profile_analyzer import Profile, ProfileAnalyzer


class GraphVisualizer:
    def __init__(self, analyzer: ProfileAnalyzer):
        self.analyzer = analyzer
    
    def generate_graph(self, target_profile: Optional[str] = None, user_only: bool = False, profile_types: List[str] = ["filament"], group: bool = False, input_dir: str = "OrcaSlicer") -> graphviz.Digraph:
        """Generate a Graphviz digraph for the profile inheritance"""
        # Store input_dir for use in _add_profile_node
        self.input_dir = input_dir
        if group:
            dot = graphviz.Digraph(comment='OrcaSlicer Profile Inheritance')
            dot.attr(rankdir='LR', size='12,10')
            dot.attr('node', shape='box', style='rounded,filled', fontname='Arial')
        else:
            dot = graphviz.Digraph(comment='OrcaSlicer Profile Inheritance')
            dot.attr(rankdir='LR', size='12,10')
            dot.attr('node', shape='box', style='rounded,filled', fontname='Arial')

        visited_profiles: set = set()

        if user_only:
            # Only show branches that include user-defined profiles
            relevant_profiles = self.analyzer.get_branches_with_user_profiles(profile_types)
            profiles_to_process = [p for p in relevant_profiles if p.profile_type in profile_types]
        elif target_profile:
            # If a target profile is specified, only visualize the inheritance chain
            # and descendants for that profile
            target_profile_obj = self.analyzer.get_profile(target_profile)
            if not target_profile_obj:
                raise ValueError(f"Profile '{target_profile}' not found")

            # Only process if the target profile is of a requested type
            if target_profile_obj.profile_type not in profile_types:
                # Find if target profile has any ancestors/descendants of the requested type
                # For now, just add it if it's in the chain even if it's not the right type
                pass

            # Get the full chain that includes the target profile
            target_chain = self.analyzer.get_profile_inheritance_chain(target_profile)
            target_descendants = self.analyzer.get_all_descendants(target_profile)
            profiles_to_process = [p for p in (target_chain + target_descendants) if p.profile_type in profile_types]

            # Add the target profile even if it's not the right type to maintain inheritance
            if target_profile_obj.profile_type not in profile_types:
                profiles_to_process.append(target_profile_obj)
        else:
            # If no target is specified, visualize profiles of the specified types
            all_profiles = self.analyzer.get_all_profiles()
            profiles_to_process = [p for p in all_profiles if p.profile_type in profile_types]

        # Create profiles mapping by directory - normalize paths to be relative from the base
        directory_profiles = {}
        for profile in profiles_to_process:
            # Extract directory path from file path
            full_path_parts = profile.file_path.split('/')
            # Assuming the base path is up to the first major directory after OrcaSlicer
            # Find where OrcaSlicer is in the path and take everything after
            base_index = -1
            for idx, part in enumerate(full_path_parts):
                if part == 'OrcaSlicer':
                    base_index = idx
                    break

            # Use the path starting after OrcaSlicer
            if base_index != -1:
                directory_parts = full_path_parts[base_index:]
                directory_path = '/' + '/'.join(directory_parts[:-1])  # Exclude the filename
            else:
                # Fallback: just remove the file name
                directory_path = '/'.join(profile.file_path.split('/')[:-1])

            if directory_path not in directory_profiles:
                directory_profiles[directory_path] = []
            directory_profiles[directory_path].append(profile)

        if group:
            # Build the directory hierarchy tree
            root = {}
            for directory_path in directory_profiles.keys():
                path_parts = [part for part in directory_path.split('/') if part]
                current = root
                for part in path_parts:
                    if part not in current:
                        current[part] = {}
                    current = current[part]

            # Recursive function to create nested subgraphs
            def create_nested_subgraphs_recursive(hierarchy_node, path_list, parent_graph):
                current_path = '/' + '/'.join(path_list) if path_list else '/'

                # Process each directory at this level
                for dir_name, sub_hierarchy in hierarchy_node.items():
                    child_path = current_path + '/' + dir_name if path_list else '/' + dir_name if dir_name else '/'

                    # Create subgraph for this directory
                    subgraph_name = child_path.replace('/', '_').replace('-', '_').replace(' ', '_').replace('(', '').replace(')', '')
                    subgraph = graphviz.Digraph(f'cluster_{subgraph_name}')
                    subgraph.attr(label=dir_name)
                    subgraph.attr(style='bold', color='lightgrey', penwidth='2')

                    # Add profiles that belong to this directory to the subgraph
                    if child_path in directory_profiles:
                        for profile in directory_profiles[child_path]:
                            if profile.profile_type in profile_types:
                                self._add_profile_node(subgraph, profile, group=True)

                    # Recursively process subdirectories within this subgraph
                    if sub_hierarchy:  # Only recurse if there are subdirectories
                        create_nested_subgraphs_recursive(sub_hierarchy, path_list + [dir_name], subgraph)

                    # Add this subgraph to the parent graph
                    parent_graph.subgraph(subgraph)

            # Create nested subgraphs structure
            create_nested_subgraphs_recursive(root, [], dot)

            # Add inheritance relationships between profiles (across subgraphs)
            for profile in profiles_to_process:
                if profile.profile_type in profile_types and profile.inherits:
                    parent_profile = self.analyzer.get_profile(profile.inherits)
                    if parent_profile and parent_profile.profile_type in profile_types and parent_profile in profiles_to_process:
                        self._add_inheritance_edge(dot, profile.inherits, profile.name)
        else:
            # Add profiles without grouping
            for profile in profiles_to_process:
                if profile.profile_type in profile_types:
                    self._add_profile_node(dot, profile, group=group)

            # Add inheritance relationships for all processed profiles
            for profile in profiles_to_process:
                if profile.profile_type in profile_types and profile.inherits:
                    parent_profile = self.analyzer.get_profile(profile.inherits)
                    if parent_profile and parent_profile.profile_type in profile_types and parent_profile in profiles_to_process:
                        self._add_inheritance_edge(dot, profile.inherits, profile.name)

        return dot
    
    def _add_profile_node(self, dot: graphviz.Digraph, profile: Profile, group: bool = False):
        """Add a profile node to the graph"""
        # Create a label with profile name and key information
        label_parts = [profile.name]  # Profile name without bolding

        # Add vendor if available
        vendor = profile.settings.get('filament_vendor')
        if vendor and isinstance(vendor, list) and len(vendor) > 0:
            label_parts.append(f"Vendor: {vendor[0]}")

        # Get just the filename without the parent directory
        filename = os.path.basename(profile.file_path)
        label_parts.append(f"File: {filename}")

        # Add the path within the input directory when not using group option
        if not group:
            # Extract the path relative to the input directory
            # Find the input directory in the path and get everything after it
            path_parts = profile.file_path.split('/')
            input_dir_name = os.path.basename(self.input_dir.rstrip('/'))  # Handle input_dir with or without trailing slash
            input_dir_idx = -1
            for i, part in enumerate(path_parts):
                if part == input_dir_name:
                    input_dir_idx = i
                    break

            if input_dir_idx >= 0:
                # Get everything after the input directory name
                relative_path_parts = path_parts[input_dir_idx + 1:]  # Skip input directory itself
                if len(relative_path_parts) > 1:  # If we have subdirectories
                    # Join all parts except the filename (last element)
                    relative_dir = '/'.join(relative_path_parts[:-1])
                    label_parts.append(f"Path: {relative_dir}")

        label = r'\n'.join(label_parts)

        # Determine if profile is from system or user directory based on file path
        is_user_profile = "user/" in profile.file_path

        # Set colors based on OrcaSlicer application theme with same border color for type regardless of system/user
        if profile.profile_type == "filament":
            color = '#2E86AB'  # Darker blue for filament type
            # Use transparency: 25% for system (lighter), 50% for user (darker)
            fillcolor = '#2E86AB33' if not is_user_profile else '#2E86AB80'  # 33 = ~20%, 80 = ~50%
        elif profile.profile_type == "machine":
            color = '#27AE60'  # Darker green for machine type
            fillcolor = '#27AE6033' if not is_user_profile else '#27AE6080'  # 33 = ~20%, 80 = ~50%
        elif profile.profile_type == "process":
            color = '#8E44AD'  # Dark purple for process type
            fillcolor = '#8E44AD33' if not is_user_profile else '#8E44AD80'  # 33 = ~20%, 80 = ~50%
        else:
            # Default color for unknown types
            color = '#7F8C8D'  # Gray for other types
            fillcolor = '#7F8C8D33' if not is_user_profile else '#7F8C8D80'  # 33 = ~20%, 80 = ~50%

        # Apply thicker border for user profiles (under user directory)
        penwidth = '3' if is_user_profile else '1'

        # Use rounded boxes for all profile types (instead of shape-based shapes)
        dot.node(profile.name, label=label, fillcolor=fillcolor, color=color, penwidth=penwidth, shape='box', style='rounded,filled')
    
    def _add_inheritance_edge(self, dot: graphviz.Digraph, parent_name: str, child_name: str):
        """Add an inheritance edge from parent to child"""
        dot.edge(parent_name, child_name, arrowhead='vee')
    
    def _add_inheritance_chain(self, dot: graphviz.Digraph, profile: Profile, visited: set):
        """Add all parent profiles in the inheritance chain"""
        current = profile
        while current and current.inherits and current.inherits not in visited:
            parent = self.analyzer.get_profile(current.inherits)
            if not parent:
                break
            
            self._add_profile_node(dot, parent)
            self._add_inheritance_edge(dot, parent.name, current.name)
            visited.add(parent.name)
            current = parent
    
    def _add_descendants(self, dot: graphviz.Digraph, profile_name: str, visited: set):
        """Add all descendant profiles"""
        descendants = self.analyzer.get_all_descendants(profile_name)
        
        for descendant in descendants:
            if descendant.name not in visited:
                self._add_profile_node(dot, descendant)
                visited.add(descendant.name)
                
                # Add inheritance edge
                if descendant.inherits:
                    self._add_inheritance_edge(dot, descendant.inherits, descendant.name)