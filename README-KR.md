# TMotorAPI

MIT CAN 프로토콜을 사용하여 AK 시리즈 T-Motor를 제어하는 고수준 Python 라이브러리

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🌟 주요 기능

- **간단하고 직관적인 API**: TMotorCANControl 기반의 사용하기 쉬운 고수준 인터페이스
- **4가지 제어 모드**: Trajectory, Velocity, Torque, Impedance 제어
- **Context Manager 지원**: Python `with` 문을 통한 자동 전원 관리
- **다중 모터 제어**: `MotorGroup`으로 여러 모터 동기화
- **타입 힌트**: IDE 지원 향상을 위한 완전한 타입 어노테이션
- **상세 로깅**: 디버깅을 위한 포괄적인 작동 로그
- **전원 모니터링**: 모터 가동 시간 및 연결 상태 추적
- **자동 CAN 설정**: 자동 CAN 인터페이스 초기화 (옵션)

## 📋 목차

- [설치](#-설치)
- [빠른 시작](#-빠른-시작)
- [제어 모드](#-제어-모드)
- [API 레퍼런스](#-api-레퍼런스)
- [예제](#-예제)
- [FAQ](#-faq)
- [문제 해결](#-문제-해결)

## 🚀 설치

### 사전 요구사항

```bash
# TMotorCANControl 라이브러리 설치
pip install TMotorCANControl

# CAN 유틸리티 설치 (Linux)
sudo apt-get install can-utils
```

### Sudo 권한 설정 (권장)

비밀번호 입력 없이 자동 CAN 인터페이스 설정을 허용하려면:

```bash
sudo visudo
# 다음 줄 추가:
your_username ALL=(ALL) NOPASSWD: /sbin/ip
```

### TMotorAPI 설치

```bash
# 저장소 복제
git clone https://github.com/KR70004526/TMotorAPI.git
cd TMotorAPI

# 프로젝트에 복사
cp src/TMotorAPI.py your_project/
```

## ⚡ 빠른 시작

### Context Manager를 사용한 기본 사용법

```python
from TMotorAPI import Motor

# Context manager를 사용한 모터 생성 및 사용 (권장)
with Motor('AK80-64', motor_id=2, auto_init=True) as motor:
    # 이 블록 내에서 모터 전원이 켜집니다
    motor.track_trajectory(1.57)  # 1.57 rad로 이동
    # 블록을 벗어나면 자동으로 전원이 꺼집니다
```

### 전원 관리 이해하기

**중요**: 모터 전원은 2단계로 작동합니다:

#### 1. 객체 생성 (연결, 전원 OFF)
```python
motor = Motor('AK80-64', motor_id=2, auto_init=True)
# TMotorManager 객체 생성됨
# CAN 연결 확립됨
# 모터 전원은 아직 OFF (모터가 움직이지 않음)
```

#### 2. Enable/With 블록 (전원 ON)
```python
with motor as m:  # __enter__() 호출 → enable() → 전원 ON
    # 이제 모터 전원이 켜지고 움직일 준비가 됨
    m.track_trajectory(1.57)
    # with 블록 내내 전원 유지
# __exit__() 호출 → disable() → 전원 OFF
```

### 수동 전원 제어

```python
motor = Motor('AK80-64', motor_id=2, auto_init=True)

motor.enable()  # 전원 ON - 이제 모터가 움직일 수 있음
print(f"전원 상태: {motor.is_power_on()}")  # True

motor.track_trajectory(1.57)

motor.disable()  # 전원 OFF
print(f"전원 상태: {motor.is_power_on()}")  # False
```

## 🎯 제어 모드

### 개요

| 모드 | 함수 | 사용 사례 |
|------|------|----------|
| **Trajectory** | `track_trajectory()` | 위치 제어, 부드러운 동작 |
| **Velocity** | `set_velocity()` | 일정 속도 회전 |
| **Torque** | `set_torque()` | 힘 제어, 중력 보상 |
| **Impedance** | `send_command()` | 유연한 상호작용, 강성 제어 |

### 1. Trajectory Control (궤적 제어)

위치 추적

```python
motor.track_trajectory(
    targetPos=1.57,      # 목표 위치 (rad)
    duration=2.0,        # 동작 시간 (초)
    kp=10.0,            # 위치 게인 (Nm/rad)
    kd=2.0,             # 속도 게인 (Nm/(rad/s))
    trajectoryType='minimum_jerk'  # 궤적 타입
)
```

**사용 시기**: 정밀한 위치 제어 작업, 궤적 추종

### 2. Velocity Control (속도 제어)

직접 속도 명령

```python
motor.set_velocity(
    targetVel=3.0,      # 목표 속도 (rad/s)
    kd=5.0,             # 속도 게인 (Nm/(rad/s))
    duration=2.0        # 동작 시간 (초)
)
```

**사용 시기**: 연속 회전, 속도 기반 작업

### 3. Torque Control (토크 제어)

직접 토크/힘 제어

```python
motor.set_torque(
    targetTor=2.5,        # 목표 토크 (Nm)
    duration=2.0          # 동작 시간 (초)
)
```

**사용 시기**: 힘 제어, 중력 보상, 햅틱

### 4. Impedance Control (임피던스 제어)

가상 스프링-댐퍼 시스템

```python
motor.send_command(
    targetPos=0.0,     # 평형 위치 (rad)
    kp=10.0,           # 강성 (Nm/rad)
    kd=1.0,            # 댐핑 (Nm/(rad/s))
    fftor=2.0          # 피드포워드 토크 (Nm)
)
```

**사용 시기**: 인간-로봇 상호작용, 유연한 조작

## 📚 API 레퍼런스

### Motor 클래스

#### 생성자

```python
Motor(
    motor_type: str,              # 모터 모델 ('AK80-64', 'AK80-9', 'AK70-10')
    motor_id: int = 1,            # CAN ID (0-127)
    can_interface: str = 'can0',  # CAN 인터페이스 이름
    auto_init: bool = True,       # CAN 인터페이스 자동 초기화
    bitrate: int = 1000000,       # CAN 비트레이트 (기본: 1Mbps)
    max_temperature: float = 50.0 # 최대 안전 온도 (°C)
)
```

#### MotorConfig 사용

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

#### 제어 메서드

| 메서드 | 파라미터 | 설명 |
|--------|----------|------|
| `track_trajectory()` | `position, duration, kp=None, kd=None` | 위치 + 속도 추적 |
| `set_velocity()` | `velocity, kd=None, duration` | 일정 속도 제어 |
| `set_torque()` | `torque, duration` | 직접 토크 제어 |
| `send_command()` | `position=0.0, kp=None, kd=None, fftor` | 임피던스 (스프링-댐퍼) 제어 |
| `set_zero_position()` | - | 현재 위치를 영점으로 설정 |

#### 상태 메서드

```python
# 현재 상태 가져오기 (딕셔너리 반환)
state = motor.update()
# 반환값: {'position': float, 'velocity': float, 'torque': float, 'temperature': float}

# 캐시된 상태 접근
pos = motor.position
vel = motor.velocity
temp = motor.temperature

# 상태 확인
motor.is_power_on()                # True/False 반환
motor.get_uptime()                 # enable() 호출 이후 경과 시간
```

#### 전원 관리

```python
motor.enable()   # 전원 켜기
motor.disable()  # 전원 끄기

# Context manager (자동 전원 관리)
with motor:
    # 모터 전원 켜짐
    pass
# 모터 전원 꺼짐
```

## 💡 예제

### 예제 1: 간단한 위치 제어

```python
from TMotorAPI import Motor
import time

with Motor('AK80-64', motor_id=1, auto_init=True) as motor:
    # 90도로 이동
    motor.track_trajectory(targetPos=1.57, duration=2.0)  # π/2 rad
    time.sleep(2)
    
    # -90도로 이동
    motor.track_trajectory(targetPos=-1.57, duration=2.0)
    time.sleep(2)
    
    # 영점으로 복귀
    motor.track_trajectory(targetPos=0.0, duration=2.0)
```

### 예제 2: 모니터링이 포함된 속도 제어

```python
from TMotorAPI import Motor
import time

motor = Motor('AK80-9', motor_id=2, auto_init=True)
motor.enable()

try:
    # 3 rad/s로 5초간 회전
    motor.set_velocity(targetVel=3.0, duration=5.0)
    
    for _ in range(50):  # 10Hz로 5초
        state = motor.update()
        print(f"속도: {state['velocity']:.2f} rad/s, "
              f"온도: {state['temperature']:.1f}°C")
        time.sleep(0.1)
        
finally:
    motor.disable()
```

### 예제 3: 임피던스 제어로 유연한 상호작용

```python
from TMotorAPI import Motor
import time

with Motor('AK70-10', motor_id=1, auto_init=True) as motor:
    # 위치 0에 부드러운 가상 스프링 설정
    print("모터를 손으로 움직여보세요...")
    
    for _ in range(100):
        motor.send_command(
            targetPos=0.0,
            kp=10.0,   # 낮은 강성 = 부드러운 스프링
            kd=0.5,    # 낮은 댐핑 = 적은 저항
            fftor=0.0
        )
        
        state = motor.update()
        print(f"위치: {state['position']:.3f} rad, "
              f"토크: {state['torque']:.3f} Nm")
        time.sleep(0.1)
```

### 예제 4: 온도 모니터링

```python
from TMotorAPI import Motor
import time

motor = Motor('AK80-64', motor_id=1, auto_init=True, max_temperature=45.0)

with motor:
    motor.set_velocity(targetVel=5.0, duration=10.0)  # 고속
    
    while True:
        state = motor.update()
        temp = state['temperature']
        
        print(f"온도: {temp:.1f}°C")
        
        # 자동 안전 점검 (내장)
        if temp > motor._config.maxTemperature:
            print("경고: 온도 한계 초과!")
            break
            
        time.sleep(1.0)
```

### 예제 5: Minimum Jerk 궤적

```python
from TMotorAPI import Motor

with Motor('AK80-64', motor_id=1, auto_init=True) as motor:
    # Minimum Jerk 궤적으로 부드러운 동작
    motor.track_trajectory(
        targetPos=3.14,              # π rad (180도)
        duration=3.0,                # 3초간
        kp=50.0,                     # 높은 위치 게인
        kd=2.0,                      # 적절한 댐핑
        trajectoryType='minimum_jerk'
    )
```

## ❓ FAQ

<details>
<summary><b>Q: 어떤 모터들이 지원되나요?</b></summary>

**A:** 현재 MIT CAN 프로토콜을 사용하는 AK 시리즈 모터를 지원합니다:
- **AK80-64** (높은 토크)
- **AK80-9** (균형잡힌 성능)
- **AK70-10** (컴팩트)
</details>

<details>
<summary><b>Q: 서로 다른 CAN 인터페이스에서 여러 모터를 제어할 수 있나요?</b></summary>

**A:** 네! 각 모터에 다른 `can_interface`를 지정하면 됩니다:

```python
motor1 = Motor('AK80-64', motor_id=1, can_interface='can0')
motor2 = Motor('AK80-9', motor_id=1, can_interface='can1')
```
</details>

<details>
<summary><b>Q: update()를 주기적으로 호출해야 하나요?</b></summary>

**A:** 네, 연속 제어를 위해서는 필요합니다. 제어 메서드는 명령을 보내지만 `update()`는 모터 피드백을 읽습니다:

```python
while running:
    motor.track_trajectory(target_pos, duration=0.1)
    state = motor.update()  # 최신 피드백 받기
    time.sleep(0.01)  # 100 Hz 권장
```
</details>

<details>
<summary><b>Q: 모터 오류를 어떻게 처리하나요?</b></summary>

**A:** API에 오류 처리와 로깅이 포함되어 있습니다:

```python
try:
    with motor:
        motor.set_velocity(10.0, duration=2.0)
        state = motor.update()
        
        if not state:  # 빈 딕셔너리는 오류를 의미
            print("통신 오류!")
            
except Exception as e:
    print(f"오류: {e}")
finally:
    motor.disable()  # 항상 안전하게 호출 가능
```
</details>

<details>
<summary><b>Q: track_trajectory()와 send_command()의 차이는 무엇인가요?</b></summary>

**A:**
- **`track_trajectory()`**: 능동적 위치 추적 (강성, 정밀)
- **`send_command()`**: 수동적 유연성 (부드러움, 상호작용)

정밀한 위치 제어에는 trajectory를, 안전한 상호작용에는 send_command를 사용하세요.
</details>

## 🔧 문제 해결

### CAN 인터페이스를 찾을 수 없음

```bash
# 인터페이스가 존재하는지 확인
ip link show can0

# 없다면 Device Tree Overlay 추가 (Raspberry Pi)
sudo nano /boot/firmware/config.txt
# 추가: dtoverlay=mcp2515-can0,oscillator=8000000,interrupt=25

# 재부팅
sudo reboot
```

### 모터가 응답하지 않음

1. **전원 확인**: 모터 전원 공급 확인 (모델에 따라 24-48V)
2. **CAN 버스 확인**: 적절한 종단 저항 확인 (양 끝에 120Ω)
3. **ID 확인**: 모터 CAN ID가 코드와 일치하는지 확인
4. **Enable 확인**: `enable()`이 호출되었거나 `with` 문을 사용하는지 확인

```python
# 디버그 모드
import logging
logging.basicConfig(level=logging.DEBUG)
motor = Motor('AK80-64', motor_id=1)
```

### 권한 거부됨

```bash
# 사용자를 dialout 그룹에 추가
sudo usermod -a -G dialout $USER

# 변경사항 적용을 위해 로그아웃 후 로그인
```

### 고온 경고

- 부하 또는 듀티 사이클 감소
- 냉각 개선 (히트싱크/팬 추가)
- 조기 경고를 위해 `max_temperature` 임계값 낮추기

### CAN 버스 오류

```bash
# CAN 버스 상태 확인
ip -details -statistics link show can0

# CAN 인터페이스 재설정
sudo ip link set can0 down
sudo ip link set can0 up type can bitrate 1000000
```

## 🏗️ 아키텍처

```
사용자 애플리케이션
       ↓
   TMotorAPI (고수준 래퍼)
       ↓ 사용
TMotorCANControl (저수준 CAN 드라이버)
       ↓
   SocketCAN
       ↓
   CAN 하드웨어
       ↓
   T-Motor
```

**설계 철학:**
- **TMotorCANControl**: 직접 CAN 프로토콜 구현 (저수준)
- **TMotorAPI**: 안전 기능이 포함된 고수준 추상화 (사용자 친화적)

## 📝 라이선스

MIT License - 자세한 내용은 [LICENSE](LICENSE) 파일 참조

## 🙏 감사의 말

이 라이브러리는 Neurobionics Lab의 [TMotorCANControl](https://github.com/neurobionics/TMotorCANControl)을 기반으로 합니다.

**특별히 감사드립니다:**
- 기본 CAN 제어 라이브러리를 제공한 [Neurobionics Lab](https://github.com/neurobionics)
- 오픈 CAN 프로토콜 명세를 제공한 MIT
- 우수한 모터 하드웨어를 제공한 T-Motor

## 📞 지원

- **이슈**: [GitHub Issues](https://github.com/KR70004526/TMotorAPI/issues)
- **기본 라이브러리**: [TMotorCANControl](https://github.com/neurobionics/TMotorCANControl)

---

**즐거운 제어 되세요! 🚀**
