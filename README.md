##  [Description (EN)]
A module with some extra files to enhance normal klipper capabilities and make instalation faster.
Allows the usage of RatRig Hybrid kinematics on klipper.
Includes slightly modified beacon files

Adds some extra commands to allow further automation:
- SET_KINEMATIC_LIMIT VELOCITY=.... ACCEL=.... (allows user to set the limits of the Z axis on the fly)
- Z_TILT_ADJUST X1=... Y1=... X2=... Y2=... X3=... Y3=... (allow user to do Z tilt on a given position, usefull for multi mode probes such as beacon that use different offsets)
- SET_PRESSURE_ADVANCE EXTRUDER=... ADVANCE=.... SMOOTH_TIME=... VERBOSE=... (included verbose term that needs to be set to one for pressure advance to announce the change. Usefull to avoid excessive messages with adaptive PA)
- Silent probing for beacon, avoid excessive spam messages on the console with no real use besides debug can be forced by using VERBOSE=1 on beacon commands

