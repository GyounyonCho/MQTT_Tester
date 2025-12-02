#!/usr/bin/env python3
"""
MQTT Data Viewer
MQTT 서버의 데이터를 실시간으로 확인하는 프로그램
"""

import paho.mqtt.client as mqtt
import json
import argparse
from datetime import datetime
import sys
import ssl


class MQTTViewer:
    def __init__(self, broker, port, topics, username=None, password=None, use_tls=False, insecure=False):
        """
        MQTT Viewer 초기화

        Args:
            broker: MQTT 브로커 주소
            port: MQTT 브로커 포트
            topics: 구독할 토픽 리스트
            username: 인증 사용자명 (선택)
            password: 인증 비밀번호 (선택)
            use_tls: TLS/SSL 사용 여부 (선택)
            insecure: TLS 인증서 검증 건너뛰기 (선택)
        """
        self.broker = broker
        self.port = port
        self.topics = topics
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.insecure = insecure

        # Callback API Version 2 사용 (최신 버전)
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

        # 콜백 함수 설정
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

        # 인증 설정
        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)

        # TLS 설정
        if self.use_tls:
            if self.insecure:
                # 인증서 검증 건너뛰기 (개발/테스트 환경용)
                self.client.tls_set(cert_reqs=ssl.CERT_NONE)
                self.client.tls_insecure_set(True)
            else:
                # 기본 TLS 설정 (인증서 검증)
                self.client.tls_set()

    def on_connect(self, client, userdata, flags, rc):
        """연결 성공 시 호출되는 콜백"""
        if rc == 0:
            print(f"✓ MQTT 브로커에 연결되었습니다: {self.broker}:{self.port}")
            print(f"✓ 구독 토픽: {', '.join(self.topics)}")
            print("-" * 80)

            # 토픽 구독
            for topic in self.topics:
                client.subscribe(topic)
                print(f"✓ '{topic}' 토픽 구독 시작")

            print("-" * 80)
            print("메시지 수신 대기 중... (Ctrl+C로 종료)\n")
        else:
            print(f"✗ 연결 실패. 에러 코드: {rc}")
            sys.exit(1)

    def on_message(self, client, userdata, msg):
        """메시지 수신 시 호출되는 콜백"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        topic = msg.topic
        payload = msg.payload.decode('utf-8', errors='replace')

        # JSON 형식 파싱 시도
        try:
            json_data = json.loads(payload)
            payload_display = json.dumps(json_data, indent=2, ensure_ascii=False)
            is_json = True
        except json.JSONDecodeError:
            payload_display = payload
            is_json = False

        # 메시지 출력
        print(f"[{timestamp}] Topic: {topic}")
        if is_json:
            print(f"Payload (JSON):")
            for line in payload_display.split('\n'):
                print(f"  {line}")
        else:
            print(f"Payload: {payload_display}")
        print("-" * 80)

    def on_disconnect(self, client, userdata, rc):
        """연결 해제 시 호출되는 콜백"""
        if rc != 0:
            print(f"\n✗ 예기치 않은 연결 해제. 에러 코드: {rc}")

    def start(self):
        """MQTT 클라이언트 시작"""
        try:
            print(f"MQTT 브로커에 연결 시도 중: {self.broker}:{self.port}")
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_forever()
        except KeyboardInterrupt:
            print("\n\n프로그램을 종료합니다...")
            self.client.disconnect()
            sys.exit(0)
        except Exception as e:
            print(f"\n✗ 에러 발생: {str(e)}")
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='MQTT 서버의 데이터를 실시간으로 확인하는 프로그램',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
  # 기본 사용 (localhost)
  python mqtt_viewer.py -t "sensor/#"

  # 특정 브로커 및 포트 지정
  python mqtt_viewer.py -b mqtt.example.com -p 1883 -t "sensor/temperature" "sensor/humidity"

  # TLS/SSL 연결 (포트 8883은 자동으로 TLS 활성화)
  python mqtt_viewer.py -b mqtt.example.com -p 8883 -u myuser -P mypass -t "sensor/#"

  # TLS 연결 + 인증서 검증 건너뛰기 (개발/테스트용)
  python mqtt_viewer.py -b mqtt.example.com -p 8883 -u myuser -P mypass --insecure -t "sensor/#"

  # 여러 토픽 구독
  python mqtt_viewer.py -t "sensor/#" "device/+/status" "logs/error"
        """
    )

    parser.add_argument('-b', '--broker',
                        default='localhost',
                        help='MQTT 브로커 주소 (기본값: localhost)')

    parser.add_argument('-p', '--port',
                        type=int,
                        default=1883,
                        help='MQTT 브로커 포트 (기본값: 1883)')

    parser.add_argument('-t', '--topics',
                        nargs='+',
                        required=True,
                        help='구독할 토픽(들). 와일드카드 사용 가능 (#, +)')

    parser.add_argument('-u', '--username',
                        help='MQTT 인증 사용자명')

    parser.add_argument('-P', '--password',
                        help='MQTT 인증 비밀번호')

    parser.add_argument('--tls',
                        action='store_true',
                        help='TLS/SSL 사용 (포트 8883은 자동으로 TLS 활성화)')

    parser.add_argument('--insecure',
                        action='store_true',
                        help='TLS 인증서 검증 건너뛰기 (개발/테스트용)')

    args = parser.parse_args()

    # 포트 8883은 자동으로 TLS 활성화
    use_tls = args.tls or args.port == 8883

    if use_tls:
        print(f"TLS/SSL 모드: {'활성화' if use_tls else '비활성화'}")
        if args.insecure:
            print("⚠ 경고: 인증서 검증을 건너뜁니다 (개발/테스트용)")

    # MQTT Viewer 시작
    viewer = MQTTViewer(
        broker=args.broker,
        port=args.port,
        topics=args.topics,
        username=args.username,
        password=args.password,
        use_tls=use_tls,
        insecure=args.insecure
    )

    viewer.start()


if __name__ == '__main__':
    main()
