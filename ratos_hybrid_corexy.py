# Code for handling the kinematics of hybrid-corexy RatRig implementation
#
# Copyright (C) 2021  Fabrice Gallet <tircown@gmail.com>
# Modified 2023 by Helge Magnus Keck <helgekeck@hotmail.com>
# Modified 2024 by Mikkel Schmidt <mikkel.schmidt@gmail.com>
# Modified 2026 by Domingos Rodrigues <domingoslamas@gmail.com>
#
# This file may be distributed under the terms of the GNU GPLv3 license.
import logging
import stepper

# The hybrid-corexy kinematic for RatRig machines using a A/B CoreXY plane + cartesian y + cartesian Z motor 
class RatOSHybridCoreXYKinematics:
    def __init__(self, toolhead, config):
        self.inverted = False
        if config.has_section('ratos_hybrid_corexy'):
            self.inverted = config.getsection('ratos_hybrid_corexy').getboolean('inverted', False)
        # itersolve parameters
        self.rails = [stepper.LookupMultiRail(config.getsection('stepper_' + n))
                      for n in 'xyz']
        for s in self.rails[0].get_steppers():
            self.rails[1].get_endstops()[0][0].add_stepper(s)

        if len(self.rails[0].steppers)!=2:
                raise self.error("Unexpected stepper configuration, must have at one of each A/B motors")

        # Assign core XY motors
        if self.inverted == False:
            self.rails[0].steppers[0].setup_itersolve('corexy_stepper_alloc', b'-')
            self.rails[0].steppers[1].setup_itersolve('corexy_stepper_alloc', b'+')  
        else:
            self.rails[0].steppers[0].setup_itersolve('corexy_stepper_alloc', b'+')
            self.rails[0].steppers[1].setup_itersolve('corexy_stepper_alloc', b'-')

        # Assign cartesion motors
        self.rails[1].setup_itersolve('cartesian_stepper_alloc', b'y')
        self.rails[2].setup_itersolve('cartesian_stepper_alloc', b'z')
        
        self.supports_dual_carriage = False

        for s in self.get_steppers():
            s.set_trapq(toolhead.get_trapq())
        config.get_printer().register_event_handler("stepper_enable:motor_off",
                                                    self._motor_off)
        # Setup boundary checks
        max_velocity, max_accel = toolhead.get_max_velocity()
        self.max_z_velocity = config.getfloat(
            'max_z_velocity', max_velocity, above=0., maxval=max_velocity)
        self.max_z_accel = config.getfloat(
            'max_z_accel', max_accel, above=0., maxval=max_accel)
        self.limits = [(1.0, -1.0)] * 3
        ranges = [r.get_range() for r in self.rails]
        self.axes_min = toolhead.Coord([r[0] for r in ranges])
        self.axes_max = toolhead.Coord([r[1] for r in ranges])

        #Commands
        config.get_printer().lookup_object('gcode').register_command("SET_KINEMATIC_LIMIT",
                               self.cmd_SET_KINEMATIC_LIMIT,
                               desc=self.cmd_SET_KINEMATIC_LIMIT_help)

    cmd_SET_KINEMATIC_LIMIT_help = "Set Kinematic limits for Z axis VELOCITY(mm/s) ACCEL(mm/s2)"
    def cmd_SET_KINEMATIC_LIMIT(self, gcmd):
        self.max_z_velocity = gcmd.get_float('VELOCITY', default=self.max_z_velocity, above=0., maxval=150)
        self.max_z_accel = gcmd.get_float('ACCEL', default=self.max_z_accel , above=0., maxval=10000)
        temp = gcmd.get_int('VERBOSE', default=0)

        if ( temp == 1):
            msg = ("max_z_velocity: %.6f\n"
                "max_z_accel: %.6f\n" % (self.max_z_velocity, self.max_z_accel))
            gcmd.respond_info(msg, log=False)


    def get_steppers(self):
        return [s for rail in self.rails for s in rail.get_steppers()]

    def calc_position(self, stepper_positions):
        pos = [stepper_positions[rail.get_name()] for rail in self.rails]
        if self.inverted == False:
            return [pos[0] + pos[1], pos[1], pos[2]]
        else:
            return [pos[0] - pos[1], pos[1], pos[2]]

    def update_limits(self, i, range):
        l, h = self.limits[i]
        # Only update limits if this axis was already homed,
        # otherwise leave in un-homed state.
        if l <= h:
            self.limits[i] = range

    def set_position(self, newpos, homing_axes):
        for i, rail in enumerate(self.rails):
            rail.set_position(newpos)
            for axis_name in homing_axes:
                axis = "xyz".index(axis_name)
                rail = self.rails[axis]
                self.limits[axis] = rail.get_range()

    def clear_homing_state(self, clear_axes):
        for axis, axis_name in enumerate("xyz"):
            if axis_name in clear_axes:
                self.limits[axis] = (1.0, -1.0)

    def note_z_not_homed(self):
        # Helper for Safe Z Home
        self.limits[2] = (1.0, -1.0)

    def home_axis(self, homing_state, axis, rail):
        position_min, position_max = rail.get_range()
        hi = rail.get_homing_info()
        homepos = [None, None, None, None]
        homepos[axis] = hi.position_endstop
        forcepos = list(homepos)
        if hi.positive_dir:
            forcepos[axis] -= 1.5 * (hi.position_endstop - position_min)
        else:
            forcepos[axis] += 1.5 * (position_max - hi.position_endstop)
        # Perform homing
        homing_state.home_rails([rail], forcepos, homepos)

    def home(self, homing_state):
        for axis in homing_state.get_axes():
            self.home_axis(homing_state, axis, self.rails[axis])

    def _motor_off(self):
        self.limits = [(1.0, -1.0)] * 3

    def _check_endstops(self, move):
        end_pos = move.end_pos
        for i in (0, 1, 2):
            if (move.axes_d[i]
                and (end_pos[i] < self.limits[i][0]
                     or end_pos[i] > self.limits[i][1])):
                if self.limits[i][0] > self.limits[i][1]:
                    raise move.move_error("Must home axis first")
                raise move.move_error()

    def check_move(self, move):
        limits = self.limits
        xpos, ypos = move.end_pos[:2]
        if (xpos < limits[0][0] or xpos > limits[0][1]
            or ypos < limits[1][0] or ypos > limits[1][1]):
            self._check_endstops(move)
        if not move.axes_d[2]:
            # Normal XY move - use defaults
            return
        # Move with Z - update velocity and accel for slower Z axis
        self._check_endstops(move)
        z_ratio = move.move_d / abs(move.axes_d[2])
        move.limit_speed(
            self.max_z_velocity * z_ratio, self.max_z_accel * z_ratio)

    def get_status(self, eventtime):
        axes = [a for a, (l, h) in zip("xyz", self.limits) if l <= h]
        return {
            'homed_axes': "".join(axes),
            'axis_minimum': self.axes_min,
            'axis_maximum': self.axes_max,
            'z_maximum_speed': self.max_z_velocity,
            'z_maximum_acceleration': self.max_z_accel
        }

def load_kinematics(toolhead, config):
    return RatOSHybridCoreXYKinematics(toolhead, config)
