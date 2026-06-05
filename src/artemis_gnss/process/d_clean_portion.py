#!python3
# -*- coding: utf-8 -*-
"""
Anomaly detection and signal treatment on a trace between prolonged stops
Created on 20/09/24
"""
import datetime
import numpy as np
import pandas as pd

from artemis_gnss.config import Config
from artemis_gnss.process.options import CleanOptions
from artemis_gnss.process.f_clean_trip_post_merge import include_stationary
from artemis_gnss.algos.gps_noise_detection import portion_is_gps_noise
from artemis_gnss.enum_attrs import IMTransport

gps_noise_replace_by_mean = True


def portion_imt(trace: pd.DataFrame) -> IMTransport:
    """
    Identification of means of transportation
    :param trace:
    :return:
    """
    max_speed_kmh = trace["speed"].max() * 3.6
    if max_speed_kmh <= Config.SPEED_STOP_THRESHOLD_low_m_s * 3.6:
        imt_guess = IMTransport.Stationary
    elif max_speed_kmh < 10:
        imt_guess = IMTransport.Pedestrian
    elif max_speed_kmh < 35:
        imt_guess = IMTransport.Bicycle
    elif max_speed_kmh < 200:
        imt_guess = IMTransport.Car
    elif max_speed_kmh < 400:
        imt_guess = IMTransport.Train
    else:
        imt_guess = IMTransport.Airplane
    return imt_guess


def clean_portion_steps(portion: pd.DataFrame, *, previous_portion: pd.DataFrame, options: CleanOptions) -> pd.DataFrame:
    """
    Function to clean a portion between two prolongated stops
    :param portion:
    :param options:
    :return: True if portion contains information on movement
    """
    # Basic Identification of means of transportation (IMT)
    if len(portion) <= 1:
        return None
    is_gps_noise = portion_is_gps_noise(portion)
    if is_gps_noise:
        imt_guess = IMTransport.Noise
    else:
        imt_guess = portion_imt(portion)
    is_speed = not imt_guess == IMTransport.Stationary
    portion.loc[:, "imt"] = imt_guess

    if Config.ENABLE_DEBUG:
        portion.attrs["debug"] = {"portion_is_speed": is_speed, "portion_is_gps_noise": is_gps_noise, "imt": imt_guess}
    if (not include_stationary) and ((not is_speed) or is_gps_noise):
        return None
    if is_gps_noise:
        portion.loc[:, "speed"] = 0
        if gps_noise_replace_by_mean:
            lon, lat = np.nanmean(portion["longitude"].values), np.nanmean(portion["latitude"].values)
            # portion = pd.concat((portion.iloc[0:1], portion.iloc[-1:]))
            portion.loc[:, "longitude"] = lon
            portion.loc[:, "latitude"] = lat
    elif not is_speed:
        # keep information on user position and destroy speed information
        portion.loc[:, "speed"] = 0
    return portion


