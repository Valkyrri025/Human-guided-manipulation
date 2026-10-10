"""Scripted teacher following a measured human object path, not a policy."""
import numpy as np


def object_tracking_target(object_goal, object_position, rotation, size, direction, radius):
    """Contact geometry plus a bounded correction; no independent goal input.

    The desired position is supplied by the human recording. The teacher cannot
    infer an unrecorded target trajectory from the square alone.
    """
    support=float(np.dot(np.abs(np.asarray(rotation).T@np.r_[direction,0.]),np.asarray(size)/2))
    correction=.75*(np.asarray(object_goal)-np.asarray(object_position))
    correction*=min(1.,.006/max(np.linalg.norm(correction),1e-12))
    return np.asarray(object_goal)-direction*(support+radius-.0005)+correction
