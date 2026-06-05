#!python3
# -*- coding: utf-8 -*-
"""
Package for mobility data manipulation
Created on 20/09/24
"""

__version__ = "0.0.1"
# import pkg_resources
# __version__ = pkg_resources.get_distribution('artemis_gnss').version

from . import enum_modes
from . import config
from . import process
from . import kpi

# alias
from artemis_gnss.config import Config

