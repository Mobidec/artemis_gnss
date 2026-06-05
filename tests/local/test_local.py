#!python3
# -*- coding: utf-8 -*-
"""
This test will not run in Github workflows because it is in the tests/local directory
"""

from artemis_gnss import hello_world


def test_hello_world():
    assert hello_world() is None
