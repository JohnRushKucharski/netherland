'''
Initialization for a single model grid cell.
'''
from dataclasses import dataclass
from typing import TypeAlias, Self

import src.live as bio
import src.sediment as sed
from src.constants import Constants
from src.stock import Measurement, Inactive
from src.validators import non_negative_attribute, positive_attribute

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
        non_negative_attribute('yrs', yrs)
        non_negative_attribute('biomass_at_surface', biomass_at_surface)
        if deposition < 0 and self.depth < -deposition:
            # this condition should be delt with in the cell.step_forward function.
            raise ValueError(f'erosion {deposition} > layer depth {self.depth}')
        # 1. Biomass: (a) transfers: turnover (+) and burial (~) or erosion (-).
        turnover, erosion = self.stocks[0].transfers(deposition, self.depths, yrs)
        # 2. Sediments:
        # (a) transfers: decomposition (-) and ash uptake (-) out of sediment system (-),
        # (b) update: add from  biomass, (c) erosion: remove sediments (no deposition below top).
        bio_delta = self.stocks[0].fxs.converter(-sum(erosion), bio.Tag.BIOMASS, Measurement.LENGTH)
        sediments = self.stocks[1].transfers(yrs).update(turnover).erosion(-deposition-bio_delta)
        # 4. Adjust depth of layer from turnover(+), erosion(-), transfers out of system (-).
        sed_delta = sediments.length - self.stocks[1].length # loss will be negative.
        new_depths = (self.depths[0] + bio_delta + sed_delta, self.depths[1])
        # 5. Biomass: (a) grow in the new depth b/c deposition/erosion comes from seperate model.
        biomass = self.stocks[0].remake(biomass_at_surface)
        # 6. Update layer.
        return Layer(new_depths, (biomass, sediments))

    def __eq__(self, other: Self) -> bool:
        '''Layer equality.'''
        isequal = True if self.depths == other.depths else False
        for i, stock in enumerate(self.stocks):
            isequal = isequal if stock.__eq__(other.stocks[i]) else False
        return isequal

    @property
    def top(self) -> float:
        '''Returns the top depth of the layer [in cm].'''
        return self.depths[0]
    @property
    def bottom(self) -> float:
        '''Returns the bottom depth of the layer [in cm].'''
        return self.depths[1]
    @property
    def depth(self) -> float:
        '''Returns the depth of the layer [in cm].'''
        return self.depths[1] - self.depths[0]

@dataclass
class Cell:
    '''
    A model grid cell layered sediment core.
    '''
    top: float
    '''Biomass at surface of cell [in g/cm^2].'''
    elevation: float
    '''Ground elevation [in cm].'''
    layers: list[Layer]
    '''List of layers in the cell.'''
    tools: tuple[bio.PartialTools, sed.Tools]
    '''Utilities for managing biomass and sediment stocks.'''

    def depth(self) -> float:
        '''Returns the depth of the cell [in cm].'''
        return self.layers[-1].depths[1]

    def step_forward(self, dep: float, top: float, yrs: float, sub_steps: int = 1) -> None:
        '''
        Steps model cell forward by specified number of years.
        
        Args:
            dep (float): deposition/erosion(+/-) [in g].
            top (float): biomass at surface of cell [in g/cm^2].
            yrs (float): length of timestep [in yrs].
            sub_steps (int): number of substeps to take. 1 by default.
            
        Returns:
            None: Updates cell in place.
            
        Raises:
            ValueError: if top < 0, yrs < 0, or substeps < 1.
            
        Note: sub_steps is used to approximate a continuous time model.
        '''
        non_negative_attribute('yrs', yrs)
        non_negative_attribute('top', top)
        positive_attribute('sub_steps', sub_steps)
        ddep, dtop, dt = dep/sub_steps, (top - self.top) / sub_steps, yrs/sub_steps # d_<var>/d_t
        for t in range(sub_steps):
            self.__substep(ddep, self.top + dtop * (t + 1), dt)
        # Update top elevation.
        # --Interate downwards (calling Layer.step_forward).
        # Pass new bottom layer depth down to next layer (as top).
        # Pass total depositon OR left over erosion down to next layer (as deposition).
        # --Infer left over erosion from change in depth of updated layer.
        # Pass biomass at surface down to next layer (as biomass).
        # --Infer biomass at surface from previous layer biomass distribution fx.
        # Stop when left over erosion AND biomass at surface is zero.

    def __substep(self, dep: float, top: float, yrs: float) -> None:
        '''
        Same as step_forward but for a substep.
        '''
        f = self.tools[0].partial_distribution(top)
        for i, layer in enumerate(self.layers):
            db = top if i == 0 else f(layer.depths[0])
            de = max(dep, -layer.depth) if dep < 0 else dep
            self.layers[i] = layer.step_forward(de, db, yrs)
            dep = dep - de if de < 0 else dep
        self.layers.append(self.top_layer(dep, top))
        self.elevation = self.elevation + dep
        self.top = top
        # check if dep < 0 does dep goto 0
        # check if dep > 0 only affect layes in rd
        # check does db only affect layers in rd
        # check does db goto 0


        # i: int = 0
        # while (erosion:= dep) < 0 and (dtop:= f(self.layers[i].depths[0])) > 0:
        #     de = max(erosion, -self.layers[i].depth) # d_erosion/d_layer
        #     self.layers[i] = self.layers[i].step_forward(de, dtop, yrs)
        #     erosion = erosion - de
        #     i = i + 1
        # if (erosion:= dep) < 0:
        #     for i, layer in enumerate(self.layers):
        #         # while dep < 0 layer.depths[0] < constants.rd
        #         de = max(dep, -layer.depth) # d_erosion/d_layer
        #         dtop = top if i == 0 else f(self.layers[i-1].depths[0])
        #         self.layers[i] = layer.step_forward(de, dtop, yrs)
        #         dep = dep - de
        #     self.layers.append(self.empty_layer())
        # else:
        #     #deposition & burial
        #     # top will be top below new layer
        #     pass
        # # cell properties to update in any case
        # self.elevation = self.elevation + dep
        # self.top = top

    # def empty_layer(self) -> Layer:
    #     '''
    #     Creates an empty layer, with no biomass and no sediments when deposition <= 0.
    #     Useful for timesteps with erosion.
    #     '''
    #     return Layer((0, 0),
    #                  (bio.factory(0, (0, 0), self.tools[0]),
    #                   sed.factory(0, self.tools[1], Measurement.LENGTH)))

    def top_layer(self, dep: float, top: float) -> Layer:
        '''
        Creates a new layer, with biomass.
        '''
        return Layer((0, dep),
                     (bio.factory(top, (0, dep), self.tools[0]),
                      sed.factory(dep, self.tools[1], Measurement.LENGTH)))

def enumerate_backwards(data: list[any] | tuple[any, ...]) -> tuple[int, any]:
    '''Enumerates over collection in reverse order.'''
    for index, item in enumerate(reversed(data)):
        yield index, item

def initial_layer(constants: Constants) -> Layer:
    '''
    Returns an initial layer for a model grid cell.
    '''
    live = bio.factory(constants.ro, (0, constants.depth), bio.PartialTools(constants))
    sediments = sed.factory(constants.depth - live.length, sed.Tools(constants), Measurement.LENGTH)
    return Layer((0, constants.depth), (live, sediments))

def factory(constants: Constants) -> Cell:
    '''
    Returns a model grid cell.
    '''
    return Cell(constants.ro, constants.du, [initial_layer(constants)],
                (bio.PartialTools(constants), sed.Tools(constants)))
