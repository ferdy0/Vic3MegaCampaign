"""Here is the code gathering data from vicky"""
import os
import re

from models import Population, Region, State, States

from reich_tools.conf import mod_path


def parse_state_data(filename: str) -> States:
    states_container = States()

    with open(filename, "r") as file:
        data = file.read()

    # Find STATES block
    states_block_match = re.search(r"STATES\s*=\s*{(.*?)}\s*$", data, re.DOTALL)
    if not states_block_match:
        raise ValueError("No STATES block found in the data")

    states_block_data = states_block_match.group(1)

    # Find all state blocks within STATES
    state_blocks = re.findall(
        r"s:(\w+)\s*=\s*({.*?})\s*(?=\s*s:|$)", states_block_data, re.DOTALL
    )

    for state_name, state_data in state_blocks:
        state = State(state_name.strip())

        # Find all create_state blocks within each state block
        create_state_blocks = re.findall(
            r"create_state\s*=\s*{\s*country\s*=\s*c:(\w+)\s*owned_provinces\s*=\s*{([^}]*)}\s*state_type\s*=\s*(\w+)\s*}",
            state_data,
            re.DOTALL,
        )

        for country, provinces_str, region_type in create_state_blocks:
            provinces = provinces_str.split()
            region = Region(country, provinces, region_type)
            state.add_region(region)

        # Find all add_homeland lines within each state block
        homeland_lines = re.findall(r"add_homeland\s*=\s*cu:([\w-]+)", state_data)
        for homeland in homeland_lines:
            state.add_homeland(homeland)

        # Find all add_claim lines within each state block
        claim_lines = re.findall(r"add_claim\s*=\s*c:(\w+)", state_data)
        for claim in claim_lines:
            state.add_claim(claim)

        # Add the state object to the States container
        states_container.add_state(state)

    return states_container


def add_population_data(states_container: States, filename: str):
    with open(filename, "r") as file:
        data = file.read()

    state_blocks = re.findall(r"s:(\w+)\s*=\s*({.*?})\s*(?=\s*s:|$)", data, re.DOTALL)

    for state_name, state_data in state_blocks:
        # Find the corresponding state in the states container
        state = states_container.states[state_name]
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


def parse_state_region_file(filename: str, states_container):
    with open(filename, "r") as file:
        data = file.read()

    # Extract state blocks
    state_blocks = re.findall(r"STATE_(\w+)\s*=\s*{([\s\S]*?)}\s*(?=STATE_|$)", data)

    for state_name, block in state_blocks:
        state_name = "STATE_" + state_name
        # Find the corresponding state in the states container
        state = states_container.states.get(state_name)

        if not state:
            continue

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
        state.resource = extract_dict(r"resource\s*=\s*\{([^}]*)\}", block)
        state.naval_exit_id = extract_field(r"naval_exit_id\s*=\s*(\d+)", block)
        state.traits = extract_list(r"traits\s*=\s*\{([^}]*)\}", block)

        if state.name == "STATE_ABRUZZO":
            print(state.name, state.arable_land)
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
        entries = match.group(1).split("\n")
        for entry in entries:
            if "=" in entry:
                key, value = entry.split("=")
                result[key.strip()] = value.strip()
    return result


def process_state_region_files(folder_path: str, states_container):
    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            if filename not in ["99_seas.txt", "readme.info"]:
                print(filename)
                file_path = os.path.join(root, filename)
                parse_state_region_file(file_path, states_container)
                write_state_region_file(file_path, states_container)


def write_state_region_file(filename: str, states_container: States):
    with open(filename, "r") as file:
        original_data = file.read()

    state_blocks = re.findall(
        r"STATE_(\w+)\s*=\s*{([\s\S]*?)}\s*(?=STATE_|$)", original_data
    )

    modified_data = original_data
    for state_name, block in state_blocks:
        state_name = "STATE_" + state_name
        state = states_container.states.get(state_name)
        if state:
            new_block = generate_state_block(state)
            modified_data = modified_data.replace(block, new_block)

    with open(filename, "w") as file:
        file.write(modified_data)


