#!python3
# -*- coding: utf-8 -*-
"""
Functions defining a stop
Created on 20/09/24
"""
import datetime
from typing import Tuple, List

import numpy as np
import pandas as pd

from artemis_gnss.config import Config
from artemis_gnss.enum_modes import StopDetectionMethod
from artemis_gnss.algos.condition_intervals import get_condition_intervals, propagate_diff_cond
from artemis_gnss.algos.gps_position import pos_diff_distance_2_points


def stop_or_gap_detection(trace: pd.DataFrame, *, method: StopDetectionMethod = None) \
        -> Tuple[Tuple[List[int], List[int]], Tuple[List[int], List[int]]]:
    """
    Stop detection algorithm entry point
    This method is used to cut portions out of traces. It is also used in the TraceKpi method.
    :param trace:
    :param method:
    :return:
    """
    if len(trace) <= 1 or method == StopDetectionMethod.NoDetection:
        return ([0], [len(trace)-1]), ([], [])
    if method is None:
        method = Config.DEFAULT_StopDetectionMethod
    if method == StopDetectionMethod.LowSpeedExceptSpaceGaps:
        return stop_or_gap_detection_speed(trace, duration_cut_s=Config.STOP_DURATION_MAX__CUT_sec)
    elif method == StopDetectionMethod.PositionRadius:
        return stop_or_gap_detection_sliding_radius(trace)
    else:
        raise(NotImplementedError())


def stop_or_gap_detection_sliding_radius(trace: pd.DataFrame, *, window_len: int = 300, threshold_m: float = 30) \
        -> Tuple[Tuple[List[int], List[int]], Tuple[List[int], List[int]]]:
    # TODO: place for the stop detection algorithm based on radius of points computed on a sliding window
    ...


def stop_or_gap_detection_speed(trace: pd.DataFrame, *, duration_cut_s: float = 0) \
        -> Tuple[Tuple[List[int], List[int]], Tuple[List[int], List[int]]]:
    bool_stop = trace["speed"].values <= Config.SPEED_STOP_THRESHOLD_high_m_s
    time_step = trace.attrs["time_step"]
    bool_time_gap = propagate_diff_cond(np.diff(trace["time"].values) > time_step * 3)
    bool_cut = np.logical_or(bool_stop, bool_time_gap)

    I_begins, I_ends = get_condition_intervals(bool_cut)
    if Config.SPEED_STOP_THRESHOLD_low_m_s < Config.SPEED_STOP_THRESHOLD_high_m_s:
        # look ahead STOP_DURATION_MAX__AHEAD_sec (a before for end of stop) and search for second threshold or cut at minimum speed
        assert(Config.STOP_DURATION_MAX__AHEAD_sec <= duration_cut_s)
        bool_I_keep = np.full(I_begins.shape, True)
        for k, (i0,i1) in enumerate(zip(I_begins, I_ends)):
            t0, t1 = trace["time"].values[i0], trace["time"].values[i1]
            if t1 - t0 < Config.STOP_DURATION_MAX__AHEAD_sec * 2 and np.min(trace["speed"].values[i0:i1+1]) > Config.SPEED_STOP_THRESHOLD_low_m_s:
                bool_I_keep[k] = False
            i0w = np.argwhere(trace["time"].values[i0:i1+1] <= t0 + Config.STOP_DURATION_MAX__AHEAD_sec)[-1][-1] + i0
            i1w = np.argwhere(trace["time"].values[i0:i1+1] >= t1 - Config.STOP_DURATION_MAX__AHEAD_sec)[0][0] + i0

            i0s = np.argwhere(trace["speed"].values[i0:i0w+1] <= Config.SPEED_STOP_THRESHOLD_low_m_s)
            i1s = np.argwhere(trace["speed"].values[i1w:i1+1] <= Config.SPEED_STOP_THRESHOLD_low_m_s)
            if len(i0s) > 0:
                i0s = i0s[0][0] + i0
            else:
                i0s = np.argmin(trace["speed"].values[i0:i0w+1]) + i0
            if len(i1s) > 0:
                i1s = i1s[-1][-1] + i1w
            else:
                i1s = np.argmin(trace["speed"].values[i1w:i1+1]) + i1w

            spd0s = trace["speed"].values[i0s]
            spd1s = trace["speed"].values[i1s]
            assert(i0 <= i0s and i0s <= i1)
            assert(i0 <= i1s and i1s <= i1)
            assert(i0s <= i1s)
            # if i0s == i1s:
            #     bool_I_keep[k] = False
            I_begins[k] = i0s
            I_ends[k] = i1s
        I_begins, I_ends = I_begins[bool_I_keep], I_ends[bool_I_keep]
    bool_I_keep = np.full(I_begins.shape, False)
    i_extract_begin = 0
    I_extract_begins, I_extract_ends = [], []
    for k, (i0,i1) in enumerate(zip(I_begins, I_ends)):
        t0, t1 = trace["time"].values[i0], trace["time"].values[i1]
        duration = t1 - t0
        distance_sqr_m = pos_diff_distance_2_points(lon1=trace["longitude"].values[i0], lat1=trace["latitude"].values[i0],
                                                    lon2=trace["longitude"].values[i1], lat2=trace["latitude"].values[i1],
                                                    squared=True)
        if (duration >= duration_cut_s and
                (not (distance_sqr_m > Config.SPACE_GAP_THRESHOLD_m_s ** 2 and duration < Config.SPACE_GAP_MAX_DURATION_sec))
                and i0 > i_extract_begin):
            bool_I_keep[k] = True
            I_extract_begins.append(i_extract_begin)
            I_extract_ends.append(i0+1)
            i_extract_begin = i1
    I_begins, I_ends = I_begins[bool_I_keep], I_ends[bool_I_keep]
    return (I_extract_begins, I_extract_ends), (I_begins, I_ends)

