'''
Initialization for a single model grid cell.
'''
from typing import TypeAlias
from dataclasses import dataclass
from collections import namedtuple

import src.live as bio
import src.sediment as sed
from src.constants import Constants
from src.stock import Measurement, Stock

Depths: TypeAlias = tuple[float, float]
Stocks = namedtuple('Stocks', [
    ('live', Stock),
    ('labile', Stock),
    ('refractory', Stock),
    ('inorganic', Stock)])

@dataclass(frozen=True)
class Layer:
    '''
    A single timestep layer in a model grid cell.
    '''
    depths: Depths
    stocks: Stocks

@dataclass
class Cell:
    '''
    A model grid cell layered sediment core.
    '''
    elevation: float
    layers: list[Layer]

def factory(constants: Constants) -> Cell:
    '''
    Returns a model grid cell.
    '''
    return Cell(constants.du, [initial_layer(constants)])

def initial_layer(constants: Constants) -> Layer:
    '''
    Returns an initial layer for a model grid cell.
    '''
    live = bio.factory(bio.PartialTools(constants), constants.ro, (0, constants.depth))
    sediments = sed.factory(constants.depth - live.length, Measurement.LENGTH, constants)
    return Layer((0, constants.depth), Stocks(live, *sediments))
