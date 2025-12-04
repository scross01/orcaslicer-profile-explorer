import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass


@dataclass
class Profile:
    name: str
    inherits: Optional[str]
    file_path: str
    from_system: bool
    settings: Dict[str, Any]
    profile_type: str = "filament"


class ProfileAnalyzer:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.profiles: Dict[str, Profile] = {}
        self.load_all_profiles()
    
    def load_all_profiles(self):
        """Load all profiles from system and user directories"""
        profile_paths = []
        
        # Add system profiles
        system_path = self.base_path / "system"
        if system_path.exists():
            profile_paths.extend(self._find_profile_files(system_path))
        
        # Add user profiles
        user_path = self.base_path / "user"
        if user_path.exists():
            profile_paths.extend(self._find_profile_files(user_path))
        
        # Load all profile files
        for profile_path in profile_paths:
            self._load_profile(profile_path)
    
    def _find_profile_files(self, directory: Path) -> List[Path]:
        """Find all JSON profile files in the directory tree"""
        profile_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.json'):
                    profile_files.append(Path(root) / file)
        return profile_files
    
    def _load_profile(self, profile_path: Path):
        """Load a profile from a JSON file"""
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            name = data.get('name')
            if name:
                inherits = data.get('inherits')
                from_system = data.get('from', '').lower() == 'system'
                
                self.profiles[name] = Profile(
                    name=name,
                    inherits=inherits,
                    file_path=str(profile_path),
                    from_system=from_system,
                    settings={k: v for k, v in data.items() if k not in ['name', 'inherits', 'from', 'type']},
                    profile_type=data.get('type', 'filament')
                )
        except Exception as e:
            print(f"Error loading profile {profile_path}: {e}")
    
    def get_profile(self, name: str) -> Optional[Profile]:
        """Get a profile by name"""
        return self.profiles.get(name)
    
    def get_all_profiles(self) -> List[Profile]:
        """Get all loaded profiles"""
        return list(self.profiles.values())
    
    def get_profile_inheritance_chain(self, profile_name: str) -> List[Profile]:
        """Get the inheritance chain for a given profile name"""
        chain = []
        visited = set()
        
        current_name = profile_name
        while current_name and current_name not in visited:
            profile = self.get_profile(current_name)
            if not profile:
                break
            
            chain.append(profile)
            visited.add(current_name)
            current_name = profile.inherits
        
        return chain
    
    def get_all_children(self, parent_name: str) -> List[Profile]:
        """Get all profiles that inherit from the given profile"""
        children = []
        for profile in self.profiles.values():
            if profile.inherits == parent_name:
                children.append(profile)
        return children
    
    def get_all_descendants(self, parent_name: str) -> List[Profile]:
        """Get all profiles that inherit (directly or indirectly) from the given profile"""
        descendants = []
        to_check = [parent_name]
        visited = set()

        while to_check:
            current_name = to_check.pop(0)
            if current_name in visited:
                continue

            visited.add(current_name)
            children = self.get_all_children(current_name)

            for child in children:
                if child not in descendants:
                    descendants.append(child)
                    to_check.append(child.name)

        return descendants

    def get_branches_with_user_profiles(self) -> List[Profile]:
        """Get all profiles that are part of branches containing user-defined profiles"""
        user_profiles = [p for p in self.profiles.values() if not p.from_system]
        all_relevant_profiles = set()

        # For each user profile, add the entire inheritance chain to the relevant set
        for user_profile in user_profiles:
            chain = self.get_profile_inheritance_chain(user_profile.name)
            for profile in chain:
                all_relevant_profiles.add(profile.name)

        # Also add all descendants of user profiles and their ancestors
        for user_profile in user_profiles:
            # Add all descendants of this user profile
            descendants = self.get_all_descendants(user_profile.name)
            for descendant in descendants:
                all_relevant_profiles.add(descendant.name)

        # Return the profiles
        return [self.profiles[name] for name in all_relevant_profiles if name in self.profiles]
    
    def get_profile_settings_comparison(self, profile_name: str) -> Dict[str, List]:
        """Get a comparison of settings across the inheritance chain"""
        chain = self.get_profile_inheritance_chain(profile_name)
        # Reverse the chain so it shows from base to specific (left to right as requested)
        chain.reverse()
        all_settings = set()

        # Collect all possible settings
        for profile in chain:
            all_settings.update(profile.settings.keys())

        # Build the comparison table
        comparison = {'setting_names': []}
        for profile in chain:
            comparison[profile.name] = []

        # Add parent names to the comparison
        comparison['setting_names'] = sorted(list(all_settings))

        for setting_name in comparison['setting_names']:
            for profile in chain:
                value = profile.settings.get(setting_name, "N/A")
                # Convert lists to comma-separated strings for display
                if isinstance(value, list):
                    value = ', '.join(str(v) for v in value)
                comparison[profile.name].append(value)

        return comparison

    def format_settings_comparison_table(self, profile_name: str) -> str:
        """Format the settings comparison as a markdown table"""
        comparison = self.get_profile_settings_comparison(profile_name)

        if not comparison or len(comparison) <= 1:  # Only has setting_names, no actual profiles
            return f"Profile '{profile_name}' not found or has no inheritance chain"

        # Get profile names in the inheritance chain (excluding 'setting_names')
        profile_names = [name for name in comparison.keys() if name != 'setting_names']

        if not profile_names:
            return f"No inheritance chain found for profile '{profile_name}'"

        # Create header row
        header = "| Setting Name | " + " | ".join(profile_names) + " |"
        separator = "| " + " | ".join(["---"] * (len(profile_names) + 1)) + " |"

        rows = [header, separator]

        # Add each setting as a row
        for i, setting_name in enumerate(comparison['setting_names']):
            row = f"| {setting_name} |"
            for profile_name_col in profile_names:
                value = comparison[profile_name_col][i] if i < len(comparison[profile_name_col]) else "N/A"
                row += f" {value} |"
            rows.append(row)

        return "\n".join(rows)