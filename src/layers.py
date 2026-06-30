'''
Main computational module
'''
from dataclasses import dataclass
from typing import Tuple, TypeAlias

from src.constants import Constants
from src.live import PartialTools

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
