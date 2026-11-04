"""Geographic reference data for Nigeria (36 States + FCT and Geopolitical Zones)."""

from typing import Dict, List, Optional

NIGERIAN_GEOPOLITICAL_ZONES: Dict[str, List[str]] = {
    "NORTH_CENTRAL": ["Benue", "Kogi", "Kwara", "Nasarawa", "Niger", "Plateau", "Federal Capital Territory"],
    "NORTH_EAST": ["Adamawa", "Bauchi", "Borno", "Gombe", "Taraba", "Yobe"],
    "NORTH_WEST": ["Jigawa", "Kaduna", "Kano", "Katsina", "Kebbi", "Sokoto", "Zamfara"],
    "SOUTH_EAST": ["Abia", "Anambra", "Ebonyi", "Enugu", "Imo"],
    "SOUTH_SOUTH": ["Akwa Ibom", "Bayelsa", "Cross River", "Delta", "Edo", "Rivers"],
    "SOUTH_WEST": ["Ekiti", "Lagos", "Ogun", "Ondo", "Osun", "Oyo"],
}

ALL_NIGERIAN_STATES: List[str] = sorted(
    [state for states in NIGERIAN_GEOPOLITICAL_ZONES.values() for state in states]
)


def validate_nigerian_state(state_name: Optional[str]) -> bool:
    """Validate if a given string is a recognized Nigerian State or FCT."""
    if not state_name:
        return False
    return state_name.strip().title() in [s.title() for s in ALL_NIGERIAN_STATES]


def get_zone_for_state(state_name: str) -> Optional[str]:
    """Retrieve the geopolitical zone for a given Nigerian State."""
    clean_state = state_name.strip().title()
    for zone, states in NIGERIAN_GEOPOLITICAL_ZONES.items():
        if any(clean_state == s.title() for s in states):
            return zone
    return None
