"""Here is the code gathering data from vicky"""
from reich_tools.conf import mod_path
import re
from typing import List, Dict


class Region:
    def __init__(self, country: str, provinces: List[str], region_type: str):
        self.country = country
        self.provinces = provinces
        self.type = region_type

    def __repr__(self):
        return f"Region(country={self.country}, provinces={self.provinces}, type={self.type})"


class State:
    def __init__(self, name: str):
        self.name = name
        self.regions: List[Region] = []
        self.homelands: List[str] = []
        self.claims: List[str] = []

    def add_region(self, region: Region):
        self.regions.append(region)

    def add_homeland(self, homeland: str):
        self.homelands.append(homeland)

    def add_claim(self, claim: str):
        self.claims.append(claim)

    def __repr__(self):
        return f"State(name={self.name}, regions={self.regions}, homelands={self.homelands}, claims={self.claims})"

    def __str__(self):
        regions_str = '\n'.join(str(region) for region in self.regions)
        homelands_str = ', '.join(self.homelands)
        claims_str = ', '.join(self.claims)
        return f"State: {self.name}\nRegions:\n{regions_str}\nHomelands: {homelands_str}\nClaims: {claims_str}"


# Replace the parse_data_from_file function with the following:

def parse_data_from_file(filename: str) -> Dict[str, State]:
    states = {}
    current_state = None

    with open(filename, 'r') as file:
        data = file.read()

    # Find STATES block
    states_block_match = re.search(r'STATES\s*=\s*{\s*(.+?)\s*}\s*$', data, re.DOTALL)
    if not states_block_match:
        raise ValueError("No STATES block found in the data")

    states_block_data = states_block_match.group(1)
    print(states_block_data)

    # Find all state blocks within STATES
    state_blocks = re.findall(r's:(\w+)\s*=\s*{([^}]*)}', states_block_data)

    for state_name, state_data in state_blocks:
        state = State(state_name.strip())

        # Find all create_state blocks within each state block
        create_state_blocks = re.findall(
            r'create_state\s*=\s*{\s*country\s*=\s*c:(\w+)\s*owned_provinces\s*=\s*{([^}]*)}\s*state_type\s*=\s*(\w+)',
            state_data)

        for country, provinces_str, region_type in create_state_blocks:
            provinces = provinces_str.split()
            region = Region(country, provinces, region_type)
            state.add_region(region)

        # Find all add_homeland lines within each state block
        homeland_lines = re.findall(r'add_homeland\s*=\s*cu:([\w-]+)', state_data)
        for homeland in homeland_lines:
            state.add_homeland(homeland)

        # Find all add_claim lines within each state block
        claim_lines = re.findall(r'add_claim\s*=\s*c:(\w+)', state_data)
        for claim in claim_lines:
            state.add_claim(claim)

        # Store the state object in the dictionary
        states[state_name] = state

    return states


# Example usage:
filename = mod_path + "/common/history/states/99_converter_states.txt" # Replace with your file path
states = parse_data_from_file(filename)

# Print all states
# for state_name, state in states.items():
#     print(state)

# Access specific state data
# state_name = "STATE_ABRUZZO"
# print(f"\nAccessing data for state: {state_name}")
# print("Regions:", states[state_name].regions)
# print("Homelands:", states[state_name].homelands)
# print("Claims:", states[state_name].claims)




