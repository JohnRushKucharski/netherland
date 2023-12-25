'''
Initialization for a single model grid cell.
'''
from dataclasses import dataclass
from typing import TypeAlias, Self

import src.live as bio
import src.sediment as sed
from src.constants import Constants
from src.stock import Measurement, Inactive, factory as inactive_factory

Depths: TypeAlias = tuple[float, float]
Stocks: TypeAlias = tuple[bio.Biomass, sed.Sediments]
Inactives: TypeAlias = tuple[Inactive, Inactive, Inactive]

@dataclass(frozen=True)
class Layer:
    '''
    A single timestep layer in a model grid cell.
    '''
    depths: Depths
    stocks: Stocks

    def step_forward(self, deposition: float, biomass_at_surface: float, yrs: float) -> Self:
        '''
        Steps the model grid cell forward one timestep.
        
        Ags:
            deposition (float): deposition/erosion(+/-) [in g] over timestep (in y).
            biomass_at_surface (float): biomass [in g/cm^2] at surface of layer.
            yrs (float): number of years to step forward.
        
        Returns:
            None: Updates layer in place.
        '''
        # TODO: if -deposition (erosion)  > self.depth empty layer.
        # 1. Biomass: (a) transfers: turnover (+) and burial (~) or erosion (-).
        turnover, erosion = self.stocks[0].transfers(deposition, self.depths, yrs)
        # 2. Sediments:
        # (a) transfers: decomposition (-) and ash uptake (-) out of sediment system (-),
        # (b) update: add from  biomass, (c) erosion: remove sediments (no deposition below top).
        sediments = self.stocks[1].transfers(yrs).update(turnover).erosion(deposition - erosion)
        # 4. Adjust depth of layer from turnover(+), erosion(-), transfers out of system (-).
        bio_delta = self.stocks[0].fxs.converter(-erosion, bio.Tag.BIOMASS, Measurement.LENGTH)
        sed_delta = sediments.length - self.stocks[1].length # loss will be negative.
        new_depths = (self.depths[0] + bio_delta + sed_delta, self.depths[1])
        # 5. Biomass: (a) grow in the new depth b/c deposition/erosion comes from seperate model.
        biomass = bio.factory(self.stocks[0].fxs, biomass_at_surface, new_depths)
        # 6. Update layer.
        return Layer(new_depths, Stocks(biomass, sediments))

    @property
    def depth(self) -> float:
        '''Returns the depth of the layer.'''
        return self.depths[1] - self.depths[0]


@dataclass
class Cell:
    '''
    A model grid cell layered sediment core.
    '''
    elevation: float
    layers: list[Layer]

    def step_forward(self, deposition: float, biomass_at_surface: float, years: float) -> None:
        '''
        Steps the model grid cell forward one timestep.
        '''
        # Update top elevation.
        # --Interate downwards (calling Layer.step_forward).
        # Pass new bottom layer depth down to next layer (as top).
        # Pass total depositon OR left over erosion down to next layer (as deposition).
        # --Infer left over erosion from change in depth of updated layer.
        # Pass biomass at surface down to next layer (as biomass).
        # --Infer biomass at surface from previous layer biomass distribution fx.
        # Stop when left over erosion AND biomass at surface is zero.

def enumerate_backwards(data: list[any] | tuple[any, ...]) -> tuple[int, any]:
    '''Enumerates over collection in reverse order.'''
    for index, item in enumerate(reversed(data)):
        yield index, item

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
    return Layer((0, constants.depth), Stocks(live, sediments))
