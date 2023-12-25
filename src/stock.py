'''
Protocols for stock variables.
'''
from enum import Enum
from dataclasses import dataclass
from typing import Protocol, Callable, Self

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
    measurement: Measurement
    @property
    def tag(self) -> Tag:
        '''Describes the stock type.'''
    @property
    def length(self) -> float:
        '''Returns the length [in cm] of the stock.'''
    @property
    def weight(self) -> float:
        '''Returns the weight [in g] of the stock.'''
    def update(self, weight: float) -> Self:
        '''Updates stock by adding or subtracting weight [in g], returning new stock container.'''

@dataclass(frozen=True)
class Inactive:
    '''Inactive stock variables.'''
    val: float
    tag: Tag
    measurement: Measurement
    converter: Callable[[float, Tag, Measurement], float]

    @property
    def length(self) -> float:
        '''Returns the length [in cm] of the stock.'''
        if self.measurement == Measurement.LENGTH:
            return self.val
        return self.converter(self.val, self.tag, Measurement.LENGTH)
    @property
    def weight(self) -> float:
        '''Returns the weight [in g] of the stock.'''
        if self.measurement == Measurement.WEIGHT:
            return self.val
        return self.converter(self.val, self.tag, Measurement.WEIGHT)
    def update(self, weight: float) -> Self:
        '''
        Add/substract sediment [in g] to stock, returning new sediment container.
        
        Args:
            weight (float): weight [in g] to add/substract.
        
        Returns:
            Inactive: updated sediment container.
        '''
        return Inactive(self.weight + weight, self.tag, Measurement.WEIGHT, self.converter)

def factory(constants: Constants) -> tuple[Inactive, Inactive, Inactive]:
    '''Returns a tuple of inactive stock variables.'''
    return (Inactive(0.0, Tag.LABILE, Measurement.WEIGHT, constants.organic_converter_g_to_cm),
            Inactive(0.0, Tag.REFRACTORY, Measurement.WEIGHT, constants.organic_converter_g_to_cm),
            Inactive(0.0, Tag.INORGANIC, Measurement.WEIGHT, constants.inorganic_converter_g_to_cm))

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