def generate_state_block(state: State) -> str:
    state_dict = state.to_dict()
    block = f"STATE_{state.name} = {{\n"
    for key, value in state_dict.items():
        if isinstance(value, list):
            if all(isinstance(item, dict) for item in value):
                # Handle list of dictionaries
                block += f"\t{key} = {{\n"
                for item in value:
                    block += "\t\t{\n"
                    for k, v in item.items():
                        block += f"\t\t\t{k} = {v}\n"
                    block += "\t\t}\n"
                block += "\t}\n"
            else:
                # Handle list of strings
                block += f"\t{key} = {{ " + " ".join(value) + " }\n"
        elif isinstance(value, dict):
            block += f"\t{key} = {{\n"
            for k, v in value.items():
                block += f"\t\t{k} = {v}\n"
            block += "\t}\n"
        elif value is not None:
            block += f"\t{key} = {value}\n"
    block += "}\n"
    return block


def write_states_file(filename: str, states_container: States):
    with open(filename, "r") as file:
        original_data = file.read()

    states_block_match = re.search(
        r"STATES\s*=\s*{(.*?)}\s*$", original_data, re.DOTALL
    )
    if not states_block_match:
        raise ValueError("No STATES block found in the data")

    states_block_data = states_block_match.group(1)

    state_blocks = re.findall(
        r"s:(\w+)\s*=\s*({.*?})\s*(?=\s*s:|$)", states_block_data, re.DOTALL
    )
    modified_states_block_data = states_block_data

    for state_name, block in state_blocks:
        state = states_container.states.get(state_name.strip())
        if state:
            new_block_content = generate_state_data_block(state)
            new_block = f"s:{state_name} = {{\n{new_block_content}\n}}\n"
            modified_states_block_data = modified_states_block_data.replace(
                block, new_block
            )

    modified_data = original_data.replace(states_block_data, modified_states_block_data)

    with open(filename, "w") as file:
        file.write(modified_data)


def generate_state_data_block(state: State) -> str:
    block = ""
    for region in state.regions:
        block += "\tcreate_state = {\n"
        block += f"\t\tcountry = c:{region.country}\n"
        block += f"\t\towned_provinces = {{ {' '.join(region.provinces)} }}\n"
        block += f"\t\tstate_type = {region.type}\n"
        block += "\t}\n"
    for homeland in state.homelands:
        block += f"\tadd_homeland = cu:{homeland}\n"
    for claim in state.claims:
        block += f"\tadd_claim = c:{claim}\n"
    return block


def write_population_file(filename: str, states_container: States):
    with open(filename, "r") as file:
        original_data = file.read()

    state_blocks = re.findall(
        r"s:(\w+)\s*=\s*({.*?})\s*(?=\s*s:|$)", original_data, re.DOTALL
    )
    modified_data = original_data

    for state_name, block in state_blocks:
        state = states_container.states.get(state_name.strip())
        if state:
            new_block_content = generate_population_data_block(state)
            new_block = f"s:{state_name} = {{\n{new_block_content}\n}}\n"
            modified_data = modified_data.replace(block, new_block)

    with open(filename, "w") as file:
        file.write(modified_data)


def generate_population_data_block(state: State) -> str:
    block = ""
    for region in state.regions:
        if region.populations:
            block += f"\tregion_state:{region.country} = {{\n"
            for pop in region.populations:
                block += "\t\tcreate_pop = {\n"
                block += f"\t\t\tculture = {pop.culture}\n"
                block += f"\t\t\treligion = {pop.religion}\n"
                block += f"\t\t\tsize = {pop.size}\n"
                block += "\t\t}\n"
            block += "\t}\n"
    return block


def modify_data(states_container: States):
    for state in states_container.states.values():
        pop_sum = 0
        for region in state.regions:
            pop_sum += region.sum_populations()
        min_arable_land = pop_sum / 50000
        if state.arable_land is None:
            print(state.to_dict())
        if state.arable_land < min_arable_land:
            old_arable_land = state.arable_land
            state.arable_land = min_arable_land
            print(
                f"{state.name}: Population = {pop_sum}, changing arable land from {old_arable_land} to {state.arable_land}"
            )


# Example usage
states_filepath = mod_path + "/common/history/states/99_converter_states.txt"
population_filepath = mod_path + "/common/history/pops/99_converted_pops.txt"
state_regions_folder = mod_path + "/map_data/state_regions"

# Parse states and population data
states = parse_state_data(states_filepath)
add_population_data(states, population_filepath)

# Modify data in memory
# modify_data(states)
#
# # Write back to states file
# write_states_file(states_filepath, states)
#
# # Write back to population file
# write_population_file(population_filepath, states)

# Process state region files in the folder and write back
process_state_region_files(state_regions_folder, states)
