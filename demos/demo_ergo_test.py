"""
Smooth Transition Torque Control for Bicycle Crank System
- Two transition zones (near π and 0/2π)
- Velocity check removed (practical for normal pedaling)
- Cosine interpolation for smooth transitions
"""

from TMotorAPI import Motor, MotorConfig
import numpy as np
import time
import signal

# ==================== Signal Setup ====================
running = True
signal.signal(signal.SIGINT, lambda s, f: globals().update(running=False))


# ==================== Smooth Transition Function ====================
def smooth_transition(angle, tAssist=15.0, tResist=-5.0, zone=0.349):
    """
    Smooth torque transition with two transition zones
    
    Zone Distribution:
    - 0 ~ π:        Assist torque (default)
    - π ~ 2π:       Resist torque (default)
    - Near π:       Smooth transition from Assist to Resist
    - Near 0/2π:    Smooth transition from Resist to Assist
    
    Args:
        angle:   Current angle (rad, any value, wrapped to 0~2π internally)
        tAssist: Assist torque (Nm, default: 15.0)
        tResist: Resist torque (Nm, default: -5.0)
        zone:    Transition zone width (rad, default: 0.349 ≈ 20°)
    
    Returns:
        target_torque (Nm)
    """
    two_pi = 2 * np.pi
    pi = np.pi
    half_zone = zone / 2.0

    # Wrap angle to [0, 2π)
    angle = angle % two_pi

    # ========== Transition 1: Near π (Assist → Resist) ==========
    # Range: [π - zone/2, π + zone/2]
    if (pi - half_zone) <= angle <= (pi + half_zone):
        ratio = (angle - (pi - half_zone)) / zone  # 0 → 1
        cosine = (1 - np.cos(np.pi * ratio)) / 2
        return tAssist * (1 - cosine) + tResist * cosine

    # ========== Transition 2: Near 0/2π (Resist → Assist) ==========
    # Wrap angle to [-π, π] to handle 0/2π boundary naturally
    wrapped = angle if angle <= pi else angle - two_pi
    # Range: [-zone/2, +zone/2]
    if abs(wrapped) <= half_zone:
        ratio = (wrapped + half_zone) / zone      # 0 → 1
        cosine = (1 - np.cos(np.pi * ratio)) / 2
        return tResist * (1 - cosine) + tAssist * cosine

    # ========== Non-transition Zones: Step function ==========
    if angle < pi:
        return tAssist   # Pure Assist zone
    else:
        return tResist   # Pure Resist zone


# ==================== Main Control Loop ====================
if __name__ == "__main__":
    # Motor Initialization
    cfg = MotorConfig(motorType='AK80-64', motorId=2, maxTemperature=80, defaultKd=2)
    motor = Motor(config=cfg)

    # Control Parameters
    T_ASSIST = 15.0             # Assist torque (Nm)
    T_RESIST = -5.0             # Resist torque (Nm)
    TRANSITION_ZONE = 20.0      # Transition zone width (degrees)
    ZONE_RAD = TRANSITION_ZONE * (np.pi / 180.0)

    try:
        motor.enable()

        input("\nPress Enter when ready...")
        print("Calibration in progress...")
        motor.zero_position()
        time.sleep(1.5)
        print("Calibration complete!")

        print("\n🚀 Control started! (Press Ctrl+C to stop)")
        print("=" * 70)

        while running:
            motor.update()

            # Get current angle (wrapped to [0, 2π))
            ang = motor.position % (2 * np.pi)

            # Calculate smooth transition torque
            tor = smooth_transition(ang, T_ASSIST, T_RESIST, ZONE_RAD)

            # Send torque command
            motor.set_torque(tor)

            # Status output
            print(f"Pos: {motor.position:7.3f} rad, "
                  f"Vel: {motor.velocity:+6.3f} rad/s, "
                  f"CmdTor: {tor:+6.2f} Nm, "
                  f"MeasTor: {motor.torque:+6.2f} Nm")

            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user (Ctrl+C)")

    finally:
        motor.disable()
        print("\n✓ Motor safely disabled")
