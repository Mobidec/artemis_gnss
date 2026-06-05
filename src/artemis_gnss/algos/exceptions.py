#!python3
# -*- coding: utf-8 -*-
"""
Exceptions used in the package
Created on 20/09/24
"""


class TimeOverlayException(Exception):
    def __init__(self, time_end, time_add):
        super.__init__(f"Time overlay exception: tried to insert {time_add} before {time_end}")

