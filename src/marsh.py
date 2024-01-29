'''A marsh composed of many cells.'''
from dataclasses import dataclass
from typing import Dict

from src.cell import Cell, factory
from src.constants import import_file

@dataclass
class Marsh:
    '''
    A marsh composed of many cells.
    '''
    input_path: str
    output_dir: str
    cells: dict[int, Cell]

    def step_forward(self, cell_inputs: Dict[int, tuple[float, float]],
                     yrs: float, substeps: float = 1.0) -> None:
        '''
        Steps all cells in the marsh forward in time.
        
        Args:
            cell_inputs (dict[int, tuple[float, float]]): cell
                deposition [in cm] and
                biomass at surface [in g/cm2] inputs keyed by cell id.
            yrs (float): length of timestep [in yrs].
            substeps (float): number of substeps to take. 1 by default.
        '''
        for cell_id, (dep, top) in cell_inputs.items():
            self.cells[cell_id].step_forward(dep, top, yrs, substeps)

def initialize(input_file: str, output_directory: str) -> Marsh:
    '''Constructs a marsh from an input file.

    Args:
        input_file (str): path to an *.toml import file containing constants.
        output_directory (str): path to an output directory for writing out data.

    Returns:
        Marsh: A marsh composed of many cells.
    '''
    cells = {constants.id: factory(constants) for constants in import_file(input_file)}
    return Marsh(input_file, output_directory, cells)
