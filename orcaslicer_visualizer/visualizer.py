import graphviz
from typing import List, Optional
from .profile_analyzer import Profile, ProfileAnalyzer


class GraphVisualizer:
    def __init__(self, analyzer: ProfileAnalyzer):
        self.analyzer = analyzer
    
    def generate_graph(self, root_profile: Optional[str] = None) -> graphviz.Digraph:
        """Generate a Graphviz digraph for the profile inheritance"""
        dot = graphviz.Digraph(comment='OrcaSlicer Filament Profile Inheritance')
        dot.attr(rankdir='LR', size='12,10')
        dot.attr('node', shape='box', style='rounded,filled', fontname='Arial')
        
        visited_profiles: set = set()
        
        if root_profile:
            # If a root profile is specified, only visualize the inheritance chain
            # and descendants for that profile
            root_profile_obj = self.analyzer.get_profile(root_profile)
            if not root_profile_obj:
                raise ValueError(f"Profile '{root_profile}' not found")
            
            # Add the root profile
            self._add_profile_node(dot, root_profile_obj)
            visited_profiles.add(root_profile)
            
            # Add inheritance chain (parents)
            self._add_inheritance_chain(dot, root_profile_obj, visited_profiles)
            
            # Add descendants
            self._add_descendants(dot, root_profile, visited_profiles)
        else:
            # If no root is specified, visualize all filament profiles
            all_profiles = self.analyzer.get_all_profiles()
            for profile in all_profiles:
                if profile.profile_type == "filament":
                    self._add_profile_node(dot, profile)
            
            # Add all inheritance relationships
            for profile in all_profiles:
                if profile.profile_type == "filament" and profile.inherits:
                    parent_profile = self.analyzer.get_profile(profile.inherits)
                    if parent_profile and parent_profile.profile_type == "filament":
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