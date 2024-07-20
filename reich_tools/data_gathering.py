"""Here is the code gathering data from vicky"""
from reich_tools.conf import mod_path
import re
import os
from models import States, State, Region, Population


def parse_state_data(filename: str) -> States:
    states_container = States()

    with open(filename, 'r') as file:
        data = file.read()

    # Find STATES block
    states_block_match = re.search(r'STATES\s*=\s*{(.*?)}\s*$', data, re.DOTALL)
    if not states_block_match:
        raise ValueError("No STATES block found in the data")

    states_block_data = states_block_match.group(1)

    # Find all state blocks within STATES
    state_blocks = re.findall(r's:(\w+)\s*=\s*({.*?})\s*(?=\s*s:|$)', states_block_data, re.DOTALL)

    for state_name, state_data in state_blocks:
        state = State(state_name.strip())

        # Find all create_state blocks within each state block
        create_state_blocks = re.findall(
            r'create_state\s*=\s*{\s*country\s*=\s*c:(\w+)\s*owned_provinces\s*=\s*{([^}]*)}\s*state_type\s*=\s*(\w+)\s*}',
            state_data, re.DOTALL)

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

        # Add the state object to the States container
        states_container.add_state(state)

    return states_container


def add_population_data(states_container: States, filename: str):
    with open(filename, 'r') as file:
        data = file.read()

    state_blocks = re.findall(r's:(\w+)\s*=\s*({.*?})\s*(?=\s*s:|$)', data, re.DOTALL)


    for state_name, state_data in state_blocks:
        # Find the corresponding state in the states container
        state = states_container.states[state_name]
        if not state:
            continue

        # Find all region_state blocks within each state block
        region_state_blocks = re.findall(r'region_state:(\w+)\s*=\s*({.*?})\s*(?=\s*region_state:|\s*s:|$)', state_data,
                                         re.DOTALL)

        for region_country, region_data in region_state_blocks:
            # Find the corresponding region within the state
            region = next((r for r in state.regions if r.country == region_country), None)
            if not region:
                continue

            # Find all create_pop blocks within each region block
            create_pop_blocks = re.findall(
                r'create_pop\s*=\s*{\s*culture\s*=\s*(\w+)\s*religion\s*=\s*(\w+)\s*size\s*=\s*(\d+)\s*}',
                region_data, re.DOTALL)


            for pop_block in create_pop_blocks:
                population = Population(culture=pop_block[0], religion=pop_block[1], size=int(pop_block[2]))
                region.add_population(population)


def parse_state_region_file(filename: str, states_container):
    with open(filename, 'r') as file:
        data = file.read()

    # Extract state blocks
    state_blocks = re.findall(r'STATE_(\w+)\s*=\s*{([\s\S]*?)}\s*(?=STATE_|$)', data)


    for state_name, block in state_blocks:
        if state_name == 'ABRUZZO':
            print('AAAA')
        state_name = 'STATE_' + state_name
        # Find the corresponding state in the states container
        state = states_container.states[state_name]

        if not state:
            continue



        # Extract individual fields
        state.id = extract_field(r'id\s*=\s*(\d+)', block)
        state.subsistence_building = extract_field(r'subsistence_building\s*=\s*"([^"]+)"', block)
        state.provinces = extract_list(r'provinces\s*=\s*\{([^}]*)\}', block)
        state.city = extract_field(r'city\s*=\s*"([^"]+)"', block)
        state.port = extract_field(r'port\s*=\s*"([^"]+)"', block)
        state.farm = extract_field(r'farm\s*=\s*"([^"]+)"', block)
        state.mine = extract_field(r'mine\s*=\s*"([^"]+)"', block)
        state.wood = extract_field(r'wood\s*=\s*"([^"]+)"', block)
        state.arable_land = extract_field(r'arable_land\s*=\s*(\d+)', block)
        state.arable_resources = extract_list(r'arable_resources\s*=\s*\{([^}]*)\}', block)
        state.capped_resources = extract_dict(r'capped_resources\s*=\s*\{([^}]*)\}', block)
        state.resource = extract_dict(r'resource\s*=\s*\{([^}]*)\}', block)
        state.naval_exit_id = extract_field(r'naval_exit_id\s*=\s*(\d+)', block)
        state.traits = extract_list(r'traits\s*=\s*\{([^}]*)\}', block)


        if state_name == 'STATE_ABRUZZO':
            print("ABRUZZO")




    return states_container

def extract_field(pattern: str, block: str):
    match = re.search(pattern, block)
    if match:
        return match.group(1)
    return None

def extract_list(pattern: str, block: str):
    match = re.search(pattern, block)
    if match:
        return [item.strip().strip('"') for item in match.group(1).split()]
    return []

def extract_dict(pattern: str, block: str):
    match = re.search(pattern, block)
    result = {}
    if match:
        entries = match.group(1).split('\n')
        for entry in entries:
            if '=' in entry:
                key, value = entry.split('=')
                result[key.strip()] = value.strip()
    return result


def process_state_region_files(folder_path: str, states_container):
    for filename in os.listdir(folder_path):
        print(filename)
        if filename.endswith('.txt'):
            file_path = os.path.join(folder_path, filename)
            parse_state_region_file(file_path, states_container)




            # for state_name, data in state_data.items():
            #     state = states_container.get_state(state_name)
            #     if not state:
            #         continue
            #
            #
            #     # Update state with data
            #     state.id = data.id
            #     state.subsistence_building = data.subsistence_building
            #     state.provinces = data.provinces
            #     state.city = data.city
            #     state.port = data.port
            #     state.farm = data.farm
            #     state.mine = data.mine
            #     state.wood = data.wood
            #     state.arable_land = data.arable_land
            #     state.arable_resources = data.arable_resources
            #     state.capped_resources = data.capped_resources
            #     state.resource = data.resource
            #     state.naval_exit_id = data.naval_exit_id
            #     state.traits = data.traits


# Example usage
states_filepath = mod_path + "/common/history/states/99_converter_states.txt"  # Replace with your file path
population_filepath = mod_path + "/common/history/pops/99_converted_pops.txt"  # Replace with your file path
state_regions_folder = mod_path + "/map_data/state_regions"  # Replace with your folder path

# Parse states and population data
states = parse_state_data(states_filepath)
add_population_data(states, population_filepath)

# Process state data files in the folder
process_state_region_files(state_regions_folder, states)

#
# for state in states.states:
#     print(state)

# Print or use the `states` object as needed
print(states.states['STATE_ABRUZZO'].to_dict())







