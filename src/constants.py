'''
The model requires the parameterization of a large number of constants.

This module reads a constants.toml files and generates an immutable Constants dataclass.
'''

import tomllib
from pathlib import Path
from typing import Callable
from dataclasses import dataclass

MORRIS_CONSTANTS: str = str(Path(__file__).parent.parent.
                            joinpath('data').joinpath('morris_constants.toml'))

@dataclass(frozen=True)
class ImportFileConstants:
    '''
    Model constants from import file. Uses Morris & Bowden's (1986) notation.
    
    Used for validation, then passed to grid cell constants class.
    '''
    # sediment core properties
    ids: tuple[int, ...]
    '''Sediment core ids.'''
    surface_areas: tuple[float, ...]
    '''Surface areas [in cm2].'''

    # initial layer properties
    du: tuple[float, ...]
    '''Initial top elevation [in cm].'''
    db: tuple[float, ...]
    '''Initial bottom elevation [in cm].'''

    # properties of stock variables
    bo: tuple[float, ...]
    '''Bulk density of organic matter [in g/cm3].'''
    bi: tuple[float, ...]
    '''Bulk density of inoganic matter [in g/cm3].'''
    fo: tuple[float, ...]
    '''Fraction of sediment that is organic [dmls].'''

    # refractory and labile content properties
    k: tuple[float, ...]
    '''Specific decay constant for labile organic material [in 1/yr].'''
    fc: tuple[float, ...]
    '''Fraction of sediment that is refractory [dmls].'''

    # biomass properties
    ro: tuple[float, ...]
    '''Initial live below ground biomass at surface 
    (assumed constant across surface area) [in g/cm2].'''
    rd: tuple[float, ...]
    '''Maximum root depth [in cm].'''
    k1: tuple[float, ...]
    '''Distribution parameter for below ground biomass a function of depth 
    (assumed constant across surface area) [in 1/cm].'''
    k2: tuple[float, ...]
    '''Turnover rate of below ground biomass (a portion) [in 1/yr].'''
    k3: tuple[float, ...]
    '''Portion of plant matter that is inorganic ash [dmls].'''

    # litter properties
    sv_to_ro: tuple[float, ...]
    '''Conversion factor for converting stem volume (from NBSDynamics) 
    into live biomass concentration at sediment surface (ro) [dmls].'''
    wa_to_rl: tuple[float, ...]
    '''Ratio of above ground biomass production to below ground biomass [dmls].'''
    b: tuple[float, ...]
    '''
    Factor decribing net transport of litter over cell [dmls].
        =0: no retention of litter.
        <1: net outflux.
        =1: no transport or influx = outflux.
        >1: net influx.
    '''

    def __post_init__(self):
        #pylint: disable=line-too-long
        for i, id_ in enumerate(self.ids):
            if self.ids.count(id_) > 1:
                raise ValueError(f'The id: {id_} is not unique.')
            if self.surface_areas[i] <= 0:
                raise ValueError(f'At id: {id_}, sa: {self.surface_areas[i]} (surface area [in cm2]) must be greater than 0.')
            if self.du[i] <= self.db[i]:
                raise ValueError(f'At id: {id_}, du: {self.du[i]} (top elevation [in cm]) must be greater than db: {self.db[i]} (bottom elevation [in cm]).')
            if self.bo[i] <= 0:
                raise ValueError(f'At id: {id_}, bo: {self.bo[i]} (bulk density of organic matter [in g/cm3]) must be greater than 0.')
            if self.bi[i] <= 0:
                raise ValueError(f'At id: {id_}, bi: {self.bi[i]} (bulk density of inorganic matter [in g/cm3]) must be greater than 0.')
            if self.fo[i] < 0 or self.fo[i] > 1:
                raise ValueError(f'At id: {id_}, fo: {self.fo[i]} (fraction of sediment that is organic [dmls]) must be greater than 0 and less than 1.')
            if self.fi[i] < 0 or self.fi[i] > 1:
                raise ValueError(f'At id: {id_}, fi: {self.fi[i]} (fraction of sediment that is inorganic [dmls]) must be greater than 0 and less than 1.')
            if self.fo[i] + self.fi[i] != 1:
                raise ValueError(f'At id: {id_}, fo: {self.fo[i]} (fraction of sediment that is organic [dmls]) plus fi: {self.fi[i]} (fraction of sediment that is inorganic [dmls]) must equal 1.')
            if self.k[i] <= 0:
                raise ValueError(f'At id: {id_}, k: {self.k[i]} (specific decay constant for labile organic material [in 1/yr]) must be greater than 0.')
            if self.fc[i] < 0 or self.fc[i] > 1:
                raise ValueError(f'At id: {id_}, fc: {self.fc[i]} (fraction of sediment that is refractory [dmls]) must be greater than 0 and less than 1.')
            if self.fc[i] + self.fl[i] != 1:
                raise ValueError(f'At id: {id_}, fc: {self.fc[i]} (fraction of sediment that is refractory [dmls]) plus fl: {self.fl[i]} (fraction of sediment that is labile [dmls]) must equal 1.')
            if self.ro[i] < 0:
                raise ValueError(f'At id: {id_}, ro: {self.ro[i]} (initial live below ground biomass at surface [in g/cm2]) must be greater than or equal to 0.')
            if self.rd[i] <= 0:
                raise ValueError(f'At id: {id_}, rd: {self.rd[i]} (maximum root depth [in cm]) must be greater than 0.')
            if (self.du[i] - self.db[i]) < self.rd[i]:
                raise ValueError(f'At id: {id_}, initial layer depth: {self.du[i] - self.db[i]} (du: {self.du[i]} - db: {self.db[i]}) must be greater than or equal to the maximum root depth: {self.rd[i]}.')
            if self.k1[i] <= 0 or self.k1[i] >= 1:
                raise ValueError(f'At id: {id_}, k1: {self.k1[i]} (distribution parameter for below ground biomass a function of depth [in 1/cm]) must be greater than 0 and less than 1.')
            if self.k2[i] <= 0:
                raise ValueError(f'At id: {id_}, k2: {self.k2[i]} (turnover rate of below ground biomass [in 1/yr]) must be greater than 0.')
            if self.k3[i] < 0 or self.k3[i] > 1:
                raise ValueError(f'At id: {id_}, k3: {self.k3[i]} (portion of plant matter that is inorganic ash [dmls]) must be greater than 0 and less than 1.')
            if self.sv_to_ro[i] <= 0:
                raise ValueError(f'At id: {id_}, sv_to_ro: {self.sv_to_ro[i]} (conversion factor for converting stem volume (from NBSDynamics) into live biomass concentration at sediment surface (ro) [dmls]) must be greater than 0.')
            if self.wa_to_rl[i] <= 0:
                raise ValueError(f'At id: {id_}, wa_to_rl: {self.wa_to_rl[i]} (ratio of above ground biomass production to below ground biomass [dmls]) must be greater than 0.')

    @property
    def depth(self) -> tuple[float, ...]:
        '''
        Depth of the soil layer [in cm].
        '''
        return tuple(du - db for du, db in zip(self.du, self.db))
    @property
    def fi(self) -> tuple[float, ...]:
        '''
        Fraction of sediment that is inorganic [dmls].
        '''
        return tuple(1 - fo for fo in self.fo)
    @property
    def fl(self) -> tuple[float, ...]:
        '''
        Fraction of sediment that is labile [dmls].
        '''
        return tuple(1 - fc for fc in self.fc)

