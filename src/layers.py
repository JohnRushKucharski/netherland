'''
Main computational module
'''
from dataclasses import dataclass
from typing import Tuple, TypeAlias

from src.constants import Constants
from src.biomass import PartialTools, Tools

Depths: TypeAlias = Tuple[float, float] # top, bottom
Stocks: TypeAlias = Tuple[float, float, float, float] # biomass, refractory, labile, inorganic

@dataclass(frozen=True)
class Layer:
    '''
    Timestep layer of sediment.
    '''
    depths: Depths
    active_stocks: Stocks

Layers: TypeAlias = Tuple[Layer, ...]

def initialize(constants: Constants) -> Tuple[PartialTools, Layers]:
    '''
    Returns a single layer of sediment with initial biomass.
    '''
    ptools = PartialTools(constants)
    tools = Tools(ptools, top=constants.ro)
    live_mass = tools.mass((constants.du, constants.db))
    #sediment =
    return (Layer(depths=(constants.du, constants.db),
                  active_stocks=(constants.ro, 0, 0, 0)),)
