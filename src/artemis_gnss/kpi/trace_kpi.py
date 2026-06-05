#!python3
# -*- coding: utf-8 -*-
"""
Functions to characterize defects in a given route trace
Created on 20/09/24
"""
from typing import Dict, List

import pandas as pd
import numpy as np

from artemis_gnss.config import Config
from artemis_gnss.algos.stop_detection import stop_or_gap_detection
from artemis_gnss.algos.time_base import trace_time_vect_from_timestamp_vect
from artemis_gnss.algos.gps_position import convert_lambert_compute_speed
from artemis_gnss.algos.slope import slope_from_elevation
from artemis_gnss.algos.curvature import curvature_from_heading


class TraceDefect:
    def __init__(self, name: str, issue_class: str, trace: pd.DataFrame, indexes, values=None, more=None):
        if more is None:
            more = ""
        self.name = name
        self.issue_class = issue_class
        self.trace_id = None
        self.indexes = indexes
        self.values = values
        self.more = more
        self.duration = -1
        self.distance = -1
        if len(indexes) > 1:
            if "time" in trace:
                diff_time = np.diff(trace["time"].values[indexes])
                diff_time[diff_time < 0] = 0
                # self.duration = trace["time"][indexes[-1]] - trace["time"][indexes[0]]
                self.duration = np.sum(diff_time)
            else:
                self.duration = (indexes[-1] - indexes[0]) * Config.DEFAULT_TIME_STEP_SEC
        elif len(indexes) > 0:
            self.duration = trace.attrs["time_step"]
        if "speed" in trace and len(indexes) > 0:
            delta_distance_m = trace["speed"].values[indexes]
            if "time" in trace and len(indexes) > 1:
                delta_distance_m = delta_distance_m * np.insert(diff_time, 0, np.median(diff_time))
            else:
                delta_distance_m = delta_distance_m * self.duration
            self.distance = np.sum(delta_distance_m)
        if "id" in trace.attrs:
            self.trace_id = trace.attrs["id"]

    def __str__(self):
        return f"{self.name} at i={self.indexes} ({self.issue_class} - {round(self.duration, 1)} s - {round(self.distance, 1)} m) {self.more}"


