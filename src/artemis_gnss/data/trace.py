#!python3
# -*- coding: utf-8 -*-
"""
Standard data fields to represent a GPS trace
The code uses pandas.DataFrame for internal usage
Created on 20/09/24
"""
from typing import Union, List
from dataclasses import dataclass, field
from copy import deepcopy

import numpy as np
import pandas as pd
from numpy.typing import NDArray


@dataclass
class TraceAttrs:
    """ Class to represent standard trace attributes """
    """ timestamp: reference for time=0 """
    timestamp: np.datetime64 = None
    """ first_timeval: value of time for the first sample """
    first_timeval: float = None
    """ id: identification of the trace """
    id: str = None

    def to_dict(self) -> dict:
        d = {k: v for k, v in self.__dict__.items() if v is not None}
        return d


@dataclass
class Trace:
    """Trace
    Class with standard field names to represent a trace

    :param attrs: attributes
    :param time: time in seconds, relative to attrs["timestamp"]
    :param timestamp: timestamp as np.datetime64
    :param speed: speed in m/s
    :param longitude: longitude coordinate in °WGS
    :param latitude: latitude coordinate in °WGS
    :param hdop: horizontal GPS dilution in meters
    :param elevation: elevation in meters
    :param heading: heading in radians
    """
    attrs: TraceAttrs = field(default_factory=TraceAttrs)
    time: NDArray[np.float64] = None
    timestamp: NDArray[np.datetime64] = None
    speed: NDArray[np.float64] = None
    longitude: NDArray[np.float64] = None
    latitude: NDArray[np.float64] = None
    hdop: NDArray[np.float64] = None
    elevation: NDArray[np.float64] = None
    heading: NDArray[np.float64] = None

    def to_dict(self) -> dict:
        d = {k: v for k, v in self.__dict__.items() if v is not None}
        d["attrs"] = self.attrs.to_dict()
        return d

    def to_dataframe(self) -> pd.DataFrame:
        d = self.to_dict()
        attrs = d.pop("attrs")
        df = pd.DataFrame(d)
        df.attrs = attrs
        return df


def convert_unit_trace_pandas(trace: Union[pd.DataFrame, dict, Trace], *,
                              deep_copy=True) -> pd.DataFrame:
    if isinstance(trace, dict):
        trace_new = pd.DataFrame.from_dict(trace)
    elif isinstance(trace, Trace):
        trace_new = trace.to_dataframe()
    else:
        assert(isinstance(trace, pd.DataFrame))
        trace_new = trace
    if deep_copy:
        trace_new = pd.DataFrame.from_dict(trace).copy(deep=True)
    return trace_new


def convert_traces_pandas(traces: Union[pd.DataFrame, dict, Trace, List[Union[dict, pd.DataFrame, Trace]]], *,
                          deep_copy=True) -> List[pd.DataFrame]:
    if not isinstance(traces, list):
        traces = [traces]
    traces_fmt: List[pd.DataFrame] = []
    for k, trace in enumerate(traces):
        traces_fmt.append(convert_unit_trace_pandas(trace, deep_copy=deep_copy))
    return traces_fmt


if __name__ == '__main__':
    timestamp = np.datetime64("2024-09-24T12:00:00")
    trace = Trace(time=[0, 1, 2])
    trace.speed = [5, 6, 7]
    trace.timestamp = timestamp + np.array(trace.time).astype(np.timedelta64)
    trace.my_new_field = [6, 10, 11]
    df = trace.to_dataframe()
    time_check = (df["timestamp"] - timestamp).apply(lambda ts: ts.total_seconds())
    assert(np.all(time_check == trace.time))
