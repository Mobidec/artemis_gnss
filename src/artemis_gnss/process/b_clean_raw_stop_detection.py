#!python3
# -*- coding: utf-8 -*-
"""
Minimal data corrections on raw trace in order to perform stop detection
    re-order data here if necessary
Created on 20/09/24
"""
from typing import List, Tuple

import pandas as pd
import numpy as np

from artemis_gnss.config import Config
from artemis_gnss.algos.stop_detection import stop_or_gap_detection
from artemis_gnss.process.options import CleanOptions
from artemis_gnss.algos.gps_position import pos_diff_distance


def clean_raw_steps(trace: pd.DataFrame, options: CleanOptions):
    # replace speed with high value if there is a space gap to prevent cuts in these indexes
    delta_dist_m_1 = pos_diff_distance(longitude=trace["longitude"].values, latitude=trace["latitude"].values)
    trace["int_gps_distance_step"] = np.concat(([0], delta_dist_m_1))


def stop_or_gap_divide(trace: pd.DataFrame, *, duration_cut_s: float=0) \
        -> Tuple[List[pd.DataFrame], pd.DataFrame]:
    (I_extract_begins, I_extract_ends), _ = stop_or_gap_detection(trace)
    portions: List[pd.DataFrame] = []
    i1 = 0
    for k, (i0, i1) in enumerate(zip(I_extract_begins, I_extract_ends)):
        portions.append(trace[i0:i1])
    if i1 < len(trace):
        residual = trace[i1:]
        assert(len(residual)>0)
    else:
        residual = None
    return portions, residual

