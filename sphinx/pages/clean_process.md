Clean process steps
=========

This page details the steps leading from a collection of raw traces to a collection of displacements.

## Definitions

- A _trace_ is a geospatial timeseries with at least a timestamp, a latitude and a longitude for each data point.
- A _portion_ is the movement between two stops.
- A _trip_ groups portions using a same means of transport.
- A _displacement_ groups trips, from an origin to its final destination. It is usually associated to one motivation class.

## Overview

The principle is to cut the _raw trace_ into successive _elementary portions_. 
An _elementary portion_ can be recorded on two successive _raw traces_. 
This is why there can be a _residual trace_ remaining after the treatment of a _trace_ if the trace does not end with a stop.
Two successive _traces_ can overlap in time. In this case, the most recent data is taken into account (__TODO__: verify).

Each _elementary portion_ is analyzed and attributed a first means of transport. The _elementary portions_
are then merged into a _displacement_. A new _displacement_ is started if the time or distance between the last point and the new _portion_ is too large.

The stateful implementation is meant to accept new traces at any moment, with the constraint of feeding them in chronological order.


# Detailed steps

## A. Time base

This step determines the start timestamp from a collection of _raw traces_.

## B. Clean raw signals and stop detection

A first set of functions is directly applied to the _raw trace_. 
These functions are to be implemented in the `clean_raw_steps` function in module `artemis_gnss.process.b_clean_raw_stop_detection`.
The current treatments are:
- Compute the distance between the successive GPS coordinates.

In the same module, the stop detection algorithm is implemented: `stop_or_gap_divide`. It returns the _elementary portions_
and _residual trace_ of the trace. 

## C. Split trace to portions

This step is defined only for the stateful implementation of the process. Its state stores the _residual trace_ of the last processed _trace_.
If the previous execution contains a _residual trace_, it prepends the incoming _trace_ with the _residual trace_.
This step is responsible for calling step B before any treatments. 

In the non-stateful implementation, a simple call to `stop_or_gap_divide` initializes the _portions_ from the list of input _traces_.

## D. Clean portion signals

This step applies treatments to each portion. The functions are to be implemented in the `clean_portion_steps` located in
module `artemis_gnss.process.d_clean_portion`. 
The current treatments are:
- Detect if signal is under noise threshold.
- First guess of transportation means.

## E. Merge portions into displacements

There is a stateful implementation of this step which keeps in its state the last unfinished _displacement_. The last
_displacement_ is released for the last call (last portion). The stateful implementation is responsible for applying step D to each portion given in input. 

The main function is `clean_trip_post_merge_steps`. It is responsible for calling the function of step F on each output displacement.

__TODO__: document this step

## F. Clean displacement signals

This step applies treatments to the finalized displacement. There are no treatments implemented for the moment.
