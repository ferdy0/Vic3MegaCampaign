import math
import re
import os
from models import Population, Region, State, States

def raise_arable_land_to_min(state: State):
    pop_sum = 0
    for region in state.regions:
        pop_sum += region.sum_populations()
    original_arable_land = int(state.arable_land)
    min_arable_land = int(math.ceil(pop_sum / 5000))
    if original_arable_land < min_arable_land:
        print(
            f"{state.name}: Population = {pop_sum}, changing arable land from {original_arable_land} to {min_arable_land}"
        )
        state.arable_land = min_arable_land

def parse_state_region_file(filename: str, states_container: States):
    with open(filename, "r") as file:
        data = file.read()

    # Extract state blocks
    state_blocks = re.findall(r"STATE_(\w+)\s*=\s*{([\s\S]*?)}\s*(?=STATE_|$)", data)

    for state_name, block in state_blocks:
        state_name = "STATE_" + state_name
        # Find the corresponding state in the states container
        state = states_container.states.get(state_name)

        if not state:
            state = State(state_name)
            states_container.add_state(state)

        # Extract individual fields
        state.id = extract_field(r"id\s*=\s*(\d+)", block)
        state.subsistence_building = extract_field(
            r'subsistence_building\s*=\s*"([^"]+)"', block
        )
        state.provinces = extract_list(r"provinces\s*=\s*\{([^}]*)\}", block)
        state.city = extract_field(r'city\s*=\s*"([^"]+)"', block)
        state.port = extract_field(r'port\s*=\s*"([^"]+)"', block)
        state.farm = extract_field(r'farm\s*=\s*"([^"]+)"', block)
        state.mine = extract_field(r'mine\s*=\s*"([^"]+)"', block)
        state.wood = extract_field(r'wood\s*=\s*"([^"]+)"', block)
        state.arable_land = extract_field(r"arable_land\s*=\s*(\d+)", block)
        state.arable_resources = extract_list(
            r"arable_resources\s*=\s*\{([^}]*)\}", block
        )
        state.capped_resources = extract_dict(
            r"capped_resources\s*=\s*\{([^}]*)\}", block
        )
        state.resources = extract_dict(r"resource\s*=\s*\{([^}]*)\}", block)
        state.naval_exit_id = extract_field(r"naval_exit_id\s*=\s*(\d+)", block)
        state.traits = extract_list(r"traits\s*=\s*\{([^}]*)\}", block)

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
    matches = re.findall(pattern, block, re.DOTALL)
    if not matches:
        return {}  # Return an empty dict if no matches

    result = []
    for match in matches:
        entry = {}
        lines = match.split("\n")
        for line in lines:
            if "=" in line:
                key, value = line.split("=", 1)
                entry[key.strip()] = value.strip()
        result.append(entry)

    # Return a single dictionary if there's only one match
    if len(result) == 1:
        return result[0]

    return result

def add_population_data(states_container: States, filename: str):
    with open(filename, "r") as file:
        data = file.read()

    state_blocks = re.findall(r"s:(\w+)\s*=\s*({.*?})\s*(?=\s*s:|$)", data, re.DOTALL)

    for state_name, state_data in state_blocks:
        # Find the corresponding state in the states container
        state = states_container.states.get(state_name)
        if not state:
            continue

        # Find all region_state blocks within each state block
        region_state_blocks = re.findall(
            r"region_state:(\w+)\s*=\s*({.*?})\s*(?=\s*region_state:|\s*s:|$)",
            state_data,
            re.DOTALL,
        )

        for region_country, region_data in region_state_blocks:
            # Find the corresponding region within the state
            region = next(
                (r for r in state.regions if r.country == region_country), None
            )
            if not region:
                continue

            # Find all create_pop blocks within each region block
            create_pop_blocks = re.findall(
                r"create_pop\s*=\s*{\s*culture\s*=\s*(\w+)\s*religion\s*=\s*(\w+)\s*size\s*=\s*(\d+)\s*}",
                region_data,
                re.DOTALL,
            )

            for pop_block in create_pop_blocks:
                population = Population(
                    culture=pop_block[0], religion=pop_block[1], size=int(pop_block[2])
                )
                region.add_population(population)

def process_state_region_files(folder_path: str, states_container: States, exclude_files=None):
    if exclude_files is None:
        exclude_files = ["99_seas.txt", "readme.info"]

    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            if filename not in exclude_files:
                print(f"Processing: {filename}")
                file_path = os.path.join(root, filename)
                parse_state_region_file(file_path, states_container)

def modify_arable_land_in_files(states_folder_path: str):
    # Parse states data from the files in the folder
    states_container = States()
    process_state_region_files(states_folder_path, states_container)

    # Modify arable land values in memory
    for state in states_container.states.values():
        raise_arable_land_to_min(state)

    # Modify the arable land lines in the original data and write back to the correct files
    for root, dirs, files in os.walk(states_folder_path):
        for filename in files:
            if filename not in ["99_seas.txt", "readme.info"]:
                file_path = os.path.join(root, filename)
                with open(file_path, "r") as file:
                    original_data = file.readlines()

                modified_data = []
                for line in original_data:
                    modified_line = line
                    arable_land_match = re.match(r"(.*arable_land\s*=\s*)(\d+)(.*)", line)
                    if arable_land_match:
                        state_name_match = re.search(r"STATE_(\w+)", line)
                        if state_name_match:
                            state_name = state_name_match.group(1)
                            state = states_container.states.get("STATE_" + state_name)
                            if state:
                                modified_line = f"{arable_land_match.group(1)}{state.arable_land}{arable_land_match.group(3)}\n"
                    modified_data.append(modified_line)

                # Write the modified data back to the original file
                with open(file_path, "w") as file:
                    file.writelines(modified_data)

# Example usage
states_folder_path = r"C:\Users\z0281712\Projects\Vic3MegaCampaign\map_data\state_regions"
population_filepath = r"C:\Users\z0281712\Projects\Vic3MegaCampaign\common\history\pops\99_converted_pops.txt"

# Parse states and population data
states_container = States()
process_state_region_files(states_folder_path, states_container)
add_population_data(states_container, population_filepath)

# Modify arable land values and write back to the correct files
modify_arable_land_in_files(states_folder_path)
