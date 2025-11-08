""" Demo Code for Torque Control """
from TMotorAPI import Motor, MotorConfig

# Define Motor Setup Config
cfg = MotorConfig(motorType='AK70-10', motorId=1, maxTemperature=80)

# Torque Control -> 1. Manually Turn on 
motor = Motor(config=cfg)
motor.enable() # Turn on Motor
motor.set_torque(targetTorque=3, duration=0) # This will run until motor turn off
time.sleep(1)                                # If you want to run during desired time, then change the duration
motor.disable() # Turn off Motor

# Torque Control --> 2. Automatically Turn on
with Motor(config=cfg) as motor:
  motor.set_torque(targetTorque=3, duration=0)
