# TMotorAPI

A high-level Python library for controlling AK-series T-Motors using the MIT CAN protocol.

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🌟 Features

- **Simple & Intuitive API**: Easy-to-use high-level interface built on TMotorCANControl
- **4 Control Modes**: Trajectory, Velocity, Torque, and Impedance control
- **Context Manager Support**: Automatic power management with Python's `with` statement
- **Multi-Motor Control**: Synchronize multiple motors with `MotorGroup`
- **Type Hints**: Full type annotations for better IDE support
- **Detailed Logging**: Comprehensive operation logs for debugging
- **Power Monitoring**: Track motor uptime and connection status
- **Auto CAN Setup**: Automatic CAN interface initialization (optional)

## 📋 Table of Contents

- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Control Modes](#-control-modes)
- [API Reference](#-api-reference)
- [Examples](#-examples)
- [FAQ](#-faq)
- [Troubleshooting](#-troubleshooting)

## 🚀 Installation

### Prerequisites

```bash
# Install TMotorCANControl library
pip install TMotorCANControl

# Install CAN utilities (Linux)
sudo apt-get install can-utils
```

### Setup Sudo Permissions (Recommended)

To allow automatic CAN interface setup without password prompts:

```bash
sudo visudo
# Add this line:
your_username ALL=(ALL) NOPASSWD: /sbin/ip
```

### Install TMotorAPI

```bash
# Clone the repository
git clone https://github.com/KR70004526/TMotorAPI.git
cd TMotorAPI

# Copy to your project
cp src/TMotorAPI.py your_project/
```

## ⚡ Quick Start

### Basic Usage with Context Manager

```python
from TMotorAPI import Motor

# Create and use motor with context manager (recommended)
with Motor('AK80-64', motor_id=2, auto_init=True) as motor:
    # Motor is powered on inside this block
    motor.track_trajectory(1.57)  # Move to 1.57 rad
    # Motor is automatically powered off when exiting
```

### Understanding Power Management

**Important**: Motor power operates in 2 stages:

#### 1. Object Creation (Connection, Power OFF)
```python
motor = Motor('AK80-64', motor_id=2, auto_init=True)
# TMotorManager object created
# CAN connection established
# Motor power is still OFF (motor won't move yet)
```

#### 2. Enable/With Block (Power ON)
```python
with motor as m:  # __enter__() called → enable() → Power ON
    # Motor is now powered and ready to move
    m.track_trajectory(1.57)
    # Power remains on throughout the with block
# __exit__() called → disable() → Power OFF
```

### Manual Power Control

```python
motor = Motor('AK80-64', motor_id=2, auto_init=True)

motor.enable()  # Power ON - motor can now move
print(f"Power status: {motor.is_power_on()}")  # True

motor.track_trajectory(1.57)

motor.disable()  # Power OFF
print(f"Power status: {motor.is_power_on()}")  # False
```

## 🎯 Control Modes

### Overview

| Mode | Function | Use Case |
|------|----------|----------|
| **Trajectory** | `track_trajectory()` | Position control, smooth motion |
| **Velocity** | `set_velocity()` | Constant speed rotation |
| **Torque** | `set_torque()` | Force control, gravity compensation |
| **Impedance** | `set_impedance()` | Compliant interaction, stiffness control |

### 1. Trajectory Control

Position tracking

```python
motor.track_trajectory(
    targetPos=1.57,      # Target position (rad)
    duration=2.0,       # Motion duration (s)
    kp=10.0,           # Position gain (Nm/rad)
    kd=2.0             # Velocity gain (Nm/(rad/s))
    trajectoryType='minimum_jerk' # Trajectory Type
)
```

**When to use**: Precise positioning tasks, trajectory following

### 2. Velocity Control

Direct velocity command.

```python
motor.set_velocity(
    targetVel=3.0,      # Target velocity (rad/s)
    kd=5.0,             # Velocity gain (Nm/(rad/s))
    duration=2.0        # Motion duration (s)
)
```

**When to use**: Continuous rotation, speed-based tasks

### 3. Torque Control

Direct torque/force control.

```python
motor.set_torque(
    targetTor=2.5,        # Desired torque (Nm)
    duration=2.0          # Motion duration (s)
)
```

**When to use**: Force control, gravity compensation, haptics

### 4. Impedance Control

Virtual spring-damper system.

```python
motor.send_command(
    targetPos=0.0,     # Equilibrium position (rad)
    kp=10.0,           # Stiffness (Nm/rad)
    kd=1.0,            # Damping (Nm/(rad/s))
    fftor=2.0          # Feedforward torque (Nm)
)
```

**When to use**: Human-robot interaction, compliant manipulation

## 📚 API Reference

### Motor Class

#### Constructor

```python
Motor(
    motor_type: str,              # Motor model ('AK80-64', 'AK80-9', 'AK70-10')
    motor_id: int = 1,            # CAN ID (0-127)
    can_interface: str = 'can0',  # CAN interface name
    auto_init: bool = True,       # Auto initialize CAN interface
    bitrate: int = 1000000,       # CAN bitrate (default: 1Mbps)
    max_temperature: float = 50.0 # Max safe temperature (°C)
)
```

#### Using MotorConfig

```python
from TMotorAPI import MotorConfig

config = MotorConfig(
    motorType='AK80-64',
    motorId=2,
    canInterface='can0',
    bitrate=1000000,
    autoInit=True,
    maxTemperature=50.0
)

motor = Motor(config=config)
```

#### Control Methods

| Method | Parameters | Description |
|--------|-----------|-------------|
| `track_trajectory()` | `position, duration, kp=None, kd=None` | Position + velocity tracking |
| `set_velocity()` | `velocity, kd=None, duration` | Constant velocity control |
| `set_torque()` | `torque, duration` | Direct torque control |
| `wnd_command()` | `position=0.0, kp=None, kd=None, fftor` | Impedance (spring-damper) control |
| `set_zero_position()` | - | Set current position as zero |

#### State Methods

```python
# Get current state (returns dict)
state = motor.update()
# Returns: {'position': float, 'velocity': float, 'torque': float, 'temperature': float}

# Access cached state
pos = motor.position
vel = motor.velocity
temp = motor.temperature

# Check status
motor.is_power_on()                # Returns True/False
motor.get_uptime()                 # Time since enable() was called
```

#### Power Management

```python
motor.enable()   # Power on
motor.disable()  # Power off

# Context manager (automatic power management)
with motor:
    # Motor powered on
    pass
# Motor powered off
```

## 🔧 Troubleshooting

### CAN Interface Not Found

```bash
# Check if interface exists
ip link show can0

# If not, add Device Tree Overlay (Raspberry Pi)
sudo nano /boot/firmware/config.txt
# Add: dtoverlay=mcp2515-can0,oscillator=8000000,interrupt=25

# Reboot
sudo reboot
```

### Motor Not Responding

1. **Check power**: Verify motor power supply (24-48V depending on model)
2. **Check CAN bus**: Ensure proper termination resistors (120Ω at each end)
3. **Check ID**: Verify motor CAN ID matches code
4. **Check enable**: Make sure `enable()` was called or using `with` statement

```python
# Debug mode
import logging
logging.basicConfig(level=logging.DEBUG)
motor = Motor('AK80-64', motor_id=1)
```

### Permission Denied

```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER

# Logout and login for changes to take effect
```

### High Temperature Warning

- Reduce load or duty cycle
- Improve cooling (add heatsink/fan)
- Lower `max_temperature` threshold for earlier warning

### CAN Bus Errors

```bash
# Check CAN bus status
ip -details -statistics link show can0

# Reset CAN interface
sudo ip link set can0 down
sudo ip link set can0 up type can bitrate 1000000
```

## 🏗️ Architecture

```
User Application
       ↓
   TMotorAPI (High-level wrapper)
       ↓ uses
TMotorCANControl (Low-level CAN driver)
       ↓
   SocketCAN
       ↓
   CAN Hardware
       ↓
   T-Motor
```

**Design Philosophy:**
- **TMotorCANControl**: Direct CAN protocol implementation (low-level)
- **TMotorAPI**: High-level abstractions with safety features (user-friendly)

## 📝 License

MIT License - See [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

This library is built on [TMotorCANControl](https://github.com/neurobionics/TMotorCANControl) by the Neurobionics Lab.

**Special thanks to:**
- [Neurobionics Lab](https://github.com/neurobionics) for the underlying CAN control library
- MIT for the open CAN protocol specification
- T-Motor for excellent motor hardware

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/KR70004526/TMotorAPI/issues)
- **Base Library**: [TMotorCANControl](https://github.com/neurobionics/TMotorCANControl)

---

**Happy Controlling! 🚀**
