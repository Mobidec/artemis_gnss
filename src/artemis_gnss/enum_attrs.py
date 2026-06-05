#!python3
# -*- coding: utf-8 -*-
"""
Codification of various properties
Created on 20/09/24
"""
from enum import IntEnum


# enum describing how the trip was generated
class GenerationType(IntEnum):
    Extract = 0
    SpaceTimeGapMissingData = 1
    StationaryData = 2
    RejectedExtract = 3

    def to_str(self) -> str:
        return str(self)[len("GenerationType."):]


class Motivation(IntEnum):
    Undefined = 0
    Work = 1
    Consumption = 2
    Recreational = 3


class IMTransport(IntEnum):
    """
    Identified Means of Transportation codes
    the codes are inspired by UNECE recommendations, more oriented for the transportation of goods
    """
    Undefined = 0
    Noise = 1  # addition
    Stationary = 2  # addition, use to notify no movement was detected
    # Maritime transport
    Boat = 1590
    Ferry = 1592
    # Rail transport
    Train = 2100
    Subway = 2101   # addition
    # Road transport
    Pedestrian = 3001   # addition
    Bicycle = 3002   # addition
    ElectricBicycle = 3003   # addition
    Scooter = 3009   # addition
    Car = 3136
    CarWithTrailer = 3102
    ## public transportation
    Taxi = 3133
    Bus = 3300
    ## transportation of goods
    Truck = 3010  # generic category
    DeliveryVan = 3041  # commercial vehicle
    Hauler = 3109  # heavy-duty truck
    HaulerTrailer = 3950  # heavy-duty truck with trailer
    HaulerTractorAlone = 3020  # tractor only
    OffroadVehicle = 3130
    SpecialConvoy = 3710  # nearest match
    # Air transport
    Airplane = 4000

    def to_str(self) -> str:
        return str(self)[len("IMTransport."):]



