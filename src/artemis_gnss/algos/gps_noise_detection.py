#!python3
# -*- coding: utf-8 -*-
"""
GPS noise detection methods
Created on 20/09/24
"""
import numpy as np
import pandas as pd

from artemis_gnss.algos.gps_position import pos_diff_distance_same_len, pos_diff_distance_2_points
from artemis_gnss.algos.gps_position import calculate_enclosing_circle
from artemis_gnss.config import Config
from artemis_gnss.enum_modes import GPSNoiseDetectMethod, NormType


def portion_is_gps_noise(trace: pd.DataFrame, method: GPSNoiseDetectMethod = None) -> bool:
    if method is None:
        method = Config.DEFAULT_GPSNoiseDetectMethod
    if method == GPSNoiseDetectMethod.NoDetection:
        return False
    elif method == GPSNoiseDetectMethod.RectangleFromInitialPoint:
        return portion_is_gps_noise_dist_method(trace, norm=NormType.NormInf_max)
    elif method == GPSNoiseDetectMethod.RadiusFromInitialPoint:
        return portion_is_gps_noise_dist_method(trace, norm=NormType.Norm2_Sqr)
    elif method == GPSNoiseDetectMethod.Circumscribed:
        return portion_is_gps_noise_circumscribed_method(trace)


def crow_fly_or_round_trip_distance(trace: pd.DataFrame, norm: NormType = None):
    if norm is None:
        norm = NormType.Norm2_Sqr
    if "int_gps_distance_step" in trace:
        delta_dist_m = trace["int_gps_distance_step"].values
    else:
        delta_dist_m = pos_diff_distance_same_len(longitude=trace["longitude"].values, latitude=trace["latitude"].values)
        trace["int_gps_distance_step"] = delta_dist_m
    cumdist_m = np.cumsum(delta_dist_m)
    i_mid = np.argwhere(cumdist_m >= cumdist_m[-1]/2)[0][0]
    lon0, lat0 = trace["longitude"].values[0], trace["latitude"].values[0]
    lon1, lat1 = trace["longitude"].values[-1], trace["latitude"].values[-1]
    lon_mid, lat_mid = trace["longitude"].values[i_mid], trace["latitude"].values[i_mid]
    dist_0 = pos_diff_distance_2_points(lon1=lon0, lat1=lat0, lon2=lon_mid, lat2=lat_mid, norm=norm)
    dist_1 = pos_diff_distance_2_points(lon1=lon1, lat1=lat1, lon2=lon_mid, lat2=lat_mid, norm=norm)
    dist_01 = pos_diff_distance_2_points(lon1=lon0, lat1=lat0, lon2=lon1, lat2=lat1, norm=norm)
    return dist_01, dist_0, dist_1


def portion_is_gps_noise_dist_method(trace: pd.DataFrame, *, norm: NormType) -> bool:
    duration_sec = trace["time"].values[-1] - trace["time"].values[0] + trace.attrs["time_step"]
    if "longitude" in trace and "latitude" in trace:
        if "speed" in trace:
            mean_speed_m_s = np.nanmean(trace["speed"].values)
        else:
            speed_gps_m_s = trace["int_gps_distance_step"].values / np.diff(trace["time"].values, append=0)
            mean_speed_m_s = np.nanmean(speed_gps_m_s)
        dist_threshold = min(Config.GPS_NOISE_RADIUS_MAX_m, duration_sec * max(mean_speed_m_s, 5/3.6) / 2)
        dist_01, dist_0, dist_1 = crow_fly_or_round_trip_distance(trace, norm)
        is_gps_noise = dist_0 <= dist_threshold and dist_1 <= dist_threshold
    else:
        is_gps_noise = False
    return is_gps_noise


def portion_is_gps_noise_circumscribed_method(trace: pd.DataFrame) -> bool:
    # TODO: place for elimination algorithm based on the radius formed by the points of the portion
    # calculate_enclosing_circle
    ...

