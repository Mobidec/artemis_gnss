#!python3
# -*- coding: utf-8 -*-
"""
Functions for computations on heading
Created on 20/09/24
"""
from typing import Tuple

import numpy as np
from numpy.typing import NDArray

from numba import jit

from artemis_gnss.algos.gps_position import convert_lambert


@jit(nopython=True)
def diff_mod(signal: NDArray[np.float64], mod: float=2*np.pi) -> NDArray[np.float64]:
    diff_sig = np.diff(signal)
    bool_pos = diff_sig > mod/2
    diff_sig[bool_pos] -= mod
    bool_neg = diff_sig < -mod/2
    diff_sig[bool_neg] += mod
    return diff_sig


def gradient_mod(signal: NDArray[np.float64], mod: float=2*np.pi) -> NDArray[np.float64]:
    diff_sig = np.gradient(signal)
    bool_pos = diff_sig > mod/2
    diff_sig[bool_pos] -= mod
    bool_neg = diff_sig < -mod/2
    diff_sig[bool_neg] += mod
    return diff_sig


def heading_from_position(*, longitude: NDArray[np.float64], latitude: NDArray[np.float64],
                          time: NDArray[np.float64]=None,
                          coord_wgs=True) -> NDArray[np.float64]:
    """
    Compute heading from GPS coordinates (not recommended) based on atan2 method
    TODO: validation
    :param longitude: longitude
    :param latitude: latitude
    :param time: time [s] If given, this option encounters time between GPS coordinates to compute speed vector
    :param coord_wgs: if True, position was given in WGS coordinates, if False, lambert conversion was already done
    """
    if coord_wgs:
        # Convert Lambert
        (x, y) = convert_lambert(longitude=longitude, latitude=latitude)
    else:
        x = longitude
        y = latitude
    if time is not None and len(time) > 0:
        dt = np.diff(time, prepend=time[0]-1.0)
        if len(time) > 1:
            dt[0] = dt[1]
    else:
        dt = 1.0
    v_x = np.gradient(x) / dt
    v_y = np.gradient(y) / dt
    heading_rad = np.arctan2(v_x, v_y)
    return heading_rad

