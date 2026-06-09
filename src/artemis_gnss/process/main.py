# -*- coding: utf-8 -*-
"""
Displacement identification from a set of raw traces
Created on 20/09/24
"""
from typing import List, Union, Tuple
from copy import deepcopy

import numpy as np
import pandas as pd

from artemis_gnss.data.trace import Trace, convert_traces_pandas
from artemis_gnss.data.clean_output import CleanOutput
from artemis_gnss.process.a_time_base import negotiate_common_timestamp, compute_first_timeval, apply_common_timestamp_init_time_vect
from artemis_gnss.config import Config
from artemis_gnss.process.b_clean_raw_stop_detection import clean_raw_steps, stop_or_gap_divide
from artemis_gnss.process.d_clean_portion import clean_portion_steps
from artemis_gnss.process.iterative.E_merge_portions import portion_decide_merge, merge_edit_init_last_trip
from artemis_gnss.process.iterative.main_iterative import CleanProcess
from artemis_gnss.process.f_clean_trip_post_merge import clean_trip_post_merge_steps
from artemis_gnss.algos.exceptions import TimeOverlayException
from artemis_gnss.process.options import CleanOptions


def sanitize_traces(traces: Union[pd.DataFrame, dict, Trace, List[Union[dict, pd.DataFrame, Trace]]], *,
                    common_timestamp: np.datetime64 = None, sort_traces=True, deep_copy=True) \
        -> Tuple[np.datetime64, List[pd.DataFrame]]:
    traces = convert_traces_pandas(traces, deep_copy=deep_copy)
    common_timestamp = negotiate_common_timestamp(traces, common_timestamp=common_timestamp) if traces is not None else None
    for k, trace in enumerate(traces):
        compute_first_timeval(trace, common_timestamp)  # creates first_timeval attribute
    if sort_traces:
        traces.sort(key=lambda trace: trace.attrs["first_timeval"])
    return common_timestamp, traces


def process_traces(traces: Union[pd.DataFrame, dict, Trace, List[Union[dict, pd.DataFrame, Trace]]], *,
                   options: CleanOptions=None, init_last_trip: pd.DataFrame = None,
                   iterative_implementation: bool = False) -> CleanOutput:
    if iterative_implementation:
        process = CleanProcess()
        process.process_all(traces, options=options, init_last_trip=init_last_trip)
        return process.get_output()
    output = CleanOutput()
    current_trip: pd.DataFrame
    previous_trip: pd.DataFrame
    if merge_edit_init_last_trip:
        current_trip, previous_trip = init_last_trip, None
        init_last_trip_passed = init_last_trip is None
    else:
        current_trip, previous_trip = None, init_last_trip
        init_last_trip_passed = True
    output.init_last_trip_has_changed = False
    common_timestamp, traces_fmt = sanitize_traces(traces)
    trace_concat = pd.DataFrame()
    # merge all traces into one
    for trace in traces_fmt:
        apply_common_timestamp_init_time_vect(trace, common_timestamp,
                                              default_time_step=Config.DEFAULT_TIME_STEP_SEC)
        clean_raw_steps(trace, options=options)
        if len(trace_concat) > 0 and trace["time"].iloc[0] <= trace_concat["time"].iloc[0]:
            raise TimeOverlayException(trace_concat["time"].iloc[0], trace["time"].iloc[0])
        trace_concat = pd.concat((trace_concat, trace))

    # cut into portions between stops and clean
    portions, residual_trace = stop_or_gap_divide(trace_concat, duration_cut_s=Config.STOP_DURATION_MAX__CUT_sec)
    if residual_trace is not None:
        portions.append(residual_trace)
    previous_portion = init_last_trip
    debug_history_portions_raw = deepcopy(portions) if Config.ENABLE_DEBUG else []
    idx_rm = []
    for i, trace in enumerate(portions):
        clean = trace
        clean_portion_steps(clean, previous_portion=previous_portion, options=options)
        if clean is not None:
            if Config.ENABLE_DEBUG:
                clean["portion_no"] = i
            portions[i] = clean
            previous_portion = clean
        else:
            idx_rm.append(i)
    debug_history_portions_clean = deepcopy(portions) if Config.ENABLE_DEBUG else []
    for i in reversed(idx_rm):
        portions.pop(i)

    # merge back into displacements
    displacements: List[pd.DataFrame] = []
    for i, trace in enumerate(portions):
        if current_trip is None:
            current_trip = trace
        elif portion_decide_merge(current_trip, trace):
            current_trip = pd.concat((current_trip, trace))
        else:
            new_trips, previous_trip = clean_trip_post_merge_steps(current_trip, options=options, previous_trip=previous_trip,
                                                                   is_last_trip=False)
            if merge_edit_init_last_trip and not init_last_trip_passed:
                if len(new_trips) == 0:
                    if previous_trip is not None:
                        init_last_trip_passed = False  # maintain value until new_trips contains something
                    else:
                        output.init_last_trip_edit = None  # destroy init_last_trip
                        output.init_last_trip_has_changed = True
                        init_last_trip_passed = True
                elif not new_trips[0] == init_last_trip:
                    output.init_last_trip_edit = new_trips.pop(0)  # replace init_last_trip & remove from outputs
                    output.init_last_trip_has_changed = True
                    init_last_trip_passed = True
            displacements += new_trips
            current_trip = trace
    if current_trip is not None:
        last_trace = current_trip
        new_trips, _ = clean_trip_post_merge_steps(last_trace, options=options, previous_trip=previous_trip,
                                                        is_last_trip=True)
        displacements += new_trips
        if displacements:
            previous_trip = displacements[-1]
        current_trip = None

    output.debug = {
        "history_portions_raw": debug_history_portions_raw,
        "history_portions_clean": debug_history_portions_clean,
    }
    output.displacements = displacements
    return output

