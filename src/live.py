'''
Below ground biomass functions.
'''
import math
from dataclasses import dataclass
from typing import TypeAlias, Callable, Self

import numpy as np

from src.constants import Constants
from src.stock import Tag, Measurement, conversion_builder
from src.validators import non_negative_attribute, ascending_non_negative_attribute

# Aliases
Depths: TypeAlias = tuple[float, float]
Turnover: TypeAlias = tuple[float, float, float]

# pylint: disable=invalid-name #underscore typealias
F_Distribution: TypeAlias = Callable[[float], float]
F_Integration: TypeAlias = Callable[[Depths], float]
F_Turnover: TypeAlias = Callable[[float], Turnover]

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
        non_negative_attribute('top', top)
        def fx(depth: float) -> float:
            '''
            Returns:
                float: biomass [in g] at a given depth [in cm].
            '''
            non_negative_attribute('depth', depth)
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
        def integrate(depths: tuple[float, float]) -> float:
            '''
            Returns: 
                float: integral of the biomass distribution function [in g] across depths [in cm].
            '''
            ascending_non_negative_attribute('depths', depths)
            return (fx(depths[1]) - fx(depths[0])) / -k1
        return integrate
    return partial

def turnover_builder(constants: Constants) -> Callable[[F_Integration], F_Turnover]:
    '''
    Returns partially parameterized biomass turnover function.
    '''
    k2 = constants.k2
    fc = constants.fc
    fl = constants.fl
    def turnover(weight: float, years: float) -> Turnover:
        '''
        Computes biomass [in g] removed due to turnover [in dmls/yr].
            
        Returns:
            Tuple[float, float, float]: refractory, labile, inorganic [in g].
        '''
        non_negative_attribute('years', years)
        non_negative_attribute('weight', weight)
        return (
            weight * k2 * fl * years,
            weight * k2 * fc * years,
            0.0 # by assumption in Morris & Bowden (1986).
        )
    return turnover

def erosion_builder(constants: Constants) -> Callable[[F_Integration], F_Turnover]:
    '''
    Returns partially parameterized function removing biomass [in g] due to erosion [in cm].
    '''
    fc = constants.fc
    fl = constants.fl
    k3 = constants.k3
    def partial(fx: F_Integration) -> F_Turnover:
        '''Returns fully parameterized function removing biomass [in g] due to erosion [in cm].'''
        def erosion(depths: tuple[float, float], erosion: float) -> Turnover:
            '''
            Computes biomass [in g] removed due to erosion [in cm].
            
            Args:
                depths (Depths): top and bottom depths [in cm] of the layer.
                erosion (float): erosion [in cm] over the timestep. Must be non-negative.
            
            Returns:
                Tuple[float, float, float]: refractory, labile, inorganic [in g].
            '''
            non_negative_attribute('erosion', erosion)
            ascending_non_negative_attribute('depths', depths)
            length = min(depths[1] - depths[0], erosion)
            mass = fx((depths[0], depths[0] + length))
            return (mass * (1 - k3) * fl, mass * (1 - k3) * fc, mass * k3)
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
        def burial(depths: tuple[float, float], deposition: float) -> Turnover:
            '''
            Computes biomass [in g] removed due to burial [in cm].
            
            Args:
                depths (Depths): top and bottom depths [in cm] of the layer.
                deposition (float): deposition [in cm] over the timestep. Must be non-negative.
            
            Returns:
                Tuple[float, float, float]: refractory, labile, inorganic [in g].
            '''
            non_negative_attribute('deposition', deposition)
            ascending_non_negative_attribute('depths', depths)
            def is_in_live_zone(depth_delta: float = 0):
                return depths[1] + depth_delta <= root_depth
            if is_in_live_zone() and not is_in_live_zone(deposition):
                removal_depth = max(root_depth - deposition, depths[0])
                mass = fx((removal_depth, root_depth))
                organic, inorganic = mass * (1 - k3), mass * k3
                return (organic * fl, organic * fc, inorganic)
            else:
                # layer complete in our out of live zone (before and after).
                return (0, 0, 0)
        return burial
    return partial

@dataclass(frozen=True)
class Tools:
    '''
    Holds fully parameterized biomass functions (intended for use as immutable object).
    '''
    turnover: F_Turnover
    integration: F_Integration
    burial: Callable[[Depths, float], Turnover]
    erosion: Callable[[Depths, float], Turnover]
    converter: Callable[[float, Tag, Measurement], float]
    tools_builder: Callable[[float], Self]

class PartialTools:
    '''
    Holds partially parameterized biomass functions (intended for use as immutable object).
    
    Should be built on construction.
    '''
    def __init__(self, constants: Constants):
        self.partial_burial = burial_builder(constants)
        self.partial_erosion = erosion_builder(constants)
        self.partial_integration = integration_builder(constants)
        self.partial_distribution = distribution_builder(constants)
        self.turnover = turnover_builder(constants)
        self.converter = conversion_builder(constants)

    def make_tools(self, top: float) -> Tools:
        '''
        Returns a fully parameterized biomass functions.
        '''
        f = self.partial_distribution(top)
        integrate = self.partial_integration(f)
        return Tools(self.turnover, integrate,
                     self.partial_burial(integrate), self.partial_erosion(integrate),
                     self.converter, self.remake_tools_builder)

    @property
    def remake_tools_builder(self) -> Callable[[float], 'Tools']:
        '''
        Returns a function that returns a fully parameterized biomass functions.
        '''
        def remake_tools(top: float) -> 'Tools':
            '''
            Returns a fully parameterized biomass functions.
            '''
            return self.make_tools(top)
        return remake_tools

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

    def transfers(self, deposition: float, depths: Depths, yrs: float) -> tuple[Turnover, Turnover]:
        '''
        Computes turnover and burial or erosion [in g] of biomass over timeperiod [in yrs].
        
        By assumption, based on Morris & Bowden (1986) preceeding equation 10, "root uptake &
        root death are equivalent" thus turnover is instantaneous replaced in equal quantities
        by new living biomass. Therefore turnover is not substracted from the biomass stock
        before accounting for burial or erosion. As a result turnover is a net gain for the cohert.
        '''
        if deposition > 0:
            return (tuple(np.sum(self.fxs.turnover(self.weight, yrs), self.fxs.burial(depths, deposition))),  # pylint: disable=line-too-long
                    (0.0, 0.0 , 0.0)) # no losses from system.
        else: # erosion
            return (self.fxs.turnover(self.weight, yrs),
                    self.fxs.erosion(depths, -deposition)) # loss from system

    def remake(self, top: float) -> Self:
        '''
        Returns a new biomass object.
        '''
        return Biomass(self.val, self.fxs.tools_builder(top))

    def __eq__(self, other: Self) -> bool:
        '''Returns True if self and other are equal.'''
        return math.isclose(self.weight, other.weight, abs_tol=0.0001) and self.tag == other.tag

def factory(top: float, depths: tuple[float, float], partial_tools: PartialTools) -> Biomass:
    '''
    Returns a biomass object.
    '''
    tools = partial_tools.make_tools(top)
    return Biomass(tools.integration(depths), tools)
