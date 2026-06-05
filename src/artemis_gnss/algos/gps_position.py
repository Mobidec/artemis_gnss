#!python3
# -*- coding: utf-8 -*-
"""
Functions common to convert between GPS coordinate systems
Created on 20/09/24
"""
from typing import Tuple, Union

import numpy as np
from scipy.spatial import ConvexHull
from numpy.typing import NDArray

from numba import jit

from artemis_gnss.enum_modes import NormType


# TODO: is there a simplified version of this function enabling to compute distances between points in meters?
@jit(nopython=True)
def convert_lambert(*, longitude: NDArray[np.float64], latitude: NDArray[np.float64]) \
    -> Tuple[NDArray[np.float64], NDArray[np.float64]]:
    """
    Méthode de conversion des données géo en lambert

    Inputs
    ------
    longitude [°]
    latitude [°]

    Outputs
    -------
    x [m]
    y [m]

    """

    a = 6378137.
    b = a * (1 - 1 / 298.257222101)
    phi1 = 44 / 180 * np.pi
    phi2 = 49 / 180 * np.pi
    lam0 = 3 / 180 * np.pi
    phi0 = (46 + 30 / 60) / 180 * np.pi
    X0 = 700000.
    Y0 = 6600000.
    e = np.sqrt(a ** 2 - b ** 2) / a

    n = (np.log(np.cos(phi2) / np.cos(phi1)) +
         0.5 * np.log((1 - e ** 2 * np.sin(phi1) ** 2) /
                        (1 - e ** 2 * np.sin(phi2) ** 2))) / \
        (np.log((np.tan(phi1 / 2 + np.pi / 4) *
                   (1 - e * np.sin(phi1)) ** (e / 2) *
                   (1 + e * np.sin(phi2)) ** (e / 2)) /
                  (np.tan(phi2 / 2 + np.pi / 4) * (1 + e * np.sin(phi1)) ** (e / 2) *
                   (1 - e * np.sin(phi2)) ** (e / 2))))

    rhof = a * np.cos(phi1) / (n * np.sqrt(1 - e ** 2 * np.sin(phi1) ** 2)) * \
           (np.tan(phi1 / 2 + np.pi / 4) *
            ((1 - e * np.sin(phi1)) / (1 + e * np.sin(phi1))) ** (e / 2)) ** n
    rho0 = rhof * (1 / np.tan(phi0 / 2 + np.pi / 4) *
                   ((1 + e * np.sin(phi0)) /
                    (1 - e * np.sin(phi0))) ** (e / 2)) ** n

    phi = latitude / 180 * np.pi
    lam = longitude / 180 * np.pi

    theta = n * (lam - lam0)
    rho = rhof * (1 / np.tan(phi / 2 + np.pi / 4) * ((1 + e * np.sin(phi)) /
                                                       (1 - e * np.sin(phi))) ** (e / 2)) ** n

    x = X0 + rho * np.sin(theta)
    y = Y0 + rho0 - rho * np.cos(theta)

    return x, y


def distance_compute_ortho(dx: Union[NDArray[np.float64], float], dy: Union[NDArray[np.float64], float],
                           norm: NormType = None, squared: bool = False) -> Union[NDArray[np.float64], float]:
    if norm is None:
        norm = NormType.Norm2_Sqr
    if norm == NormType.NormInf_max:
        dist = np.maximum(np.abs(dx), np.abs(dy))
    elif norm == NormType.Norm2_Sqr:
        dist_sqr = (np.square(dx) + np.square(dy))
        if squared:
            return dist_sqr
        else:
            dist = np.sqrt(dist_sqr)
    elif norm == NormType.Norm1_Abs:
        dist = np.abs(dx) + np.abs(dy)
    else:
        raise(NotImplementedError)
    assert(not squared)
    return dist



#% reference functions for distance computations
def pos_diff_distance(*, longitude: NDArray[np.float64], latitude: NDArray[np.float64],
                      norm: NormType = None, squared: bool = False) -> NDArray[np.float64]:
    x, y = convert_lambert(longitude=longitude, latitude=latitude)
    return distance_compute_ortho(np.diff(x), np.diff(y), norm=norm, squared=squared)


def pos_diff_distance_same_len(*, longitude: NDArray[np.float64], latitude: NDArray[np.float64],
                               norm: NormType = None, squared: bool = False) -> NDArray[np.float64]:
    x, y = convert_lambert(longitude=longitude, latitude=latitude)
    return distance_compute_ortho(np.diff(x, append=0.), np.diff(y, append=0.), norm=norm, squared=squared)


def pos_diff_distance_2_points(*, lon1: float, lat1: float, lon2: float, lat2: float,
                               norm: NormType = None, squared: bool = False) -> float:
    longitude = np.array([lon1, lon2])
    latitude = np.array([lat1, lat2])
    return pos_diff_distance(longitude=longitude, latitude=latitude, norm=norm, squared=squared)[0]


def pos_diff_distance_from_point(*, lon0: float, lat0: float,
                                 longitude: NDArray[np.float64], latitude: NDArray[np.float64],
                                 norm: NormType = None, squared: bool = False) -> NDArray[np.float64]:
    x0, y0 = convert_lambert(longitude=lon0, latitude=lat0)
    x, y = convert_lambert(longitude=longitude, latitude=latitude)
    return distance_compute_ortho(x0 - x, y0 - y, norm=norm, squared=squared)


def convert_lambert_compute_speed(*, longitude: NDArray[np.float64], latitude: NDArray[np.float64], \
                                  time: NDArray[np.float64]) \
        -> Tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    x, y = convert_lambert(longitude=longitude, latitude=latitude)
    delta_distance_m = pos_diff_distance_same_len(longitude=longitude, latitude=latitude)
    delta_t = np.diff(time, append=0.)
    if len(longitude) > 1:
        delta_distance_m[-1] = delta_distance_m[-2]
        delta_t[-1] = delta_t[-2]
    elif len(longitude) == 1:
        delta_distance_m[0] = 0.
        delta_t[0] = 0.
    speed_m_s = delta_distance_m / delta_t
    return x, y, delta_distance_m, speed_m_s

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # Rayon moyen de la Terre en mètres

    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    
    distance = R * c
    return distance

def calculate_enclosing_circle(points):

    # Trouver l'enveloppe convexe des points (le plus petit polygone entourant les points)
    hull = ConvexHull(points)

    # Trouver le point moyen des points de l'enveloppe convexe pour l'utiliser comme centre
    center = np.mean(points[hull.vertices], axis=0)

    # Calculer le rayon en utilisant la distance maximale entre le centre et les points de l'enveloppe convexe
    radius_in_meters = np.max([haversine_distance(center[0], center[1], point[0], point[1]) for point in points[hull.vertices]])

    return center, radius_in_meters


if __name__ == '__main__':
    time = np.array([0, 1])
    lon = np.array([44, 45])
    lat = np.array([5, 5])
    x, y = convert_lambert(longitude=lon, latitude=lat)
    print(x)
    print(y)
    distance_m = pos_diff_distance(longitude=lon, latitude=lat, squared=False)
    print(distance_m)
    distance_m = pos_diff_distance_2_points(lon1=lon[0], lat1=lat[0], lon2=lon[1], lat2=lat[1])
    print(distance_m)
    x, y, distance_m, speed_m_s = convert_lambert_compute_speed(longitude=lon, latitude=lat, time=time)
    print(distance_m)
    print(speed_m_s)

