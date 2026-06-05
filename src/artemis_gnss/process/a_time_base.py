#!python3
# -*- coding: utf-8 -*-
"""
Functions to define a common time base

timestamp: np.datetime64 format (0 = 01/01/1970 0:0:0)
time: numeric vector in seconds (0 = trace.attrs["timestamp"])
The treatments require a time vector. If the user gives a timestamp vector, this vector is generated below.

Created on 20/09/24
"""
import warnings
from typing import List

import pandas as pd
import numpy as np

from artemis_gnss.config import Config
from artemis_gnss.algos.time_base import np_timedelta_total_seconds, trace_generate_time_vect


def negotiate_common_timestamp(traces: List[pd.DataFrame], *,
                               common_timestamp: np.datetime64=None) -> np.datetime64:
    if common_timestamp is None:
        timestamps: List[np.datetime64] = []
        for trace in traces:
            if "timestamp" in trace:
                timestamps.append(trace["timestamp"].values[0])
            elif "timestamp" in trace.attrs:
                timestamps.append(trace.attrs["timestamp"])
        if len(timestamps) == len(traces):
            common_timestamp = min(timestamps)
        elif len(timestamps) > 0:
            raise Exception("User gave traces with/without timestamps")
    return common_timestamp


def apply_common_timestamp_init_time_vect(trace: pd.DataFrame, common_timestamp: np.datetime64=None, *,
                                          default_time_step: float=None):
    trace_generate_time_vect(trace, ref_timestamp=common_timestamp, default_time_step=default_time_step)
    if "time_step" not in trace.attrs:
        default_time_step = np.median(np.diff(trace["time"].values))
        trace.attrs["time_step"] = default_time_step


def compute_first_timeval(trace: pd.DataFrame, common_timestamp: np.datetime64=None):
    """
    Apply to a trace with the time field -> gives the value of time for the first sample
    The value is also stored in trace.attrs
    :param trace:
    :param common_timestamp:
    :return:
    """
    if common_timestamp is not None:
        if "timestamp" in trace:
            time_delta = trace["timestamp"].values[0] - common_timestamp
            first_timeval = np_timedelta_total_seconds(time_delta)
            if "time" in trace:
                assert(trace["time"].values[0] == first_timeval)
        elif "timestamp" in trace.attrs:
            time_delta = trace.attrs["timestamp"] - common_timestamp
            first_timeval = trace["time"].values[0] + np_timedelta_total_seconds(time_delta)
        else:
            first_timeval = trace["time"].values[0]
    else:
        first_timeval = trace["time"].values[0]
    trace.attrs["first_timeval"] = first_timeval
    return first_timeval

