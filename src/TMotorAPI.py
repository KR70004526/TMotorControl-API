"""
TMotor Control API v3.1 - Final Corrected Version
Based on TMotorCANControl by Neurobionics Lab

Major Fixes (v3.1):
- CORRECT usage of TMotorCANControl API (property assignment + update())
- Fixed track_trajectory() parameter order (duration as 2nd argument)
- Unified naming: camelCase for variables, snake_case for functions  
- Improved error handling for RuntimeWarning
- All comments in English

Author: TMotor Control Team
License: MIT
"""

import os
import sys
import time
import subprocess
import logging
import re
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
import numpy as np

try:
    from TMotorCANControl.mit_can import TMotorManager_mit_can
except ImportError:
    print("Error: TMotorCANControl not installed. Run: pip install TMotorCANControl")
    sys.exit(1)


# ==================== Constants ====================
CONTROL_LOOP_FREQUENCY = 100  # Hz
CONTROL_LOOP_PERIOD = 1.0 / CONTROL_LOOP_FREQUENCY  # 0.01 seconds
STEP_COMMAND_THRESHOLD = 0.02  # 20ms
ZERO_POSITION_SETTLE_TIME = 0.5  # seconds
CAN_INTERFACE_PATTERN = re.compile(r'^can\d+$')


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)


# ==================== Configuration Class ====================
@dataclass
class MotorConfig:
    """
    Motor configuration with camelCase naming
    
    Attributes:
        motorType: Motor model (e.g., 'AK80-64', 'AK80-9', 'AK80-10')
        motorId: CAN ID (1-32)
        canInterface: CAN interface name (e.g., 'can0')
        bitrate: CAN bitrate (default: 1000000)
        autoInit: Auto initialize CAN interface
        maxTemperature: Maximum safe temperature (°C)
        defaultKp: Default position gain (Nm/rad)
        defaultKd: Default velocity gain (Nm/(rad/s))
        defaultTorqueLimit: Default torque limit (Nm)
    """
    motorType: str = 'AK80-64'
    motorId: int = 1
    canInterface: str = 'can0'
    bitrate: int = 1000000
    autoInit: bool = True
    maxTemperature: float = 50.0
    
    # Default control gains
    defaultKp: float = 10.0
    defaultKd: float = 0.5
    
    def __post_init__(self):
        """Validate configuration"""
        if not 1 <= self.motorId <= 32:
            raise ValueError(f"motorId must be between 1 and 32, got {self.motorId}")
        if not CAN_INTERFACE_PATTERN.match(self.canInterface):
            raise ValueError(f"Invalid CAN interface: {self.canInterface}")


# ==================== CAN Interface Management ====================
class CANInterface:
    """CAN interface setup and management"""
    
    @staticmethod
    def setup_interface(canInterface: str = 'can0', bitrate: int = 1000000) -> bool:
        """
        Setup CAN interface
        
        Args:
            canInterface: CAN interface name
            bitrate: CAN bitrate
            
        Returns:
            bool: True if successful
        """
        if not CAN_INTERFACE_PATTERN.match(canInterface):
            raise ValueError(f"Invalid CAN interface: {canInterface}")
        
        try:
            subprocess.run(['sudo', 'ip', 'link', 'set', canInterface, 'down'],
                         check=True, capture_output=True)
            subprocess.run(['sudo', 'ip', 'link', 'set', canInterface,
                          'type', 'can', 'bitrate', str(bitrate)],
                         check=True, capture_output=True)
            subprocess.run(['sudo', 'ip', 'link', 'set', canInterface, 'up'],
                         check=True, capture_output=True)
            
            logging.info(f"✓ CAN interface {canInterface} setup complete")
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to setup CAN: {e}")
            return False


# ==================== Trajectory Generator ====================
class TrajectoryGenerator:
    """Trajectory generation utilities"""
    
    @staticmethod
    def minimum_jerk(startPos: float, endPos: float,
                    currentTime: float, totalDuration: float) -> Tuple[float, float]:
        """
        Minimum jerk trajectory (5th order polynomial)
        
        Returns:
            tuple: (position, velocity)
        """
        if currentTime >= totalDuration:
            return endPos, 0.0
        
        tau = currentTime / totalDuration
        posDelta = endPos - startPos
        
        s = 10 * tau**3 - 15 * tau**4 + 6 * tau**5
        sDot = (30 * tau**2 - 60 * tau**3 + 30 * tau**4) / totalDuration
        
        position = startPos + posDelta * s
        velocity = posDelta * sDot
        
        return position, velocity
    
    @staticmethod
    def cubic(startPos: float, endPos: float,
             currentTime: float, totalDuration: float) -> Tuple[float, float]:
        """Cubic polynomial trajectory"""
        if currentTime >= totalDuration:
            return endPos, 0.0
        
        tau = currentTime / totalDuration
        posDelta = endPos - startPos
        
        s = -2 * tau**3 + 3 * tau**2
        sDot = (-6 * tau**2 + 6 * tau) / totalDuration
        
        return startPos + posDelta * s, posDelta * sDot
    
    @staticmethod
    def linear(startPos: float, endPos: float,
              currentTime: float, totalDuration: float) -> Tuple[float, float]:
        """Linear interpolation"""
        if currentTime >= totalDuration:
            return endPos, 0.0
        
        posDelta = endPos - startPos
        velocity = posDelta / totalDuration
        return startPos + velocity * currentTime, velocity


