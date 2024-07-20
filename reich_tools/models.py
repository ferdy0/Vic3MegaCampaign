from typing import Dict, List

class Population:
    def __init__(self, culture: str, religion: str, size: int):
        self.culture = culture
        self.religion = religion
        self.size = size

    def to_dict(self):
        return {
            "culture": self.culture,
            "religion": self.religion,
            "size": self.size,
        }


class Region:
    def __init__(self, country: str, provinces: List[str], type: str):
        self.country = country
        self.provinces = provinces
        self.type = type
        self.populations = []


    def add_population(self, population: Population):
        self.populations.append(population)

    def to_dict(self):
        return {
            "country": self.country,
            "provinces": self.provinces,
            "type": self.type,
            "populations": [population.to_dict() for population in self.populations],
        }


    def sum_populations(self):
        return sum(population.size for population in self.populations)

class State:
    def __init__(self, name: str):
        self.name = name
        self.regions = []
        self.homelands = []
        self.claims = []
        self.provinces = []
        self.id = None
        self.subsistence_building = None
        self.city = None
        self.port = None
        self.farm = None
        self.mine = None
        self.wood = None
        self.arable_land = None
        self.arable_resources = []
        self.capped_resources = {}
        self.resource = {}
        self.naval_exit_id = None
        self.traits = []

    def add_region(self, region: Region):
        self.regions.append(region)

    def add_homeland(self, homeland: str):
        self.homelands.append(homeland)

    def add_claim(self, claim: str):
        self.claims.append(claim)

    def to_dict(self):
        return {
            "name": self.name,
            "regions": [region.to_dict() for region in self.regions],
            "homelands": self.homelands,
            "claims": self.claims,
            "provinces": self.provinces,
            "id": self.id,
            "subsistence_building": self.subsistence_building,
            "city": self.city,
            "port": self.port,
            "farm": self.farm,
            "mine": self.mine,
            "wood": self.wood,
            "arable_land": self.arable_land,
            "arable_resources": self.arable_resources,
            "capped_resources": self.capped_resources,
            "resource": self.resource,
            "naval_exit_id": self.naval_exit_id,
            "traits": self.traits,
        }

class States:
    def __init__(self):
        self.states: Dict[str, State] = {}

    def add_state(self, state: State):
        self.states[state.name] = state


    def to_dict(self):
        return {state_name: state.to_dict() for state_name, state in self.states.items()}