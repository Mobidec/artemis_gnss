#!python3
# -*- coding: utf-8 -*-
"""
Representation of a collection of trips forming a displacement
"""
from typing import List

import pandas as pd


class Displacement:
    """
    A displacement is a collection of trips.
    For future releases !!!
    """
    def __init__(self, trips: List[pd.DataFrame] = None):
        if trips is None:
            trips = []
        self.trips: List[pd.DataFrame] = trips
        self.attrs: dict = {}

    def get_df(self) -> pd.DataFrame:
        if len(self.trips) == 0:
            return pd.DataFrame()
        return pd.concat(self.trips)
