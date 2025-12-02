# MQTT Data Viewer

MQTT 서버의 데이터를 실시간으로 확인하는 Python 프로그램입니다.

**두 가지 버전 제공:**
- **GUI 버전** (`mqtt_viewer_gui.py`) - 사용하기 쉬운 그래픽 인터페이스
- **CLI 버전** (`mqtt_viewer.py`) - 명령줄 인터페이스

## 기능

### 기본 기능
- MQTT 브로커에 연결하여 실시간 메시지 수신
- 여러 토픽 동시 구독 지원
- 와일드카드 토픽 지원 (`#`, `+`)
- JSON 자동 파싱 및 포맷팅
- 타임스탬프와 함께 메시지 출력
- MQTT 인증 지원 (Username/Password)

### 보안 기능
- **TLS/SSL 암호화 연결 지원**
- 포트 8883 자동 TLS 활성화
- **인증서 기반 인증 지원 (AWS IoT Core 등)**
- CA 인증서, 클라이언트 인증서, 프라이빗 키 지원

### GUI 전용 기능
- 사용하기 쉬운 그래픽 인터페이스
- **연결 프로필 관리** (여러 연결 설정 저장/불러오기)
- 인증서 파일 선택 대화상자
- 실시간 메시지 색상 구분 표시

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

### GUI 버전 (권장)

GUI 버전은 사용하기 쉽고 직관적입니다.

```bash
python mqtt_viewer_gui.py
```

또는 Windows에서:
```bash
pythonw mqtt_viewer_gui.py
```

#### GUI 사용 방법

1. **프로필 관리** (선택사항)
   - 연결 프로필 콤보박스에서 저장된 프로필 선택
   - "새로만들기": 현재 설정으로 새 프로필 생성
   - "저장": 현재 프로필 업데이트
   - "삭제": 선택한 프로필 삭제
   - 프로필은 자동으로 `~/.mqtt_viewer_profiles.json`에 저장됨

2. **기본 연결 설정**
   - Broker: MQTT 브로커 주소 입력
   - Port: 포트 번호 (기본값: 1883, TLS는 8883)
   - Username/Password: 인증 정보 입력 (필요한 경우)

3. **보안 설정**
   - **TLS/SSL 사용**: 보안 연결이 필요한 경우 체크
   - **인증서 검증 건너뛰기**: 개발/테스트 환경에서만 사용
   - **인증서 기반 인증 (AWS IoT 등)**:
     - 체크 시 CA 인증서, 클라이언트 인증서, 프라이빗 키 파일 선택
     - "찾기" 버튼으로 파일 선택 가능
     - TLS가 자동으로 활성화됨

4. **토픽 설정**
   - 구독할 토픽 입력 (여러 개는 쉼표로 구분)
   - 예: `data/0` 또는 `sensor/temp, sensor/humidity`

5. **연결 및 모니터링**
   - "연결" 버튼 클릭
   - 메시지 창에서 실시간으로 데이터 확인
   - "메시지 지우기" 버튼으로 화면 정리 가능

#### AWS IoT Core 연결 예제

1. **AWS IoT Core 콘솔에서 인증서 다운로드**
   - Thing 생성 및 인증서 생성
   - 다음 파일들을 다운로드:
     - ✅ AmazonRootCA1.pem (CA 인증서)
     - ✅ xxxx-certificate.pem.crt (클라이언트 인증서)
     - ✅ xxxx-private.pem.key (프라이빗 키)
     - ❌ xxxx-public.pem.key (사용 안 함!)

2. **GUI에서 설정:**
   - Broker: `xxxxx-ats.iot.region.amazonaws.com` (AWS IoT 엔드포인트)
   - Port: `8883`
   - ✓ 인증서 기반 인증 체크
   - CA 인증서: `AmazonRootCA1.pem`
   - 클라이언트 인증서: `xxxx-certificate.pem.crt` ⚠️ NOT public.pem.key!
   - 프라이빗 키: `xxxx-private.pem.key`
   - 토픽: `test/topic` (정책에서 허용된 토픽)

3. **"연결" 클릭**

**중요:** public.pem.key 파일은 클라이언트 인증서가 아닙니다! certificate.pem.crt 파일을 사용하세요.

---

### CLI 버전 (명령줄)

#### 기본 사용

```bash
python mqtt_viewer.py -t "sensor/#"
```

#### 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `-b`, `--broker` | MQTT 브로커 주소 | localhost |
| `-p`, `--port` | MQTT 브로커 포트 | 1883 |
| `-t`, `--topics` | 구독할 토픽(들) - **필수** | - |
| `-u`, `--username` | MQTT 인증 사용자명 | - |
| `-P`, `--password` | MQTT 인증 비밀번호 | - |
| `--tls` | TLS/SSL 사용 (포트 8883은 자동 활성화) | False |
| `--insecure` | TLS 인증서 검증 건너뛰기 (개발/테스트용) | False |

#### CLI 사용 예제

**로컬 MQTT 브로커에서 특정 토픽 구독:**
```bash
python mqtt_viewer.py -t "sensor/temperature"
```

**원격 브로커 및 포트 지정 (일반 연결):**
```bash
python mqtt_viewer.py -b mqtt.example.com -p 1883 -t "sensor/#"
```

**TLS/SSL 보안 연결 (포트 8883은 자동으로 TLS 활성화):**
```bash
python mqtt_viewer.py -b mqtt.example.com -p 8883 -u myuser -P mypass -t "sensor/#"
```

**TLS 연결 + 인증서 검증 건너뛰기 (개발/테스트용):**
```bash
python mqtt_viewer.py -b mqtt.example.com -p 8883 -u myuser -P mypass --insecure -t "sensor/#"
```

**여러 토픽 구독:**
```bash
python mqtt_viewer.py -t "sensor/temperature" "sensor/humidity" "device/+/status"
```

**모든 토픽 구독:**
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
