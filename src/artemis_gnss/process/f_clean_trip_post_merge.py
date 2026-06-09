#!python3
# -*- coding: utf-8 -*-
"""
Computations on a finalized trip and final validation
Created on 20/09/24
"""
from typing import List, Tuple

import pandas as pd
import numpy as np

from artemis_gnss.config import Config
from artemis_gnss.enum_attrs import GenerationType, IMTransport
from artemis_gnss.process.options import CleanOptions
from artemis_gnss.algos.time_base import trace_time_vect_to_timestamp_vect
from artemis_gnss.algos.gps_position import pos_diff_distance_2_points
from artemis_gnss.algos.gps_noise_detection import crow_fly_or_round_trip_distance
from artemis_gnss.algos.condition_intervals import propagate_diff_cond

include_space_jumps = True
include_stationary = True   # also used in D. clean portion
include_rejected = True
trip_remove_extremities = True
post_merge_edit_last_trip = True
stationary_resume_one_point = not Config.ENABLE_DEBUG
internal_fields = ["int_gps_distance_step"]


def clean_trip_steps(trip: pd.DataFrame, options: CleanOptions) -> None:
    """
    Final cleaning steps implemented on the trip.
    Current implementation includes:
    - Recompute "timestamp" vector

    :param trip:
    :param options:
    :return:
    """
    # recompute timestamp vector
    trip.attrs["generation"] = GenerationType.Extract
    common_timestamp = options.common_timestamp
    if common_timestamp is not None:
        trip.attrs["timestamp"] = common_timestamp
        if options.output_timestamp:
            mem_timestamp_vect = trip["timestamp"] if "timestamp" in trip else None
            trace_time_vect_to_timestamp_vect(trip, ref_timestamp=common_timestamp)
            if mem_timestamp_vect is not None:
                assert(np.all(trip["timestamp"] == mem_timestamp_vect))


def merge_new_trip_check_space_gap(new_trip: pd.DataFrame, previous_trip: pd.DataFrame) -> List[pd.DataFrame]:
    """
    This function tests if there is a space gap between the previous trip and the first point of the new trip under construction.
    It adds the last point of the previous trip and the first point as a new trip if there was a gap.
    This ensures the algorithm will send a continuous trace of localizations.
    :param new_trip: first portion of the trip under construction
    :param previous_trip: previously finished trip
    :return: list of missing displacements
    """
    if previous_trip is None:
        return []
    last_point = previous_trip.iloc[-1:]
    new_point = new_trip.iloc[0:1]
    distance_sqr_m = pos_diff_distance_2_points(lon1=last_point["longitude"].values[0], lat1=last_point["latitude"].values[0],
                                                lon2=new_point["longitude"].values[0], lat2=new_point["latitude"].values[0], squared=True)
    duration_s = new_point["time"] - last_point["time"]
    if include_space_jumps and distance_sqr_m > Config.SPACE_GAP_THRESHOLD_m_s**2:
        missing_trip = pd.concat((last_point, new_point))
        missing_trip.attrs["generation"] = GenerationType.SpaceTimeGapMissingData
        return [missing_trip]
    return []


def curate_trip_post_merge_div(trip: pd.DataFrame, options: CleanOptions):
    """
    Steps after points removal in clean_trip_post_merge_steps
    :param trip:
    :return:
    """
    # remove internally generated fields
    if options.remove_internal_fields:
        for field in internal_fields:
            if field in trip:
                trip.pop(field)


def reformat_stationary_trip(portion: pd.DataFrame) -> pd.DataFrame:
    """
    Change portion attributes for a trip which was found stationary (in a restricted radius).
    This function can annihilate the portion if it is too short.
    It optionally reduces the data points to a unique point with an estimated radius of presence.

    :param portion:
    :return:
    """
    if len(portion) < Config.DISPLACEMENT_MIN_LEN and not include_rejected:
        return None
    if stationary_resume_one_point:
        point = portion.iloc[:1]
        point["longitude"] = np.nanmean(portion["longitude"].values)
        point["latitude"] = np.nanmean(portion["latitude"].values)
        # TODO: compute radius of points
        point["radius"] = Config.SPACE_GAP_THRESHOLD_m_s
        point["duration"] = portion["time"].iloc[-1] - portion["time"].iloc[0]
        point["timestamp_0"] = portion["timestamp"].iloc[0]
        point["timestamp_end"] = portion["timestamp"].iloc[-1]
        point["len"] = len(portion)
        portion = point
    portion.loc[:,"imt"] = IMTransport.Stationary
    portion.attrs["generation"] = GenerationType.StationaryData
    portion.attrs["timestamp_0"] = portion["timestamp"].values[0]
    return portion


