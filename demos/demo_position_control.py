from TMotorAPI import Motor, MotorConfig
import time
import numpy as np

# Motor Config & Setup
cfg = MotorConfig(motorType='AK70-10', motorId=2, maxTemperature=90)
motor = Motor(config=cfg)

#%% Example 1 - Step Command without Torque (duration=0, feedTor=0)
motor.enable()
motor.zero_position()
motor.set_position(targetPos=np.pi/2, duration=0, kp=10, kd=0.5, feedTor=0)
time.sleep(1)
motor.disable()

# To use the with statement, write it as follows:
with Motor(config=cfg) as motor:
    motor.set_position(targetPos=np.pi/2, duration=0, kp=10, kd=0.5, feedTor=0)
    time.sleep(1)

#%% Example 2 - Trajectory Tracking without Torque (duration≠0, feedTor=0)
motor.enable()
motor.zero_position()
motor.set_position(targetPos=np.pi/2, duration=3, kp=5, kd=0.5, feedTor=0, trajectoryType='minimum_jerk')
time.sleep(1)
motor.disable()

#%% Example 3 - Step Command with Torque (duration=0, feedTor≠0)
motor.enable()
motor.zero_position()
motor.set_position(targetPos=np.pi/2, duration=0, kp=10, kd=0.5, feedTor=0.5)
time.sleep(1)
motor.disable()

#%% Example 4 - Trajectory Tracking with Torque (duration≠0, feedTor≠0)
motor.enable()
motor.zero_position()
motor.set_position(targetPos=np.pi/2, duration=4, kp=10, kd=0.5, feedTor=0.5)
time.sleep(1)
motor.disable()
