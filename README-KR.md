# TMotorAPI v4.3

MIT CAN 프로토콜을 사용하여 AK 시리즈 T-Motor를 제어하는 고수준 Python 라이브러리

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-4.3-green.svg)](https://github.com/KR70004526/TMotorAPI)

## 🆕 v4.3의 새로운 기능

### 스텝 명령을 위한 안정화 시간 로직
- **강건한 위치 제어**: 위치가 N번의 연속 사이클 동안 허용오차 내에 유지되어야 함
- **드리프트 방지**: 피드포워드 토크 사용 시 조기 리턴 방지
- **자동 안정화 감지**: 도착 확인 전 안정성 모니터링
- **향상된 로깅**: 실시간 안정화 진행 상황 업데이트

### 주요 개선사항
```python
# v4.3 이전: 단순 허용오차 체크 (조기 리턴 가능)
motor.set_position(1.57, duration=0.0)  # 허용오차 내 도달 시 즉시 리턴

# v4.3: 안정화 시간 검증 (더욱 강건)
motor.set_position(1.57, duration=0.0, feedTor=2.0)  
# → 위치가 0.1초 동안(설정 가능) 안정적으로 유지되어야 리턴
# → 피드포워드 토크로 인한 드리프트 방지
```

## 🌟 주요 기능

- **4가지 제어 모드**: 위치, 속도, 토크, 고급 임피던스 제어
- **안정화 시간 로직**: 안정성 검증이 포함된 강건한 스텝 명령 동작 (v4.3 신규)
- **피드포워드 토크**: 위치 제어를 위한 중력 보상 지원 (v4.3 신규)
- **컨텍스트 매니저 지원**: Python `with` 구문을 통한 자동 전원 관리
- **타입 힌트**: IDE 지원을 위한 완전한 타입 어노테이션
- **상세한 로깅**: 안정화 진행 상황 추적이 포함된 종합 작동 로그
- **자동 CAN 설정**: 자동 CAN 인터페이스 초기화 (선택 사항)
- **궤적 계획**: Minimum jerk, cubic, linear 궤적 생성기

## 📋 목차

- [v4.3의 새로운 기능](#-v43의-새로운-기능)
- [설치](#-설치)
- [빠른 시작](#-빠른-시작)
- [제어 모드](#-제어-모드)
- [고급 기능](#-고급-기능)
- [설정](#-설정)
- [API 레퍼런스](#-api-레퍼런스)
- [예제](#-예제)
- [문제 해결](#-문제-해결)

## 🚀 설치

### 필수 조건

```bash
# TMotorCANControl 라이브러리 설치
pip install TMotorCANControl

# CAN 유틸리티 설치 (Linux)
sudo apt-get install can-utils
```

### Sudo 권한 설정 (권장)

비밀번호 입력 없이 자동 CAN 인터페이스 설정을 위해:

```bash
sudo visudo
# 다음 라인 추가:
your_username ALL=(ALL) NOPASSWD: /sbin/ip
```

### TMotorAPI 설치

```bash
# 저장소 클론
git clone https://github.com/KR70004526/TMotorAPI.git
cd TMotorAPI

# 프로젝트에 복사
cp src/TMotorAPI.py your_project/

# pip을 사용한 API 설치
python3 -m pip install -e . --break-system-packages # pyproject.toml 파일이 있는 TMotorAPI 폴더에서 실행
# 편집 가능한 버전으로 다운로드 --> 코드를 수정하면 재다운로드 없이 자동으로 업데이트됩니다.
```

## ⚡ 빠른 시작

### 컨텍스트 매니저를 사용한 기본 사용법

```python
from TMotorAPI import Motor

# 컨텍스트 매니저로 모터 생성 및 사용 (권장)
with Motor('AK80-64', motorId=2, autoInit=True) as motor:
    # 이 블록 내에서 모터가 켜짐
    motor.set_position(1.57)  # 안정화 검증과 함께 1.57 rad로 이동
    # 블록을 벗어나면 자동으로 모터가 꺼짐
```

### 전원 관리 이해하기

**중요**: 모터 전원은 2단계로 작동합니다:

#### 1. 객체 생성 (연결됨, 전원 꺼짐)
```python
motor = Motor('AK80-64', motorId=2, autoInit=True)
# TMotorManager 객체 생성
# CAN 연결 설정
# 모터 전원은 아직 꺼져 있음 (모터가 아직 움직이지 않음)
```

#### 2. Enable/With 블록 (전원 켜짐)
```python
with motor as m:  # __enter__() 호출 → enable() → 전원 켜짐
    # 이제 모터가 켜지고 움직일 준비가 됨
    m.set_position(1.57)
    # with 블록 전체에서 전원이 유지됨
# __exit__() 호출 → disable() → 전원 꺼짐
```

### 수동 전원 제어

```python
motor = Motor('AK80-64', motorId=2, autoInit=True)

motor.enable()  # 전원 켜짐 - 이제 모터가 움직일 수 있음
print(f"전원 상태: {motor.is_power_on()}")  # True

motor.set_position(1.57)

motor.disable()  # 전원 꺼짐
print(f"전원 상태: {motor.is_power_on()}")  # False
```

## 🎯 제어 모드

### 개요

| 모드 | 함수 | 사용 사례 |
|------|------|----------|
| **위치** | `set_position()` | 궤적 계획이 포함된 위치 제어 |
| **속도** | `set_velocity()` | 일정 속도 회전 |
| **토크** | `set_torque()` | 힘 제어, 중력 보상 |

### 1. 위치 제어 (v4.3에서 향상)

궤적 계획 및 안정화 검증이 포함된 위치 추적.

#### 스텝 명령 (duration ≤ 0.02초)
```python
# 안정화 검증이 포함된 간단한 스텝 명령
motor.set_position(
    targetPos=1.57,      # 목표 위치 (rad)
    duration=0.0,        # 스텝 명령 (궤적 없음)
    kp=10.0,             # 위치 게인 (Nm/rad)
    kd=2.0,              # 속도 게인 (Nm/(rad/s))
    feedTor=0.0          # 피드포워드 토크 (Nm) - 신규!
)
```

**안정화 동작:**
```
Step: 0.000 → 1.570 rad
  Settling: 0.100s (10 cycles @ 100Hz)
    Settling: 10% (1/10)
    Settling: 20% (2/10)
    ...
    Settling: 100% (10/10)
  ✓ Reached and STABLE in 0.15s
    Final position: 1.570 rad
    Final error: 0.0023 rad
```

#### 궤적 명령 (duration > 0.02초)
```python
# minimum jerk를 사용한 부드러운 궤적
motor.set_position(
    targetPos=1.57,          # 목표 위치 (rad)
    duration=2.0,            # 동작 시간 (초)
    kp=10.0,                 # 위치 게인 (Nm/rad)
    kd=2.0,                  # 속도 게인 (Nm/(rad/s))
    feedTor=0.0,             # 피드포워드 토크 (Nm)
    trajectoryType='minimum_jerk'  # 'minimum_jerk', 'cubic', 'linear'
)
```

**궤적 타입:**
- `'minimum_jerk'`: 부드러운 5차 다항식 (기본값, 인간-로봇 상호작용에 최적)
- `'cubic'`: 3차 다항식 (더 빠름, 덜 부드러움)
- `'linear'`: 선형 보간 (가장 빠름, 가장 덜 부드러움)

#### 피드포워드 토크 (중력 보상)
```python
# 예제: 수평 암의 중력 보상
import numpy as np

# 중력 토크 계산: τ = m * g * L * cos(θ)
mass = 2.0  # kg
g = 9.81    # m/s²
length = 0.3  # m

def gravity_torque(angle):
    return mass * g * length * np.cos(angle)

# 중력 보상과 함께 이동
target_angle = 1.57
motor.set_position(
    targetPos=target_angle,
    duration=0.0,
    feedTor=gravity_torque(target_angle)  # 중력 보상
)
```

**사용 시기:** 
- **스텝 명령**: 안정성 검증이 있는 빠른 위치 결정
- **궤적**: 부드러운 동작, 예측 가능한 속도 프로파일
- **피드포워드**: 중력 보상, 부하 보상

### 2. 속도 제어

직접 속도 명령.

```python
motor.set_velocity(
    targetVel=3.0,      # 목표 속도 (rad/s)
    kd=5.0,             # 속도 게인 (Nm/(rad/s))
    duration=2.0        # 동작 시간 (초), 0은 연속
)
```

**사용 시기**: 연속 회전, 속도 기반 작업

### 3. 토크 제어

직접 토크/힘 제어.

```python
motor.set_torque(
    targetTor=2.5,        # 원하는 토크 (Nm)
    duration=2.0          # 동작 시간 (초), 0은 단일 명령
)
```

**사용 시기**: 힘 제어, 컴플라이언스, 햅틱스

## 🔬 고급 기능

### 안정화 시간 설정

모터가 위치 안정성을 검증하는 엄격도 제어:

```python
from TMotorAPI import MotorConfig

config = MotorConfig(
    motorType='AK80-64',
    motorId=2,
    stepTimeout=5.0,        # 스텝 명령의 최대 시간 (초)
    stepTolerance=0.05,     # 위치 허용오차 (rad, ±2.87°)
    stepSettlingTime=0.1    # 필요한 안정화 시간 (초)
)

motor = Motor(config=config)
```

**안정화 시간 가이드라인:**
- `0.0초`: 안정화 체크 없음 (허용오차 내 도달 시 즉시 리턴)
- `0.05초 - 0.1초`: 약한 검증 (100Hz에서 5-10 사이클)
- `0.2초 - 0.5초`: 강한 검증 (20-50 사이클)
- `> 0.5초`: 매우 엄격한 검증 (드물게 사용, 고정밀 애플리케이션)

### 궤적 계획

부드러운 동작을 위한 내장 궤적 생성기:

```python
# Minimum jerk (5차) - 가장 부드러움, 인간 상호작용에 최적
motor.set_position(1.57, duration=2.0, trajectoryType='minimum_jerk')

# Cubic (3차) - 더 빠름, 덜 부드러움
motor.set_position(1.57, duration=2.0, trajectoryType='cubic')

# Linear - 가장 빠름, 가속도 스무딩 없음
motor.set_position(1.57, duration=2.0, trajectoryType='linear')
```

### 위치 영점 설정

현재 위치를 영점 기준으로 설정:

```python
motor.zero_position()
# 현재 위치가 이제 0.0 rad로 간주됨
```

### 상태 모니터링

```python
# 현재 상태 가져오기 (업데이트 트리거)
state = motor.update()
print(f"위치: {state['position']:.3f} rad")
print(f"속도: {state['velocity']:.3f} rad/s")
print(f"토크: {state['torque']:.3f} Nm")
print(f"온도: {state['temperature']:.1f} °C")

# 캐시된 상태 접근 (통신 없음)
pos = motor.position
vel = motor.velocity
temp = motor.temperature

# 모터 상태 확인
is_on = motor.is_power_on()
uptime = motor.get_uptime()  # enable() 이후 경과 시간 (초)
connected = motor.check_connection()
```

## ⚙️ 설정

### MotorConfig 클래스

모터 파라미터를 위한 완전한 설정 객체:

```python
from TMotorAPI import MotorConfig

config = MotorConfig(
    # 모터 식별
    motorType='AK80-64',        # 'AK80-64', 'AK80-9', 'AK70-10'
    motorId=2,                  # CAN ID (0-127)
    
    # CAN 설정 (CANInterface.setup_interface 전용)
    canInterface='can0',        # 'can0', 'can1', 등
    bitrate=1000000,            # CAN 비트레이트 (기본값: 1Mbps)
    autoInit=True,              # CAN 인터페이스 자동 설정
    
    # 안전
    maxTemperature=50.0,        # 최대 MOSFET 온도 (°C)
    
    # 기본 제어 게인
    defaultKp=10.0,             # 위치 게인 (Nm/rad)
    defaultKd=0.5,              # 속도 게인 (Nm/(rad/s))
    
    # 스텝 명령 파라미터 (v4.3 신규)
    stepTimeout=5.0,            # 스텝 명령의 최대 시간 (초)
    stepTolerance=0.05,         # 위치 허용오차 (rad)
    stepSettlingTime=0.1        # 필요한 안정화 시간 (초)
)

motor = Motor(config=config)
```

### 파라미터 설명

#### 모터 식별
- **motorType**: 모터 모델 문자열 (실제 모터와 일치해야 함)
- **motorId**: 모터에 설정된 CAN ID (0-127)

#### CAN 설정
- **canInterface**: `CANInterface.setup_interface()`에만 사용됨
- **bitrate**: CAN 버스 속도 (T-Motor의 기본값은 1Mbps)
- **autoInit**: `True`이면 자동으로 CAN 인터페이스 설정 실행

**참고**: `TMotorManager_mit_can`은 설정 후 자동으로 CAN 인터페이스를 감지합니다.

#### 안전
- **maxTemperature**: 초과 시 경고 발생 (모터를 멈추지는 않음)

#### 제어 게인
- **defaultKp**: `set_position()`에서 `kp=None`일 때 사용
- **defaultKd**: `set_position()` 및 `set_velocity()`에서 `kd=None`일 때 사용

#### 스텝 명령 튜닝 (v4.3)
- **stepTimeout**: 모터가 목표에 도달할 수 없는 경우 무한 대기 방지
- **stepTolerance**: 허용 가능한 위치 오차 (±0.05 rad ≈ ±2.87°)
- **stepSettlingTime**: 확인 전 위치가 안정적으로 유지되어야 하는 시간

## 📚 API 레퍼런스

### Motor 클래스

#### 생성자

```python
Motor(
    motorType: Optional[str] = None,        # 모터 모델
    motorId: Optional[int] = None,          # CAN ID (0-127)
    canInterface: Optional[str] = None,     # CAN 인터페이스 이름
    bitrate: Optional[int] = None,          # CAN 비트레이트
    autoInit: Optional[bool] = None,        # CAN 자동 초기화
    maxTemperature: Optional[float] = None, # 최대 안전 온도 (°C)
    config: Optional[MotorConfig] = None,   # 또는 config 객체 사용
    **kwargs
)
```

**모터 생성의 세 가지 방법:**

```python
# 방법 1: 직접 파라미터
motor = Motor('AK80-64', motorId=2, autoInit=True)

# 방법 2: Config 객체
config = MotorConfig(motorType='AK80-64', motorId=2)
motor = Motor(config=config)

# 방법 3: 혼합 (파라미터가 config를 재정의)
config = MotorConfig(motorType='AK80-64', motorId=2)
motor = Motor(config=config, maxTemperature=60.0)  # 온도 재정의
```

#### 제어 메소드

| 메소드 | 파라미터 | 설명 |
|--------|----------|------|
| `set_position()` | `targetPos, duration=0.0, kp=None, kd=None, feedTor=0.0, trajectoryType='minimum_jerk'` | 궤적 계획이 포함된 위치 제어 |
| `set_velocity()` | `targetVel, kd=None, duration=0.0` | 속도 제어 |
| `set_torque()` | `targetTor, duration=0.0` | 토크 제어 |
| `zero_position()` | - | 현재 위치를 영점으로 설정 |

#### 상태 메소드

```python
# 현재 상태 가져오기 (CAN 통신 트리거)
state = motor.update()
# 리턴: {'position': float, 'velocity': float, 'torque': float, 'temperature': float}

# 캐시된 상태 접근 (CAN 통신 없음)
pos = motor.position        # rad
vel = motor.velocity        # rad/s
tor = motor.torque          # Nm
temp = motor.temperature    # °C

# 상태 확인
motor.is_power_on()         # True/False 리턴
motor.get_uptime()          # enable() 이후 경과 시간 (초)
motor.check_connection()    # CAN 통신 테스트
```

#### 전원 관리

```python
motor.enable()   # 전원 켜기 (모든 명령 전에 필요)
motor.disable()  # 전원 끄기

# 컨텍스트 매니저 (자동 전원 관리)
with motor:
    # 모터 자동으로 켜짐
    motor.set_position(1.57)
# 모터 자동으로 꺼짐
```

### CANInterface 클래스

수동 CAN 인터페이스 설정 (선택 사항, `autoInit=True`로 자동 수행):

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

### TrajectoryGenerator 클래스

저수준 궤적 계획 유틸리티:

```python
from TMotorAPI import TrajectoryGenerator

# Minimum jerk 궤적
pos, vel = TrajectoryGenerator.minimum_jerk(
    startPos=0.0,
    endPos=1.57,
    currentTime=0.5,
    totalDuration=2.0
)

# Cubic 궤적
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

## 💡 예제

### 예제 1: 간단한 위치 제어

```python
from TMotorAPI import Motor

with Motor('AK80-64', motorId=1, autoInit=True) as motor:
    # 빠른 스텝 명령
    motor.set_position(1.57)  # π/2 rad
    
    # 부드러운 궤적
    motor.set_position(-1.57, duration=2.0)  # 부드럽게 되돌아감
    
    # 영점으로 복귀
    motor.set_position(0.0, duration=1.5)
```

### 예제 2: 중력 보상

```python
from TMotorAPI import Motor, MotorConfig
import numpy as np

# 모터 설정
config = MotorConfig(
    motorType='AK80-64',
    motorId=1,
    stepSettlingTime=0.2,  # 중력 보상을 위한 더 엄격한 안정화
    stepTolerance=0.03     # 더 타이트한 허용오차
)

# 시스템 파라미터
mass = 2.0      # kg
g = 9.81        # m/s²
length = 0.3    # m

def gravity_torque(angle):
    """중력 보상 토크 계산"""
    return mass * g * length * np.cos(angle)

with Motor(config=config) as motor:
    # 수평 위치에서 영점 설정
    motor.zero_position()
    
    # 중력 보상과 함께 다양한 각도로 이동
    angles = [0.0, 0.5, 1.0, 1.57, 2.0]
    
    for angle in angles:
        print(f"{np.degrees(angle):.1f}°로 이동 중...")
        motor.set_position(
            targetPos=angle,
            duration=0.0,
            feedTor=gravity_torque(angle)
        )
        print(f"  위치가 {motor.position:.3f} rad에서 안정됨")
```

### 예제 3: 속도 스윕

```python
from TMotorAPI import Motor
import time

with Motor('AK80-9', motorId=2, autoInit=True) as motor:
    # 속도 스윕 테스트
    velocities = [1.0, 2.0, 3.0, 2.0, 1.0, 0.0]
    
    for vel in velocities:
        print(f"속도 설정: {vel} rad/s")
        motor.set_velocity(vel, duration=1.0)
        time.sleep(0.5)  # 변경 간 짧은 일시정지
```

### 예제 4: 모니터링이 있는 토크 제어

```python
from TMotorAPI import Motor
import time

config = MotorConfig(
    motorType='AK70-10',
    motorId=1,
    maxTemperature=45.0  # 안전을 위한 낮은 임계값
)

with Motor(config=config) as motor:
    target_torque = 2.0  # Nm
    duration = 5.0       # 초
    
    print(f"{duration}초 동안 {target_torque} Nm 적용 중...")
    
    start_time = time.time()
    motor.set_torque(target_torque, duration=0.0)  # 단일 명령
    
    # 토크 적용 중 모니터링
    while time.time() - start_time < duration:
        state = motor.update()
        print(f"위치: {state['position']:.3f} rad, "
              f"속도: {state['velocity']:.3f} rad/s, "
              f"토크: {state['torque']:.3f} Nm, "
              f"온도: {state['temperature']:.1f} °C")
        time.sleep(0.1)
    
    # 토크 정지
    motor.set_torque(0.0)
```

### 예제 5: 커스텀 안정화 파라미터

```python
from TMotorAPI import Motor, MotorConfig

# 고정밀 애플리케이션
precise_config = MotorConfig(
    motorType='AK80-64',
    motorId=1,
    stepTolerance=0.01,      # ±0.57° 허용오차
    stepSettlingTime=0.5,    # 0.5초 안정성 필요
    stepTimeout=10.0         # 더 긴 안정화 시간 허용
)

# 빠른 애플리케이션 (완화된 안정화)
fast_config = MotorConfig(
    motorType='AK80-64',
    motorId=2,
    stepTolerance=0.1,       # ±5.73° 허용오차
    stepSettlingTime=0.05,   # 50ms 안정성
    stepTimeout=3.0
)

with Motor(config=precise_config) as motor1, \
     Motor(config=fast_config) as motor2:
    
    # Motor 1: 고정밀, 시간이 더 오래 걸림
    motor1.set_position(1.57)
    
    # Motor 2: 빠른 응답, 덜 엄격
    motor2.set_position(1.57)
```

### 예제 6: 궤적 비교

```python
from TMotorAPI import Motor
import time

with Motor('AK80-64', motorId=1, autoInit=True) as motor:
    target = 1.57
    duration = 2.0
    
    # 모든 궤적 타입 테스트
    trajectories = ['minimum_jerk', 'cubic', 'linear']
    
    for traj_type in trajectories:
        print(f"\n{traj_type} 궤적 테스트 중...")
        
        motor.set_position(0.0, duration=1.0)  # 리셋
        time.sleep(0.5)
        
        motor.set_position(
            targetPos=target,
            duration=duration,
            trajectoryType=traj_type
        )
        time.sleep(0.5)
```

## 🔧 문제 해결

### CAN 인터페이스를 찾을 수 없음

```bash
# 인터페이스가 존재하는지 확인
ip link show can0

# Raspberry Pi에서 찾을 수 없는 경우, Device Tree Overlay 추가
sudo nano /boot/firmware/config.txt
# 추가: dtoverlay=mcp2515-can0,oscillator=8000000,interrupt=25

# 재부팅
sudo reboot
```

### 모터가 응답하지 않음

1. **전원 확인**: 모터 전원 공급 확인 (모델에 따라 24-48V)
2. **CAN 버스 확인**: 적절한 종단 저항 확인 (각 끝에 120Ω)
3. **ID 확인**: 모터 CAN ID가 코드와 일치하는지 확인
4. **Enable 확인**: `enable()`이 호출되었거나 `with` 구문을 사용 중인지 확인

```python
# 디버그 모드
import logging
logging.basicConfig(level=logging.DEBUG)

motor = Motor('AK80-64', motorId=1, autoInit=True)
motor.enable()

# 연결 테스트
if motor.check_connection():
    print("✓ 모터 연결됨")
else:
    print("✗ 모터가 응답하지 않음")
```

### 위치가 안정화되지 않음 (v4.3)

스텝 명령이 안정화 없이 타임아웃되는 경우:

```python
# 안정화 시간 또는 허용오차 증가
config = MotorConfig(
    motorType='AK80-64',
    motorId=1,
    stepTolerance=0.1,        # 허용오차 완화
    stepSettlingTime=0.05,    # 필요한 안정성 시간 감소
    stepTimeout=10.0          # 더 많은 시간 허용
)

motor = Motor(config=config)
```

또는 안정화 체크 비활성화:
```python
config.stepSettlingTime = 0.0  # 안정화 검증 없음
```

### 피드포워드 토크로 인한 드리프트

피드포워드 사용 시 위치가 드리프트되는 경우:

```python
# 안정성을 검증하기 위해 안정화 시간 증가
config = MotorConfig(
    motorType='AK80-64',
    motorId=1,
    stepSettlingTime=0.2,  # 더 긴 검증
    stepTolerance=0.03     # 더 타이트한 허용오차
)

# 피드포워드 토크 계산 확인
def gravity_torque(angle):
    # 물리 계산을 재확인하세요!
    return mass * g * length * np.cos(angle)
```

### 권한 거부됨

```bash
# dialout 그룹에 사용자 추가
sudo usermod -a -G dialout $USER

# CAN 명령을 위한 sudo 권한 설정
sudo visudo
# 추가: your_username ALL=(ALL) NOPASSWD: /sbin/ip

# 변경사항 적용을 위해 로그아웃 후 다시 로그인
```

### 고온 경고

```python
# 온도 임계값 낮추기
config = MotorConfig(
    motorType='AK80-64',
    motorId=1,
    maxTemperature=45.0  # 낮은 경고 임계값
)

# 작동 중 온도 모니터링
state = motor.update()
if state['temperature'] > 50:
    print("⚠ 고온!")
    motor.disable()
```

### CAN 버스 오류

```bash
# CAN 버스 상태 확인
ip -details -statistics link show can0

# 오류 확인
# RX-ERR 및 TX-ERR은 0이어야 함

# 필요시 CAN 인터페이스 재설정
sudo ip link set can0 down
sudo ip link set can0 up type can bitrate 1000000

# bus-off 상태 확인
# bus-off인 경우, 배선 및 종단 저항 확인
```

### 안정화 카운터가 계속 리셋됨

```
Settling: 10% (1/10)
Settling: 20% (2/10)
⚠ Drift detected! Resetting settling counter (3→0)
Settling: 10% (1/10)
...
```

**가능한 원인:**
1. **외부 교란**: 진동, 부하 변화
2. **잘못된 피드포워드**: 토크 계산 확인
3. **낮은 제어 게인**: `kp`와 `kd` 증가
4. **너무 엄격한 허용오차**: `stepTolerance` 증가

**해결 방법:**
```python
# 해결 방법 1: 제어 게인 증가
motor.set_position(1.57, kp=20.0, kd=2.0)

# 해결 방법 2: 허용오차 완화
config.stepTolerance = 0.1

# 해결 방법 3: 안정화 요구사항 감소
config.stepSettlingTime = 0.05
```

## 🏗️ 아키텍처

```
사용자 애플리케이션
       ↓
   TMotorAPI v4.3 (고수준 래퍼)
       ↓ 사용
TMotorCANControl (저수준 CAN 드라이버)
       ↓
   SocketCAN
       ↓
   CAN 하드웨어 (MCP2515 등)
       ↓
   T-Motor (AK 시리즈)
```

**설계 철학:**
- **TMotorCANControl**: MIT CAN 프로토콜 직접 구현 (저수준)
- **TMotorAPI**: 안전 기능이 포함된 고수준 추상화 (사용자 친화적)
- **v4.3**: 안정화 검증 및 피드포워드 지원으로 향상된 강건성

## 🎓 안정화 시간 로직 이해하기

### 왜 안정화 시간이 필요한가?

**안정화 시간 없는 문제:**
```python
# 단순 허용오차 체크
while abs(position - target) > tolerance:
    send_command(target)
    
# 허용오차 내에 들어오자마자 리턴
# 하지만 위치가 여전히 움직이고 있을 수 있음!
# 피드포워드 토크로 인해 목표에 "도달" 후 위치가 드리프트될 수 있음
```

**안정화 시간을 사용한 해결책 (v4.3):**
```python
# N번의 연속 사이클 동안 허용오차를 유지해야 함
settling_counter = 0
while settling_counter < required_cycles:
    if abs(position - target) < tolerance:
        settling_counter += 1
    else:
        settling_counter = 0  # 드리프트 감지 시 리셋
    send_command(target)
    
# 위치가 진정으로 안정적임!
```

### 안정화 시간 계산

```
settling_time = 0.1초 (기본값)
control_frequency = 100 Hz
required_cycles = settling_time * control_frequency = 10 사이클

위치가 10번의 연속 사이클 동안 허용오차 내에 유지되어야 함.
```

### 튜닝 가이드라인

| 애플리케이션 | 허용오차 | 안정화 시간 | 비고 |
|------------|----------|-------------|------|
| 고속 | 0.1 rad | 0.05초 | 빠름, 덜 엄격 |
| 일반 | 0.05 rad | 0.1초 | 균형잡힘 (기본값) |
| 정밀 | 0.03 rad | 0.2초 | 타이트, 잘 검증됨 |
| 초고정밀 | 0.01 rad | 0.5초 | 매우 엄격, 느림 |

## 📊 성능 특성

### 제어 루프 타이밍
- **주파수**: 100 Hz (10ms 주기)
- **스텝 명령 임계값**: 0.02초
- **기본 안정화**: 0.1초 (10 사이클)

### 일반적인 스텝 응답 시간
```
피드포워드 없음:   0.15 - 0.30초
피드포워드 있음:    0.20 - 0.40초 (안정화 검증 포함)
궤적 (2초):        2.0 - 2.1초
```

## 📝 라이선스

MIT License - 자세한 내용은 [LICENSE](LICENSE) 파일 참조

## 🙏 감사의 말

이 라이브러리는 Neurobionics Lab의 [TMotorCANControl](https://github.com/neurobionics/TMotorCANControl)을 기반으로 만들어졌습니다.

**특별한 감사:**
- 기반 CAN 제어 라이브러리를 제공한 [Neurobionics Lab](https://github.com/neurobionics)
- 오픈 CAN 프로토콜 명세를 제공한 MIT
- 훌륭한 모터 하드웨어를 제공한 T-Motor

## 📞 지원

- **이슈**: [GitHub Issues](https://github.com/KR70004526/TMotorAPI/issues)
- **기반 라이브러리**: [TMotorCANControl](https://github.com/neurobionics/TMotorCANControl)
- **문서**: 이 README 및 코드 주석

## 🔄 버전 히스토리

### v4.3 (현재)
- ✨ 스텝 명령을 위한 안정화 시간 로직 추가
- ✨ `set_position()`에 피드포워드 토크 지원 추가
- 🔧 `track_trajectory()` → `set_position()`으로 이름 변경
- 🐛 피드포워드 토크로 인한 드리프트 문제 수정
- 📝 안정화 진행 상황이 포함된 로깅 강화
- 🎯 더욱 강건한 위치 제어

### v4.2 (이전)
- 기본 궤적 제어
- 단순 허용오차 체크
- 컨텍스트 매니저 지원

---

**즐거운 제어되세요! 🚀**

*이제 강건한 안정화 검증 기능이 포함되었습니다!*