def merge_stationary_trips(reformated_stationary_trip_1: pd.DataFrame,
                           reformated_stationary_trip_2: pd.DataFrame) -> List[pd.DataFrame]:
    lon1, lat1 = reformated_stationary_trip_1["longitude"].iloc[-1], reformated_stationary_trip_1["latitude"].iloc[-1]
    lon2, lat2 = reformated_stationary_trip_2["longitude"].iloc[0], reformated_stationary_trip_2["latitude"].iloc[0]
    distance_m = pos_diff_distance_2_points(lon1=lon1, lat1=lat1, lon2=lon2, lat2=lat2)
    if distance_m < Config.SPACE_GAP_THRESHOLD_m_s and stationary_resume_one_point:
        assert(len(reformated_stationary_trip_1) == 1 and len(reformated_stationary_trip_2) == 1)
        point = reformated_stationary_trip_1.iloc[:1]
        n1, n2 = reformated_stationary_trip_1["len"].iloc[0], reformated_stationary_trip_2["len"].iloc[0]
        point["longitude"] = (n1 * reformated_stationary_trip_1["longitude"].iloc[0] + n2 * reformated_stationary_trip_2["longitude"].iloc[0]) / (n1+n2)
        point["latitude"] = (n1 * reformated_stationary_trip_1["latitude"].iloc[0] + n2 * reformated_stationary_trip_2["latitude"].iloc[0]) / (n1+n2)
        point["len"] = reformated_stationary_trip_1["len"].iloc[0] + reformated_stationary_trip_2["len"].iloc[0]
        point["duration"] = reformated_stationary_trip_1["duration"].iloc[0] + reformated_stationary_trip_2["duration"].iloc[0]
        point["radius"] = reformated_stationary_trip_1["radius"].iloc[0] + reformated_stationary_trip_2["radius"].iloc[0]  # approx
        point["timestamp_0"] = reformated_stationary_trip_1["timestamp_0"].iloc[0]
        point["timestamp_end"] = reformated_stationary_trip_2["timestamp_end"].iloc[-1]
        return [point]
    else:
        trip = pd.concat((reformated_stationary_trip_1, reformated_stationary_trip_2))
        trip.attrs = reformated_stationary_trip_2.attrs.copy()
        trip.attrs.update(reformated_stationary_trip_1.attrs)
        return [trip]


def clean_trip_post_merge_steps(trip: pd.DataFrame, options: CleanOptions,
                                previous_trip: pd.DataFrame, is_last_trip: bool) \
        -> Tuple[List[pd.DataFrame], pd.DataFrame]:
    """
    Rearrange trip into multiple displacements according to previous trip.

    :param trip:
    :param options:
    :param previous_trip:
    :param is_last_trip:
    :return:
    """
    init_previous_trip = previous_trip
    init_previous_trip_has_movement = not previous_trip.attrs["generation"] == GenerationType.StationaryData if previous_trip is not None else False
    new_trips: List[pd.DataFrame] = [init_previous_trip] if init_previous_trip is not None else []
    last_point = None
    # remove points with no speed from beginning and end of trip
    if "speed" in trip:
        bool_space_gap = propagate_diff_cond(trip["int_gps_distance_step"].values[1:] > Config.SPACE_GAP_THRESHOLD_m_s)
        bool_move = np.logical_or(trip["speed"].values > Config.SPEED_STOP_THRESHOLD_low_m_s, bool_space_gap)
        idx = np.argwhere(bool_move)
        if len(idx) > 2:
            if trip_remove_extremities:
                i0 = idx[0][0]
                i1 = idx[-1][-1]
                trip_on_move = trip.iloc[i0:i1 + 1]
            else:
                i0, i1 = 0, len(trip)
                trip_on_move = trip
            # cancel the trip?
            t0, t1 = trip_on_move["time"].values[0], trip_on_move["time"].values[-1]
            duration_sec = t1 - t0
            dist_01, dist_0, dist_1 = crow_fly_or_round_trip_distance(trip_on_move)
            if ((dist_0 < Config.DISPLACEMENT_MIN_DISTANCE_m/2 and dist_1 < Config.DISPLACEMENT_MIN_DISTANCE_m/2)
                    or duration_sec < Config.DISPLACEMENT_MIN_DURATION_sec
                    or len(trip_on_move) < Config.DISPLACEMENT_MIN_LEN):
                if include_rejected:
                    trip_on_move.loc[:,"imt"] = IMTransport.Undefined
                    trip_on_move.attrs["generation"] = GenerationType.RejectedExtract
                else:
                    trip_on_move = None
            # add stationary portions and trip_on_move
            if include_stationary and i0 > 0:
                stationary_0 = reformat_stationary_trip(trip.iloc[:i0])
                if stationary_0 is not None:
                    if (post_merge_edit_last_trip and init_previous_trip is not None
                            and not init_previous_trip_has_movement):
                        new_trips.pop(0)
                        new_trips += merge_stationary_trips(init_previous_trip, stationary_0)
                        previous_trip = new_trips[-1]
                    else:
                        new_trips += merge_new_trip_check_space_gap(stationary_0, previous_trip)
                        new_trips.append(stationary_0)
                        previous_trip = stationary_0
            if trip_on_move is not None:
                trip_on_move.attrs["timestamp_0"] = trip_on_move["timestamp"].values[0]
                new_trips += merge_new_trip_check_space_gap(trip_on_move, previous_trip)
                new_trips.append(trip_on_move)
                previous_trip = trip_on_move
            if include_stationary and i1 < len(trip)-1:
                stationary_1 = reformat_stationary_trip(trip.iloc[i1 + 1:])
                if stationary_1 is not None:
                    new_trips += merge_new_trip_check_space_gap(stationary_1, previous_trip)
                    new_trips.append(stationary_1)
                    previous_trip = stationary_1
        elif include_stationary:
            trip = reformat_stationary_trip(trip)
            if (post_merge_edit_last_trip and init_previous_trip is not None
                    and not init_previous_trip_has_movement):
                new_trips.pop(0)
                new_trips += merge_stationary_trips(init_previous_trip, trip)
                previous_trip = new_trips[-1]
            else:
                new_trips += merge_new_trip_check_space_gap(trip, previous_trip)
                new_trips.append(trip)
                previous_trip = trip
        else:
            last_point = trip.iloc[-1:]
            if is_last_trip:
                new_trips += merge_new_trip_check_space_gap(last_point, previous_trip)
                previous_trip = new_trips[-1]
    else:
        raise NotImplementedError

    for i, trip in enumerate(new_trips):
        curate_trip_post_merge_div(trip, options=options)

    # TODO: edit last_trip if necessary
    if is_last_trip:
        last_trip = None
    else:
        last_trip = new_trips.pop(-1)
    for trip in new_trips:
        clean_trip_steps(trip, options=options)
    return new_trips, last_trip


