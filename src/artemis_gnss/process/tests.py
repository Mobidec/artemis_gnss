# -*- coding: utf-8 -*-
"""
Functions to test properties of the output of the process
Created on 20/09/24
"""
from typing import List, Tuple

from artemis_gnss.data.clean_output import CleanOutput
from artemis_gnss.config import Config
from artemis_gnss.enum_attrs import GenerationType
from artemis_gnss.algos.gps_position import pos_diff_distance_2_points


def test_position_continuity(output: CleanOutput) -> Tuple[bool, List]:
    """
    Verify the continuity of position in a sequence of displacements
    :param output: output of the clean process
    :return:
    """
    traces = output.displacements
    idx_continuity_error = []
    if len(traces) == 0:
        return True, idx_continuity_error
    trace = traces[0]
    last_lon_lat = trace["longitude"].iloc[0], trace["latitude"].iloc[0]
    last_generation = trace.attrs["generation"]
    dist_threshold = Config.SPACE_GAP_THRESHOLD_m_s
    if trace.attrs["generation"] == GenerationType.StationaryData:
        dist_threshold = trace["radius"]
    for i, trace in enumerate(traces):
        first_lon_lat = trace["longitude"].iloc[0], trace["latitude"].iloc[0]
        distance_m = pos_diff_distance_2_points(lon1=last_lon_lat[0], lat1=last_lon_lat[1],
                                                lon2=first_lon_lat[0], lat2=first_lon_lat[1])
        if trace.attrs["generation"] == GenerationType.StationaryData:
            dist_threshold = trace["radius"]
        elif not last_generation == GenerationType.StationaryData:
            dist_threshold = Config.SPACE_GAP_THRESHOLD_m_s
        if distance_m > dist_threshold:
            idx_continuity_error.append(i)
        last_lon_lat = trace["longitude"].iloc[-1], trace["latitude"].iloc[-1]
    return len(idx_continuity_error) == 0, idx_continuity_error


