'''
Labile, refractory and inorganic sediment functions.
'''
from typing import Callable, Self
from dataclasses import dataclass

from src.constants import Constants
from src.stock import Tag, Measurement, conversion_builder

def decomposition_builder(constants: Constants) -> Callable[[float, float], float]:
    '''
    Returns a function that send decomposed labile sediment [in g] out of the layer.
    '''
    def decomposition(labile_weight: float, yrs: float) -> float:
        '''
        Decomposition of labile material [in g], this a loss from the system.

        Notes:
            [1] This is part of eq. 5: kCl(t) in Morris & Bowden.
            [2] Labile weight is in g not g/cm2 (as it is in Morris & Bowden).
        '''
        return labile_weight * constants.k * yrs
    return decomposition

def ash_uptake_builder(constants: Constants) -> Callable[[float], float]:
    '''
    Returns a function that send ash [in g] to above ground biomass production, out of the layer.
    '''
    def ash_uptake(biomass_weight: float) -> float:
        '''
        Ash uptake [in g], this a loss from the system.

        Notes:
            [1] This is part of eq. 10: -k3(Wb)B/Rl in Morris & Bowden.
        '''
        return constants.k3 * biomass_weight * constants.wa_to_rl
    return ash_uptake

class Tools:
    '''
    Holds fully parameterized sediment functions.
    '''
    def __init__(self, constants: Constants):
        self.converter = conversion_builder(constants)
        self.ash_uptake = ash_uptake_builder(constants)
        self.decomposition = decomposition_builder(constants)

@dataclass(frozen=True)
class Sediment:
    '''Labile sediment.'''
    val: float
    fxs: Tools
    tag: Tag
    measurement: Measurement = Measurement.WEIGHT

    @property
    def length(self) -> float:
        '''Returns the length [in cm] of the labile sediment.'''
        if self.measurement == Measurement.LENGTH:
            return self.val
        return self.fxs.converter(self.val, self.tag, Measurement.LENGTH)
    @property
    def weight(self) -> float:
        '''Returns the weight [in g] of the labile sediment.'''
        if self.measurement == Measurement.WEIGHT:
            return self.val
        return self.fxs.converter(self.val, self.tag, Measurement.WEIGHT)

    @staticmethod
    def factory(tag: Tag, val: float, measurement: Measurement, tools: Tools) -> Self:
        '''Generates a single sediment stock.'''
        match tag:
            case Tag.LABILE:
                tools.ash_uptake = None
                return Sediment(val, tools, tag.Labile, measurement)
            case Tag.REFRACTORY:
                tools.ash_uptake = None
                tools.decomposition = None
                return Sediment(val, tools, tag.Refractory, measurement)
            case Tag.INORGANIC:
                tools.decomposition = None
                return Sediment(val, tools, tag.Inorganic, measurement)
            case _:
                raise ValueError(f'Invalid sediment tag: {tag}.')

def factory(sum_of_stocks: float, measurement: Measurement, constants: Constants) -> tuple[Sediment, Sediment, Sediment]: # pylint: disable=line-too-long
    '''
    Returns labile, refractory and inorganic sediment stocks.
    '''
    tools = Tools(constants)
    organic, inorganic = sum_of_stocks * constants.fo, sum_of_stocks * constants.fi
    labile, refractory = organic * constants.fl, organic * constants.fc
    return (Sediment.factory(Tag.LABILE, labile, measurement, tools),
            Sediment.factory(Tag.REFRACTORY, refractory, measurement, tools),
            Sediment.factory(Tag.INORGANIC, inorganic, measurement, tools))
