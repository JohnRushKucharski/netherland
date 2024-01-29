'''Supports data logging.'''
import csv
from typing import Callable
from dataclasses import dataclass, field

REGISTRY: dict[int, 'Log'] = {}

@dataclass
class Log:
    '''Stores cell data for logging.'''
    headers: tuple[str, ...] = field(default_factory=tuple)
    data: list[tuple[float, ...]] = field(default_factory=list)
    '''Data is in format:
            stock_1, stock_2, ..., stock_n
        0   x_1,     x_2,     ..., x_n  
        1       ...
        ...         ...
        t-1             ...
        t   x_1,     x_2,     ..., x_n
    '''

    def write(self, csv_path: str) -> None:
        '''Writes data to a csv file.'''
        with open(csv_path, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(self.headers)
            for row in self.data:
                if isinstance(row, (tuple, list)):
                    writer.writerow(row)
                else:
                    writer.writerow((row,))

def logger(f: Callable[..., tuple[float,...]]) -> Callable[..., tuple[float,...]]:
    '''Decorator that wraps a function (i.e. cell.step_forward()) to log its output.'''
    is_initialized: bool = False
    def wrapper(*args, **kwargs) -> tuple[float,...]:
        output = f(*args, **kwargs)
        if not is_initialized:
            log = Log()
            log.headers = args[0].output_headers
            REGISTRY[args[0].id] = log
        log.data.append(output)
        return output
    return wrapper
