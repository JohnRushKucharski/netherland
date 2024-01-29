'''
Initialization for a single model grid cell.
'''
import math
import operator
from dataclasses import dataclass
from typing import TypeAlias, Self

import src.live as bio
import src.sediment as sed
from src.data import logger
from src.constants import Constants
from src.stock import Measurement, Inactive
from src.validators import non_negative_attribute, positive_attribute

# TODO: add logging to cell.step_forward (may need to be 3D data array: x: stock, y: layer, z: time is simulation).
# TODO: enumerate backwards should also reverse index numbers so layer[-1] is index 0 and layer[0] is max index.
# TODO: data example in notebook, and add this to readme too, with output log files for single cell and multiple cells.
# TODO: marsh (e.g. all the cells in a marsh object since step_forward may provide entire array of updates).

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

    # def step_forward(self, deposition: float, biomass_at_surface: float, yrs: float,
    #                  is_top_layer: bool = False) -> Self:
    #     '''
    #     Steps the model grid cell forward one timestep.

    #     Ags:
    #         deposition (float): deposition/erosion(+/-) [in g] over timestep (in y).
    #         biomass_at_surface (float): biomass [in g/cm^2] at surface of layer.
    #         yrs (float): number of years to step forward.

    #     Returns:
    #         None: Updates layer in place.
    #     '''
    #     non_negative_attribute('yrs', yrs)
    #     non_negative_attribute('biomass_at_surface', biomass_at_surface)
    #     if deposition < 0 and self.depth < -deposition:
    #         # this condition should be delt with in the cell.step_forward function.
    #         raise ValueError(f'erosion {deposition} > layer depth {self.depth}')

    #     # 1. Biomass: (a) transfers: turnover (+) and burial (~) or erosion (-).
    #     turnover, erosion = self.stocks[0].transfers(deposition, self.depths, yrs)
    #     # 2. Sediments:
    #     # (a) transfers: decomposition (-) and ash uptake (-) out of sediment system (-),
    #     # (b) update: add from  biomass, (c) erosion: remove sediments (no deposition below top).
    #     bio_delta = self.stocks[0].fxs.converter(-sum(erosion), bio.Tag.BIOMASS, Measurement.LENGTH)
    #     sediments = self.stocks[1].transfers(yrs).update(turnover).erosion(-deposition-bio_delta)
    #     # 4. Adjust depth of layer from turnover(+), erosion(-), transfers out of system (-).
    #     sed_delta = sediments.length - self.stocks[1].length # loss will be negative.
    #     new_depths = (self.depths[0] + bio_delta + sed_delta, self.depths[1])
    #     # 5. Biomass: (a) grow in the new depth b/c deposition/erosion comes from seperate model.
    #     biomass = self.stocks[0].remake(biomass_at_surface)
    #     # 6. Update layer.
    #     return Layer(new_depths, (biomass, sediments))

    def step_forward(self, deposition: float, biomass_at_surface: float, yrs: float,
                    is_top_layer: bool = False) -> tuple[tuple[float, float], sed.Sediments]:
        '''
        Manages transfers in and out of stock variables.
        NOTE: Biomass stock is NOT updated.
        
        Computes in the following order:
        1. Biomass: (a) turnover (+), (b) burial (~) or erosion (-).
        2. Sediments: (a) labile decomposition (-), (b) inorganic ash uptake (-).
        3. Sediments: (a) add turnover and burial transfers from biomass (from step 1).
        4. Sediments: erosion (-) (remove eroded sediment less eroded biomass [from step 1]). 
        5. Sediments: add deposition (+) if is_top_layer is True, otherwise ignore this step.
        6. Adjust depth of layer from turnover(+), erosion(-), transfers out of system (-).
        
        Note:
            + represents a net gain for the layer.
            - represents a net loss for the layer.
            ~ represents transfer between stocks within layer.
            
        Returns:
            Layer: layer with updated layer depths and sediments stock (NO updates to biomass).
        '''
        non_negative_attribute('yrs', yrs)
        non_negative_attribute('biomass_at_surface', biomass_at_surface)
        if deposition < 0 and self.depth < -deposition:
            # this condition should be delt with in the cell.step_forward function.
            raise ValueError(f'erosion {deposition} > layer depth {self.depth}')
        # 1. Biomass - transfers: (a) turnover (+) (b) burial (~) or (c) erosion (-).
        turnover, burial, erosion = self.stocks[0].transfers(deposition, self.depths, yrs)
        # 2. Sediments transfers: (a) decomposition (-) and (b) ash uptake (-).
        # 3. Sediments update: add turnover (+) and burial transfers (~) from biomass.
        # 4. Sediments transfers: erosion (-) of sediments (after adjustment for biomass erosion).
        bio_inflow = tuple(map(operator.add, turnover, burial))
        bio_delta = self.stocks[0].fxs.converter(-sum(erosion), bio.Tag.BIOMASS, Measurement.LENGTH)
        sediments = self.stocks[1].transfers(yrs).update(bio_inflow).erosion(-deposition-bio_delta)
        # 5. Sediments update: add deposition (+) if is_top_layer, otherwise ignore this step.
        if is_top_layer and deposition > 0: # if deposition <= 0 this is pointless.
            sediments = sediments.update(self.stocks[1].tools.deposition(deposition))
        # 6. Adjust depth of layer from turnover(+), erosion(-), transfers out of system (-).
        sed_delta = sediments.length - self.stocks[1].length # loss will be negative.
        new_depths = (self.depths[0] + bio_delta + sed_delta, self.depths[1])
        # 7. Remake biomass stock with new biomass at surface and new depths.
        biomass = self.stocks[0].remake(biomass_at_surface, (new_depths[1] - new_depths[0]))
        ngrowth = self.stocks[0].val - (math.fsum(erosion) + math.fsum(burial)) - biomass.val
        if ngrowth > 0:
            removal = self.stocks[0].fxs.negative_growth(ngrowth)
            sediments = sediments.update(removal)
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
    @property
    def headers(self) -> tuple[str, ...]:
        '''Writes data headers for logging.'''
        return ('top', 'bottom', 'depth', 'biomass', 'labile', 'refractory', 'inorganic')
    @property
    def write_data(self) -> tuple[float,...]:
        '''Writes data for logging.'''
        return (self.top, self.bottom, self.depth,
                self.stocks[0].length, self.stocks[1].labile.length,
                self.stocks[1].refractory.length, self.stocks[1].inorganic.length)

