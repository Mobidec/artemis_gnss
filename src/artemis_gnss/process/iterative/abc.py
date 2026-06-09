#!python3
# -*- coding: utf-8 -*-
"""
Base class
Created on 20/09/24
"""
from typing import List
from abc import ABC
import pandas as pd

purge_only_once = True


class StatefulStep(ABC):
    """
    Base methods defined for a step which has an internal variable to memorize between each call
    """
    def __init__(self):
        self._purged: bool = False

    def initialize(self, *args, **kwargs) -> List[pd.DataFrame]:
        """
        Initialize internal variables
        """
        self._purged = False

    def append(self, trace: pd.DataFrame, *args, **kwargs) -> List[pd.DataFrame]:
        """
        Append trace to current treatment
        """
        if purge_only_once:
            assert(not self._purged)

    def purge_last_step(self, *args, **kwargs) -> List[pd.DataFrame]:
        """
        Last steps to finalize treatment (if necessary)
        """
        if purge_only_once:
            assert(not self._purged)
        self._purged = True

    def flush_purge_and_reset(self, *args, **kwargs) -> List[pd.DataFrame]:
        """
        Do last steps, return result and initialize
        """
        output = self.purge_last_step(**kwargs)
        self.initialize()
        return output

    def get_state(self) -> dict:
        """
        Get dict of state variables necessary to restore the computation later

        :return:
        """
        raise NotImplementedError

    def restore(self, state: dict):
        """
        Restore state of the process
        :param state:
        :return:
        """
        raise NotImplementedError