@dataclass(frozen=True)
class Constants:
    '''
    Constants for a model grid cell.
    '''
    # sediment core properties
    id: int
    '''Sediment core id.'''
    sa: float
    '''Surface area [in cm2].'''

    # initial layer properties
    du: float
    '''Initial top elevation [in cm].'''
    db: float
    '''Initial bottom elevation [in cm].'''

    # properties of stock variables
    bo: float
    '''Bulk density of organic matter [in g/cm3].'''
    bi: float
    '''Bulk density of inoganic matter [in g/cm3].'''
    fo: float
    '''Fraction of sediment that is organic [dmls].'''

    # refractory and labile content properties
    k: float
    '''Specific decay constant for labile organic material [in 1/yr].'''
    fc: float
    '''Fraction of sediment that is refractory [dmls].'''

    # biomass properties
    ro: float
    '''Initial live below ground biomass at surface 
    (assumed constant across surface area) [in g/cm2].'''
    rd: float
    '''Maximum root depth [in cm].'''
    k1: float
    '''Distribution parameter for below ground biomass a function of depth 
    (assumed constant across surface area) [in 1/cm].'''
    k2: float
    '''Turnover rate of below ground biomass (a portion) [in 1/yr].'''
    k3: float
    '''Portion of plant matter that is inorganic ash [dmls].'''

    # litter properties
    sv_to_ro: float
    '''Conversion factor for converting stem volume (from NBSDynamics) 
    into live biomass concentration at sediment surface (ro) [dmls].'''
    wa_to_rl: float
    '''Ratio of above ground biomass production to below ground biomass [dmls].'''
    b: float
    '''
    Factor decribing net transport of litter over cell [dmls].
        =0: no retention of litter.
        <1: net outflux.
        =1: no transport or influx = outflux.
        >1: net influx.
    '''

    @property
    def depth(self) -> float:
        '''
        Depth of the soil layer [in cm].
        '''
        return self.du - self.db
    @property
    def fi(self) -> float:
        '''
        Fraction of sediment that is inorganic [dmls].
        '''
        return 1 - self.fo
    @property
    def fl(self) -> float:
        '''
        Fraction of sediment that is labile [dmls].
        '''
        return 1 - self.fc
    @property
    def organic_g_to_cm3(self) -> Callable[[float], float]:
        '''
        Returns 1/self.bo constant [in cm3/g] for g to cm3 conversion.
        '''
        return 1 / self.bo
    @property
    def inorganic_g_to_cm3(self) -> Callable[[float], float]:
        '''
        Returns 1/self.bi constant [in cm3/g] for g to cm3 conversion.
        '''
        return 1 / self.bi
    @property
    def organic_converter_g_to_cm(self) -> Callable[[float], float]:
        '''
        Converts g to cm.
        
        Returns: 
            Function takes weight [in g], computes: g * (cm3/g) * (1/cm2) returning a length in cm.
        '''
        return lambda g: g * self.organic_g_to_cm3 / self.sa
    @property
    def inorganic_converter_g_to_cm(self) -> Callable[[float], float]:
        '''
        Converts g to cm.
        
        Returns: 
            Function takes weight [in g], computes: g * (cm3/ g) * (1/cm2) returning a length in cm.
        '''
        return lambda g: g * self.inorganic_g_to_cm3 / self.sa
    @property
    def organic_converter_cm_to_g(self) -> Callable[[float], float]:
        '''
        Converts cm to g.
        
        Returns: 
            Function takes length [in cm], computes: cm * (cm2) * (g/cm3) returning a weight in g.
        '''
        return lambda cm: cm * self.sa * self.bo
    @property
    def inorganic_converter_cm_to_g(self) -> Callable[[float], float]:
        '''
        Converts cm to g.
        
        Returns: 
            Function takes length [in cm], computes: cm * (cm2) * (g/cm3) returning a weight in g.
        '''
        return lambda cm: cm * self.sa * self.bi

