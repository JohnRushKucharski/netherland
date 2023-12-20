'''
Below ground biomass functions.
'''
from dataclasses import dataclass
from typing import TypeAlias, Callable

import numpy as np

from src.constants import Constants
from src.stock import Tag, Measurement, conversion_builder

# Aliases
Depths: TypeAlias = tuple[float, float]
Turnover: TypeAlias = tuple[float, float, float]

# pylint: disable=invalid-name #underscore typealias
F_Distribution: TypeAlias = Callable[[float], float]
F_Integration: TypeAlias = Callable[[Depths], float]
F_Turnover: TypeAlias = Callable[[Depths, float], Turnover]

def distribution_builder(constants: Constants) -> Callable[[float], F_Distribution]:
    '''
    Returns partially parametersized biomass distribution function.
    '''
    k1 = constants.k1
    root_depth = constants.rd
    surface_area = constants.sa
    def partial(top: float) -> Callable[[float], float]:
        '''
        Returns a fully parameterized biomass distribution function.
        '''
        def fx(depth: float) -> float:
            '''
            Computes biomass [in g] at a given depth [in cm].
            '''
            if depth > root_depth:
                return 0
            return top * np.exp(-k1 * depth) * surface_area
        return fx
    return partial

def integration_builder(constants: Constants) -> Callable[[F_Distribution], F_Integration]:
    '''
    Returns a partially paramterized function for integrating the biomass distribution function.
    '''
    k1 = constants.k1
    def partial(fx: F_Distribution) -> F_Integration:
        '''
        Returns a fully parameterized function for integrating the biomass distribution function.
        '''
        def integrate(depths: Depths) -> float:
            '''
            Returns the integral of the biomass [in g] distribution function across depths [in cm].
            '''
            return fx(depths[1]) - fx(depths[0]) / -k1
        return integrate
    return partial

def turnover_builder(constants: Constants) -> Callable[[F_Integration], F_Turnover]:
    '''
    Returns partially parameterized biomass turnover function.
    '''
    fc = constants.fc
    fl = constants.fl
    def partial(fx: F_Integration) -> F_Turnover:
        '''
        Returns fully parameterized biomass turnover function.
        '''
        def turnover(depths: Depths, years: float) -> Turnover:
            '''
            Computes biomass [in g] removed due to turnover [in dmls/yr].
            
            Returns:
                Tuple[float, float, float]: refractory, labile, inorganic [in g].
            '''
            mass = fx(depths)
            return (
                fl * mass * years,
                fc * mass * years,
                0.0 # by assumption in Morris & Bowden (1986).
            )
        return turnover
    return partial

def erosion_builder(constants: Constants) -> Callable[[F_Integration], F_Turnover]:
    '''
    Returns partially parameterized function removing biomass [in g] due to erosion [in cm].
    '''
    fc = constants.fc
    fl = constants.fl
    k3 = constants.k3
    def partial(fx: F_Integration) -> F_Turnover:
        '''Returns fully parameterized function removing biomass [in g] due to erosion [in cm].'''
        def erosion(depths: Depths, erosion: float) -> Turnover:
            '''
            Computes biomass [in g] removed due to erosion [in cm].
            
            Returns:
                Tuple[float, float, float]: refractory, labile, inorganic [in g].
            '''
            mass = fx((depths[0], depths[0] + erosion))
            return (mass * fl, mass * fc, mass * k3)
        return erosion
    return partial

def burial_builder(constants: Constants) -> Callable[[F_Integration], F_Turnover]:
    '''
    Returns partially parameterized function removing biomass [in g] due to burial [in cm].
    '''
    fc = constants.fc
    fl = constants.fl
    k3 = constants.k3
    root_depth = constants.rd
    def partial(fx: F_Integration) -> F_Turnover:
        '''Returns fully parameterized function removing biomass [in g] due to burial [in cm].'''
        def burial(depths: Depths, deposition: float) -> Turnover:
            '''
            Computes biomass [in g] removed due to burial [in cm].
            
            Returns:
                Tuple[float, float, float]: refractory, labile, inorganic [in g].
            '''
            def is_in_live_zone(depth_delta: float = 0):
                return depths[1] + depth_delta <= root_depth
            if is_in_live_zone() and not is_in_live_zone(deposition):
                removal_depth = depths[1] + deposition - root_depth
                mass = fx((depths[1] - removal_depth, depths[1]))
                organic, inorganic = mass * (1 - k3), mass * k3
                return (organic * fl, organic * fc, inorganic)
            else:
                # layer complete in our out of live zone (before and after).
                return (0, 0, 0)
        return burial
    return partial

class PartialTools:
    '''
    Holds partially parameterized biomass functions (intended for use as immutable object).
    
    Should be built on construction.
    '''
    def __init__(self, constants: Constants):
        self.partial_burial = burial_builder(constants)
        self.partial_erosion = erosion_builder(constants)
        self.partial_turnover = turnover_builder(constants)
        self.partial_integration = integration_builder(constants)
        self.partial_distribution = distribution_builder(constants)
        self.converter = conversion_builder(constants)

class Tools:
    '''
    Holds fully parameterized biomass functions (intended for use as immutable object).
    '''
    def __init__(self, partial_tools: PartialTools, integration: F_Integration):
        self.converter = partial_tools.converter
        self.burial = partial_tools.partial_burial(integration)
        self.erosion = partial_tools.partial_erosion(integration)
        self.turnover = partial_tools.partial_turnover(integration)

@dataclass(frozen=True)
class Biomass:
    '''Below ground biomass.'''
    val: float
    fxs: Tools
    tag: Tag = Tag.BIOMASS
    measurement: Measurement = Measurement.WEIGHT

    @property
    def length(self) -> float:
        '''Returns the length [in cm] of the biomass.'''
        if self.measurement == Measurement.LENGTH:
            return self.val
        return self.fxs.converter(self.val, self.tag, Measurement.LENGTH)
    @property
    def weight(self) -> float:
        '''Returns the weight [in g] of the biomass.'''
        if self.measurement == Measurement.WEIGHT:
            return self.val
        return self.fxs.converter(self.val, self.tag, Measurement.WEIGHT)

def factory(top: float, depths: Depths, tools: PartialTools) -> Biomass:
    '''
    Returns a biomass object.
    '''
    distribution = tools.partial_distribution(top)
    integration = tools.partial_integration(distribution)
    tools = Tools(tools, integration)
    return Biomass(integration(depths), tools)
