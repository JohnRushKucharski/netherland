'''
Validation functions for input parameters.
'''
from typing import Any, Callable

def non_negative_attribute(key: str, value: float|int) -> None:
    '''Validates attribute is non-negative.'''
    if isinstance(value, (float, int)) and not isinstance(value, bool) and value < 0:
        raise ValueError(f'{key} must be non-negative.')

def non_negative(fx: Callable[...,Any]) -> Callable[...,Any]:  # pylint: disable=invalid-name
    '''Decorator that validates non-negative inputs.'''
    def validator(**kwargs) -> Any:
        for key, value in kwargs.items():
            non_negative_attribute(key=key, value=value)
        return fx(**kwargs)
    return validator

def positive_attribute(key: str, value: float|int) -> None:
    '''Validates attribute is positive.'''
    if isinstance(value, (float, int)) and not isinstance(value, bool) and value <= 0:
        raise ValueError(f'{key} must be non-negative.')

def descending_attribute(key: str, value: list|tuple) -> None:
    '''Validates tuple or list is in descending order.'''
    for index, item in enumerate(value):
        if not isinstance(item, (float, int)):
            break
        if index > 0 and item > value[index-1]:
            raise ValueError(f'{key}: {value} values must in decending order.')

def ascending_non_negative_attribute(key: str, value: list|tuple) -> None:
    '''Validates tuple or list is in ascending order and non-negative.'''
    for index, item in enumerate(value):
        if not isinstance(item, (float, int)):
            break
        if index > 0 and item < value[index-1]:
            raise ValueError(f'{key}: {value} values must in accending order.')
        non_negative_attribute(key=key, value=item)
