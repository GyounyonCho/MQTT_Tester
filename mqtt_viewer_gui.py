#!/usr/bin/env python3
"""
MQTT Data Viewer GUI
MQTT 서버의 데이터를 실시간으로 확인하는 GUI 프로그램
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import paho.mqtt.client as mqtt
import json
from datetime import datetime
import threading
import ssl
import os


class MQTTViewerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MQTT Data Viewer")
        self.root.geometry("950x750")

        self.client = None
        self.connected = False
        self.config_file = os.path.join(os.path.expanduser("~"), ".mqtt_viewer_profiles.json")
        self.profiles = {}
        self.current_profile = None

        self.create_widgets()
        self.load_profiles()

    def create_widgets(self):
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 프로필 관리 프레임
        profile_frame = ttk.Frame(main_frame)
        profile_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))

        ttk.Label(profile_frame, text="연결 프로필:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.profile_var = tk.StringVar()
        self.profile_combo = ttk.Combobox(profile_frame, textvariable=self.profile_var, width=30, state="readonly")
        self.profile_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 5))
        self.profile_combo.bind('<<ComboboxSelected>>', self.on_profile_selected)

        ttk.Button(profile_frame, text="저장", command=self.save_profile, width=8).grid(row=0, column=2, padx=2)
        ttk.Button(profile_frame, text="삭제", command=self.delete_profile, width=8).grid(row=0, column=3, padx=2)
        ttk.Button(profile_frame, text="새로만들기", command=self.new_profile, width=10).grid(row=0, column=4, padx=2)

        # 연결 설정 프레임
        connection_frame = ttk.LabelFrame(main_frame, text="연결 설정", padding="10")
        connection_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        # Broker 주소
        ttk.Label(connection_frame, text="Broker:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.broker_var = tk.StringVar(value="localhost")
        ttk.Entry(connection_frame, textvariable=self.broker_var, width=40).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))

        # Port
        ttk.Label(connection_frame, text="Port:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.port_var = tk.StringVar(value="1883")
        self.port_var.trace_add('write', self.on_port_change)
        ttk.Entry(connection_frame, textvariable=self.port_var, width=10).grid(row=0, column=3, sticky=tk.W)

        # Username
        ttk.Label(connection_frame, text="Username:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.username_var = tk.StringVar()
        ttk.Entry(connection_frame, textvariable=self.username_var, width=25).grid(row=1, column=1, sticky=tk.W, pady=(5, 0))

        # Password
        ttk.Label(connection_frame, text="Password:").grid(row=1, column=2, sticky=tk.W, padx=(10, 5), pady=(5, 0))
        self.password_var = tk.StringVar()
        ttk.Entry(connection_frame, textvariable=self.password_var, width=25, show="*").grid(row=1, column=3, sticky=tk.W, pady=(5, 0))

        # TLS/인증서 설정
        ttk.Label(connection_frame, text="보안 설정:", font=("TkDefaultFont", 9, "bold")).grid(row=2, column=0, columnspan=4, sticky=tk.W, pady=(10, 5))

        # TLS 옵션
        self.tls_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(connection_frame, text="TLS/SSL 사용", variable=self.tls_var,
                       command=self.on_tls_toggle).grid(row=3, column=0, columnspan=2, sticky=tk.W)

        self.insecure_var = tk.BooleanVar(value=False)
        self.insecure_check = ttk.Checkbutton(connection_frame, text="인증서 검증 건너뛰기",
                                             variable=self.insecure_var, state=tk.DISABLED)
        self.insecure_check.grid(row=3, column=2, columnspan=2, sticky=tk.W)

        # AWS IoT / 인증서 기반 인증
        self.use_cert_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(connection_frame, text="인증서 기반 인증 (AWS IoT 등)",
                       variable=self.use_cert_var, command=self.on_cert_toggle).grid(row=4, column=0, columnspan=4, sticky=tk.W, pady=(5, 0))

        # CA 인증서
        ttk.Label(connection_frame, text="CA 인증서:").grid(row=5, column=0, sticky=tk.W, padx=(20, 5), pady=(5, 0))
        self.ca_cert_var = tk.StringVar()
        self.ca_cert_entry = ttk.Entry(connection_frame, textvariable=self.ca_cert_var, width=35, state=tk.DISABLED)
        self.ca_cert_entry.grid(row=5, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        self.ca_cert_btn = ttk.Button(connection_frame, text="찾기", command=lambda: self.browse_file(self.ca_cert_var), state=tk.DISABLED, width=8)
        self.ca_cert_btn.grid(row=5, column=3, sticky=tk.W, padx=(5, 0), pady=(5, 0))

        # 클라이언트 인증서
        ttk.Label(connection_frame, text="클라이언트 인증서:").grid(row=6, column=0, sticky=tk.W, padx=(20, 5), pady=(5, 0))
        self.client_cert_var = tk.StringVar()
        self.client_cert_entry = ttk.Entry(connection_frame, textvariable=self.client_cert_var, width=35, state=tk.DISABLED)
        self.client_cert_entry.grid(row=6, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        self.client_cert_btn = ttk.Button(connection_frame, text="찾기", command=lambda: self.browse_file(self.client_cert_var), state=tk.DISABLED, width=8)
        self.client_cert_btn.grid(row=6, column=3, sticky=tk.W, padx=(5, 0), pady=(5, 0))

        # 프라이빗 키
        ttk.Label(connection_frame, text="프라이빗 키:").grid(row=7, column=0, sticky=tk.W, padx=(20, 5), pady=(5, 0))
        self.private_key_var = tk.StringVar()
        self.private_key_entry = ttk.Entry(connection_frame, textvariable=self.private_key_var, width=35, state=tk.DISABLED)
        self.private_key_entry.grid(row=7, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        self.private_key_btn = ttk.Button(connection_frame, text="찾기", command=lambda: self.browse_file(self.private_key_var), state=tk.DISABLED, width=8)
        self.private_key_btn.grid(row=7, column=3, sticky=tk.W, padx=(5, 0), pady=(5, 0))

        # 도움말
        ttk.Label(connection_frame, text="팁: AWS IoT의 경우 Broker에 엔드포인트 주소, Port는 8883을 사용하세요",
                 font=("TkDefaultFont", 8), foreground="gray").grid(row=8, column=0, columnspan=4, sticky=tk.W, pady=(5, 0))

        # 토픽 설정 프레임
        topic_frame = ttk.LabelFrame(main_frame, text="토픽 설정", padding="10")
        topic_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Label(topic_frame, text="구독 토픽 (여러 개는 쉼표로 구분):").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.topics_var = tk.StringVar(value="data/0")
        ttk.Entry(topic_frame, textvariable=self.topics_var, width=60).grid(row=1, column=0, sticky=(tk.W, tk.E))

        # 연결 버튼 프레임
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=(0, 10))

        self.connect_btn = ttk.Button(button_frame, text="연결", command=self.connect)
        self.connect_btn.grid(row=0, column=0, padx=5)

        self.disconnect_btn = ttk.Button(button_frame, text="연결 해제", command=self.disconnect, state=tk.DISABLED)
        self.disconnect_btn.grid(row=0, column=1, padx=5)

        self.clear_btn = ttk.Button(button_frame, text="메시지 지우기", command=self.clear_messages)
        self.clear_btn.grid(row=0, column=2, padx=5)

        # 상태 표시
        self.status_var = tk.StringVar(value="연결 대기 중")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, foreground="blue")
        status_label.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))

        # 메시지 표시 영역
        message_frame = ttk.LabelFrame(main_frame, text="수신 메시지", padding="10")
        message_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.message_text = scrolledtext.ScrolledText(message_frame, wrap=tk.WORD, height=20, width=100)
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
        main_frame.rowconfigure(5, weight=1)
        message_frame.columnconfigure(0, weight=1)
        message_frame.rowconfigure(0, weight=1)
        connection_frame.columnconfigure(1, weight=1)
        topic_frame.columnconfigure(0, weight=1)

        # 인증서 입력 필드는 이미 self.ca_cert_entry, self.client_cert_entry, self.private_key_entry로 저장됨

    def browse_file(self, var):
        """파일 선택 대화상자"""
        filename = filedialog.askopenfilename(
            title="인증서/키 파일 선택",
            filetypes=[
                ("인증서 파일", "*.pem *.crt *.cer"),
                ("키 파일", "*.key *.pem"),
                ("모든 파일", "*.*")
            ]
        )
        if filename:
            var.set(filename)

    def on_cert_toggle(self):
        """인증서 기반 인증 체크박스 토글"""
        if self.use_cert_var.get():
            # 인증서 필드 활성화
            self.ca_cert_entry.config(state=tk.NORMAL)
            self.client_cert_entry.config(state=tk.NORMAL)
            self.private_key_entry.config(state=tk.NORMAL)
            self.ca_cert_btn.config(state=tk.NORMAL)
            self.client_cert_btn.config(state=tk.NORMAL)
            self.private_key_btn.config(state=tk.NORMAL)
            # TLS 자동 활성화
            self.tls_var.set(True)
            self.insecure_var.set(False)
            self.insecure_check.config(state=tk.DISABLED)
        else:
            # 인증서 필드 비활성화
            self.ca_cert_entry.config(state=tk.DISABLED)
            self.client_cert_entry.config(state=tk.DISABLED)
            self.private_key_entry.config(state=tk.DISABLED)
            self.ca_cert_btn.config(state=tk.DISABLED)
            self.client_cert_btn.config(state=tk.DISABLED)
            self.private_key_btn.config(state=tk.DISABLED)

    def on_port_change(self, *args):
        """포트 번호 변경 시 호출"""
        try:
            port = int(self.port_var.get())
            if port == 8883:
                self.tls_var.set(True)
                if not self.use_cert_var.get():
                    self.insecure_check.config(state=tk.NORMAL)
        except ValueError:
            pass

    def on_tls_toggle(self):
        """TLS 체크박스 토글 시 호출"""
        if self.tls_var.get() and not self.use_cert_var.get():
            self.insecure_check.config(state=tk.NORMAL)
        elif not self.use_cert_var.get():
            self.insecure_check.config(state=tk.DISABLED)
            self.insecure_var.set(False)

    def new_profile(self):
        """새 프로필 생성"""
        dialog = tk.Toplevel(self.root)
        dialog.title("새 프로필")
        dialog.geometry("300x100")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="프로필 이름:").pack(pady=(20, 5))
        name_var = tk.StringVar()
        entry = ttk.Entry(dialog, textvariable=name_var, width=30)
        entry.pack(pady=(0, 10))
        entry.focus()

        def save():
            name = name_var.get().strip()
            if not name:
                messagebox.showerror("오류", "프로필 이름을 입력하세요.", parent=dialog)
                return
            if name in self.profiles:
                messagebox.showerror("오류", "이미 존재하는 프로필 이름입니다.", parent=dialog)
                return

            # 현재 설정으로 새 프로필 생성
            self.profiles[name] = self.get_current_settings()
            self.current_profile = name
            self.update_profile_list()
            self.save_profiles()
            dialog.destroy()

        ttk.Button(dialog, text="저장", command=save).pack()

    def save_profile(self):
        """현재 프로필 저장"""
        if not self.current_profile:
            # 프로필 이름이 없으면 새로 만들기
            self.new_profile()
            return

        self.profiles[self.current_profile] = self.get_current_settings()
        self.save_profiles()
        messagebox.showinfo("저장", f"'{self.current_profile}' 프로필이 저장되었습니다.")

    def delete_profile(self):
        """현재 프로필 삭제"""
        if not self.current_profile:
            messagebox.showwarning("경고", "삭제할 프로필을 선택하세요.")
            return

        if messagebox.askyesno("확인", f"'{self.current_profile}' 프로필을 삭제하시겠습니까?"):
            del self.profiles[self.current_profile]
            self.current_profile = None
            self.update_profile_list()
            self.save_profiles()
            # 기본값으로 초기화
            self.clear_settings()

    def on_profile_selected(self, event):
        """프로필 선택 시 호출"""
        profile_name = self.profile_var.get()
        if profile_name and profile_name in self.profiles:
            self.current_profile = profile_name
            self.load_profile_settings(self.profiles[profile_name])

    def get_current_settings(self):
        """현재 GUI 설정을 딕셔너리로 반환"""
        return {
            "broker": self.broker_var.get(),
            "port": self.port_var.get(),
            "username": self.username_var.get(),
            "topics": self.topics_var.get(),
            "use_tls": self.tls_var.get(),
            "insecure": self.insecure_var.get(),
            "use_cert": self.use_cert_var.get(),
            "ca_cert": self.ca_cert_var.get(),
            "client_cert": self.client_cert_var.get(),
            "private_key": self.private_key_var.get()
        }

    def load_profile_settings(self, settings):
        """프로필 설정을 GUI에 로드"""
        self.broker_var.set(settings.get("broker", "localhost"))
        self.port_var.set(settings.get("port", "1883"))
        self.username_var.set(settings.get("username", ""))
        self.topics_var.set(settings.get("topics", "data/0"))
        self.tls_var.set(settings.get("use_tls", False))
        self.insecure_var.set(settings.get("insecure", False))
        self.use_cert_var.set(settings.get("use_cert", False))
        self.ca_cert_var.set(settings.get("ca_cert", ""))
        self.client_cert_var.set(settings.get("client_cert", ""))
        self.private_key_var.set(settings.get("private_key", ""))

        # TLS 상태에 따라 insecure 체크박스 활성화
        if self.tls_var.get() and not self.use_cert_var.get():
            self.insecure_check.config(state=tk.NORMAL)

        # 인증서 필드 상태 업데이트
        self.on_cert_toggle()

    def clear_settings(self):
        """설정 초기화"""
        self.broker_var.set("localhost")
        self.port_var.set("1883")
        self.username_var.set("")
        self.password_var.set("")
        self.topics_var.set("data/0")
        self.tls_var.set(False)
        self.insecure_var.set(False)
        self.use_cert_var.set(False)
        self.ca_cert_var.set("")
        self.client_cert_var.set("")
        self.private_key_var.set("")
        self.on_cert_toggle()

    def update_profile_list(self):
        """프로필 콤보박스 업데이트"""
        self.profile_combo['values'] = list(self.profiles.keys())
        if self.current_profile:
            self.profile_var.set(self.current_profile)
        else:
            self.profile_var.set('')

    def save_profiles(self):
        """프로필을 파일에 저장"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "profiles": self.profiles,
                    "last_profile": self.current_profile
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"프로필 저장 실패: {e}")

    def load_profiles(self):
        """저장된 프로필 불러오기"""
        if not os.path.exists(self.config_file):
            return

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.profiles = data.get("profiles", {})
            last_profile = data.get("last_profile")

            self.update_profile_list()

            # 마지막 프로필 로드
            if last_profile and last_profile in self.profiles:
                self.current_profile = last_profile
                self.profile_var.set(last_profile)
                self.load_profile_settings(self.profiles[last_profile])

        except Exception as e:
            print(f"프로필 불러오기 실패: {e}")

    def on_connect(self, client, userdata, flags, reason_code, properties):
        """MQTT 연결 성공 시 호출 (Callback API v2)"""
        rc = reason_code if isinstance(reason_code, int) else reason_code.value

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
        self.message_text.see(tk.END)

    def on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
        """MQTT 연결 해제 시 호출 (Callback API v2)"""
        rc = reason_code if isinstance(reason_code, int) else reason_code.value

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

        # 프로토콜 프리픽스 제거
        if '://' in broker:
            protocol_part, host_part = broker.split('://', 1)
            broker = host_part
            if protocol_part.lower() in ['ssl', 'mqtts', 'wss']:
                self.tls_var.set(True)
                self.append_message(f"ℹ 프로토콜 '{protocol_part}://' 감지, TLS 자동 활성화\n", "topic")

        # Broker 주소에서 포트 분리
        if ':' in broker:
            broker_parts = broker.rsplit(':', 1)
            if broker_parts[1].isdigit():
                broker = broker_parts[0]
                extracted_port = int(broker_parts[1])
                self.port_var.set(str(extracted_port))
                self.append_message(f"ℹ Broker 주소에서 포트 {extracted_port} 추출\n", "topic")

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
        use_cert = self.use_cert_var.get()

        # 인증서 기반 인증 검증
        if use_cert:
            ca_cert = self.ca_cert_var.get().strip()
            client_cert = self.client_cert_var.get().strip()
            private_key = self.private_key_var.get().strip()

            if not ca_cert or not client_cert or not private_key:
                messagebox.showerror("오류", "인증서 기반 인증을 사용하려면 CA 인증서, 클라이언트 인증서, 프라이빗 키를 모두 지정해야 합니다.")
                return

            if not os.path.exists(ca_cert):
                messagebox.showerror("오류", f"CA 인증서 파일을 찾을 수 없습니다:\n{ca_cert}")
                return
            if not os.path.exists(client_cert):
                messagebox.showerror("오류", f"클라이언트 인증서 파일을 찾을 수 없습니다:\n{client_cert}")
                return
            if not os.path.exists(private_key):
                messagebox.showerror("오류", f"프라이빗 키 파일을 찾을 수 없습니다:\n{private_key}")
                return

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
                if use_cert:
                    # 인증서 기반 TLS
                    self.client.tls_set(
                        ca_certs=ca_cert,
                        certfile=client_cert,
                        keyfile=private_key,
                        cert_reqs=ssl.CERT_REQUIRED,
                        tls_version=ssl.PROTOCOL_TLSv1_2
                    )
                    self.append_message("ℹ 인증서 기반 TLS 연결 사용\n", "topic")
                else:
                    # 일반 TLS
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
                    error_str = str(e)
                    # 더 친절한 에러 메시지
                    if "getaddrinfo failed" in error_str or "Name or service not known" in error_str:
                        error_msg = f"호스트를 찾을 수 없습니다.\n\n확인 사항:\n- Broker 주소: {broker}\n- 인터넷 연결\n- DNS 설정\n\n원본 오류: {error_str}"
                    elif "Connection refused" in error_str:
                        error_msg = f"연결이 거부되었습니다.\n\n확인 사항:\n- 포트: {port}\n- MQTT 브로커 실행 상태\n- 방화벽 설정\n\n원본 오류: {error_str}"
                    elif "timed out" in error_str or "timeout" in error_str.lower():
                        error_msg = f"연결 시간 초과\n\nBroker: {broker}:{port}\n\n확인 사항:\n- 네트워크 연결\n- 방화벽/보안그룹 설정\n\n원본 오류: {error_str}"
                    elif "certificate" in error_str.lower() or "ssl" in error_str.lower():
                        error_msg = f"인증서 오류\n\n확인 사항:\n- 인증서 파일 경로 확인\n- 인증서 유효성 확인\n- 인증서와 키 매칭 확인\n\n원본 오류: {error_str}"
                    else:
                        error_msg = f"연결 실패\n\nBroker: {broker}:{port}\n\n오류: {error_str}"

                    self.root.after(0, lambda: self.status_var.set(f"연결 실패: {broker}:{port}"))
                    self.root.after(0, lambda msg=error_msg: messagebox.showerror("연결 오류", msg))

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
        self.save_profiles()
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
