#!python3
# -*- coding: utf-8 -*-
"""
Parameters used for data handling functions
Created on 20/09/24
"""
from abc import ABC

from artemis_gnss.enum_modes import StopDetectionMethod
from artemis_gnss.enum_modes import GPSNoiseDetectMethod


class Config(ABC):
    # time step if not given in the dataframe
    DEFAULT_TIME_STEP_SEC = 1.0
    # expected relative precision of the time base (for kpi)
    TIME_BASE_PRECISION_THR = 0.001

    # stop detection ----
    DEFAULT_StopDetectionMethod = StopDetectionMethod.LowSpeedExceptSpaceGaps
    # speed threshold for stop detection
    SPEED_STOP_THRESHOLD_high_m_s = 2 / 3.6
    SPEED_STOP_THRESHOLD_low_m_s = 1 / 3.6
    # window after first threshold to look for second threshold (or cut)
    STOP_DURATION_MAX__AHEAD_sec = 5
    # minimum duration of a stop for the cut step & kpi
    STOP_DURATION_MAX__CUT_sec = 15
    # stop duration for a pause (for kpi)
    STOP_DURATION_PAUSE_sec = 60
    # space gap threshold
    SPACE_GAP_THRESHOLD_m_s = 100.0
    # space gap max duration
    SPACE_GAP_MAX_DURATION_sec = 60*60
    # displacement definition
    DISPLACEMENT_MIN_DURATION_sec = 15.0
    DISPLACEMENT_MIN_DISTANCE_m = 100.0
    DISPLACEMENT_MIN_LEN = 2
    # maximum duration between displacements
    DISPLACEMENT_MAX_TIME_GAP_sec = 60 * 60

    # thresholds for anomaly detection (for kpi) ----
    # acceleration threshold
    ACCEL_THR_DEFECT_m_s2 = 15.0
    # acceleration from stop
    ACCEL_FROM_STOP_THR_DEFECT_m_s2 = 10.0
    # error tolerance between speed and GPS position
    GPS_POSITION_VS_SPEED_PRECISION = 1.
    # hdop threshold
    HDOP_THR = 5
    # curvature threshold
    CURVATURE_MAX_1_m = 5000
    # slope threshold
    SLOPE_MAX_wu = .2

    # elimination of portions ----
    DEFAULT_GPSNoiseDetectMethod = GPSNoiseDetectMethod.RadiusFromInitialPoint
    # threshold to separate noise from movement
    GPS_NOISE_RADIUS_MAX_m = 100.

    ENABLE_DEBUG = True

