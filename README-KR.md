# TMotorAPI v5.0

MIT CAN 프로토콜을 사용하는 AK 시리즈 T-Motor 제어를 위한 고수준 Python 라이브러리

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-5.0-green.svg)](https://github.com/KR70004526/TMotorAPI)

## 🆕 v5.0의 새로운 기능

### 논블로킹 제어 설계 🚀
**실시간 제어 애플리케이션**을 위한 완전한 재설계

**v4.3 대비 주요 변경사항:**

#### ✅ Duration 파라미터 제거
```python
# v4.3 (블로킹)
motor.set_position(1.57, duration=2.0)  # 2초 동안 블로킹
motor.set_torque(5.0, duration=1.0)     # 1초 동안 블로킹

# v5.0 (논블로킹) ⭐
motor.set_position(1.57)  # 즉시 반환
motor.set_torque(5.0)     # 즉시 반환
# 사용자가 update() 루프로 타이밍 제어
```

#### ✅ 간소화된 제어 흐름
```python
# v5.0: 사용자 제어 루프
while running:
    motor.set_torque(calculate_torque())  # 명령 설정
    motor.update()                         # 송신 & 수신
    time.sleep(0.01)                       # 100 Hz 제어
```

#### ✅ Settling Time 로직 제거
- 자동 settling 검증 없음
- 필요시 사용자가 직접 구현
- 제거된 파라미터: `stepTimeout`, `stepTolerance`, `stepSettlingTime`

#### ✅ zero_position() 버그 수정
```python
# v4.3: 영점 설정 후 의도하지 않은 움직임 발생 가능
motor.zero_position()  # 버그: 모터가 움직일 수 있음

# v5.0: 안전한 영점 설정 (위치 명령 리셋)
motor.zero_position()  # 안전: 모터 제자리 유지
```

#### ✅ 비상 정지 추가
```python
motor.stop()  # 새로운 메서드: 즉시 토크를 0으로 설정
```

---

## 🌟 주요 특징

- **논블로킹 제어**: 모든 명령이 즉시 반환되어 실시간 애플리케이션에 적합
- **4가지 제어 모드**: Position, Velocity, Torque, Impedance 제어
- **Context Manager**: `with` 구문으로 자동 전원 관리
- **타입 힌트**: 완전한 타입 어노테이션으로 IDE 지원
- **상세한 로깅**: 포괄적인 작동 로그
- **자동 CAN 설정**: CAN 인터페이스 자동 초기화 (선택 사항)
- **비상 정지**: `stop()` 메서드로 안전한 모터 정지
- **안전한 영점 설정**: zero_position()이 의도하지 않은 움직임 방지

---

## 📋 목차

- [v5.0의 새로운 기능](#-v50의-새로운-기능)
- [설치](#-설치)
- [빠른 시작](#-빠른-시작)
- [제어 모드](#-제어-모드)
- [논블로킹 설계](#-논블로킹-설계)
- [고급 기능](#-고급-기능)
- [구성](#-구성)
- [API 참조](#-api-참조)
- [예제](#-예제)
- [v4.3에서 마이그레이션](#-v43에서-마이그레이션)
- [문제 해결](#-문제-해결)

---

## 🚀 설치

### 사전 요구사항

```bash
# TMotorCANControl 라이브러리 설치
pip install TMotorCANControl

# CAN 유틸리티 설치 (Linux)
sudo apt-get install can-utils
```

### Sudo 권한 설정 (권장)

비밀번호 없이 CAN 인터페이스를 자동으로 설정하려면:

```bash
sudo visudo
# 다음 줄 추가:
your_username ALL=(ALL) NOPASSWD: /sbin/ip
```

### TMotorAPI 설치

```bash
# 저장소 클론
git clone https://github.com/KR70004526/TMotorAPI.git
cd TMotorAPI

# 프로젝트에 복사
cp src/TMotorAPI.py your_project/

# 또는 pip으로 설치 (편집 가능 모드)
python3 -m pip install -e . --break-system-packages
# 편집 가능 모드: 코드 변경이 즉시 적용됨
```

---

## ⚡ 빠른 시작

### 기본 논블로킹 제어

```python
from TMotorAPI import Motor
import time
import signal

# 깨끗한 종료를 위한 시그널 핸들러
running = True
signal.signal(signal.SIGINT, lambda s,f: globals().update(running=False))

# Context manager로 모터 생성 및 사용
with Motor('AK80-64', motorId=2, autoInit=True) as motor:
    print("모터 활성화!")
    
    # 논블로킹 제어 루프
    while running:
        # 제어 명령 설정
        motor.set_position(1.57)  # 목표 위치
        
        # 명령 전송 및 상태 수신
        motor.update()
        
        # 현재 상태 출력
        print(f"위치: {motor.position:.3f} rad, "
              f"속도: {motor.velocity:.3f} rad/s, "
              f"토크: {motor.torque:.3f} Nm")
        
        # 제어 루프 타이밍 (100 Hz)
        time.sleep(0.01)
    
print("모터 비활성화!")
```

### 전원 관리 이해하기

**중요**: 모터 전원은 2단계로 작동합니다:

#### 1. 객체 생성 (연결, 전원 OFF)
```python
motor = Motor('AK80-64', motorId=2, autoInit=True)
# ✅ TMotorManager 객체 생성됨
# ✅ CAN 연결 확립됨
# ⚠️ 모터 전원은 아직 OFF (모터가 움직이지 않음)
```

#### 2. Enable/With 블록 (전원 ON)
```python
with motor:  # __enter__() → enable() → 전원 ON
    # ✅ 모터가 이제 전원이 켜지고 움직일 준비됨
    motor.set_position(1.57)
    motor.update()  # 실제로 명령 전송
    # with 블록 내내 전원 유지
# __exit__() → disable() → 전원 OFF
```

### 수동 전원 제어

```python
motor = Motor('AK80-64', motorId=2, autoInit=True)

motor.enable()  # 전원 ON
print(f"전원: {motor.is_power_on()}")  # True

while running:
    motor.set_position(1.57)
    motor.update()
    time.sleep(0.01)

motor.disable()  # 전원 OFF
print(f"전원: {motor.is_power_on()}")  # False
```

---

## 🎯 제어 모드

### 개요

| 모드 | 함수 | 사용 사례 |
|------|------|-----------|
| **위치** | `set_position()` | PD 제어를 이용한 위치 추적 |
| **속도** | `set_velocity()` | 속도 제어 |
| **토크** | `set_torque()` | 힘 제어, 중력 보상 |

**v5.0에서 모든 모드가 논블로킹입니다!**

---

### 1. 위치 제어

PD 게인과 선택적 피드포워드 토크를 사용한 위치 추적

```python
motor.set_position(
    targetPos=1.57,      # 목표 위치 (rad)
    kp=10.0,             # 위치 게인 (Nm/rad), 선택 사항
    kd=2.0,              # 속도 게인 (Nm/(rad/s)), 선택 사항
    feedTor=0.0          # 피드포워드 토크 (Nm), 선택 사항
)
```

**파라미터:**
- `targetPos`: 라디안 단위의 목표 위치
- `kp`: 위치 게인 (None이면 `defaultKp` 사용)
- `kd`: 속도 게인 (None이면 `defaultKd` 사용)
- `feedTor`: 중력/부하 보상용 피드포워드 토크

**사용 패턴:**
```python
while running:
    motor.set_position(target_angle, kp=10, kd=2)
    motor.update()
    time.sleep(0.01)  # 100 Hz 제어 루프
```

**사용 시기:**
- 사용자 정의 제어 루프를 이용한 위치 추적
- 센서 데이터 기반 실시간 위치 업데이트
- 외부 궤적 계획기와의 통합

---

### 2. 속도 제어

댐핑 게인을 사용한 직접 속도 명령

```python
motor.set_velocity(
    targetVel=3.0,      # 목표 속도 (rad/s)
    kd=5.0              # 속도 게인 (Nm/(rad/s)), 선택 사항
)
```

**파라미터:**
- `targetVel`: rad/s 단위의 목표 속도
- `kd`: 속도 게인 (None이면 `defaultKd` 사용)

**사용 패턴:**
```python
while running:
    motor.set_velocity(target_speed, kd=5)
    motor.update()
    time.sleep(0.01)
```

**사용 시기:**
- 연속 회전 애플리케이션
- 속도 기반 제어
- 바퀴/관절 속도 제어

---

### 3. 토크 제어

직접 토크/힘 제어

```python
motor.set_torque(
    targetTor=2.5       # 목표 토크 (Nm)
)
```

**파라미터:**
- `targetTor`: Nm 단위의 목표 토크

**사용 패턴:**
```python
while running:
    torque = calculate_torque()  # 사용자의 제어 알고리즘
    motor.set_torque(torque)
    motor.update()
    time.sleep(0.01)
```

**사용 시기:**
- 힘 제어 애플리케이션
- 중력 보상
- 임피던스 제어
- 햅틱 피드백
- 유연한 조작

---

## 🔄 논블로킹 설계

### 핵심 개념

**v5.0은 사용자가 타이밍을 제어하는 논블로킹 설계를 사용합니다:**

```python
# 제어 루프 패턴
while running:
    # 1. 명령 계산/업데이트
    target = calculate_target()
    
    # 2. 명령 설정 (논블로킹, 즉시 반환)
    motor.set_position(target)
    
    # 3. 명령 전송 & 상태 수신 (CAN 통신)
    motor.update()
    
    # 4. 다음 반복을 위해 현재 상태 사용
    current_pos = motor.position
    current_vel = motor.velocity
    
    # 5. 제어 루프 타이밍
    time.sleep(0.01)  # 100 Hz
```

### v4.3과의 주요 차이점

| 측면 | v4.3 (블로킹) | v5.0 (논블로킹) |
|------|--------------|----------------|
| **명령** | 완료될 때까지 블로킹 | 즉시 반환 |
| **Duration** | `duration=2.0` | duration 파라미터 없음 |
| **타이밍** | 라이브러리가 처리 | 사용자가 타이밍 제어 |
| **유연성** | 제한적 | 높은 유연성 |
| **실시간** | 어려움 | 쉬움 |

### 논블로킹 설계의 장점

#### 1. 실시간 제어
```python
# 센서 데이터에 즉시 반응
while running:
    sensor_data = read_sensor()
    
    if sensor_data > threshold:
        motor.set_torque(0)  # 즉각적인 반응
    else:
        motor.set_torque(5.0)
    
    motor.update()
    time.sleep(0.001)  # 1000 Hz 가능
```

#### 2. 다중 모터 조정
```python
# 여러 모터를 동시에 제어
with Motor('AK80-64', motorId=1) as motor1, \
     Motor('AK80-64', motorId=2) as motor2:
    
    while running:
        # 두 모터의 명령 설정
        motor1.set_position(angle1)
        motor2.set_position(angle2)
        
        # 동시에 업데이트
        motor1.update()
        motor2.update()
        
        time.sleep(0.01)
```

#### 3. 사용자 정의 제어 알고리즘
```python
# 자체 settling 로직 구현
def wait_until_settled(motor, target, tolerance=0.05, timeout=5.0):
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        motor.set_position(target)
        motor.update()
        
        if abs(motor.position - target) < tolerance:
            return True
        
        time.sleep(0.01)
    
    return False

# 사용
if wait_until_settled(motor, 1.57):
    print("위치 도달!")
```

#### 4. 외부 시스템과의 통합
```python
# ROS, 게임 루프 등과 통합
def ros_control_loop():
    rate = rospy.Rate(100)  # 100 Hz
    
    while not rospy.is_shutdown():
        # ROS에서 명령 받기
        target = get_ros_command()
        
        # 모터로 전송
        motor.set_position(target)
        motor.update()
        
        # ROS로 상태 퍼블리시
        publish_motor_state(motor.position, motor.velocity)
        
        rate.sleep()
```

---

## 🔬 고급 기능

### 비상 정지

안전을 위해 즉시 토크를 0으로 설정:

```python
# 비상 상황에서
motor.stop()  # 토크를 0으로 설정하고 업데이트

# 다음과 동일:
motor.set_torque(0.0)
motor.update()
```

**사용 사례:**
- 안전 정지 버튼
- 충돌 감지
- 과열 보호
- 오류 상황

### 위치 영점 설정

현재 위치를 영점 기준으로 설정 (v5.0에서 안전함):

```python
motor.zero_position()
# ✅ 현재 위치가 이제 0.0 rad
# ✅ 모터가 움직이지 않음
# ✅ 위치 명령이 0으로 리셋됨
# ✅ 약 1초 소요 (EEPROM 저장)
```

**동작 과정:**
1. 컨트롤러에 영점 위치 명령 전송
2. EEPROM 저장을 위해 1초 대기
3. 위치 명령을 0으로 설정 (움직임 방지)
4. 모터 상태 업데이트

**사용 시기:**
- 초기 캘리브레이션
- 홈 위치 설정
- 기계적 조정 후 엔코더 리셋

### 중력 보상

위치 제어에서 중력 보상:

```python
import numpy as np

# 시스템 파라미터
mass = 2.0      # kg
g = 9.81        # m/s²
length = 0.3    # m

def gravity_torque(angle):
    """중력 보상 토크 계산"""
    return mass * g * length * np.cos(angle)

# 제어 루프에서 사용
while running:
    target_angle = 1.57  # 90도
    
    motor.set_position(
        targetPos=target_angle,
        kp=10.0,
        kd=2.0,
        feedTor=gravity_torque(target_angle)
    )
    motor.update()
    time.sleep(0.01)
```

### 상태 모니터링

실시간으로 모터 상태에 접근:

```python
# 모든 상태 업데이트 및 가져오기
state = motor.update()
print(f"위치: {state['position']:.3f} rad")
print(f"속도: {state['velocity']:.3f} rad/s")
print(f"토크: {state['torque']:.3f} Nm")
print(f"온도: {state['temperature']:.1f} °C")

# 또는 속성으로 접근 (마지막 업데이트된 값 사용)
pos = motor.position        # rad
vel = motor.velocity        # rad/s
tor = motor.torque          # Nm
temp = motor.temperature    # °C

# 모터 상태 확인
is_on = motor.is_power_on()
uptime = motor.get_uptime()  # enable() 이후 경과 시간(초)
connected = motor.check_connection()
```

### 사용자 정의 제어 루프

고급 제어 알고리즘 구현:

```python
# 예제: 간단한 settling 로직
def move_with_settling(motor, target, tolerance=0.05, 
                       stable_count=10):
    """
    목표로 이동하고 위치가 안정될 때까지 대기
    
    Args:
        motor: Motor 인스턴스
        target: 목표 위치 (rad)
        tolerance: 위치 허용 오차 (rad)
        stable_count: 필요한 연속 안정 측정 횟수
    """
    count = 0
    
    while count < stable_count:
        motor.set_position(target)
        motor.update()
        
        if abs(motor.position - target) < tolerance:
            count += 1
        else:
            count = 0  # 위치가 변하면 리셋
        
        time.sleep(0.01)
    
    print(f"위치 안정: {motor.position:.3f} rad")

# 사용
move_with_settling(motor, 1.57, tolerance=0.03, stable_count=20)
```

---

## ⚙️ 구성

### MotorConfig 클래스

모터 파라미터에 대한 완전한 구성:

```python
from TMotorAPI import MotorConfig

config = MotorConfig(
    # ==================== 모터 식별 ====================
    motorType='AK80-64',        # 'AK80-64', 'AK80-9', 'AK70-10'
    motorId=2,                  # CAN ID (0-127)
    
    # ==================== CAN 설정 ====================
    canInterface='can0',        # 'can0', 'can1' 등
    bitrate=1000000,            # CAN 비트레이트 (기본: 1 Mbps)
    autoInit=True,              # CAN 인터페이스 자동 설정
    
    # ==================== 안전 ====================
    maxTemperature=50.0,        # 최대 MOSFET 온도 (°C)
    
    # ==================== 기본 제어 게인 ====================
    defaultKp=10.0,             # 위치 게인 (Nm/rad)
    defaultKd=0.5,              # 속도 게인 (Nm/(rad/s))
)

motor = Motor(config=config)
```

### 파라미터 상세 설명

#### 모터 식별
- **motorType**: 모터 모델 문자열
  - 물리적 모터와 일치해야 함
  - 예: `'AK80-64'`, `'AK80-9'`, `'AK70-10'`
- **motorId**: CAN ID (0-127)
  - 모터 하드웨어에 설정됨
  - CAN 버스에서 고유해야 함

#### CAN 설정
- **canInterface**: Linux CAN 인터페이스 이름
  - `CANInterface.setup_interface()`에서만 사용됨
  - 일반적: `'can0'`, `'can1'`
- **bitrate**: CAN 버스 속도
  - 기본: 1000000 (1 Mbps) T-Motor용
  - 버스의 모든 장치와 일치해야 함
- **autoInit**: CAN 인터페이스 자동 설정
  - `True`: 자동으로 설정 실행
  - `False`: 수동 설정 필요

**참고**: `TMotorManager_mit_can`은 설정 후 CAN 인터페이스를 자동으로 감지합니다.

#### 안전
- **maxTemperature**: 온도 경고 임계값 (°C)
  - 초과 시 경고 로그
  - 모터를 자동으로 정지하지 않음
  - 사용자가 모니터링하고 조치해야 함

#### 기본 제어 게인
- **defaultKp**: 기본 위치 게인 (Nm/rad)
  - `set_position()`에서 `kp=None`일 때 사용
  - 높을수록 = 더 강한 위치 제어
  - 일반적: 5.0 - 20.0
- **defaultKd**: 기본 속도 게인 (Nm/(rad/s))
  - `set_position()`과 `set_velocity()`에서 `kd=None`일 때 사용
  - 높을수록 = 더 많은 댐핑
  - 일반적: 0.5 - 5.0

### 모터를 생성하는 세 가지 방법

```python
# 방법 1: 직접 파라미터 (간단)
motor = Motor('AK80-64', motorId=2, autoInit=True)

# 방법 2: Config 객체 (복잡한 설정에 권장)
config = MotorConfig(
    motorType='AK80-64',
    motorId=2,
    maxTemperature=60.0,
    defaultKp=15.0,
    defaultKd=2.0
)
motor = Motor(config=config)

# 방법 3: 둘 다 혼합 (파라미터가 config를 오버라이드)
config = MotorConfig(motorType='AK80-64', motorId=2)
motor = Motor(config=config, maxTemperature=70.0)  # 오버라이드
```

---

## 📚 API 참조

### Motor 클래스

#### 생성자

```python
Motor(
    motorType: Optional[str] = None,
    motorId: Optional[int] = None,
    canInterface: Optional[str] = None,
    bitrate: Optional[int] = None,
    autoInit: Optional[bool] = None,
    maxTemperature: Optional[float] = None,
    config: Optional[MotorConfig] = None,
    **kwargs
)
```

#### 제어 메서드

모든 메서드는 **논블로킹**이며 즉시 반환됩니다.

| 메서드 | 파라미터 | 설명 |
|--------|---------|------|
| `set_position()` | `targetPos, kp=None, kd=None, feedTor=0.0` | 위치 명령 설정 |
| `set_velocity()` | `targetVel, kd=None` | 속도 명령 설정 |
| `set_torque()` | `targetTor` | 토크 명령 설정 |
| `stop()` | - | 비상 정지 (토크 = 0) |
| `zero_position()` | - | 현재 위치를 영점으로 설정 |

#### 상태 메서드

```python
# 명령 전송 및 상태 수신 (CAN 통신)
state = motor.update()
# 반환: {'position': float, 'velocity': float, 
#        'torque': float, 'temperature': float}

# 캐시된 상태 접근 (CAN 통신 없음)
pos = motor.position        # rad
vel = motor.velocity        # rad/s
tor = motor.torque          # Nm
temp = motor.temperature    # °C

# 상태 확인
motor.is_power_on()         # True/False
motor.get_uptime()          # enable() 이후 초
motor.check_connection()    # CAN 통신 테스트
```

#### 전원 관리

```python
motor.enable()   # 전원 ON (명령 전 필수)
motor.disable()  # 전원 OFF

# Context manager (자동 전원 관리)
with motor:
    # 모터 전원 켜짐
    motor.set_position(1.57)
    motor.update()
# 모터 전원 꺼짐
```

---

### CANInterface 클래스

수동 CAN 인터페이스 설정 (`autoInit=True`로 자동):

```python
from TMotorAPI import CANInterface

# CAN 인터페이스 설정
CANInterface.setup_interface(
    canInterface='can0',
    bitrate=1000000
)

# 또는 config 사용
CANInterface.setup_interface(config=motor_config)
```

---

### TrajectoryGenerator 클래스 (유틸리티)

사용자 정의 구현을 위한 저수준 궤적 계획 유틸리티:

```python
from TMotorAPI import TrajectoryGenerator

# 최소 저크 궤적 (5차)
pos, vel = TrajectoryGenerator.minimum_jerk(
    startPos=0.0,
    endPos=1.57,
    currentTime=0.5,
    totalDuration=2.0
)

# 3차 궤적
pos, vel = TrajectoryGenerator.cubic(
    startPos=0.0,
    endPos=1.57,
    currentTime=0.5,
    totalDuration=2.0
)

# 선형 보간
pos, vel = TrajectoryGenerator.linear(
    startPos=0.0,
    endPos=1.57,
    currentTime=0.5,
    totalDuration=2.0
)
```

**참고**: 이것들은 제어 루프에서 사용자 정의 궤적 추종을 구현하기 위한 유틸리티입니다.

---

## 💡 예제

### 예제 1: 간단한 위치 제어

```python
from TMotorAPI import Motor
import time
import signal

running = True
signal.signal(signal.SIGINT, lambda s,f: globals().update(running=False))

with Motor('AK80-64', motorId=1, autoInit=True) as motor:
    print("90도로 이동 중...")
    
    target = 1.57  # π/2 rad
    
    while running:
        motor.set_position(target, kp=10, kd=2)
        motor.update()
        
        print(f"위치: {motor.position:.3f} rad, "
              f"오차: {abs(motor.position - target):.4f} rad")
        
        time.sleep(0.01)  # 100 Hz
```

### 예제 2: 중력 보상

```python
from TMotorAPI import Motor, MotorConfig
import numpy as np
import time
import signal

# 시스템 파라미터
mass = 2.0      # kg
g = 9.81        # m/s²
length = 0.3    # m (질량 중심 거리)

def gravity_torque(angle):
    """중력 보상 토크 계산"""
    return mass * g * length * np.cos(angle)

# 모터 구성
config = MotorConfig(
    motorType='AK80-64',
    motorId=1,
    defaultKp=15.0,
    defaultKd=2.0
)

running = True
signal.signal(signal.SIGINT, lambda s,f: globals().update(running=False))

with Motor(config=config) as motor:
    # 수평 위치에서 영점 설정
    print("위치 영점 설정 중...")
    motor.zero_position()
    
    # 중력 보상으로 다양한 각도로 이동
    angles = [0.0, 0.5, 1.0, 1.57, 2.0]  # 라디안
    
    for target_angle in angles:
        print(f"\n{np.degrees(target_angle):.1f}°로 이동 중...")
        
        # 2초 동안 이동
        start_time = time.time()
        while time.time() - start_time < 2.0 and running:
            motor.set_position(
                targetPos=target_angle,
                kp=15.0,
                kd=2.0,
                feedTor=gravity_torque(target_angle)
            )
            motor.update()
            
            print(f"  위치: {motor.position:.3f} rad, "
                  f"토크: {motor.torque:.2f} Nm, "
                  f"온도: {motor.temperature:.1f}°C")
            
            time.sleep(0.01)
        
        if not running:
            break
    
    print("\n완료!")
```

### 예제 3: 속도 스윕

```python
from TMotorAPI import Motor
import time
import signal

running = True
signal.signal(signal.SIGINT, lambda s,f: globals().update(running=False))

with Motor('AK80-9', motorId=2, autoInit=True) as motor:
    velocities = [1.0, 2.0, 3.0, 2.0, 1.0, 0.0]  # rad/s
    
    for target_vel in velocities:
        print(f"\n속도 설정: {target_vel} rad/s")
        
        # 2초 동안 속도 유지
        start_time = time.time()
        while time.time() - start_time < 2.0 and running:
            motor.set_velocity(target_vel, kd=5.0)
            motor.update()
            
            print(f"  속도: {motor.velocity:.3f} rad/s, "
                  f"위치: {motor.position:.3f} rad")
            
            time.sleep(0.01)
        
        if not running:
            break
    
    # 정지
    motor.set_velocity(0.0)
    motor.update()
```

### 예제 4: 안전 모니터링이 있는 토크 제어

```python
from TMotorAPI import Motor, MotorConfig
import time
import signal

# 낮은 온도 임계값으로 구성
config = MotorConfig(
    motorType='AK70-10',
    motorId=1,
    maxTemperature=45.0
)

running = True
signal.signal(signal.SIGINT, lambda s,f: globals().update(running=False))

with Motor(config=config) as motor:
    target_torque = 2.0  # Nm
    duration = 5.0       # 초
    
    print(f"{duration}초 동안 {target_torque} Nm 적용 중...")
    
    start_time = time.time()
    
    while time.time() - start_time < duration and running:
        # 토크 적용
        motor.set_torque(target_torque)
        motor.update()
        
        # 상태 모니터링
        print(f"위치: {motor.position:.3f} rad, "
              f"속도: {motor.velocity:.3f} rad/s, "
              f"토크: {motor.torque:.3f} Nm, "
              f"온도: {motor.temperature:.1f}°C")
        
        # 안전 확인
        if motor.temperature > config.maxTemperature:
            print("⚠ 온도가 너무 높습니다! 정지 중...")
            motor.stop()
            break
        
        time.sleep(0.1)
    
    # 토크 정지
    motor.stop()
    print("토크 정지됨")
```

### 예제 5: 사용자 정의 Settling 로직

```python
from TMotorAPI import Motor
import time
import signal

def move_and_settle(motor, target, tolerance=0.05, stable_cycles=10):
    """
    목표로 이동하고 위치가 안정될 때까지 대기
    
    Args:
        motor: Motor 인스턴스
        target: 목표 위치 (rad)
        tolerance: 위치 허용 오차 (rad)
        stable_cycles: 필요한 연속 안정 측정 횟수
    
    Returns:
        안정되면 True, 중단되면 False
    """
    count = 0
    running = True
    
    def stop_handler(s, f):
        nonlocal running
        running = False
    
    signal.signal(signal.SIGINT, stop_handler)
    
    print(f"{target:.3f} rad로 이동 중...")
    
    while count < stable_cycles and running:
        motor.set_position(target, kp=10, kd=2)
        motor.update()
        
        error = abs(motor.position - target)
        
        if error < tolerance:
            count += 1
            print(f"  안정화: {count}/{stable_cycles} "
                  f"(오차: {error:.4f} rad)")
        else:
            if count > 0:
                print(f"  표류 감지! 카운터 리셋 "
                      f"({count}→0)")
            count = 0
        
        time.sleep(0.01)
    
    if running:
        print(f"✓ 위치 안정: {motor.position:.3f} rad")
        return True
    else:
        print("✗ 중단됨")
        return False

# 사용
with Motor('AK80-64', motorId=1, autoInit=True) as motor:
    if move_and_settle(motor, 1.57, tolerance=0.03, stable_cycles=20):
        print("다음 작업 준비 완료")
```

### 예제 6: 다중 모터 동기화

```python
from TMotorAPI import Motor
import time
import signal
import numpy as np

running = True
signal.signal(signal.SIGINT, lambda s,f: globals().update(running=False))

# 두 개의 모터 생성
with Motor('AK80-64', motorId=1, canInterface='can0') as motor1, \
     Motor('AK80-64', motorId=2, canInterface='can0') as motor2:
    
    print("두 모터 동기화 중...")
    
    # 동기화된 사인파 동작
    t = 0.0
    dt = 0.01  # 100 Hz
    
    while running:
        # 동기화된 위치 계산
        angle1 = np.sin(2 * np.pi * 0.5 * t)  # 0.5 Hz 사인
        angle2 = np.cos(2 * np.pi * 0.5 * t)  # 0.5 Hz 코사인
        
        # 두 모터에 명령 설정
        motor1.set_position(angle1, kp=10, kd=2)
        motor2.set_position(angle2, kp=10, kd=2)
        
        # 두 모터 업데이트
        motor1.update()
        motor2.update()
        
        print(f"모터1: {motor1.position:.3f} rad, "
              f"모터2: {motor2.position:.3f} rad")
        
        time.sleep(dt)
        t += dt
    
    print("정지됨")
```

### 예제 7: 사용자 정의 궤적 구현

```python
from TMotorAPI import Motor, TrajectoryGenerator
import time
import signal

running = True
signal.signal(signal.SIGINT, lambda s,f: globals().update(running=False))

with Motor('AK80-64', motorId=1, autoInit=True) as motor:
    # 궤적 파라미터
    start_pos = 0.0
    end_pos = 1.57
    duration = 2.0
    
    print(f"궤적 추종: {start_pos} → {end_pos} rad "
          f"{duration}초 동안")
    
    # 궤적 실행
    start_time = time.time()
    
    while running:
        t = time.time() - start_time
        
        if t > duration:
            break
        
        # 궤적 포인트 계산
        target_pos, target_vel = TrajectoryGenerator.minimum_jerk(
            startPos=start_pos,
            endPos=end_pos,
            currentTime=t,
            totalDuration=duration
        )
        
        # 명령 전송
        motor.set_position(target_pos, kp=10, kd=2)
        motor.update()
        
        print(f"t={t:.2f}초: 목표={target_pos:.3f}, "
              f"실제={motor.position:.3f}, "
              f"오차={abs(motor.position - target_pos):.4f}")
        
        time.sleep(0.01)
    
    print(f"✓ 궤적 완료!")
    print(f"최종 위치: {motor.position:.3f} rad")
```

---

## 🔄 v4.3에서 마이그레이션

### 주요 변경사항

| 기능 | v4.3 | v5.0 |
|------|------|------|
| **제어** | 블로킹 | 논블로킹 |
| **Duration** | `duration=2.0` | 제거됨 |
| **Settling** | 자동 | 사용자 구현 |
| **타이밍** | 라이브러리 제어 | 사용자 제어 |
| **update()** | 내부적으로 호출 | 사용자가 명시적으로 호출 |

### 마이그레이션 단계

#### 1. Duration 파라미터 제거

**이전 (v4.3):**
```python
motor.set_position(1.57, duration=2.0)  # 2초 동안 블로킹
motor.set_velocity(3.0, duration=1.0)   # 1초 동안 블로킹
motor.set_torque(5.0, duration=0.5)     # 0.5초 동안 블로킹
```

**이후 (v5.0):**
```python
# 자체 제어 루프 구현
while running:
    motor.set_position(1.57)
    motor.update()
    time.sleep(0.01)  # 타이밍을 직접 제어
```

#### 2. 제어 루프 추가

**이전 (v4.3):**
```python
with motor:
    motor.set_position(1.57, duration=2.0)
    motor.set_position(0.0, duration=2.0)
    # 모터가 자동으로 타이밍 처리
```

**이후 (v5.0):**
```python
with motor:
    # 1.57로 이동
    for _ in range(200):  # 100 Hz에서 2초
        motor.set_position(1.57)
        motor.update()
        time.sleep(0.01)
    
    # 0.0으로 이동
    for _ in range(200):
        motor.set_position(0.0)
        motor.update()
        time.sleep(0.01)
```

#### 3. 사용자 정의 Settling 구현 (필요시)

**이전 (v4.3):**
```python
# 자동 settling
motor.set_position(1.57, duration=0.0)  # 안정될 때까지 대기
```

**이후 (v5.0):**
```python
# 자체 settling 구현
def wait_settled(motor, target, tolerance=0.05, cycles=10):
    count = 0
    while count < cycles:
        motor.set_position(target)
        motor.update()
        
        if abs(motor.position - target) < tolerance:
            count += 1
        else:
            count = 0
        
        time.sleep(0.01)

wait_settled(motor, 1.57)
```

#### 4. Settling Config 제거

**이전 (v4.3):**
```python
config = MotorConfig(
    motorType='AK80-64',
    motorId=1,
    stepTimeout=5.0,        # v5.0에서 제거됨
    stepTolerance=0.05,     # v5.0에서 제거됨
    stepSettlingTime=0.1    # v5.0에서 제거됨
)
```

**이후 (v5.0):**
```python
config = MotorConfig(
    motorType='AK80-64',
    motorId=1,
    # 이 파라미터들만 남음
    maxTemperature=50.0,
    defaultKp=10.0,
    defaultKd=0.5
)
```

### 왜 변경했나?

**v4.3의 문제점:**
- ❌ 블로킹 호출이 유연성을 제한
- ❌ 사용자 정의 제어 구현 어려움
- ❌ 다중 모터 조정 어려움
- ❌ 실시간 센서 반응 불가

**v5.0의 장점:**
- ✅ 타이밍에 대한 완전한 제어
- ✅ 쉬운 사용자 정의 알고리즘
- ✅ 간단한 다중 모터 동기화
- ✅ 실시간 센서 통합
- ✅ 더 깔끔한 코드 구조

---

## 🔧 문제 해결

### CAN 인터페이스를 찾을 수 없음

```bash
# 인터페이스가 존재하는지 확인
ip link show can0

# Raspberry Pi에서 찾을 수 없다면 Device Tree Overlay 추가
sudo nano /boot/firmware/config.txt
# 추가: dtoverlay=mcp2515-can0,oscillator=8000000,interrupt=25

# 재부팅
sudo reboot
```

### 모터가 응답하지 않음

**체크리스트:**
1. ✅ 전원 공급 (모델에 따라 24-48V)
2. ✅ CAN 버스 종단 (양 끝에 각각 120Ω)
3. ✅ 올바른 모터 CAN ID
4. ✅ 모터 활성화 (`enable()` 또는 `with` 구문)
5. ✅ 루프에서 `update()` 호출

**디버그:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)

motor = Motor('AK80-64', motorId=1, autoInit=True)
motor.enable()

# 연결 테스트
if motor.check_connection():
    print("✓ 모터 연결됨")
else:
    print("✗ 모터가 응답하지 않음")
    print("전원, CAN 버스, 모터 ID를 확인하세요")
```

### update() 호출하지 않음

**문제:**
```python
# 잘못됨: 명령 설정했지만 전송 안 함
motor.set_position(1.57)
# 모터가 움직이지 않음!
```

**해결:**
```python
# 올바름: 명령 후 항상 update() 호출
motor.set_position(1.57)
motor.update()  # 이것이 실제로 명령을 전송
```

### 위치가 목표에 도달하지 않음

v5.0에는 자동 settling이 없습니다. 직접 구현하세요:

```python
def wait_for_position(motor, target, tolerance=0.05, timeout=5.0):
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        motor.set_position(target)
        motor.update()
        
        if abs(motor.position - target) < tolerance:
            return True
        
        time.sleep(0.01)
    
    return False

# 사용
if wait_for_position(motor, 1.57):
    print("위치 도달!")
else:
    print("타임아웃!")
```

### 권한 거부됨

```bash
# dialout 그룹에 사용자 추가
sudo usermod -a -G dialout $USER

# CAN용 sudo 권한 설정
sudo visudo
# 추가: your_username ALL=(ALL) NOPASSWD: /sbin/ip

# 로그아웃 후 재로그인
```

### 높은 온도 경고

```python
# 제어 루프에서 온도 모니터링
while running:
    motor.set_torque(5.0)
    motor.update()
    
    if motor.temperature > 55.0:
        print("⚠ 높은 온도! 정지 중...")
        motor.stop()
        break
    
    time.sleep(0.01)
```

### CAN 버스 오류

```bash
# CAN 상태 확인
ip -details -statistics link show can0

# 오류 확인 (RX-ERR과 TX-ERR은 0이어야 함)

# 필요시 CAN 리셋
sudo ip link set can0 down
sudo ip link set can0 up type can bitrate 1000000

# 오류가 계속되면 배선과 종단 확인
```

### zero_position()이 움직임을 유발함

이것은 v4.3의 버그였으며, **v5.0에서 수정되었습니다**!

```python
# v5.0: 안전한 영점 설정
motor.zero_position()
# ✓ 위치 명령이 0으로 리셋됨
# ✓ 모터가 제자리 유지
```

---

## 🏗️ 아키텍처

```
사용자 애플리케이션
       ↓
   TMotorAPI v5.0 (논블로킹 래퍼)
       ↓ 사용
TMotorCANControl (저수준 CAN 드라이버)
       ↓
   SocketCAN (Linux 커널)
       ↓
   CAN 하드웨어 (MCP2515 등)
       ↓
   T-Motor (AK 시리즈)
```

**설계 철학:**
- **TMotorCANControl**: 직접 MIT CAN 프로토콜 (저수준)
- **TMotorAPI v5.0**: 논블로킹, 실시간 제어 (고수준)
- **사용자 애플리케이션**: 타이밍과 로직에 대한 완전한 제어

---

## 📊 성능 특성

### 제어 루프 타이밍

**권장 주파수:**
- **100 Hz (10ms)**: 일반 목적, 좋은 균형
- **200 Hz (5ms)**: 고성능 애플리케이션
- **500 Hz (2ms)**: 연구, 고속 제어
- **1000 Hz (1ms)**: 최대 성능 (빠른 CPU 필요)

**예제:**
```python
# 100 Hz 제어
while running:
    motor.set_position(target)
    motor.update()
    time.sleep(0.01)  # 10ms

# 500 Hz 제어
while running:
    motor.set_torque(torque)
    motor.update()
    time.sleep(0.002)  # 2ms
```

### 일반적인 응답 시간

| 제어 모드 | 응답 시간 |
|----------|-----------|
| 토크 | 10-20 ms |
| 속도 | 50-100 ms |
| 위치 (PD) | 100-300 ms |

*응답 시간은 제어 게인과 시스템 역학에 따라 다릅니다*

---

## 📝 라이센스

MIT License - 자세한 내용은 [LICENSE](LICENSE) 파일 참조

**중요 고지사항:**

이 라이브러리는 Neurobionics Lab의 [TMotorCANControl](https://github.com/neurobionics/TMotorCANControl)을 기반으로 합니다.

### 라이센스 준수

```
TMotorAPI v5.0
Copyright (c) 2024 TMotor Control Team

Based on TMotorCANControl
Copyright (c) 2021 Neurobionics Lab, Carnegie Mellon University

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### Attribution 요구사항

이 소프트웨어를 사용할 때:
1. 위의 저작권 고지 포함
2. TMotorCANControl에 대한 attribution 유지
3. MIT 라이센스 조건 준수

---

## 🙏 감사의 말

이 라이브러리는 Neurobionics Lab의 [TMotorCANControl](https://github.com/neurobionics/TMotorCANControl)을 기반으로 구축되었습니다.

**특별히 감사드립니다:**
- [Neurobionics Lab](https://github.com/neurobionics) - TMotorCANControl 제공
- MIT - 오픈 CAN 프로토콜 사양
- T-Motor - 우수한 모터 하드웨어

---

## 📞 지원

- **Issues**: [GitHub Issues](https://github.com/KR70004526/TMotorAPI/issues)
- **기반 라이브러리**: [TMotorCANControl](https://github.com/neurobionics/TMotorCANControl)
- **문서**: 이 README

---

## 🔄 버전 히스토리

### v5.0 (현재 - 메이저 릴리스)
- 🚀 **논블로킹 제어 설계**
- ✂️ 모든 제어 메서드에서 `duration` 파라미터 제거
- ✂️ 자동 settling time 로직 제거
- ✂️ `stepTimeout`, `stepTolerance`, `stepSettlingTime` 파라미터 제거
- 🐛 `zero_position()`이 의도하지 않은 움직임을 유발하는 버그 수정
- ✨ 비상 정지를 위한 `stop()` 메서드 추가
- 🎯 실시간 애플리케이션을 위한 API 간소화
- 📝 사용자가 이제 `update()` 루프로 타이밍 제어

### v4.3 (이전)
- Step 명령을 위한 Settling time 로직
- 피드포워드 토크 지원
- Duration 파라미터를 사용한 블로킹 제어
- 자동 위치 settling 검증

### v4.2
- 기본 궤적 제어
- Context manager 지원
- 간단한 허용 오차 확인

---

**즐거운 제어 되세요! 🚀**

*실시간 제어를 위한 논블로킹 설계!*
