#!python3
# -*- coding: utf-8 -*-
"""
Object returned by the clean process for one trip
Contains fields for the trace, the map-matched points and the full map-matched route
Created on 20/09/24
"""
from typing import Union
from dataclasses import dataclass

import pandas as pd

from artemis_gnss.data.trace import Trace, convert_unit_trace_pandas


@dataclass
class MatchedTrace:
    """MatchedTrace
    Class representing a trace with additional representations

    :param attrs: place for scalar values
    :param points: initial trace recordings
    :param match: map-matched points
    :param route: list of links representing the full trajectory
    """
    attrs: dict
    points: pd.DataFrame
    match: pd.DataFrame = None
    route: pd.DataFrame = None

    def __init__(self, points: Union[pd.DataFrame, Trace, dict], attrs: dict = None):
        self.points = convert_unit_trace_pandas(points)
        self.attrs = points.attrs
        if attrs is not None:
            self.attrs.update(attrs)

