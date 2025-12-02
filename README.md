# MQTT Data Viewer

MQTT 서버의 데이터를 실시간으로 확인하는 Python 프로그램입니다.

## 기능

- MQTT 브로커에 연결하여 실시간 메시지 수신
- 여러 토픽 동시 구독 지원
- 와일드카드 토픽 지원 (`#`, `+`)
- JSON 자동 파싱 및 포맷팅
- 타임스탬프와 함께 메시지 출력
- MQTT 인증 지원
- **TLS/SSL 암호화 연결 지원**
- 포트 8883 자동 TLS 활성화

## 설치

### 1. Python 설치
Python 3.7 이상이 필요합니다.

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

또는 직접 설치:
```bash
pip install paho-mqtt
```

## 사용법

### 기본 사용

```bash
python mqtt_viewer.py -t "sensor/#"
```

### 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `-b`, `--broker` | MQTT 브로커 주소 | localhost |
| `-p`, `--port` | MQTT 브로커 포트 | 1883 |
| `-t`, `--topics` | 구독할 토픽(들) - **필수** | - |
| `-u`, `--username` | MQTT 인증 사용자명 | - |
| `-P`, `--password` | MQTT 인증 비밀번호 | - |
| `--tls` | TLS/SSL 사용 (포트 8883은 자동 활성화) | False |
| `--insecure` | TLS 인증서 검증 건너뛰기 (개발/테스트용) | False |

### 사용 예제

#### 1. 로컬 MQTT 브로커에서 특정 토픽 구독
```bash
python mqtt_viewer.py -t "sensor/temperature"
```

#### 2. 원격 브로커 및 포트 지정 (일반 연결)
```bash
python mqtt_viewer.py -b mqtt.example.com -p 1883 -t "sensor/#"
```

#### 3. TLS/SSL 보안 연결 (포트 8883은 자동으로 TLS 활성화)
```bash
python mqtt_viewer.py -b mqtt.example.com -p 8883 -u myuser -P mypass -t "sensor/#"
```

#### 4. TLS 연결 + 인증서 검증 건너뛰기 (개발/테스트용)
```bash
python mqtt_viewer.py -b mqtt.example.com -p 8883 -u myuser -P mypass --insecure -t "sensor/#"
```

#### 5. 여러 토픽 구독
```bash
python mqtt_viewer.py -t "sensor/temperature" "sensor/humidity" "device/+/status"
```

#### 6. 모든 토픽 구독
```bash
python mqtt_viewer.py -t "#"
```

## 토픽 와일드카드

MQTT는 두 가지 와일드카드를 지원합니다:

- `#` (멀티 레벨): 토픽 계층의 여러 레벨 매칭
  - 예: `sensor/#` → `sensor/temperature`, `sensor/humidity/room1` 등 모두 매칭

- `+` (싱글 레벨): 토픽 계층의 한 레벨만 매칭
  - 예: `sensor/+/status` → `sensor/device1/status`, `sensor/device2/status` 매칭

## 출력 형식

프로그램은 수신한 메시지를 다음 형식으로 출력합니다:

```
[2025-12-02 10:30:45.123] Topic: sensor/temperature
Payload (JSON):
  {
    "value": 23.5,
    "unit": "celsius",
    "timestamp": 1733132445
  }
--------------------------------------------------------------------------------
```

JSON이 아닌 경우:
```
[2025-12-02 10:30:45.123] Topic: sensor/status
Payload: online
--------------------------------------------------------------------------------
```

## 종료

프로그램을 종료하려면 `Ctrl+C`를 누르세요.

## 테스트

MQTT 브로커가 없는 경우, 무료 테스트 브로커를 사용할 수 있습니다:

```bash
python mqtt_viewer.py -b test.mosquitto.org -p 1883 -t "test/#"
```

다른 터미널에서 메시지 발행:
```bash
mosquitto_pub -h test.mosquitto.org -t "test/hello" -m "Hello MQTT!"
```

## 라이선스

MIT License
