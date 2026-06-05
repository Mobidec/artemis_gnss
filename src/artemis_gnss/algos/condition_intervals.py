#!python3
# -*- coding: utf-8 -*-
"""
Functions to find the extremity indexes of the intervals of a given condition
Created on 20/09/24
"""
from typing import Tuple

import numpy as np
from numpy.typing import NDArray

from numba import jit


def propagate_diff_cond(diff_cond_1: NDArray[np.bool]) -> NDArray[np.bool]:
    """
    Propagate a condition which was computed on a diffed signal d_i = x_i+1 - x_i to the both indexes of x
    :param diff_cond_1:
    :return:
    """
    if len(diff_cond_1) == 0:
        return np.array([False])
    return np.logical_or(np.insert(diff_cond_1, 0, diff_cond_1[0]),
                         np.append(diff_cond_1, diff_cond_1[-1]))


@jit(nopython=True)
def get_condition_intervals(condition: NDArray[np.bool]) -> Tuple[NDArray[np.int64], NDArray[np.int64]]:
    # condition_ext = np.concatenate((np.ndarray([False]), condition, np.ndarray([False])))
    # condition_ext = np.append(np.insert(condition, False, axis=0), False, axis=0)
    condition_ext = np.full((len(condition)+2,), False)
    condition_ext[1:-1] = condition
    I_begins = np.where(condition_ext[1:] & ~condition_ext[:-1])[0]
    I_ends = np.where(~condition_ext[1:] & condition_ext[:-1])[0] - 1
    assert(len(I_begins) == len(I_ends))
    assert(np.all(I_begins <= I_ends))
    return I_begins, I_ends


@jit(nopython=True)
def hold_values(values: np.array, condition: NDArray[np.bool], init: float=0.) -> np.array:
    I_begins, I_ends = get_condition_intervals(condition)
    if len(I_begins) == 0:
        return values
    if I_begins[0] == 0:
        values[I_begins[0]:I_ends[0]+1] = init
        i_start = 1
    else:
        i_start = 0
    for i1, i2 in zip(I_begins[i_start:], I_ends[i_start:]):
        values[i1:i2+1] = values[i1-1]
    return values


if __name__ == '__main__':
    bool_cond = np.array([True, True, False, True, True, True, False, True, False, True])
    values =    np.array([5,    3,    2,     1,    3,    np.nan, 6,   5,    4,     3])
    I_begins, I_ends = get_condition_intervals(bool_cond)
    print(I_begins)
    print(I_ends)
    values_hold = hold_values(values, bool_cond)
    print(values_hold)

