'''
Labile, refractory and inorganic sediment functions.
'''
from dataclasses import dataclass
from typing import Callable, Self

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

def deposition_builder(constants: Constants) -> Callable[[float], tuple[float, float, float]]:
    '''
    Divides deposited sediment into labile, refractory and inorganic components.
    '''
    def deposition(weigth: float) -> tuple[float, float, float]:
        '''
        Computes biomass [in g] deposited as sediment [in cm].

        Returns:
            Tuple[float, float, float]: labile, refractory, inorganic [in g].
        '''
        return (weigth * constants.fo * constants.fl,
                weigth * constants.fo * constants.fc,
                weigth * constants.fi)
    return deposition

class Tools:
    '''
    Holds fully parameterized sediment functions.
    '''
    def __init__(self, constants: Constants):
        self.converter = conversion_builder(constants)
        self.ash_uptake = ash_uptake_builder(constants)
        self.decomposition = decomposition_builder(constants)
        self.deposition = deposition_builder(constants)

@dataclass(frozen=True)
class Sediment:
    '''Sediment base class.'''
    val: float
    tag: Tag
    converter: Callable[[float, Tag, Measurement], float]
    measurement: Measurement = Measurement.WEIGHT

    @property
    def length(self) -> float:
        '''Returns the length [in cm] of the labile sediment.'''
        if self.measurement == Measurement.LENGTH:
            return self.val
        return self.converter(self.val, self.tag, Measurement.LENGTH)
    @property
    def weight(self) -> float:
        '''Returns the weight [in g] of the labile sediment.'''
        if self.measurement == Measurement.WEIGHT:
            return self.val
        return self.converter(self.val, self.tag, Measurement.WEIGHT)
    def update(self, weight: float) -> Self:
        '''
        Add/substract sediment [in g] to stock, returning new sediment container.
        '''
        return Sediment(self.weight + weight, self.tag, Measurement.WEIGHT, self.converter)

@dataclass(frozen=True)
class Sediments:
    '''Container for labile, refractory and inorganic sediment.'''
    fxs: Tools
    labile: Sediment
    refractory: Sediment
    inorganic: Sediment

    def portions(self) -> tuple[float, float, float]:
        '''
        Computes portion labile, refractory and inorganic sediment.
        '''
        total = self.labile.weight + self.refractory.weight + self.inorganic.weight
        return (self.labile.weight / total,
                self.refractory.weight / total,
                self.inorganic.weight / total)

    def transfers(self, yrs: float) -> Self:
        '''
        Transfers losses of sediment from system due to decomposition and ash uptake.
        '''
        return Sediments(self.fxs,
                         self.labile.update(self.fxs.decomposition(self.labile.weight, yrs)),
                         self.refractory, # non-reactive no change expect by removal by erosion.
                         self.inorganic.update(self.fxs.ash_uptake(self.inorganic.weight)))

    def erosion(self, weight: float) -> Self:
        '''
        Adds or removes sediment [in g] to stocks, returning new sediment container.
        '''
        if weight < 0: # erosion
            labile, refractory, inorganic = tuple(portion * weight for portion in self.portions())
            return Sediments(self.fxs,
                             self.labile.update(labile),
                             self.refractory.update(refractory),
                             self.inorganic.update(inorganic))
        return self # no deposition below top layer.

    def update(self, weights: tuple[float, float, float]) -> Self:
        '''
        Adds/substract sediment [in g] to stocks, returning new sediment container.
        
        Args:
            weights (tuple[float, float, float]): labile, refractory, inorganic [in g].
            
        Returns:
            Sediments: updated sediment container.
        '''
        return Sediments(self.fxs,
                         self.labile.update(weights[0]),
                         self.refractory.update(weights[1]),
                         self.inorganic.update(weights[2]))

def factory(sum_of_stocks: float, measurement: Measurement, constants: Constants) -> Sediments: # pylint: disable=line-too-long
    '''
    Returns labile, refractory and inorganic sediment stocks.
    '''
    tools = Tools(constants)
    organic, inorganic = sum_of_stocks * constants.fo, sum_of_stocks * constants.fi
    labile, refractory = organic * constants.fl, organic * constants.fc
    return Sediments(tools,
                     Sediment(labile, Tag.LABILE, measurement, tools.converter),
                     Sediment(refractory, Tag.REFRACTORY, measurement, tools.converter),
                     Sediment(inorganic, Tag.INORGANIC, measurement, tools.converter))
