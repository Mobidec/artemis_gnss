#!python3
# -*- coding: utf-8 -*-
"""
Codification of implementation variants
Created on 20/09/24
"""
from enum import IntEnum

# module algos.stop_detection   ---------------
class StopDetectionMethod(IntEnum):
    NoDetection = 0
    LowSpeedExceptSpaceGaps = 1
    PositionRadius = 2

# module algos.gps_noise_detection   ---------------
class GPSNoiseDetectMethod(IntEnum):
    NoDetection = 0
    RectangleFromInitialPoint = 1
    RadiusFromInitialPoint = 1
    Circumscribed = 2

class NormType(IntEnum):
    Norm1_Abs = 1
    Norm2_Sqr = 2
    NormInf_max = 3