class TraceKpi:
    def __init__(self, trace: pd.DataFrame, trace_add_hover_data=True):
        self.trace: pd.DataFrame = None
        self.defects: Dict[str, List[TraceDefect]] = {}
        self.defects_text_vect: pd.Series = None
        self.validity: Dict[str, np.ndarray] = {}
        self.validity_global: np.ndarray = None
        self.defects_count: Dict[str, int] = {}  # counts by issue
        self.issues_count: Dict[str, int] = {}  # counts by issue_class
        self.defects_total: int = -1
        self.validity_total: int = -1
        self.length: int = -1
        self.duration: float = -1  # [s]
        self.count = 0
        self.time_step: float = -1  # [s]
        self.distance: float = -1  # [m]
        self.max_speed: float = -1  # [m/s]
        self.mean_speed: float = -1  # [m/s]
        self.mean_speed_move: float = -1  # [m/s]
        self.duration_move: float = -1
        self.max_speed_valid: float = -1  # [m/s]
        self.mean_speed_move_valid: float = -1  # [m/s]
        self.distance_move_valid: float = -1
        self.duration_move_valid: float = -1
        self.distance_valid: float = -1
        self.duration_valid: float = -1
        self.stops_index_begin: List[int] = None
        self.stops_index_end: List[int] = None
        self.stops_duration: List[float] = None
        self.stop_count: int = -1
        if trace is not None:
            self._list_defects_compute_kpi(trace)
            if trace_add_hover_data:
                self.trace_add_hover_data()

    def _add_defect_list(self, name: str, issue_class: str, trace: pd.DataFrame, bool_defect, values=None, more=None):
        if name not in self.defects:
            self.defects[name] = []
        if issue_class not in self.issues_count:
            self.issues_count[issue_class] = 0
        if issue_class not in self.validity:
            self.validity[issue_class] = np.full((len(trace),), True)
        len_diff = len(bool_defect) - len(trace)
        if len_diff == 0:
            self.validity[issue_class] = np.logical_and(self.validity[issue_class], np.logical_not(bool_defect))
        elif len_diff == -1:
            # shift invalidity vector to the right (prepend with False)
            self.validity[issue_class] = np.logical_and(self.validity[issue_class],
                                                        np.logical_not(np.insert(bool_defect, 0, False)))
        else:
            raise NotImplementedError
        indexes = np.nonzero(bool_defect)[0]
        if values is not None:
            for i in indexes:
                self.defects[name].append(TraceDefect(name, issue_class, trace, [i - len_diff], [values[i]], more=more))
        else:
            for i in indexes:
                self.defects[name].append(TraceDefect(name, issue_class, trace, [i - len_diff], more=more))
        self.issues_count[issue_class] += len(indexes)

    def _list_defects_compute_kpi(self, trace: pd.DataFrame):
        trace = trace.copy()
        self.trace = trace
        self.length = len(trace)
        self.count = 1

        # find defects in time vector
        if "time" in trace or "timestamp" in trace:
            if "time" in trace:
                diff_time = np.diff(trace["time"].values)
            else:
                diff_time = trace["timestamp"].diff().apply(lambda x: x.total_seconds()).values[1:]
            time_step = np.median(diff_time[diff_time > 0])
            self.time_step = time_step
            trace.attrs["time_step"] = time_step

            timestamp_defect = None
            if "time" in trace:
                if "timestamp" in trace:
                    if "timestamp" in trace.attrs:
                        delta_t = (trace["timestamp"].iloc[0] - trace.attrs["timestamp"]).total_seconds()
                        if delta_t == trace["time"].values[0]:
                            timestamp_defect = "DualTimeFields"
                        else:
                            # severe inconsistency between time and timestamp fields
                            timestamp_defect = "DualTimestampInconsistent"
                    else:
                        # no timestamp as reference for time field
                        timestamp_defect = "DualTimeFieldsIncomplete"
                elif "timestamp" not in trace.attrs:
                    timestamp_defect = "NoTimestamp"
            else:
                trace_time_vect_from_timestamp_vect(trace, ref_timestamp=trace["timestamp"].iloc[0])
            if timestamp_defect is not None:
                bool_defect = np.full((len(trace),), False)
                bool_defect[0] = True
                self._add_defect_list(timestamp_defect, "time", trace, bool_defect, trace["time"].values)

            bool_defect_1 = np.abs(diff_time - time_step) > time_step * Config.TIME_BASE_PRECISION_THR
            self._add_defect_list("IrregularTimeInterval", "time", trace, bool_defect_1, diff_time)
            bool_defect_1 = diff_time >= time_step * 2
            self._add_defect_list("TimeGap", "time", trace, bool_defect_1, diff_time)
            bool_defect_1 = diff_time < 0
            self._add_defect_list("TimeBacktrack", "time", trace, bool_defect_1, diff_time)
            bool_defect_1 = diff_time == 0
            self._add_defect_list("DoubleTime", "time", trace, bool_defect_1, diff_time)
            idx = np.where(bool_defect_1)[0]
            for i in idx:
                point_A = trace.iloc[i]
                point_B = trace.iloc[i + 1]
                field_comp = point_A == point_B
                if not field_comp.all():
                    # double time with a value that changed
                    bool_defect_1[i] = False
            self._add_defect_list("DoubleTimeRepeat", "time", trace, bool_defect_1, diff_time)
            self.duration = np.sum(diff_time, where=(diff_time >= 0))
        else:
            diff_time = np.full((len(trace) - 1,), Config.DEFAULT_TIME_STEP_SEC)
            time_step = Config.DEFAULT_TIME_STEP_SEC
            self.time_step = time_step
            trace.attrs["time_step"] = time_step
            self.duration = len(trace)
        diff_time_int = np.insert(diff_time, 0, time_step)
        diff_time_int[diff_time_int < 0] = 0
        # find invalid values
        for field in trace.keys():
            try:
                bool_defect = np.logical_not(np.isfinite(trace[field].values))
                self._add_defect_list("NonFinite", "values", trace, bool_defect, trace[field].values, more=field)
            except Exception:
                pass

        # find defects in speed vector
        if "speed" in trace:
            bool_defect = np.logical_not(np.isfinite(trace["speed"].values))
            self._add_defect_list("NonFiniteValue", "speed", trace, bool_defect, diff_time)

            bool_stop = np.abs(trace["speed"].values) < Config.SPEED_STOP_THRESHOLD_high_m_s
            bool_move = np.logical_not(bool_stop)
            delta_distance_m = np.abs(trace["speed"].values) * diff_time_int
            delta_distance_m[bool_stop] = 0
            delta_distance_m[bool_defect] = 0
            distance_m = np.cumsum(delta_distance_m)
            total_distance_m = np.sum(delta_distance_m)
            self.distance = total_distance_m
            self.max_speed = np.max(trace["speed"].values, initial=0)
            self.mean_speed = np.mean(np.abs(trace["speed"].values))
            self.mean_speed_move = np.mean(np.abs(trace["speed"].values), where=bool_move)
            self.duration_move = np.sum(diff_time_int, where=bool_move)
            time_int = np.cumsum(diff_time_int)
            _, (I_begins, I_ends) = stop_or_gap_detection(trace)
            I_begins, I_ends = np.array(I_begins), np.array(I_ends)
            if len(I_begins) == 0:
                I_begins, I_ends = np.full(0, (1,)), np.full(0, (1,))
            stop_duration = time_int[I_ends] - time_int[I_begins]
            self.stops_index_end = I_ends
            self.stops_index_begin = I_begins
            self.stops_duration = stop_duration
            self.stop_count = len(stop_duration)

            bool_defect_I = stop_duration >= Config.DISPLACEMENT_MAX_TIME_GAP_sec
            bool_defect = np.full((len(trace),), False)
            bool_defect[I_begins[bool_defect_I]] = True
            self._add_defect_list("SplitDisplacements", "time", trace, bool_defect, diff_time)

            bool_defect_I = np.logical_and(Config.STOP_DURATION_PAUSE_sec <= stop_duration,
                                           stop_duration < Config.DISPLACEMENT_MAX_TIME_GAP_sec)
            bool_defect[:] = False
            bool_defect[I_begins[bool_defect_I]] = True
            self._add_defect_list("Stop", "time", trace, bool_defect, diff_time)

            accel_m_s2 = np.diff(trace["speed"].values) / diff_time

            bool_defect_1 = (np.logical_and(accel_m_s2 > Config.ACCEL_FROM_STOP_THR_DEFECT_m_s2,
                                            np.logical_and(np.insert(bool_stop[:-2], 0, True),
                                                           bool_move[:-1])))
            self._add_defect_list("AccelFromStop", "speed", trace, bool_defect_1, accel_m_s2)
            bool_defect_1 = (np.logical_and(accel_m_s2 > Config.ACCEL_THR_DEFECT_m_s2,
                                            bool_move[:-1]))
            self._add_defect_list("Acceleration", "speed", trace, bool_defect_1, accel_m_s2)
            bool_defect = np.full((len(trace),), False)
            if bool_move[0]:
                bool_defect[0] = True
            if bool_move[-1]:
                bool_defect[-1] = True
            self._add_defect_list("IncompleteDisplacement", "speed", trace, bool_defect, trace["speed"].values)
        else:
            bool_move = np.full((len(trace),), True)
            delta_distance_m = np.full(bool_move.shape, np.nan)

        # find defects in GPS position
        if "hdop" in trace:
            bool_defect = (np.logical_and(trace["hdop"].values > Config.HDOP_THR,
                                          bool_move))
            self._add_defect_list("Hdop", "hdop", trace, bool_defect, trace["hdop"].values)
            self.validity["gps"] = self.validity["hdop"]  # transfer validity
        if "longitude" in trace and "latitude" in trace:
            bool_zero_pos = np.logical_and(trace["longitude"].values == 0, trace["latitude"].values == 0)
            bool_defect = bool_zero_pos
            self._add_defect_list("PositionZero", "gps", trace, bool_defect)

            x, y, pos_delta_distance_m, pos_speed_m_s = convert_lambert_compute_speed(
                longitude=trace["longitude"].values, latitude=trace["latitude"].values, time=time_int)
            pos_delta_distance_m[np.logical_or(bool_zero_pos, np.concatenate(([False], bool_zero_pos[1:])))] = np.nan
            bool_defect_1 = (pos_delta_distance_m[:-1] > Config.SPACE_GAP_THRESHOLD_m_s * diff_time)
            self._add_defect_list("PositionGap", "gps", trace, bool_defect_1, pos_delta_distance_m)
            if "speed" in trace:
                bool_defect_1 = (np.abs(pos_delta_distance_m - delta_distance_m)[:-1] > np.clip(delta_distance_m[:-1],
                                                                                                a_min=1.,
                                                                                                a_max=None) * diff_time * Config.GPS_POSITION_VS_SPEED_PRECISION)
                self._add_defect_list("PositionVsSpeed", "gps", trace, bool_defect_1, pos_delta_distance_m)
        # heading
        if "heading" in trace and "speed" in trace:
            curvature_1_m = curvature_from_heading(trace["heading"].values, trace["speed"].values)
            bool_defect = (np.abs(curvature_1_m) > Config.CURVATURE_MAX_1_m)
            self._add_defect_list("CurvatureSat", "heading", trace, bool_defect, curvature_1_m)
        # elevation
        if "elevation" in trace and "speed" in trace:
            slope = slope_from_elevation(elevation_m=trace["elevation"].values, distance_m=distance_m)
            bool_defect = (np.abs(slope) > Config.SLOPE_MAX_wu)
            self._add_defect_list("SlopeSat", "elevation", trace, bool_defect, slope)

        # cumulate defects on validity vector
        self.validity_global = np.full((len(trace),), True)
        for bool_valid in self.validity.values():
            self.validity_global = np.logical_and(self.validity_global, bool_valid)
        self.validity_total = np.sum(self.validity_global)
        self.defects_total = sum(self.issues_count.values(), 0)
        self.defects_count = {name: len(issues) for name, issues in self.defects.items()}
        bool_valid = self.validity_global
        if "speed" in trace:
            bool_move_valid = np.logical_and(bool_move, bool_valid)
            self.max_speed_valid = np.max(np.abs(trace["speed"].values), where=bool_move_valid, initial=0)
            self.mean_speed_move_valid = np.mean(np.abs(trace["speed"].values), where=bool_move_valid)
            self.duration_move_valid = np.sum(diff_time_int, where=bool_move_valid)
            self.distance_move_valid = np.sum(delta_distance_m, where=bool_move_valid)
            self.distance_valid = np.sum(delta_distance_m, where=bool_valid)
        self.duration_valid = np.sum(diff_time_int, where=bool_valid)

    def trace_add_hover_data(self):
        trace = self.trace
        all_defects: List[TraceDefect] = sum([lst for lst in self.defects.values()], [])
        defects_text = [[] for _ in range(len(trace))]
        for defect in all_defects:
            for i in defect.indexes:
                defects_text[i].append(str(defect))
        defects_text = ["; \n".join(lst) for lst in defects_text]
        trace["defects_text"] = defects_text
        self.defects_text_vect = trace["defects_text"]

    def __copy__(self):
        # basic copy function
        cp = TraceKpi(None)
        cp.__dict__.update(self.__dict__)
        return cp

    def copy(self):
        return self.__copy__()

    def __add__(self, other):
        dest = self.copy()
        dest += other
        return dest

    def __iadd__(self, other):
        self.trace = None
        self.defects_text_vect = None
        self.validity = {}
        self.validity_global = None
        self.stops_index_begin = None
        self.stops_index_end = None
        self.stops_duration = None
        for name, defects in other.defects.items():
            if name not in self.defects:
                self.defects[name] = defects
            else:
                self.defects[name] += defects
        for name, count in other.issues_count.items():
            if name not in self.defects:
                self.issues_count[name] = count
            else:
                self.issues_count[name] += count
        for name, count in other.defects_count.items():
            if name not in self.defects_count:
                self.defects_count[name] = count
            else:
                self.defects_count[name] += count
        self.defects_total = self.defects_total + other.defects_total
        self.validity_total = self.validity_total + other.validity_total
        self.count = self.count + other.count
        self.length = self.length + other.length
        self.duration = self.duration + other.duration
        self.distance = self.distance + other.distance
        self.max_speed = max(self.max_speed, other.max_speed)
        self.duration_move = self.duration_move + other.duration_move
        self.max_speed_valid = max(self.max_speed_valid, other.max_speed_valid)
        self.distance_move_valid = self.distance_move_valid + other.distance_move_valid
        self.duration_move_valid = self.duration_move_valid + other.duration_move_valid
        self.distance_valid = self.distance_valid + other.distance_valid
        self.duration_valid = self.duration_valid + other.duration_valid
        if self.stops_duration is None:
            self.stops_duration = other.stops_duration
        else:
            self.stops_duration = np.concatenate((self.stops_duration, other.stops_duration))
        self.stop_count = self.stop_count + other.stop_count
        # computations
        self.mean_speed = self.distance / self.duration
        self.mean_speed_move = self.distance / self.duration_move
        self.mean_speed_move_valid = self.distance_move_valid / self.duration_move_valid
        self.time_step = self.duration / self.length
        return self

    def to_dict(self, include_details=False):
        kpi = self.__dict__.copy()
        pop_list = []
        if not include_details:
            kpi.pop("defects")
        for f, v in kpi.items():
            if v is None:
                pop_list.append(f)
            elif isinstance(v, np.ndarray):
                kpi[f] = v.tolist()
            elif not isinstance(v, dict):
                kpi[f] = np.base_repr(v)
        for f in pop_list:
            kpi.pop(f)
        return kpi