# ==================== Motor Class ====================
class Motor:
    """
    High-level motor control API
    
    Naming Convention:
    - Variables: camelCase
    - Functions: snake_case
    
    Example:
        with Motor('AK80-10', motorId=2, autoInit=True) as motor:
            motor.track_trajectory(1.57, 2.0)  # pos=1.57, duration=2.0
    """
    
    def __init__(self,
                 motorType: str = 'AK80-64',
                 motorId: int = 1,
                 canInterface: str = 'can0',
                 bitrate: int = 1000000,
                 autoInit: bool = True,
                 maxTemperature: float = 50.0,
                 **kwargs):
        """
        Initialize Motor
        
        Args:
            motorType: Motor model
            motorId: CAN ID (1-32)
            canInterface: CAN interface
            bitrate: CAN bitrate
            autoInit: Auto setup CAN
            maxTemperature: Max safe temperature (°C)
        """
        # Create config
        self.config = MotorConfig(
            motorType=motorType,
            motorId=motorId,
            canInterface=canInterface,
            bitrate=bitrate,
            autoInit=autoInit,
            maxTemperature=maxTemperature,
            **kwargs
        )
        
        # Internal state
        self._manager: Optional[TMotorManager_mit_can] = None
        self._isEnabled = False
        self._powerOnTime = 0.0
        
        # Last state
        self._lastPosition = 0.0
        self._lastVelocity = 0.0
        self._lastTorque = 0.0
        self._lastTemperature = 0.0
        
        # Setup CAN
        if self.config.autoInit:
            CANInterface.setup_interface(self.config.canInterface, self.config.bitrate)
        
        # Initialize manager
        try:
            self._manager = TMotorManager_mit_can(
                motor_type=self.config.motorType,
                motor_ID=self.config.motorId,
                max_mosfett_temp=self.config.maxTemperature
            )
            logging.info(f"✓ Motor connected: {self.config.motorType} ID={self.config.motorId}")
        except Exception as e:
            logging.error(f"Failed to connect motor: {e}")
            raise
    
    # ==================== Context Manager ====================
    
    def __enter__(self):
        """Enter context (power ON)"""
        self.enable()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context (power OFF)"""
        self.disable()
        return False
    
    # ==================== Properties ====================
    
    @property
    def position(self) -> float:
        """Current position (rad)"""
        return self._lastPosition
    
    @property
    def velocity(self) -> float:
        """Current velocity (rad/s)"""
        return self._lastVelocity
    
    @property
    def torque(self) -> float:
        """Current torque (Nm)"""
        return self._lastTorque
    
    @property
    def temperature(self) -> float:
        """Current temperature (°C)"""
        return self._lastTemperature
    
    # ==================== Power Management ====================
    
    def enable(self) -> None:
        """
        Enable motor (Power ON)
        
        Automatically called when using context manager
        """
        if self._isEnabled:
            logging.warning("Motor already enabled")
            return
        
        if self._manager is None:
            raise RuntimeError("Motor manager not initialized")
        
        try:
            self._manager.__enter__()
            self._isEnabled = True
            self._powerOnTime = time.time()
            
            time.sleep(0.1)  # Stabilization delay
            self.update()
            
            logging.info("=" * 60)
            logging.info("Motor ENABLED (Powered ON)")
            logging.info("=" * 60)
        except Exception as e:
            logging.error(f"Failed to enable motor: {e}")
            raise
    
    def disable(self) -> None:
        """
        Disable motor (Power OFF)
        
        Automatically called when exiting context manager
        """
        if self._manager and self._isEnabled:
            try:
                uptime = time.time() - self._powerOnTime
                self._manager.__exit__(None, None, None)
                self._isEnabled = False
                
                logging.info("=" * 60)
                logging.info("Motor DISABLED (Powered OFF)")
                logging.info(f"Total powered-on time: {uptime:.2f} seconds")
                logging.info("=" * 60)
            except Exception as e:
                logging.error(f"Error disabling motor: {e}")
    
    def update(self) -> Dict[str, float]:
        """
        Update motor state
        
        THIS IS THE CORRECT TMotorCANControl API USAGE:
        - Reads CAN messages from motor
        - Updates internal state
        
        Returns:
            dict: Motor state
        """
        if not self._isEnabled or self._manager is None:
            raise RuntimeError("Motor not enabled")
        
        try:
            # CORRECT API: TMotorManager.update()
            self._manager.update()
            
            # Read state from manager
            self._lastPosition = self._manager.position
            self._lastVelocity = self._manager.velocity
            self._lastTorque = self._manager.torque
            self._lastTemperature = self._manager.get_temperature_celsius()
            
            return {
                'position': self._lastPosition,
                'velocity': self._lastVelocity,
                'torque': self._lastTorque,
                'temperature': self._lastTemperature
            }
        except Exception as e:
            # RuntimeWarning is common - just log without raising
            logging.debug(f"Update warning: {e}")
            return {
                'position': self._lastPosition,
                'velocity': self._lastVelocity,
                'torque': self._lastTorque,
                'temperature': self._lastTemperature
            }
    
    def is_power_on(self) -> bool:
        """Check if motor is powered on"""
        return self._isEnabled
    
    def get_uptime(self) -> float:
        """Get motor uptime (seconds)"""
        if self._isEnabled:
            return time.time() - self._powerOnTime
        return 0.0
    
    # ==================== Control Mode 1: Trajectory Control ====================
    
    def track_trajectory(self,
                        targetPos: float,
                        duration: float = 0.0,  # ⭐ 2nd parameter!
                        kp: Optional[float] = None,
                        kd: Optional[float] = None,
                        trajectoryType: str = 'minimum_jerk') -> None:
        """
        Trajectory control (Position control)
        
        CRITICAL: duration is the 2nd positional argument!
        
        Args:
            targetPos: Target position (rad)
            duration: Motion duration (seconds) [2ND ARGUMENT!]
                - 0: Immediate step position
                - >0: Smooth trajectory
            kp: Position gain (Nm/rad)
            kd: Velocity gain (Nm/(rad/s))
            trajectoryType: 'minimum_jerk', 'cubic', 'linear'
        
        Examples:
            motor.track_trajectory(1.57)           # Immediate
            motor.track_trajectory(1.57, 2.0)      # 2-second trajectory
            motor.track_trajectory(1.57, 2.0, kp=10, kd=0.5)
        """
        if not self._isEnabled or self._manager is None:
            raise RuntimeError("Motor not enabled")
        
        if kp is None:
            kp = self.config.defaultKp
        if kd is None:
            kd = self.config.defaultKd
        
        try:
            # Set impedance gains
            self._manager.set_impedance_gains_real_unit(K=kp, B=kd)
            
            if duration <= STEP_COMMAND_THRESHOLD:
                # ===== Step Position Mode =====
                logging.info(f"Step position: {self._lastPosition:.3f} → {targetPos:.3f} rad")
                
                # CORRECT API: Property assignment + update()
                self._manager.position = targetPos
                self._manager.velocity = 0.0
                self._manager.torque = 0.0
                self.update()
                return
            
            # ===== Trajectory Following Mode =====
            if trajectoryType == 'minimum_jerk':
                trajFunc = TrajectoryGenerator.minimum_jerk
            elif trajectoryType == 'cubic':
                trajFunc = TrajectoryGenerator.cubic
            elif trajectoryType == 'linear':
                trajFunc = TrajectoryGenerator.linear
            else:
                raise ValueError(f"Unknown trajectory type: {trajectoryType}")
            
            startPos = self._lastPosition
            t0 = time.time()
            
            logging.info(f"Trajectory: {startPos:.3f} → {targetPos:.3f} rad "
                        f"({duration:.2f}s, {trajectoryType})")
            
            while True:
                t = time.time() - t0
                if t >= duration:
                    break
                
                # Calculate trajectory point
                p, v = trajFunc(startPos, targetPos, t, duration)
                
                # CORRECT API: Property assignment + update()
                self._manager.position = p
                self._manager.velocity = v
                self._manager.torque = 0.0
                self.update()
                
                time.sleep(CONTROL_LOOP_PERIOD)
            
            # Final position
            self._manager.position = targetPos
            self._manager.velocity = 0.0
            self._manager.torque = 0.0
            self.update()
            
            logging.info(f"✓ Trajectory complete: {self._lastPosition:.3f} rad")
            
        except Exception as e:
            logging.error(f"Trajectory failed: {e}")
            raise
    
    # ==================== Control Mode 2: Velocity Control ====================
    
    def set_velocity(self,
                    targetVel: float,
                    kd: Optional[float] = None,
                    duration: float = 0.0) -> None:
        """
        Velocity control
        
        Args:
            targetVel: Target velocity (rad/s)
            kd: Damping gain
            duration: How long to maintain (0=indefinite)
        """
        if not self._isEnabled or self._manager is None:
            raise RuntimeError("Motor not enabled")
        
        if kd is None:
            kd = self.config.defaultKd
        
        try:
            logging.info(f"Velocity control: {targetVel:.3f} rad/s")
            
            # Low kp for velocity control
            self._manager.set_impedance_gains_real_unit(K=0.0, B=kd)
            
            if duration <= 0:
                # Single command
                self._manager.position = self._lastPosition
                self._manager.velocity = targetVel
                self._manager.torque = 0.0
                self.update()
            else:
                # Maintain for duration
                t0 = time.time()
                while time.time() - t0 < duration:
                    self._manager.position = self._lastPosition
                    self._manager.velocity = targetVel
                    self._manager.torque = 0.0
                    self.update()
                    time.sleep(CONTROL_LOOP_PERIOD)
                
                # Stop
                self._manager.position = self._lastPosition
                self._manager.velocity = 0.0
                self._manager.torque = 0.0
                self.update()
                logging.info("✓ Velocity control complete")
        except Exception as e:
            logging.error(f"Velocity control failed: {e}")
            raise
    
    # ==================== Control Mode 3: Torque Control ====================
    
    def set_torque(self,
                  targetTorque: float,
                  duration: float = 0.0) -> None:
        """
        Torque control
        
        Args:
            targetTorque: Target torque (Nm)
            duration: How long to apply (0=single command)
        """
        if not self._isEnabled or self._manager is None:
            raise RuntimeError("Motor not enabled")
        
        # # Clamp torque
        # targetTorque = np.clip(targetTorque,
        #                       -self.config.defaultTorqueLimit,
        #                       self.config.defaultTorqueLimit)
        
        try:
            logging.info(f"Torque control: {targetTorque:.3f} Nm")
            
            # Zero impedance for pure torque
            self._manager.set_impedance_gains_real_unit(K=0.0, B=0.0)
            
            if duration <= 0:
                self._manager.position = self._lastPosition
                self._manager.velocity = 0.0
                self._manager.torque = targetTorque
                self.update()
            else:
                t0 = time.time()
                while time.time() - t0 < duration:
                    self._manager.position = self._lastPosition
                    self._manager.velocity = 0.0
                    self._manager.torque = targetTorque
                    self.update()
                    time.sleep(CONTROL_LOOP_PERIOD)
                
                # Stop torque
                self._manager.torque = 0.0
                self.update()
                logging.info("✓ Torque control complete")
        except Exception as e:
            logging.error(f"Torque control failed: {e}")
            raise
    
    # ==================== Control Mode 4: Impedance Control ====================
    
    def send_command(self,
                    targetPos: float,
                    targetVel: float,
                    kp: float,
                    kd: float,
                    feedforwardTorque: float = 0.0) -> None:
        """
        Low-level impedance control
        
        Args:
            targetPos: Target position (rad)
            targetVel: Target velocity (rad/s)
            kp: Position gain
            kd: Velocity gain
            feedforwardTorque: Feedforward torque (Nm)
        """
        if not self._isEnabled or self._manager is None:
            raise RuntimeError("Motor not enabled")
        
        try:
            # Set gains
            self._manager.set_impedance_gains_real_unit(K=kp, B=kd)
            
            # CORRECT API: Property assignment + update()
            self._manager.position = targetPos
            self._manager.velocity = targetVel
            self._manager.torque = feedforwardTorque
            self.update()
        except Exception as e:
            logging.error(f"Send command failed: {e}")
            raise
    
    # ==================== Utility ====================
    
    def zero_position(self) -> None:
        """Zero motor position at current angle"""
        if not self._isEnabled or self._manager is None:
            raise RuntimeError("Motor not enabled")
        
        try:
            logging.info("Zeroing position...")
            self._manager.zero_position()
            time.sleep(ZERO_POSITION_SETTLE_TIME)
            self.update()
            logging.info("✓ Position zeroed")
        except Exception as e:
            logging.error(f"Failed to zero: {e}")
            raise


# ==================== Main ====================

if __name__ == "__main__":
    print("TMotor Control API v3.1 - CORRECT TMotorCANControl Usage")
    print("=" * 70)
    print()
    print("CORRECT API:")
    print("  manager.position = pos")
    print("  manager.velocity = vel")
    print("  manager.torque = tau")
    print("  manager.update()  # Sends command via CAN")
    print()
    print("Example:")
    print("  with Motor('AK80-10', motorId=2) as motor:")
    print("      motor.track_trajectory(1.57, 2.0)")
    print()
