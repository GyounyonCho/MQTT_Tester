#!/usr/bin/env python3
"""
MQTT Data Viewer GUI
MQTT 서버의 데이터를 실시간으로 확인하는 GUI 프로그램
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import paho.mqtt.client as mqtt
import json
from datetime import datetime
import threading
import ssl


class MQTTViewerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MQTT Data Viewer")
        self.root.geometry("900x700")

        self.client = None
        self.connected = False

        self.create_widgets()

    def create_widgets(self):
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 연결 설정 프레임
        connection_frame = ttk.LabelFrame(main_frame, text="연결 설정", padding="10")
        connection_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        # Broker 주소
        ttk.Label(connection_frame, text="Broker:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.broker_var = tk.StringVar(value="localhost")
        ttk.Entry(connection_frame, textvariable=self.broker_var, width=40).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))

        # Port
        ttk.Label(connection_frame, text="Port:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.port_var = tk.StringVar(value="1883")
        ttk.Entry(connection_frame, textvariable=self.port_var, width=10).grid(row=0, column=3, sticky=tk.W)

        # Username
        ttk.Label(connection_frame, text="Username:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.username_var = tk.StringVar()
        ttk.Entry(connection_frame, textvariable=self.username_var, width=25).grid(row=1, column=1, sticky=tk.W, pady=(5, 0))

        # Password
        ttk.Label(connection_frame, text="Password:").grid(row=1, column=2, sticky=tk.W, padx=(10, 5), pady=(5, 0))
        self.password_var = tk.StringVar()
        ttk.Entry(connection_frame, textvariable=self.password_var, width=25, show="*").grid(row=1, column=3, sticky=tk.W, pady=(5, 0))

        # TLS 옵션
        self.tls_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(connection_frame, text="TLS/SSL 사용", variable=self.tls_var,
                       command=self.on_tls_toggle).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))

        self.insecure_var = tk.BooleanVar(value=False)
        self.insecure_check = ttk.Checkbutton(connection_frame, text="인증서 검증 건너뛰기 (개발/테스트용)",
                                             variable=self.insecure_var, state=tk.DISABLED)
        self.insecure_check.grid(row=2, column=2, columnspan=2, sticky=tk.W, pady=(5, 0))

        # 토픽 설정 프레임
        topic_frame = ttk.LabelFrame(main_frame, text="토픽 설정", padding="10")
        topic_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Label(topic_frame, text="구독 토픽 (여러 개는 쉼표로 구분):").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.topics_var = tk.StringVar(value="data/0")
        ttk.Entry(topic_frame, textvariable=self.topics_var, width=60).grid(row=1, column=0, sticky=(tk.W, tk.E))

        # 연결 버튼 프레임
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(0, 10))

        self.connect_btn = ttk.Button(button_frame, text="연결", command=self.connect)
        self.connect_btn.grid(row=0, column=0, padx=5)

        self.disconnect_btn = ttk.Button(button_frame, text="연결 해제", command=self.disconnect, state=tk.DISABLED)
        self.disconnect_btn.grid(row=0, column=1, padx=5)

        self.clear_btn = ttk.Button(button_frame, text="메시지 지우기", command=self.clear_messages)
        self.clear_btn.grid(row=0, column=2, padx=5)

        # 상태 표시
        self.status_var = tk.StringVar(value="연결 대기 중")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, foreground="blue")
        status_label.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))

        # 메시지 표시 영역
        message_frame = ttk.LabelFrame(main_frame, text="수신 메시지", padding="10")
        message_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.message_text = scrolledtext.ScrolledText(message_frame, wrap=tk.WORD, height=25, width=100)
        self.message_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 메시지 텍스트 태그 설정 (색상)
        self.message_text.tag_config("timestamp", foreground="gray")
        self.message_text.tag_config("topic", foreground="blue", font=("TkDefaultFont", 9, "bold"))
        self.message_text.tag_config("payload", foreground="black")
        self.message_text.tag_config("separator", foreground="lightgray")

        # 그리드 가중치 설정 (리사이징)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        message_frame.columnconfigure(0, weight=1)
        message_frame.rowconfigure(0, weight=1)
        connection_frame.columnconfigure(1, weight=1)
        topic_frame.columnconfigure(0, weight=1)

    def on_tls_toggle(self):
        """TLS 체크박스 토글 시 호출"""
        if self.tls_var.get():
            self.insecure_check.config(state=tk.NORMAL)
        else:
            self.insecure_check.config(state=tk.DISABLED)
            self.insecure_var.set(False)

    def on_connect(self, client, userdata, flags, rc):
        """MQTT 연결 성공 시 호출"""
        if rc == 0:
            self.root.after(0, lambda: self.status_var.set("✓ 연결됨"))
            topics = [t.strip() for t in self.topics_var.get().split(',') if t.strip()]

            for topic in topics:
                client.subscribe(topic)
                self.append_message(f"✓ '{topic}' 토픽 구독 시작\n", "topic")

            self.append_message("-" * 80 + "\n", "separator")
        else:
            error_msg = f"✗ 연결 실패. 에러 코드: {rc}"
            self.root.after(0, lambda: self.status_var.set(error_msg))
            self.root.after(0, lambda: messagebox.showerror("연결 실패", error_msg))
            self.disconnect()

    def on_message(self, client, userdata, msg):
        """MQTT 메시지 수신 시 호출"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        topic = msg.topic

        try:
            payload = msg.payload.decode('utf-8', errors='replace')
        except:
            payload = str(msg.payload)

        # JSON 파싱 시도
        try:
            json_data = json.loads(payload)
            payload_display = json.dumps(json_data, indent=2, ensure_ascii=False)
            is_json = True
        except json.JSONDecodeError:
            payload_display = payload
            is_json = False

        # UI 스레드에서 메시지 추가
        self.root.after(0, lambda: self._display_message(timestamp, topic, payload_display, is_json))

    def _display_message(self, timestamp, topic, payload, is_json):
        """메시지를 UI에 표시"""
        self.message_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
        self.message_text.insert(tk.END, f"Topic: {topic}\n", "topic")

        if is_json:
            self.message_text.insert(tk.END, "Payload (JSON):\n", "payload")
            for line in payload.split('\n'):
                self.message_text.insert(tk.END, f"  {line}\n", "payload")
        else:
            self.message_text.insert(tk.END, f"Payload: {payload}\n", "payload")

        self.message_text.insert(tk.END, "-" * 80 + "\n", "separator")
        self.message_text.see(tk.END)  # 자동 스크롤

    def on_disconnect(self, client, userdata, rc):
        """MQTT 연결 해제 시 호출"""
        if rc != 0:
            msg = f"✗ 예기치 않은 연결 해제. 에러 코드: {rc}"
            self.root.after(0, lambda: self.status_var.set(msg))
            self.root.after(0, lambda: messagebox.showwarning("연결 해제", msg))

    def append_message(self, text, tag=None):
        """메시지 추가 헬퍼 함수"""
        self.message_text.insert(tk.END, text, tag)
        self.message_text.see(tk.END)

    def connect(self):
        """MQTT 브로커에 연결"""
        if self.connected:
            messagebox.showwarning("경고", "이미 연결되어 있습니다.")
            return

        # 입력 검증
        broker = self.broker_var.get().strip()
        if not broker:
            messagebox.showerror("오류", "Broker 주소를 입력하세요.")
            return

        try:
            port = int(self.port_var.get())
        except ValueError:
            messagebox.showerror("오류", "올바른 포트 번호를 입력하세요.")
            return

        topics = [t.strip() for t in self.topics_var.get().split(',') if t.strip()]
        if not topics:
            messagebox.showerror("오류", "최소 하나의 토픽을 입력하세요.")
            return

        username = self.username_var.get().strip() or None
        password = self.password_var.get().strip() or None
        use_tls = self.tls_var.get() or port == 8883
        insecure = self.insecure_var.get()

        # MQTT 클라이언트 생성
        try:
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.on_disconnect = self.on_disconnect

            # 인증 설정
            if username and password:
                self.client.username_pw_set(username, password)

            # TLS 설정
            if use_tls:
                if insecure:
                    self.client.tls_set(cert_reqs=ssl.CERT_NONE)
                    self.client.tls_insecure_set(True)
                    self.append_message("⚠ 경고: TLS 인증서 검증을 건너뜁니다 (개발/테스트용)\n", "topic")
                else:
                    self.client.tls_set()
                self.append_message(f"TLS/SSL 모드 활성화\n", "topic")

            # 연결 시작
            self.status_var.set(f"연결 중: {broker}:{port}...")
            self.append_message(f"MQTT 브로커에 연결 시도 중: {broker}:{port}\n", "topic")

            # 별도 스레드에서 연결
            def connect_thread():
                try:
                    self.client.connect(broker, port, 60)
                    self.client.loop_start()
                    self.connected = True
                    self.root.after(0, self.update_ui_connected)
                except Exception as e:
                    error_msg = f"연결 실패: {str(e)}"
                    self.root.after(0, lambda: self.status_var.set(error_msg))
                    self.root.after(0, lambda: messagebox.showerror("연결 오류", error_msg))

            threading.Thread(target=connect_thread, daemon=True).start()

        except Exception as e:
            messagebox.showerror("오류", f"MQTT 클라이언트 생성 실패: {str(e)}")

    def disconnect(self):
        """MQTT 브로커 연결 해제"""
        if self.client and self.connected:
            try:
                self.client.loop_stop()
                self.client.disconnect()
            except:
                pass

        self.connected = False
        self.status_var.set("연결 해제됨")
        self.append_message("\n연결이 해제되었습니다.\n", "topic")
        self.append_message("=" * 80 + "\n\n", "separator")
        self.update_ui_disconnected()

    def update_ui_connected(self):
        """연결 시 UI 업데이트"""
        self.connect_btn.config(state=tk.DISABLED)
        self.disconnect_btn.config(state=tk.NORMAL)

    def update_ui_disconnected(self):
        """연결 해제 시 UI 업데이트"""
        self.connect_btn.config(state=tk.NORMAL)
        self.disconnect_btn.config(state=tk.DISABLED)

    def clear_messages(self):
        """메시지 영역 지우기"""
        self.message_text.delete(1.0, tk.END)

    def on_closing(self):
        """윈도우 닫기 시 호출"""
        if self.connected:
            self.disconnect()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = MQTTViewerGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == '__main__':
    main()
