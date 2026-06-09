#!python3
# -*- coding: utf-8 -*-
"""
Minimal data corrections on raw trace in order to perform stop detection
    re-order data here if necessary
Created on 20/09/24
"""
from typing import List, Tuple, Union

import pandas as pd
import numpy as np

from artemis_gnss.config import Config
from artemis_gnss.algos.stop_detection import stop_or_gap_detection
from artemis_gnss.process.options import CleanOptions
from artemis_gnss.algos.gps_position import pos_diff_distance


def clean_raw_steps(trace: pd.DataFrame, options: CleanOptions) -> None:
    """
    Step B main function performs treatments on raw trace signals:
    - distance between GPS points

    :param trace:
    :param options:
    :return:
    """
    # replace speed with high value if there is a space gap to prevent cuts in these indexes
    delta_dist_m_1 = pos_diff_distance(longitude=trace["longitude"].values, latitude=trace["latitude"].values)
    trace["int_gps_distance_step"] = np.concat(([0], delta_dist_m_1))


def stop_or_gap_divide(trace: pd.DataFrame, *, duration_cut_s: float=0) \
        -> Tuple[List[pd.DataFrame], Union[pd.DataFrame,None]]:
    """
    Cut a raw trace into elementary portions (data between two stops).
    If the trace does not end with a stop, a residual trace is returned.

    :param trace:
    :param duration_cut_s:
    :return: Tuple (portions, residual_trace) with
        - portions: a List of the elementary portions
        - residual_trace: the residual trace or None
    """
    (I_extract_begins, I_extract_ends), _ = stop_or_gap_detection(trace)
    portions: List[pd.DataFrame] = []
    i1 = 0
    for k, (i0, i1) in enumerate(zip(I_extract_begins, I_extract_ends)):
        portions.append(trace.iloc[i0:i1])
    if i1 < len(trace):
        # trace does not end with a stop => residual trace
        residual_trace = trace.iloc[i1:]
        assert(len(residual_trace)>0)
    else:
        residual_trace = None
    return portions, residual_trace