def parse_ids(ids: list[any]) -> tuple[int, ...]:
    '''
    Parses a list of ids.
    '''
    if ids[1] == '...':
        if len(ids) != 3:
            raise ValueError('Too many values after "...".')
        ids = tuple(range(ids[0], ids[2] + 1))
    for id_ in ids:
        if ids.count(id_) > 1:
            raise ValueError(f'The id: {id_} is not unique.')
    return tuple(map(int, ids))

def parse_var(var: list[any], n_ids: int) -> tuple[float, ...]:
    '''
    Parses a list of surface areas.
    '''
    if var[1] == '...':
        if len(var) != 2:
            raise ValueError('Invalid value after "...".')
        var = [var[0]] * n_ids
    if len(var) != n_ids:
        raise ValueError('The number of variable entries must match the number of ids.')
    return tuple(map(float, var))

def import_file(path: str = MORRIS_CONSTANTS) -> tuple[Constants, ...]:
    '''
    Reads a constants.toml file and returns a tuple of constants.
    '''
    with open(path, 'rb') as file:
        data = tomllib.load(file)
        # sediment core properties
        ids = parse_ids(data['core']['ids'])
        n = len(ids)
        surface_areas = parse_var(data['core']['surface_areas'],  n)

        # initial layer properties
        du = parse_var(data['layer']['du'], n)
        db = parse_var(data['layer']['db'], n)
        # stock properties
        bo = parse_var(data['stocks']['bo'], n)
        bi = parse_var(data['stocks']['bi'], n)
        fo = parse_var(data['stocks']['fo'], n)
        # refractory and labile content properties
        k = parse_var(data['stocks']['k'], n)
        fc = parse_var(data['stocks']['fc'], n)
        # biomass properties
        ro = parse_var(data['stocks']['ro'], n)
        rd = parse_var(data['stocks']['rd'], n)
        k1 = parse_var(data['stocks']['k1'], n)
        k2 = parse_var(data['stocks']['k2'], n)
        k3 = parse_var(data['stocks']['k3'], n)
        # litter properties
        sv_to_ro = parse_var(data['stocks']['sv_to_ro'], n)
        wa_to_rl = parse_var(data['stocks']['wa_to_rl'], n)
        b = parse_var(data['stocks']['b'], n)
    file_constants = ImportFileConstants(
        ids, surface_areas,
        du, db,
        bo, bi, fo,
        k, fc,
        ro, rd, k1, k2, k3,
        sv_to_ro, wa_to_rl, b)
    return tuple(_factory(file_constants, i) for i in range(n))

def _factory(file_constants: ImportFileConstants, i: int) -> Constants:
    '''
    Returns a model grid cell's constants.
    '''
    return Constants(
        id=file_constants.ids[i],
        sa=file_constants.surface_areas[i],
        du=file_constants.du[i],
        db=file_constants.db[i],
        bo=file_constants.bo[i],
        bi=file_constants.bi[i],
        fo=file_constants.fo[i],
        k=file_constants.k[i],
        fc=file_constants.fc[i],
        ro=file_constants.ro[i],
        rd=file_constants.rd[i],
        k1=file_constants.k1[i],
        k2=file_constants.k2[i],
        k3=file_constants.k3[i],
        sv_to_ro=file_constants.sv_to_ro[i],
        wa_to_rl=file_constants.wa_to_rl[i],
        b=file_constants.b[i]
    )
