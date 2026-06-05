#!python3
# -*- coding: utf-8 -*-
"""
Functions to switch from a time vector to a timestamp vector
Created on 20/09/24
"""
import warnings

import pandas as pd
import datetime
import numpy as np
from numpy.typing import NDArray

from artemis_gnss.config import Config


def np_timedelta_total_seconds(dt: np.timedelta64):
    return dt / np.timedelta64(1, 's')


def time_vect_from_timestamp_vect(timestamp_vect: NDArray[np.datetime64], *, ref_timestamp: np.datetime64 = None) -> NDArray[np.datetime64]:
    if len(timestamp_vect) == 0:
        return np.array([])
    if ref_timestamp is None:
        ref_timestamp = timestamp_vect[0]
    return np_timedelta_total_seconds(timestamp_vect - ref_timestamp)
def trace_time_vect_from_timestamp_vect(trace: pd.DataFrame, *, ref_timestamp: np.datetime64):
    """
    Generate time vector from timestamp vector
    :param trace:
    :param ref_timestamp: reference timestep, where t=0
    :return:
    """
    assert("time" not in trace)
    trace["time"] = time_vect_from_timestamp_vect(trace["timestamp"], ref_timestamp=ref_timestamp)
    trace.attrs["timestamp"] = ref_timestamp


def time_vect_to_timestamp_vect(time_vect: NDArray[np.float64], *, ref_timestamp: np.datetime64) -> NDArray[np.datetime64]:
    return time_vect.astype("timedelta64[s]") + ref_timestamp
def trace_time_vect_to_timestamp_vect(trace: pd.DataFrame, *, ref_timestamp: np.datetime64):
    """
    Generate timestamp vector from time vector + ref_timestamp
    :param trace:
    :param ref_timestamp:
    :return:
    """
    if ref_timestamp is None:
        ref_timestamp = trace.attrs["timestamp"]
    elif "timestamp" in trace.attrs:
        assert(ref_timestamp == trace.attrs["timestamp"])
    trace["timestamp"] = time_vect_to_timestamp_vect(trace["time"], ref_timestamp=ref_timestamp)


def diff_timestamp(timestamp_vect: NDArray[np.datetime64]):
    """
    Element-wise time difference in seconds
    :param timestamp_vect: Series of np.datetime64 length n
    :return: length n - 1
    """
    if len(timestamp_vect) > 1:
        return np_timedelta_total_seconds(np.diff(timestamp_vect))
    else:
        return np.array([], dtype=np.datetime64)

def trace_shift_timestamp(trace: pd.DataFrame, *, new_timestamp: np.datetime64,
                          trace_timestamp: np.datetime64=None):
    """
    Shift the reference timestamp of a trace
    :param trace:
    :param new_timestamp:
    :param trace_timestamp: reference timestamp of the trace (should be contained in trace.attrs)
    :return:
    """
    if trace_timestamp is None:
        trace_timestamp = trace.attrs["timestamp"]
    delta_time = np_timedelta_total_seconds(trace_timestamp - new_timestamp)
    if "time" in trace:
        trace["time"] = trace["time"] + delta_time
    trace.attrs["timestamp"] = new_timestamp


def trace_generic_time_vect(trace: pd.DataFrame, *, ref_timestamp: np.datetime64 = None,
                            time_step: float = None, time_offset: float = 0):
    """
    Generate a time vector with a regular spacing, according to the index of the samples
    :param trace:
    :param ref_timestamp:
    :param time_step:
    :param time_offset:
    :return:
    """
    assert("time" not in trace and "timestamp" not in trace)
    if time_step is None:
        time_step = Config.DEFAULT_TIME_STEP_SEC
    trace["time"] = np.arange(0., len(trace)) * time_step + time_offset
    if ref_timestamp is not None:
        if "timestamp" in trace.attrs:
            trace_shift_timestamp(trace, new_timestamp=ref_timestamp)
        trace.attrs["timestamp"] = ref_timestamp


def trace_generate_time_vect(trace: pd.DataFrame, *, ref_timestamp: np.datetime64 = None,
                             default_time_step: float = None, generic_time_offset: float = 0):
    """
    Add the time field to a trace if missing, or shift it to ref_timestamp
    :param trace:
    :param ref_timestamp:
    :param default_time_step:
    :param generic_time_offset:
    :return:
    """
    if "time" not in trace and "timestamp" not in trace:
        trace_generic_time_vect(trace, ref_timestamp=ref_timestamp,
                                time_step=default_time_step, time_offset=generic_time_offset)
    if ref_timestamp is not None:
        if "timestamp" in trace:
            # generate time vector relative to the common timestamp thanks to the existing timestamp vector
            if "time" in trace:
                raise(Exception("User gave time vector and timestamp vector"))
            trace_time_vect_from_timestamp_vect(trace, ref_timestamp=ref_timestamp)
            if "first_timeval" in trace.attrs:
                assert(trace.attrs["first_timeval"] == trace["time"].iloc[0])
        elif "timestamp" in trace.attrs:
            # translation of time values according to the timestamp stored in the trace.attrs
            trace_shift_timestamp(trace, new_timestamp=ref_timestamp)
        else:
            # responsability of the common time reference is transfered to the user
            warnings.warn("User gave time vector without timestamp")


if __name__ == '__main__':
    timestamp = np.datetime64("2024-09-24T12:00:00")
    timestamp_2 = timestamp + np.timedelta64(datetime.timedelta(seconds=6.5))
    time_vect = np.array([0., 1., 10.])
    timestamp_vect = time_vect_to_timestamp_vect(time_vect, ref_timestamp=timestamp)
    time_vect_check = time_vect_from_timestamp_vect(timestamp_vect, ref_timestamp=timestamp)
    diff_timestamp_vect = diff_timestamp(timestamp_vect)
    df = pd.DataFrame({"timestamp": timestamp_vect})
    trace_time_vect_from_timestamp_vect(df, ref_timestamp=timestamp)
    time_vect_shift = trace_shift_timestamp(df, new_timestamp=timestamp_2)



