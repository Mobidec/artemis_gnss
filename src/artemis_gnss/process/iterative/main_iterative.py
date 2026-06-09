#!python3
# -*- coding: utf-8 -*-
"""
Main entry points for process functions
Created on 20/09/24
"""
from typing import List, Tuple
import pandas as pd

from artemis_gnss.data.clean_output import CleanOutput
from artemis_gnss.process.iterative.abc import StatefulStep
from artemis_gnss.process.options import CleanOptions, StepDeepCopy
from artemis_gnss.process.a_time_base import negotiate_common_timestamp, compute_first_timeval, apply_common_timestamp_init_time_vect
from artemis_gnss.process.iterative.C_split_trace_to_portions import SplitTraceStep
from artemis_gnss.process.iterative.E_merge_portions import MergePortionStep


class CleanProcess(StatefulStep):
    """
    Implementation of the steps to extract displacements from raw traces with data cleaning options
    """

    def __init__(self):
        super().__init__()
        self.options: CleanOptions = None
        self.trips: List[pd.DataFrame] = []
        self._process_split_trace: SplitTraceStep = SplitTraceStep()
        self._process_merge: MergePortionStep = MergePortionStep()
        self.initialize()

    def initialize(self, traces: List[pd.DataFrame] = None, *,
                   options: CleanOptions = None, init_last_trip: pd.DataFrame = None, **kwargs) -> List[pd.DataFrame]:
        """
        Reset state of main process and initialize common_timestamp from options.common_timestamp or from an initial
        stack of traces, sort this stack of traces according to the timestamp of the first sample

        :param traces:
        :param options: options to use for this iteration of the process process
        If user gives options.common_timestamp, the value from the user is used
        :param kwargs:
        :return:
        """
        super().initialize()
        self.trips: List[pd.DataFrame] = []
        if options is not None:
            self.options = options.copy()
        else:
            self.options = CleanOptions()
        self.options.common_timestamp = negotiate_common_timestamp(traces, common_timestamp=self.options.common_timestamp) if traces is not None else None
        if traces is not None:
            if self.options.inputs_deepcopy == StepDeepCopy.Beginning_NoSideEffect:
                traces = traces.copy()  # do not deep copy
            for k, trace in enumerate(traces):
                if self.options.inputs_deepcopy == StepDeepCopy.Beginning_NoSideEffect:
                    trace = trace.copy(deep=True)
                    traces[k] = trace
                compute_first_timeval(trace, self.options.common_timestamp)  # creates first_timeval attribute
            traces.sort(key=lambda trace: trace.attrs["first_timeval"])
        self._process_split_trace.initialize()
        self._process_merge.initialize(init_last_trip=init_last_trip)
        return traces

    def append(self, trace: pd.DataFrame, *args, **kwargs) -> List[pd.DataFrame]:
        """
        Feed process with new trace. The traces must be fed in chronological order.

        :param trace:
        :param args:
        :param kwargs:
        :return:
        """
        super().append(trace)
        if self.options.inputs_deepcopy == StepDeepCopy.Post_Init:
            trace = trace.copy(deep=True)
        apply_common_timestamp_init_time_vect(trace, self.options.common_timestamp,
                                              default_time_step=self.options.default_time_step)
        if self.options.inputs_deepcopy == StepDeepCopy.Post_TimeBase:
            trace = trace.copy(deep=True)
        new_portions = self._process_split_trace.append(trace, self.options)
        new_trips: List[pd.DataFrame] = []
        for portion in new_portions:
            new_trips += self._process_merge.append(portion, self.options)
        self.trips += new_trips
        return new_trips

    def purge_last_step(self, *args, **kwargs) -> List[pd.DataFrame]:
        """
        Last steps to finalize treatment (if necessary)
        """
        super().purge_last_step()
        residual_portion = self._process_split_trace.purge_last_step()
        if residual_portion is not None:
            new_trips = self._process_merge.append(residual_portion[0], self.options)
        else:
            new_trips = []
        last_trip = self._process_merge.purge_last_step(self.options)
        if last_trip is not None:
            new_trips.append(last_trip[0])
        self.trips += new_trips
        return new_trips

    def process_all(self, traces: List[pd.DataFrame], *,
                    options: CleanOptions = None, init_last_trip: pd.DataFrame = None) -> List[pd.DataFrame]:
        """
        Main entry point which applies the process to a collection of traces.

        :param traces: list of raw traces to process
        :param options: options.common_timestamp: timestamp for t=0 in output traces
        Usage 1: no timestamp for each trace => the time vectors are referenced to options.common_timestamp
        Usage 2: give timestamp for t=0 each individual trace using trace.attrs["timestamp"]
        Usage 3: give timestamp vector instead of time vector
        :return: list of cleaned traces
        """
        traces = self.initialize(traces, options=options, init_last_trip=init_last_trip)
        for trace in traces:
            self.append(trace)
        self.purge_last_step()
        return self.trips

    def flush_purge_and_reset(self, *args, **kwargs) -> List[pd.DataFrame]:
        """
        Do last steps, return result and initialize
        """
        self.purge_last_step()
        trips = self.trips
        self.trips: List[pd.DataFrame] = []
        self._process_merge.flush_purge_and_reset(self.options)
        self._process_split_trace.flush_purge_and_reset()
        self.initialize()
        return trips

    def get_output_trips(self):
        assert(self._purged)
        return self.trips

    def get_init_last_trip_edit(self) -> Tuple[bool, pd.DataFrame]:
        """
        if merge_edit_init_last_trip is enabled, the last trip in the database before the clean process can be modified
        this function returns the modified trip (call after purge)
        :return:
        """
        assert(self._purged)
        return self._process_merge.init_last_trip_has_changed, self._process_merge.init_last_trip_edit

    def get_debug(self):
        debug = {
             "history_portions_raw": self._process_split_trace.debug_history_portions_raw,
             "history_portions_clean": self._process_merge.debug_history_portions_clean,
        }
        return debug

    def get_output(self) -> CleanOutput:
        assert(self._purged)
        output = CleanOutput()
        output.displacements = self.get_output_trips()
        output.init_last_trip_has_changed, output.init_last_trip_edit = self.get_init_last_trip_edit()
        output.debug = self.get_debug()
        return output

    def get_state(self, include_trips=False) -> dict:
        state = {"options": self.options.to_dict()}
        if include_trips:
            state["trips"] = [trip.to_dict() for trip in self.trips]
        state.update(self._process_split_trace.get_state())
        state.update(self._process_merge.get_state())
        return state

    def restore(self, state: dict):
        self.options = CleanOptions.from_dict(state["options"])
        if "trips" in state:
            self.trips = [pd.DataFrame.from_dict(trip) for trip in state["trips"]]
        else:
            self.trips = []
        self._process_split_trace.restore(state)
        self._process_merge.restore(state, self.trips)
