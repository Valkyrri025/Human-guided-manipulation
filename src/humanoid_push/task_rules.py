"""Shared geometric success and simulated-time stopping rules."""
from dataclasses import dataclass

import cv2
import numpy as np


def box_inside_polygon(position, rotation, size, polygon):
    """All projected box vertices inside target; no desired orientation."""
    if polygon is None:
        return False
    local=np.array([[sx*size[0]/2,sy*size[1]/2,sz*size[2]/2]
                    for sx in [-1,1] for sy in [-1,1] for sz in [-1,1]])
    corners=local@np.asarray(rotation).T+position
    contour=np.asarray(polygon,np.float32)
    return all(cv2.pointPolygonTest(contour,tuple(c[:2]),False)>=0 for c in corners)


@dataclass
class StopRule:
    timeout_s: float
    dwell_s: float = .2
    inside_since: float | None = None

    def update(self, elapsed_s, inside):
        if inside:
            if self.inside_since is None:
                self.inside_since=elapsed_s
            if elapsed_s-self.inside_since >= self.dwell_s-1e-9:
                return 'goal_reached'
        else:
            self.inside_since=None
        # Goal takes precedence if dwell completion and timeout coincide.
        if elapsed_s >= self.timeout_s-1e-9:
            return 'timeout'
        return None
