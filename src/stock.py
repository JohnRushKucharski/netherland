'''
Protocols for stock variables.
'''
from enum import Enum
from dataclasses import dataclass
from typing import Protocol, Callable

from src.constants import Constants

class Tag(Enum):
    '''Stock type tag.'''
    BIOMASS = 0
    LABILE = 1
    REFRACTORY = 2
    INORGANIC = 3

class Measurement(Enum):
    '''Type of measurement tag for stock values.'''
    LENGTH = 0
    WEIGHT = 1

@dataclass(frozen=True)
class Stock(Protocol):
    '''Protocol for stock variables.'''
    val: float
    tag: Tag
    measurement: Measurement

    @property
    def length(self) -> float:
        '''Returns the length [in cm] of the stock.'''
    @property
    def weight(self) -> float:
        '''Returns the weight [in g] of the stock.'''

def conversion_builder(constants: Constants) -> Callable[[float, Tag, Measurement], float]:
    '''Returns a functon that converts between length [in cm] and weight [in g] values.'''
    def converter(val: float, tag: Tag, output: Measurement) -> float:
        '''
        Returns biomass value as a length [in cm] or weight [in g].
        '''
        match output:
            case Measurement.LENGTH:
                if tag == Tag.INORGANIC:
                    return constants.inorganic_converter_g_to_cm(val)
                return constants.organic_converter_g_to_cm(val)
            case Measurement.WEIGHT:
                if tag == Tag.INORGANIC:
                    return constants.inorganic_converter_cm_to_g(val)
                return constants.organic_converter_cm_to_g(val)
            case _:
                raise ValueError(f'Invalid measurement type: {output}')
    return converter
