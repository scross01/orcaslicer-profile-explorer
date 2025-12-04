import graphviz
from typing import List, Optional
from .profile_analyzer import Profile, ProfileAnalyzer


class GraphVisualizer:
    def __init__(self, analyzer: ProfileAnalyzer):
        self.analyzer = analyzer
    
    def generate_graph(self, target_profile: Optional[str] = None, user_only: bool = False, profile_types: List[str] = ["filament"]) -> graphviz.Digraph:
        """Generate a Graphviz digraph for the profile inheritance"""
        dot = graphviz.Digraph(comment='OrcaSlicer Profile Inheritance')
        dot.attr(rankdir='LR', size='12,10')
        dot.attr('node', shape='box', style='rounded,filled', fontname='Arial')

        visited_profiles: set = set()

        if user_only:
            # Only show branches that include user-defined profiles
            relevant_profiles = self.analyzer.get_branches_with_user_profiles()
            for profile in relevant_profiles:
                if profile.profile_type in profile_types:
                    self._add_profile_node(dot, profile)

            # Add inheritance relationships between relevant profiles
            for profile in relevant_profiles:
                if profile.profile_type in profile_types and profile.inherits:
                    parent_profile = self.analyzer.get_profile(profile.inherits)
                    if parent_profile and parent_profile.profile_type in profile_types and parent_profile in relevant_profiles:
                        self._add_inheritance_edge(dot, profile.inherits, profile.name)

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

            # Add the target profile
            self._add_profile_node(dot, target_profile_obj)
            visited_profiles.add(target_profile)

            # Add inheritance chain (parents)
            self._add_inheritance_chain(dot, target_profile_obj, visited_profiles)

            # Add descendants
            self._add_descendants(dot, target_profile, visited_profiles)
        else:
            # If no target is specified, visualize profiles of the specified types
            all_profiles = self.analyzer.get_all_profiles()
            for profile in all_profiles:
                if profile.profile_type in profile_types:
                    self._add_profile_node(dot, profile)

            # Add all inheritance relationships for the specified types
            for profile in all_profiles:
                if profile.profile_type in profile_types and profile.inherits:
                    parent_profile = self.analyzer.get_profile(profile.inherits)
                    if parent_profile and parent_profile.profile_type in profile_types:
                        self._add_inheritance_edge(dot, profile.inherits, profile.name)

        return dot
    
    def _add_profile_node(self, dot: graphviz.Digraph, profile: Profile):
        """Add a profile node to the graph"""
        # Create a label with profile name and key information
        label_parts = [profile.name]
        
        # Add vendor if available
        vendor = profile.settings.get('filament_vendor')
        if vendor and isinstance(vendor, list) and len(vendor) > 0:
            label_parts.append(f"Vendor: {vendor[0]}")
        
        # Add file location
        label_parts.append(f"File: {profile.file_path.split('/')[-1]}")
        
        label = r'\n'.join(label_parts)
        
        # Set color based on source (system vs user)
        fillcolor = 'lightblue' if profile.from_system else 'lightyellow'
        
        dot.node(profile.name, label=label, fillcolor=fillcolor)
    
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