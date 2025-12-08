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
        # Keep track of duplicate profile names to handle conflicts
        self.profile_name_to_file_paths: Dict[str, List[str]] = {}
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
                    # Use OS-appropriate path separators for checking
                    process_path = os.path.sep + "process" + os.path.sep
                    machine_path = os.path.sep + "machine" + os.path.sep
                    filament_path = os.path.sep + "filament" + os.path.sep

                    if process_path in path_str:
                        profile_type = 'process'
                    elif machine_path in path_str:
                        profile_type = 'machine'
                    elif filament_path in path_str:
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
                # Use OS-appropriate path separators for checking
                process_path = os.path.sep + "process" + os.path.sep
                machine_path = os.path.sep + "machine" + os.path.sep
                filament_path = os.path.sep + "filament" + os.path.sep

                if process_path in path_str:
                    profile_type = 'process'
                elif machine_path in path_str:
                    profile_type = 'machine'
                elif filament_path in path_str:
                    # Explicitly set to filament if in filament directory
                    profile_type = 'filament'

                # Track file paths for each profile name to handle duplicates
                if name not in self.profile_name_to_file_paths:
                    self.profile_name_to_file_paths[name] = []
                self.profile_name_to_file_paths[name].append(str(profile_path))

                # If there are multiple profiles with the same name, create unique identifiers
                # but also maintain the original name relationship
                original_name = name
                unique_name = original_name
                if len(self.profile_name_to_file_paths[original_name]) > 1:
                    # When multiple profiles have the same name, append path info to make unique
                    profile_dir = str(Path(profile_path).parent)
                    dir_parts = profile_dir.split(os.path.sep)
                    unique_dir_part = "/".join(dir_parts[-2:]) if len(dir_parts) >= 2 else dir_parts[-1]
                    unique_name = f"{original_name} [{unique_dir_part}]"

                self.profiles[unique_name] = Profile(
                    name=original_name,  # Keep original name for reference
                    inherits=inherits,
                    file_path=str(profile_path),
                    from_system=from_system,
                    settings={k: v for k, v in data.items() if k not in ['name', 'inherits', 'from', 'type']},
                    profile_type=profile_type
                )
        except Exception as e:
            print(f"Error loading profile {profile_path}: {e}")
    
    def get_profile(self, name: str, requesting_file_path: str = None) -> Optional[Profile]:
        """Get a profile by name, with optional requesting file path for disambiguation"""

        # First, try to get by exact key name (may be unique or with path suffix)
        exact_match = self.profiles.get(name)

        # Find all profiles with the same original name for potential disambiguation
        profile_candidates = []
        for profile_key, profile_obj in self.profiles.items():
            if profile_obj.name == name:  # This looks for original name in the profile's name attribute
                profile_candidates.append(profile_obj)

        # If no profiles with the requested name exist, return None
        if not profile_candidates:
            return None

        # If only one profile exists with this name, return it regardless of exact key match
        if len(profile_candidates) == 1:
            return profile_candidates[0]

        # If multiple profiles exist with the same original name, apply heuristics
        # This will be the case when we need to disambiguate based on directory proximity
        if requesting_file_path:
            requesting_path_obj = Path(requesting_file_path)
            requesting_parts = requesting_path_obj.parts

            # Find the closest matching profile based on directory proximity
            closest_candidate = self._find_closest_profile(profile_candidates, requesting_path_obj)

            if closest_candidate:
                return closest_candidate

        # If no specific file context provided, or no close match found,
        # prefer profiles in system/OrcaFilamentLibrary before others
        orca_filament_library_candidates = [
            candidate for candidate in profile_candidates
            if 'system/OrcaFilamentLibrary' in candidate.file_path or
               '/system/OrcaFilamentLibrary' in candidate.file_path or
               candidate.file_path.startswith('system/OrcaFilamentLibrary')
        ]

        if orca_filament_library_candidates:
            return orca_filament_library_candidates[0]

        # If no OrcaFilamentLibrary profiles, return the first one as a fallback
        return profile_candidates[0]

    def _find_closest_profile(self, candidates: List[Profile], requesting_path: Path) -> Optional[Profile]:
        """Find the closest profile based on directory hierarchy proximity

        Implements the heuristic:
        1. First prioritize profiles in the same directory as requesting file
        2. Then prioritize profiles with the most common path components
        3. If no path matches, prefer profiles in system/OrcaFilamentLibrary
        4. As a last resort, return the first available profile
        """
        requesting_path_obj = Path(requesting_path)
        requesting_parent_dir = requesting_path_obj.parent
        requesting_parts = requesting_path_obj.parts

        # First, check for profiles in the exact same parent directory
        for candidate in candidates:
            candidate_path = Path(candidate.file_path)
            candidate_parent_dir = candidate_path.parent
            if candidate_parent_dir == requesting_parent_dir:
                return candidate

        # Then look for profiles in the same vendor/manufacturer directory or with the most common path
        closest_matches = []

        for candidate in candidates:
            candidate_path = Path(candidate.file_path)
            candidate_parts = candidate_path.parts

            # Find the common path length between requesting file and candidate file
            common_length = 0
            min_len = min(len(requesting_parts), len(candidate_parts))

            for i in range(min_len):
                if requesting_parts[i] == candidate_parts[i]:
                    common_length += 1
                else:
                    break

            if common_length > 0:  # At least some common path
                closest_matches.append((candidate, common_length))

        if closest_matches:
            # Return the candidate with the longest common path
            closest_match = max(closest_matches, key=lambda x: x[1])
            return closest_match[0]

        # If no candidates share any path components with the requesting file,
        # look for candidates in system/OrcaFilamentLibrary as a fallback
        orca_filament_library_candidates = [
            candidate for candidate in candidates
            if 'system/OrcaFilamentLibrary' in candidate.file_path or
               '/system/OrcaFilamentLibrary' in candidate.file_path or
               candidate.file_path.startswith('system/OrcaFilamentLibrary')
        ]

        if orca_filament_library_candidates:
            return orca_filament_library_candidates[0]

        # No close matches found, return None to let the caller handle fallback
        return None
    
    def get_all_profiles(self) -> List[Profile]:
        """Get all loaded profiles"""
        return list(self.profiles.values())
    
    def get_profile_inheritance_chain(self, profile_name: str) -> List[Profile]:
        """Get the inheritance chain for a given profile name"""
        chain = []
        visited = set()

        current_name = profile_name
        requesting_file_path = None  # Will be set after we get the first profile
        while current_name and current_name not in visited:
            profile = self.get_profile(current_name, requesting_file_path)
            if not profile:
                break

            chain.append(profile)
            visited.add(current_name)
            requesting_file_path = profile.file_path  # Use this profile's path for subsequent lookups
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
                    # Use the profile's unique key to store it
                    all_relevant_profiles.add(profile.name)

        # Also add all descendants of user profiles and their ancestors
        for user_profile in user_profiles:
            # Add all descendants of this user profile
            descendants = self.get_all_descendants(user_profile.name)
            for descendant in descendants:
                # Only add profiles that are in the requested types
                if descendant.profile_type in profile_types:
                    all_relevant_profiles.add(descendant.name)

        # Return the profile objects (need to get them by name from the profiles dictionary)
        result = []
        for name in all_relevant_profiles:
            # Look for profiles with this original name
            found_profiles = [p for p in self.profiles.values() if p.name == name]
            result.extend(found_profiles)

        return result
    
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
        # Get the inheritance chain to access original profiles
        chain = self.get_profile_inheritance_chain(profile_name)
        chain.reverse()  # Reverse the chain so it shows from base to specific (left to right as requested)

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

                # For gcode and filament_notes settings, just indicate if value is set or not
                if 'gcode' in setting_name.lower() or setting_name.lower() == 'filament_notes':
                    # Only mark as SET if the profile actually defines this setting and has a non-empty value
                    # Find the profile in the chain to check if setting is actually defined there
                    prof = next((p for p in chain if p.name == profile_name_col), None)
                    if prof and setting_name in prof.settings:
                        actual_value = prof.settings.get(setting_name)
                        if actual_value and isinstance(actual_value, str) and actual_value.strip():
                            value = "SET"
                        elif isinstance(actual_value, list) and any(str(v).strip() for v in actual_value if isinstance(v, str)):
                            value = "SET"
                        elif actual_value:  # Non-empty value that's not a string or list
                            value = "SET"
                        else:
                            value = "-"  # Empty value
                    else:
                        value = "-"  # Setting not defined in this profile
                else:
                    # Replace N/A with - for non-gcode and non-filament_notes settings
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
                # For gcode and filament_notes, just show SET if the profile defines this setting, otherwise -
                if 'gcode' in setting_name.lower() or setting_name.lower() == 'filament_notes':
                    # Check if this specific profile defines the setting
                    if setting_name in profile.settings:
                        actual_value = profile.settings.get(setting_name)
                        if actual_value and isinstance(actual_value, str) and actual_value.strip():
                            value = "SET"
                        elif isinstance(actual_value, list) and any(str(v).strip() for v in actual_value if isinstance(v, str)):
                            value = "SET"
                        elif actual_value:  # Non-empty value that's not a string or list
                            value = "SET"
                        else:
                            value = "-"  # Empty value
                    else:
                        value = "-"  # Setting not defined in this profile
                else:
                    # For other settings, use the effective value (original logic)
                    value = effective_values[setting_name][profile.name]

                    # Format the value appropriately
                    if isinstance(value, list):
                        if len(value) == 1:
                            value = value[0]
                        else:
                            value = ", ".join(str(v) for v in value)

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
        requesting_file_path = None  # Will be set after we get the first profile
        while current_name and current_name not in visited:
            profile = self.get_profile(current_name, requesting_file_path)
            if not profile:
                break

            chain.append(profile)
            visited.add(current_name)
            requesting_file_path = profile.file_path  # Use this profile's path for subsequent lookups
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

        # Get the target profile (the one we're showing settings for)
        target_profile = chain[0] if chain else None
        if not target_profile:
            return f"Profile '{profile_name}' not found"

        # Collect all unique settings names across the entire chain
        all_setting_names = set()
        for profile in chain:
            all_setting_names.update(profile.settings.keys())

        # Format as a markdown table
        header = f"| Setting Name | {target_profile.name} |"
        separator = "| --- | --- |"

        rows = [header, separator]

        # Sort the setting names for consistent output
        sorted_settings = sorted(all_setting_names)

        for setting_name in sorted_settings:
            # For gcode and filament_notes, just show SET if the target profile defines this setting, otherwise -
            if 'gcode' in setting_name.lower() or setting_name.lower() == 'filament_notes':
                if setting_name in target_profile.settings:
                    actual_value = target_profile.settings.get(setting_name)
                    if actual_value and isinstance(actual_value, str) and actual_value.strip():
                        value = "SET"
                    elif isinstance(actual_value, list) and any(str(v).strip() for v in actual_value if isinstance(v, str)):
                        value = "SET"
                    elif actual_value:  # Non-empty value that's not a string or list
                        value = "SET"
                    else:
                        value = "-"  # Empty value
                else:
                    value = "-"  # Setting not defined in this profile
            else:
                # For other settings, use the effective value (original logic)
                effective_value = "-"
                # Walk through the chain from base to target (reversed order) to apply overrides in the right order
                # The chain is originally [specific, parent, grandparent, ... base], so we need to reverse it
                for profile in reversed(chain):  # Start with base profile and move to target
                    if setting_name in profile.settings:
                        profile_value = profile.settings[setting_name]
                        # Update the value if this profile provides a meaningful value
                        is_meaningful = False
                        if profile_value is not None and profile_value != "":
                            if isinstance(profile_value, list):
                                if len(profile_value) > 0 and not all((v == "" or v == "-" or v is None) for v in profile_value):
                                    is_meaningful = True
                            elif isinstance(profile_value, str):
                                if profile_value.strip() and profile_value != "-":
                                    is_meaningful = True
                            else:
                                is_meaningful = True

                            if is_meaningful:
                                effective_value = profile_value
                                # Don't break here - continue to allow more specific profiles to override
                value = effective_value

                # Format the value appropriately
                if isinstance(value, list):
                    if len(value) == 1:
                        value = value[0]
                    else:
                        value = ", ".join(str(v) for v in value)

                # Convert empty values to "-", leaving "N/A" as is
                if not value or (isinstance(value, str) and not value.strip()):
                    value = "-"

            row = f"| {setting_name} | {value} |"
            rows.append(row)

        return "\n".join(rows)