'''
The model requires the parameterization of a large number of constants.

This module reads a constants.toml files and generates an immutable Constants dataclass.
'''

import tomllib
from pathlib import Path
from dataclasses import dataclass

MORRIS_CONSTANTS: str = str(Path(__file__).parent.parent.
                            joinpath('data').joinpath('morris_constants.toml'))

@dataclass(frozen=True)
class Constants:
    '''
    Model constants.
    '''
    ids: tuple[int, ...]
    surface_areas: tuple[float, ...]

def factory(path: str = MORRIS_CONSTANTS) -> dict:
    '''
    Reads a constants.toml file and returns a dictionary.
    '''
    with open(path, 'rb') as file:
        data = tomllib.load(file)
    return data
