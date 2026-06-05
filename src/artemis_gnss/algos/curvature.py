#!python3
# -*- coding: utf-8 -*-
"""
Functions for computations on curvature
Created on 20/09/24
"""
from typing import Tuple

import numpy as np
from numpy.typing import NDArray

from numba import jit

from artemis_gnss.algos.condition_intervals import hold_values
from artemis_gnss.algos.heading import gradient_mod


def curvature_from_heading(heading_rad: NDArray[np.float64], speed_m_s: NDArray[np.float64],
                           *, min_speed_for_curvature_compute: float=None,
                           max_curvature_value_1_m: float=None) -> NDArray[np.float64]:
    """
    Compute curvature from heading derivative [1/m]

    Curvature is maintained when speed is near zero
    """
    yaw_rad_s = gradient_mod(heading_rad, mod=2*np.pi)
    if min_speed_for_curvature_compute is None:
        min_speed_for_curvature_compute = 2.0/3.6
    curvature_1_m = yaw_rad_s / speed_m_s
    if max_curvature_value_1_m is not None:
        curvature_1_m = np.clip(curvature_1_m, a_max=max_curvature_value_1_m, a_min=-max_curvature_value_1_m)
    curvature_1_m = hold_values(curvature_1_m, speed_m_s < min_speed_for_curvature_compute)
    return curvature_1_m


