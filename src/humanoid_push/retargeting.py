"""Initial-state-only geometric adaptation; no learning or online steering."""
import numpy as np


def adapt_reference(reference, object_start, mode, radius=.004):
    """Keep contact offsets in metres; scale only recorded displacement."""
    if mode not in ('absolute', 'relative', 'relative-scaled'):
        raise ValueError('Unknown retargeting mode')
    result=dict(reference)
    original_start=np.asarray(reference['object_start'])
    new_start=np.asarray(object_start,dtype=float)
    old_direction=reference['target']-original_start
    new_direction=reference['target']-new_start
    old_distance=np.linalg.norm(old_direction);new_distance=np.linalg.norm(new_direction)
    if min(old_distance,new_distance)<.01:
        raise ValueError('Start-to-goal distance must be at least 1 cm')
    old_yaw=np.arctan2(old_direction[1],old_direction[0])
    new_yaw=np.arctan2(new_direction[1],new_direction[0])
    angle=float(new_yaw-old_yaw)
    rotation=np.array([[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]])
    result['object_start']=new_start
    # Same initial orientation rule in every method, including absolute replay.
    result['push_yaw_rad']=float(new_yaw)
    result['original_reference_xy']=reference['reference_xy'].copy()
    result['original_object_start']=original_start.copy()
    scale=float(new_distance/old_distance) if mode=='relative-scaled' else 1.
    if mode!='absolute':
        path=reference['reference_xy']
        # Rotate the initial contact offset but do not stretch cube/tool size.
        offset=rotation@(path[0]-original_start)
        old_support=np.dot(np.abs(old_direction/old_distance),reference['object_size'][:2]/2)
        new_support=np.dot(np.abs(new_direction/new_distance),reference['object_size'][:2]/2)
        offset-=new_direction/new_distance*(new_support-old_support)
        result['reference_xy']=new_start+offset+scale*((path-path[0])@rotation.T)
        result['endpoint']=new_start+scale*(rotation@(reference['endpoint']-original_start))
    result['retargeting']={'mode':mode,'rotation_degrees':float(np.degrees(angle)) if mode!='absolute' else 0.,
                          'displacement_scale':scale,'original_start_xy_m':original_start.tolist(),
                          'new_start_xy_m':new_start.tolist(),
                          'orientation_rule':'all modes face new initial object-to-target direction; fixed during push',
                          'feedback':'initial geometry only; cube feedback subsequently monitors termination'}
    return result
