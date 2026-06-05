#!python3
# -*- coding: utf-8 -*-
"""
Fields returned by the clean process
Created on 20/09/24
"""
import datetime
from typing import List
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from artemis_gnss.data.matched_trace import MatchedTrace
from artemis_gnss.enum_attrs import IMTransport, GenerationType
from artemis_gnss.algos.gps_position import pos_diff_distance_2_points

from artemis_gnss import __version__ as data_handling_version
VRS_DISP_TABLE_VERSION = "0.0.0"
one_line_per_day_no_displacement = False


@dataclass
class CleanOutput:
    """CleanOutput
    Class containing the fields returned by the clean process

    :param attrs: place for scalar values
    :param points: initial trace recordings
    :param match: map-matched points
    :param route: list of links representing the full trajectory
    """
    # TODO: displacements will be in MatchedTrace format
    displacements: List[pd.DataFrame] = field(default_factory=list)
    init_last_trip_has_changed: bool = None
    init_last_trip_edit: pd.DataFrame = None
    debug: dict = field(default_factory=dict)

    def get_displacement_table(self) -> pd.DataFrame:
        days_of_week = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
        last_date = None
        day_traj_no = 0
        table_lines = []
        for i, trace in enumerate(self.displacements):
            generation_type = trace.attrs["generation"]
            start_datetime = trace["timestamp"].iloc[0]
            stop_datetime = trace["timestamp"].iloc[-1]
            start_lon = trace["longitude"].iloc[0]
            stop_lon = trace["longitude"].iloc[-1]
            start_lat = trace["latitude"].iloc[0]
            stop_lat = trace["latitude"].iloc[-1]
            dist_OD_m = pos_diff_distance_2_points(lon1=start_lon, lat1=start_lat, lon2=stop_lon, lat2=stop_lat)
            imt_max = IMTransport(np.bincount(trace["imt"]).argmax())
            if last_date is not None and last_date != start_datetime.date():
                # add all missing dates as lines with no trajectory
                day_traj_no = 0
                if one_line_per_day_no_displacement:
                    last_date = last_date + datetime.timedelta(days=1)
                    while last_date < start_datetime.date():
                        line_dict = dict(date=last_date, day=days_of_week[start_datetime.day_of_week], num_depl=0,
                                         datetime_O=datetime.datetime.fromtimestamp(0),
                                         datetime_D=datetime.datetime.fromtimestamp(0),
                                         dist_OD=0)
                        table_lines.append(pd.DataFrame(line_dict, index=[len(table_lines)]))
                        last_date = last_date + datetime.timedelta(days=1)
                    last_date = last_date - datetime.timedelta(days=1)
                else:
                    last_date = start_datetime.date()
            if generation_type == GenerationType.Extract and imt_max != IMTransport.Noise:
                last_date = start_datetime.date()
                day_traj_no = day_traj_no + 1
                line_dict = dict(date=start_datetime.date(), day=days_of_week[start_datetime.day_of_week], num_depl=day_traj_no,
                                 datetime_O=start_datetime,
                                 datetime_D=stop_datetime,
                                 duration=(stop_datetime-start_datetime).total_seconds(),
                                 lon_O=start_lon, lat_O=start_lat,
                                 lon_D=stop_lon, lat_D=stop_lat,
                                 dist_OD=dist_OD_m, clean_index=i,
                                 mode=imt_max.to_str())
                table_lines.append(pd.DataFrame(line_dict, index=[len(table_lines)]))
        if one_line_per_day_no_displacement and last_date is not None and last_date != stop_datetime.date():
            # add all missing dates as lines with no trajectory
            while last_date < stop_datetime.date():
                line_dict = dict(date=last_date, day=days_of_week[start_datetime.day_of_week], num_depl=0,
                                 datetime_O=datetime.datetime.fromtimestamp(0),
                                 datetime_D=datetime.datetime.fromtimestamp(0),
                                 dist_OD=0)
                table_lines.append(pd.DataFrame(line_dict, index=[len(table_lines)]))
                last_date = last_date + datetime.timedelta(days=1)
        table = pd.concat(table_lines) if len(table_lines) > 0 else pd.DataFrame()
        table.attrs["VRS_DISP_TABLE_VERSION"] = VRS_DISP_TABLE_VERSION
        table.attrs["data_handling_version"] = data_handling_version
        table["VRS_DISP_TABLE_VERSION"] = VRS_DISP_TABLE_VERSION
        table["data_handling_version"] = data_handling_version
        return table