def enumerate_backwards(data: list[any]|tuple[any,...]) -> tuple[int, any]:
    '''
    Enumerates a list or tuple backwards, or in case of cell from surface layer to bottom layer.
    '''
    for i in range(len(data)-1, -1, -1):
        yield (i, data[i])

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

    def depth_of_layer(self, index: int) -> float:
        '''Returns the depth of the top of the ith layer (from top of cell) [in cm].'''
        if index < 0 or index >= len(self.layers):
            raise IndexError(f'index {index} out of range')
        i: int = 0
        depth: float = 0
        while i < index:
            depth += self.layers[i].depth
            i += 1
        return depth

    def step_forward(self, dep: float, top: float, yrs: float, sub_steps: int = 1) -> Self:
        '''
        Steps model cell forward by specified number of years.
        
        Args:
            dep (float): deposition/erosion(+/-) [in g].
            top (float): biomass at surface of cell [in g/cm^2].
            yrs (float): length of timestep [in yrs].
            sub_steps (int): number of substeps to take. 1 by default.
            
        Returns:
            Cell: updated cell.
            
        Raises:
            ValueError: if top < 0, yrs < 0, or substeps < 1.
            
        Note: sub_steps is used to approximate a continuous time model.
        '''
        non_negative_attribute('yrs', yrs)
        non_negative_attribute('top', top)
        positive_attribute('sub_steps', sub_steps)
        layers = self.layers
        ddep, dtop, dt = dep/sub_steps, (top - self.top) / sub_steps, yrs/sub_steps # d_<var>/d_t
        for i in range(sub_steps):
            layers = self.__substep(ddep, self.top + dtop * (i + 1), dt, i, layers)
        return Cell(top, self.elevation, layers, self.tools)
        # Update top elevation.
        # --Interate downwards (calling Layer.step_forward).
        # Pass new bottom layer depth down to next layer (as top).
        # Pass total depositon OR left over erosion down to next layer (as deposition).
        # --Infer left over erosion from change in depth of updated layer.
        # Pass biomass at surface down to next layer (as biomass).
        # --Infer biomass at surface from previous layer biomass distribution fx.
        # Stop when left over erosion AND biomass at surface is zero.

    def __substep(self, deposition: float, top: float, years: float,
                i: int, layers: list[Layer]) -> list[Layer]:
        '''
        Steps model forward by less than a full timestep.
        
        Computes in the following order:
        1. Biomass distribution which applys to all layers in cell is computed.
        2. Depth of current top layer is computed (this increments at the bottom of the loop).
        3. Loop from surface to bottom layer of cell (i.e. last to first item, reverse order).
        4. Compute biomass as surface of current layer.
        5. Erosion versus deposition: is_top_layer if not first substep and first layer
        (a) deposition - if is_top_layer then sedimentation and burial, othersise only burial.
        (b) erosion - (negative deposition) less than or equal to layer depth.
        6. Update layer (see Layer.step_forward for details).

        Args:
            deposition (float): _description_
            top (float): _description_
            years (float): _description_
            i (int): _description_
            n (int): _description_
            layers (list[Layer]): _description_

        Returns:
            list[Layer]: _description_
        '''
        # 1. Biomass Distribution applies to entire cell.
        f = self.tools[0].partial_distribution(top)
        # 2. Depth of top of current layer, if this is the first pass
        # then i == 0 and we start on the "second" layer, then starting depth
        # (for the top of the first layer in the loop) is below the deposition.
        depth = 0 if deposition < 0 or i != 0 else deposition
        # 3. Loop from top to bottom layer = last to first item in list.
        for j, layer in enumerate_backwards(layers): # top to bottom
            # 4. biomass at surface of layer
            dtop = top if depth == 0 else f(depth)
            # 5. Erosion versus deposition and burial tracks.
            is_top_layer = i != 0 and j==0 # false if first pass or not top layer.
            ddep = max(deposition, -layer.depth) if deposition < 0 else deposition
            # 6. Update layer.
            layers[j] = layer.step_forward(ddep, dtop, years, is_top_layer)
            derosion = ddep if deposition < 0 else 0
            deposition -= derosion # left over erosion.
            depth += layer.depth
        if i == 0: # first pass
            layers.append(self.top_layer(deposition, top))
        return layers

    # def __substep(self, deposition: float, top: float, yrs: float,
    #               is_first_pass: bool) -> list[Layer]:
    #     '''
    #     Adds or updates top layer, updates existing layers.

    #     Returns:
    #         tuple[bool, list[Layer]]: updated top layer and list of updated layers.
    #     '''
    #     f = self.tools[0].partial_distribution(top)
    #     def update_layers():
    #         '''Updates existing layers.'''
    #         for i, layer in enumerate(self.layers[1:]):
    #             db = top if i == 0 else f(layer.depths[0])                              # biomass
    #             de = max(deposition, -layer.depth) if deposition < 0 else deposition    # erosion

    #     if is_first_pass:

    #     f = self.tools[0].partial_distribution(top)
    #     for i, layer in enumerate(layers[1]):
    #         db = top if i == 0 else f(layer.depths[0])                              # biomass
    #         de = max(deposition, -layer.depth) if deposition < 0 else deposition    # erosion
    #         self.layers[i] = layer.step_forward(de, db, yrs)
    #         deposition = deposition - de if de < 0 else deposition                  # left over erosion

    #     self.layers.append(self.top_layer(deposition, top))
    #     self.elevation = self.elevation + deposition
    #     self.top = top
    #     # check if dep < 0 does dep goto 0
    #     # check if dep > 0 only affect layes in rd
    #     # check does db only affect layers in rd
    #     # check does db goto 0


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
