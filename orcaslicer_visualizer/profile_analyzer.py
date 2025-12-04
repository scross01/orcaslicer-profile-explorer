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

    def load_profiles_by_type(self, profile_types: List[str]):
        """Load only profiles of specific types"""
        profile_paths = []

        # Add system profiles
        system_path = self.base_path / "system"
        if system_path.exists():
            profile_paths.extend(self._find_profile_files(system_path))

        # Add user profiles
        user_path = self.base_path / "user"
        if user_path.exists():
            profile_paths.extend(self._find_profile_files(user_path))

        # Load only profiles matching the specified types
        for profile_path in profile_paths:
            try:
                with open(profile_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                profile_type = data.get('type', 'filament')

                # If type is default 'filament', try to infer from directory
                if profile_type == 'filament':
                    path_str = str(profile_path)
                    if '/process/' in path_str:
                        profile_type = 'process'
                    elif '/machine/' in path_str:
                        profile_type = 'machine'
                    elif '/filament/' in path_str:
                        profile_type = 'filament'

                if profile_type in profile_types:
                    self._load_profile(profile_path)
            except Exception:
                # If there's an error reading, just skip this file
                continue

    def get_profiles_by_type(self, profile_type: str) -> List[Profile]:
        """Get all profiles of a specific type"""
        return [p for p in self.profiles.values() if p.profile_type == profile_type]
    
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

                # Determine profile type from JSON data or directory structure
                profile_type = data.get('type', 'filament')

                # If type is default or if we should infer from directory, check the directory
                path_str = str(profile_path)
                if '/process/' in path_str:
                    profile_type = 'process'
                elif '/machine/' in path_str:
                    profile_type = 'machine'
                elif '/filament/' in path_str:
                    # Explicitly set to filament if in filament directory
                    profile_type = 'filament'

                self.profiles[name] = Profile(
                    name=name,
                    inherits=inherits,
                    file_path=str(profile_path),
                    from_system=from_system,
                    settings={k: v for k, v in data.items() if k not in ['name', 'inherits', 'from', 'type']},
                    profile_type=profile_type
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

    def get_branches_with_user_profiles(self, profile_types: List[str] = ["filament"]) -> List[Profile]:
        """Get all profiles that are part of branches containing user-defined profiles, filtered by profile types"""
        user_profiles = [p for p in self.profiles.values() if not p.from_system and p.profile_type in profile_types]
        all_relevant_profiles = set()

        # For each user profile, add the entire inheritance chain to the relevant set
        for user_profile in user_profiles:
            chain = self.get_profile_inheritance_chain(user_profile.name)
            for profile in chain:
                # Only add profiles that are in the requested types
                if profile.profile_type in profile_types:
                    all_relevant_profiles.add(profile.name)

        # Also add all descendants of user profiles and their ancestors
        for user_profile in user_profiles:
            # Add all descendants of this user profile
            descendants = self.get_all_descendants(user_profile.name)
            for descendant in descendants:
                # Only add profiles that are in the requested types
                if descendant.profile_type in profile_types:
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
                value = comparison[profile_name_col][i] if i < len(comparison[profile_name_col]) else "-"

                # For gcode settings, just indicate if value is set or not
                if 'gcode' in setting_name.lower():
                    if value != "-":
                        # Check if the actual value is empty or just whitespace
                        if isinstance(value, str) and not value.strip():
                            value = "-"
                        else:
                            value = "SET"
                    # If it was already "-", leave it as "-"
                else:
                    # Replace N/A with - for non-gcode settings
                    if value == "N/A":
                        value = "-"

                row += f" {value} |"
            rows.append(row)

        return "\n".join(rows)

    def get_effective_profile_settings_multiple(self, profile_names: tuple) -> str:
        """
        Get effective settings for multiple profiles of the same type, showing them in a comparison table.
        """
        if not profile_names:
            return "No profile names provided"

        # Get all requested profiles
        profiles = []
        for profile_name in profile_names:
            profile = self.get_profile(profile_name)
            if not profile:
                return f"Profile '{profile_name}' not found"
            profiles.append(profile)

        # Check that all profiles are of the same type
        profile_types = {p.profile_type for p in profiles}
        if len(profile_types) > 1:
            return f"All profiles must be of the same type. Found types: {', '.join(profile_types)}"

        # Get all unique setting names across the inheritance chains of all requested profiles
        all_setting_names = set()
        all_chains = []
        for profile in profiles:
            chain = self.get_profile_inheritance_chain_with_types(profile.name)
            all_chains.append(chain)
            for chain_profile in chain:
                all_setting_names.update(chain_profile.settings.keys())

        # For each setting and each profile, find the effective value
        effective_values = {}
        for setting_name in all_setting_names:
            effective_values[setting_name] = {}
            for profile, chain in zip(profiles, all_chains):
                # Find the effective value for this setting in this profile's chain
                # Process from base to target (first to last in the chain) allowing child profiles to override parent values
                value_found = "-"
                for chain_profile in chain:  # Start with base profile and move to target
                    if setting_name in chain_profile.settings:
                        value = chain_profile.settings[setting_name]
                        # Update the value if this profile provides a meaningful value
                        is_meaningful = False
                        if value is not None and value != "":
                            if isinstance(value, list):
                                if len(value) > 0 and not all((v == "" or v == "-" or v is None) for v in value):
                                    is_meaningful = True
                            elif isinstance(value, str):
                                if value.strip() and value != "-":
                                    is_meaningful = True
                            else:
                                is_meaningful = True

                        if is_meaningful:
                            value_found = value
                            # Don't break - continue to allow more specific profiles to override
                effective_values[setting_name][profile.name] = value_found

        # Format as a markdown table with a column for each profile
        header = "| Setting Name | " + " | ".join(p.name for p in profiles) + " |"
        separator = "|" + " --- |" * (len(profiles) + 1)

        rows = [header, separator]

        # Sort the setting names for consistent output
        sorted_settings = sorted(effective_values.keys())

        for setting_name in sorted_settings:
            row = f"| {setting_name} |"
            for profile in profiles:
                value = effective_values[setting_name][profile.name]

                # Format the value appropriately
                if isinstance(value, list):
                    if len(value) == 1:
                        value = value[0]
                    else:
                        value = ", ".join(str(v) for v in value)

                # For gcode settings, just indicate if value is set or not
                if 'gcode' in setting_name.lower():
                    if value and str(value).strip() and value != "-":
                        value = "SET"
                    else:
                        value = "-"
                else:
                    # Convert empty values to "-", leaving "N/A" as is
                    if not value or (isinstance(value, str) and not value.strip()) or value == "-":
                        value = "-"

                row += f" {value} |"
            rows.append(row)

        return "\n".join(rows)

    def get_profile_inheritance_chain_with_types(self, profile_name: str) -> List[Profile]:
        """
        Get the inheritance chain for a given profile name, regardless of profile type
        """
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

    def get_effective_profile_settings(self, profile_name: str) -> str:
        """
        Get effective settings for a profile by traversing the inheritance chain
        and taking values from parents if not set in the current profile.
        """
        chain = self.get_profile_inheritance_chain_with_types(profile_name)

        if not chain:
            return f"Profile '{profile_name}' not found"

        # The chain is from the target profile up to the root (base), so we traverse from base to specific profile
        # We'll go in order from base to target, with later profiles overriding settings from earlier ones
        effective_values = {}

        # Collect all unique settings names across the entire chain
        all_setting_names = set()
        for profile in chain:
            all_setting_names.update(profile.settings.keys())

        # Initialize with "-" for all settings
        for setting_name in all_setting_names:
            effective_values[setting_name] = "-"

        # For each setting, find the effective value by going from base to specific profile
        # and taking each meaningful value (child overrides parent)
        for setting_name in all_setting_names:
            # Walk through the chain from base to target (reversed order) to apply overrides in the right order
            # The chain is originally [specific, parent, grandparent, ... base], so we need to reverse it
            for profile in reversed(chain):  # Start with base profile and move to target
                if setting_name in profile.settings:
                    value = profile.settings[setting_name]
                    # Update the value if this profile provides a meaningful value
                    is_meaningful = False
                    if value is not None and value != "":
                        if isinstance(value, list):
                            if len(value) > 0 and not all((v == "" or v == "-" or v is None) for v in value):
                                is_meaningful = True
                        elif isinstance(value, str):
                            if value.strip() and value != "-":
                                is_meaningful = True
                        else:
                            is_meaningful = True

                        if is_meaningful:
                            effective_values[setting_name] = value
                            # Don't break here - continue to allow more specific profiles to override

        # Format as a markdown table
        header = f"| Setting Name | {chain[0].name} |"
        separator = "| --- | --- |"

        rows = [header, separator]

        # Sort the setting names for consistent output
        sorted_settings = sorted(effective_values.keys())

        for setting_name in sorted_settings:
            value = effective_values[setting_name]

            # Format the value appropriately
            if isinstance(value, list):
                if len(value) == 1:
                    value = value[0]
                else:
                    value = ", ".join(str(v) for v in value)

            # For gcode settings, just indicate if value is set or not
            if 'gcode' in setting_name.lower():
                if value and str(value).strip():
                    value = "SET"
                else:
                    value = "-"
            else:
                # Convert empty values to "-", leaving "N/A" as is
                if not value or (isinstance(value, str) and not value.strip()):
                    value = "-"

            row = f"| {setting_name} | {value} |"
            rows.append(row)

        return "\n".join(rows)