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


def process_state_region_files(folder_path: str, states_container):
    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            if filename not in ["99_seas.txt", "readme.info"]:
                print(f"Processing: {filename}")
                file_path = os.path.join(root, filename)
                parse_state_region_file(file_path, states_container)
                write_state_region_file(file_path, states_container)


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
            new_block = generate_state_data_block(state)
            modified_states_block_data = modified_states_block_data.replace(
                f"s:{state_name} = {block}", new_block
            )

    modified_data = original_data.replace(states_block_data, modified_states_block_data)

    with open(filename, "w") as file:
        file.write(modified_data)


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
            new_block = generate_population_data_block(state)
            modified_data = modified_data.replace(
                f"s:{state_name} = {block}", new_block
            )
    modified_data = modified_data.rstrip() + "\n}"
    with open(filename, "w") as file:
        file.write(modified_data)


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
            new_block = generate_state_regions_block(state)
            modified_data = modified_data.replace(block, new_block)

    with open(filename, "w") as file:
        file.write(modified_data)


def generate_state_data_block(state: State) -> str:
    block = f"\ts:{state.name} = {{\n"
    for region in state.regions:
        block += "\t\t\t\tcreate_state = {\n"
        block += f"\t\t\t\t\t\tcountry = c:{region.country}\n"
        block += f"\t\t\t\t\t\towned_provinces = {{ {' '.join(region.provinces)} }}\n"
        block += f"\t\t\t\t\t\tstate_type = {region.type}\n"
        block += "\t\t\t\t}\n"
    for homeland in state.homelands:
        block += f"\t\t\t\tadd_homeland = cu:{homeland}\n"
    for claim in state.claims:
        block += f"\t\t\t\tadd_claim = c:{claim}\n"
    block += "\t\t}"
    return block


def generate_population_data_block(state: State) -> str:
    block = f"\ts:{state.name} = {{\n"
    for region in state.regions:
        if region.populations:
            block += f"\t\t\t\tregion_state:{region.country} = {{\n"
            for pop in region.populations:
                block += "\t\t\t\t\t\tcreate_pop = {\n"
                block += f"\t\t\t\t\t\t\t\tculture = {pop.culture}\n"
                block += f"\t\t\t\t\t\t\t\treligion = {pop.religion}\n"
                block += f"\t\t\t\t\t\t\t\tsize = {pop.size}\n"
                block += "\t\t\t\t\t\t}\n"
            block += "\t\t\t\t}\n"
    block += "\t\t}"
    return block


def generate_state_regions_block(state: State) -> str:
    block = "\n"
    block += f"\tid = {state.id}\n"
    block += f'\tsubsistence_building = "{state.subsistence_building}"\n'

    # Format provinces list correctly
    provinces_formatted = " ".join(f'"{prov}"' for prov in state.provinces)
    block += f"\tprovinces = {{ {provinces_formatted} }}\n"

    if state.traits:
        traits_formatted = " ".join(f'"{trait}"' for trait in state.traits)
        block += f"\ttraits = {{ {traits_formatted} }}\n"

    if state.city:
        block += f'\tcity = "{state.city}"\n'

    if state.port:
        block += f'\tport = "{state.port}"\n'

    if state.farm:
        block += f'\tfarm = "{state.farm}"\n'

    if state.mine:
        block += f'\tmine = "{state.mine}"\n'

    if state.wood:
        block += f'\twood = "{state.wood}"\n'

    block += f"\tarable_land = {state.arable_land}\n"

    if state.arable_resources:
        arable_resources_formatted = " ".join(
            f'"{res}"' for res in state.arable_resources
        )
        block += f"\tarable_resources = {{ {arable_resources_formatted} }}\n"

    if state.capped_resources:
        block += "\tcapped_resources = {\n"
        for resource, amount in state.capped_resources.items():
            block += f"\t\t{resource} = {amount}\n"

    if state.resources:
        if isinstance(state.resources, list):
            for resource in state.resources:
                block += "\tresource = {\n"
                for key, value in resource.items():
                    try:
                        value = int(value)
                    except ValueError:
                        pass
                    block += f'\t\t{key} = "{value}"\n'

                block += "\t}\n"
        else:
            block += "\tresource = {\n"
            for key, value in state.resources.items():
                try:
                    value = int(value)
                except ValueError:
                    pass
                block += f'\t\t{key} = "{value}"\n'

    if state.naval_exit_id:
        block += f"\tnaval_exit_id = {state.naval_exit_id}\n"

    block += "}"
    return block


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
# Write back to states file
write_states_file(states_filepath, states)

# Write back to population file
write_population_file(population_filepath, states)

# Process state region files in the folder and write back
process_state_region_files(state_regions_folder, states)
