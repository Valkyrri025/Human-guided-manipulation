"""Panda, passive free-joint die and rigid pushing attachment on a table."""
import xml.etree.ElementTree as ET

import numpy as np
from scipy.spatial.transform import Rotation
from robosuite.environments.manipulation.lift import Lift
from robosuite.environments.manipulation.manipulation_env import ManipulationEnv
from robosuite.models.arenas import TableArena
from robosuite.models.objects import BoxObject
from robosuite.models.tasks import ManipulationTask
from .task_rules import box_inside_polygon


class PlanarPush(Lift):
    def __init__(self, object_start, target_xy, object_size, tool_radius=0.004, tool_kind="paddle", target_polygon=None, goal_tolerance=.02, paper_size=(.30,.297), **kwargs):
        self.paper_size=np.asarray(paper_size,float)
        self.object_start = np.asarray(object_start, float)
        self.target_xy = np.asarray(target_xy, float)
        self.object_size = np.asarray(object_size, float)
        self.tool_radius = tool_radius
        self.tool_kind = tool_kind
        self.target_polygon = target_polygon
        self.goal_tolerance = goal_tolerance
        super().__init__(**kwargs)

    def _load_model(self):
        ManipulationEnv._load_model(self)
        robot = self.robots[0].robot_model
        robot.set_base_xpos(robot.base_xpos_offset['table'](self.table_full_size[0]))
        arena = TableArena(table_full_size=self.table_full_size,
                           table_friction=self.table_friction, table_offset=self.table_offset)
        arena.set_origin([0, 0, 0])
        # Visual only: calibrated paper area and demonstration endpoint marker.
        arena.worldbody.append(ET.Element('geom', name='paper_visual', type='box',
            size=f'{self.paper_size[0]/2} {self.paper_size[1]/2} 0.0002', pos='0 0 0.8003', rgba='0.95 0.95 0.95 1',
            contype='0', conaffinity='0', group='1'))
        arena.worldbody.append(ET.Element('site', name='demonstrated_endpoint', type='cylinder',
            size='0.012 0.0005', pos=f'{self.target_xy[0]} {self.target_xy[1]} 0.801',
            rgba='0 0.5 1 0.5', group='1'))
        if self.target_polygon is not None:
            for i,a in enumerate(self.target_polygon):
                b=self.target_polygon[(i+1)%len(self.target_polygon)]
                arena.worldbody.append(ET.Element('geom', name=f'goal_border_{i}',type='capsule',
                    fromto=f'{a[0]} {a[1]} 0.801 {b[0]} {b[1]} 0.801',size='0.0007',
                    rgba='0.05 0.05 0.05 1',mass='0',contype='0',conaffinity='0',group='1'))
        position = np.array([0.50, 0.55, 1.28])
        z = position - np.array([0, 0, .82]); z /= np.linalg.norm(z)
        x = np.cross([0, 0, 1], z); x /= np.linalg.norm(x)
        y = np.cross(z, x)
        q = Rotation.from_matrix(np.column_stack([x, y, z])).as_quat()
        arena.worldbody.append(ET.Element('camera', name='pushview', pos=' '.join(map(str, position)),
            quat=' '.join(map(str, q[[3, 0, 1, 2]])), fovy='25'))
        # Robot-aligned overhead view: +X (away from base) is screen up.
        # Camera right is -Y; camera up is +X. Robot base lies below the table.
        arena.worldbody.append(ET.Element('camera',name='robotview',pos='0 0 1.65',
            xyaxes='0 -1 0 1 0 0',fovy='27'))
        self.cube = BoxObject(name='cube', size=self.object_size/2, rgba=[.2, .8, .1, 1],
                              density=2000, friction=[.3, .005, .0001])
        # Local +z is downward under the commanded fixed orientation.
        eef = next(b for b in robot.worldbody.iter('body') if b.get('name', '').endswith('_eef'))
        # Visible rigid mount: connect the existing contact stem to the grip
        # site/fingers. These massless, non-colliding sleeve pieces avoid
        # changing the validated contact geometry or robot inertia.
        eef.append(ET.Element('geom', name='pusher_mount_shaft', type='capsule',
            fromto='0 0 -0.010 0 0 0.025', size='0.003',
            rgba='1 0.45 0.05 1', mass='0', contype='0', conaffinity='0', group='1'))
        eef.append(ET.Element('geom', name='pusher_mount_collar', type='cylinder',
            pos='0 0 0.010', size='0.008 0.004', rgba='0.3 0.3 0.3 1',
            mass='0', contype='0', conaffinity='0', group='1'))
        if self.tool_kind == 'capsule':
            eef.append(ET.Element('geom', name='pusher_tip', type='capsule',
                fromto='0 0 0.025 0 0 0.060', size=str(self.tool_radius),
                rgba='1 0.45 0.05 1', mass='0.01', friction='0.5 0.005 0.0001',
                contype='1', conaffinity='1', group='1'))
        else:
            # A flat contact face avoids the sideways deflection of a narrow
            # rounded tip against a tiny die. Rigid simulated attachment.
            eef.append(ET.Element('geom', name='pusher_stem', type='capsule',
                fromto='0 0 0.025 0 0 0.054', size='0.003', rgba='1 0.45 0.05 1',
                mass='0.005', contype='1', conaffinity='1', group='1'))
            eef.append(ET.Element('geom', name='pusher_tip', type='box',
                pos='0 0 0.060', size=f'{self.tool_radius} 0.012 0.006',
                rgba='1 0.45 0.05 1', mass='0.005', friction='0.5 0.005 0.0001',
                contype='1', conaffinity='1', group='1'))
        self.model = ManipulationTask(mujoco_arena=arena, mujoco_robots=[robot], mujoco_objects=self.cube)

    def _reset_internal(self):
        ManipulationEnv._reset_internal(self)
        self.sim.data.set_joint_qpos(self.cube.joints[0], np.r_[self.object_start,
            self.table_offset[2]+self.object_size[2]/2+.0005, 1., 0., 0., 0.])
        # This is the sole object placement; no object writes during rollout.
        self.sim.forward()

    def _check_success(self):
        pos = self.sim.data.body_xpos[self.cube_body_id]
        on_table=abs(pos[2]-(self.table_offset[2]+self.object_size[2]/2))<.005
        if self.target_polygon is not None:
            rotation=self.sim.data.body_xmat[self.cube_body_id].reshape(3,3)
            return bool(on_table and box_inside_polygon(pos,rotation,self.object_size,self.target_polygon))
        return bool(on_table and np.linalg.norm(pos[:2]-self.target_xy)<self.goal_tolerance)

    def reward(self, action=None):
        return float(self._check_success())
