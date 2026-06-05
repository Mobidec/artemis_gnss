#!python3
# -*- coding: utf-8 -*-
"""
Functions for computations on slope
Created on 20/09/24
"""
from typing import Tuple

import numpy as np
from numpy.typing import NDArray

from numba import jit

elevation_computer_step_m = 100.


def slope_from_elevation(*, elevation_m: NDArray[np.float64], distance_m: NDArray[np.float64]) -> NDArray[np.float64]:
    if len(elevation_m) == 0:
        return np.array([])
    elif distance_m[-1] - distance_m[0] < elevation_computer_step_m:
        return np.full(elevation_m.shape, np.nan)
    temp_distance_m = np.arange(distance_m[0], distance_m[-1], elevation_computer_step_m)
    bool_move = np.diff(distance_m, prepend=distance_m[0]) > 0
    temp_elevation_m = np.interp(temp_distance_m, distance_m[bool_move], elevation_m[bool_move])
    temp_slope_wu = np.gradient(temp_elevation_m) / elevation_computer_step_m
    slope_wu = np.interp(distance_m, temp_distance_m, temp_slope_wu)
    slope_wu[distance_m > temp_distance_m[-1]] = 0
    return slope_wu

