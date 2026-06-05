#!python3
# -*- coding: utf-8 -*-
"""
Clean treatment options
Created on 20/09/24
"""
from enum import IntEnum

import numpy as np

from artemis_gnss.config import Config


class StepDeepCopy(IntEnum):
    Beginning_NoSideEffect = 0   # ensure no change is done to the input vectors
    Post_Init = 1                # initialization create an attribute "first_timeval" and sorts the traces
    Post_TimeBase = 2            # this option ensures the time base is shifted to the same reference timestamp as the output
    None_CleanRaw = 3            # do not apply deepcopy to trace (all treatments until process raw will be applied)


class CleanOptions:
    """
    Options for the process process
    :attrib common_timestamp:  reference timestamp to use in output routes, for t=0
    :attrib inputs_deepcopy:   option to activate deep copy and remove any side effects of the algorithm on the inputs
    :attrib output_timestamp:  option to recompute the timestamp vector for the output (if possible)
    :attrib default_time_step: default time step to consider if no time vector / timestamp vector is given
    """
    def __init__(self, common_timestamp: np.datetime64 = None):
        self.common_timestamp: np.datetime64 = common_timestamp
        self.inputs_deepcopy: StepDeepCopy = StepDeepCopy.Beginning_NoSideEffect
        self.output_timestamp = True
        self.default_time_step = Config.DEFAULT_TIME_STEP_SEC
        self.remove_internal_fields = not Config.ENABLE_DEBUG

    def __copy__(self):
        # basic copy function
        cp = CleanOptions()
        cp.__dict__.update(self.__dict__)
        return cp

    def copy(self):
        return self.__copy__()

    def to_dict(self):
        return self.__dict__

    @staticmethod
    def from_dict(d: dict):
        obj = CleanOptions()
        obj.__dict__.update({k: v for k, v in d.items() if k in obj.__dict__})
        return obj

