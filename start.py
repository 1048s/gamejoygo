import tkinter as tk
from tkinter import font, messagebox
import subprocess
import sys
import webbrowser
import urllib.request
import json
import threading
import os
import map_editor
import hashlib
import hashlib
from tkinter import simpledialog, filedialog, scrolledtext
from data import version
import sys
# 빌드 모듈은 필요할 때 임포트하거나 subprocess로 실행

class ModernButton(tk.Canvas):
    def __init__(self, parent, text, command, width=200, height=50, 
                 bg_color="#333333", hover_color="#444444", text_color="white", font=None):
        parent_bg = parent.cget("bg")
        super().__init__(parent, width=width, height=height, bg=parent_bg, highlightthickness=0)
        self.command = command
        self.bg_color = bg_color
        self.hover_color = hover_color
        
        def draw_rounded_rect(x1, y1, x2, y2, radius, **kwargs):
            points = [x1+radius, y1,
                      x1+radius, y1,
                      x2-radius, y1,
                      x2-radius, y1,
                      x2, y1,
                      x2, y1+radius,
                      x2, y1+radius,
                      x2, y2-radius,
                      x2, y2-radius,
                      x2, y2,
                      x2-radius, y2,
                      x2-radius, y2,
                      x1+radius, y2,
                      x1+radius, y2,
                      x1, y2,
                      x1, y2-radius,
                      x1, y2-radius,
                      x1, y1+radius,
                      x1, y1+radius,
                      x1, y1]
            return self.create_polygon(points, **kwargs, smooth=True)

        # 2.5D 그림자 (Shadow)
        draw_rounded_rect(4, 4, width, height, 15, fill="#000000", outline="")
        
        # 버튼 본체 (Main Body)
        self.rect = draw_rounded_rect(0, 0, width-4, height-4, 15, fill=bg_color, outline="")
        
        # 텍스트 (Text)
        self.text_id = self.create_text((width-4)/2, (height-4)/2, text=text, fill=text_color, font=font)
        
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
        self.bind("<ButtonRelease-1>", self.on_release)
        self.config(cursor="hand2")

    def on_enter(self, e):
        self.itemconfig(self.rect, fill=self.hover_color)

    def on_leave(self, e):
        self.itemconfig(self.rect, fill=self.bg_color)

    def on_click(self, e):
        self.move(self.rect, 2, 2)
        self.move(self.text_id, 2, 2)

    def on_release(self, e):
        self.move(self.rect, -2, -2)
        self.move(self.text_id, -2, -2)
        if self.command:
            self.command()

class LauncherApp:
    def __init__(self, root):
        self.root = root
        self.config_file = "data/launcher_config.json"
        self.load_config()
        self.should_launch_game = False

        # Initialize tk variables from loaded config
        self.display_var = tk.IntVar(value=self.config.get("display_mode", 0))
        self.sfx_var = tk.DoubleVar(value=self.config.get("sfx_volume", 0.5))
        self.bgm_var = tk.DoubleVar(value=self.config.get("bgm_volume", 0.3))
        self.cheat_var = tk.BooleanVar(value=self.config.get("cheat_mode", False))
        self.skip_var = tk.BooleanVar(value=self.config.get("skip_intro_screen", False))
        self.server_ip_var = tk.StringVar(value=self.config.get("server_ip", "127.0.0.1"))
        self.server_port_var = tk.StringVar(value=str(self.config.get("server_port", "12345")))
        self.nickname_var = tk.StringVar(value=self.config.get("nickname", "Player"))

        self.root.title("Kane Defense Launcher")
        self.root.geometry("900x600")
        self.root.configure(bg="#121212")
        self.root.resizable(False, False)

        # 폰트 설정 (시스템에 맑은 고딕이 없으면 기본 폰트 사용)
        try:
            self.title_font = font.Font(family="Malgun Gothic", size=40, weight="bold")
            self.subtitle_font = font.Font(family="Malgun Gothic", size=12)
            self.menu_btn_font = font.Font(family="Malgun Gothic", size=14, weight="bold")
            self.btn_font = font.Font(family="Malgun Gothic", size=11, weight="bold")
            self.text_font = font.Font(family="Malgun Gothic", size=10)
            self.notice_title_font = font.Font(family="Malgun Gothic", size=11, weight="bold")
        except:
            self.title_font = font.Font(family="Helvetica", size=40, weight="bold")
            self.subtitle_font = font.Font(family="Helvetica", size=12)
            self.menu_btn_font = font.Font(family="Helvetica", size=14, weight="bold")
            self.btn_font = font.Font(family="Helvetica", size=11, weight="bold")
            self.text_font = font.Font(family="Helvetica", size=10)
            self.notice_title_font = font.Font(family="Helvetica", size=11, weight="bold")

        # 메인 컨테이너
        main_container = tk.Frame(root, bg="#121212")
        main_container.pack(fill="both", expand=True, padx=50, pady=50)

        # 왼쪽: 타이틀 및 정보
        left_frame = tk.Frame(main_container, bg="#121212")
        left_frame.pack(side="left", fill="both", expand=True)

        # 타이틀 영역 (2.5D 효과: 그림자 텍스트)
        title_canvas = tk.Canvas(left_frame, bg="#121212", height=80, highlightthickness=0)
        title_canvas.pack(fill="x")
        title_canvas.create_text(3, 43, text="케인 디펜스", font=self.title_font, fill="#000000", anchor="w")
        title_canvas.create_text(0, 40, text="케인 디펜스", font=self.title_font, fill="#FF3333", anchor="w")
        
        tk.Label(left_frame, text="게이조이고의 전설", font=self.subtitle_font, bg="#121212", fg="#666666", anchor="w").pack(fill="x", pady=(0, 30))

        # 공지사항 박스 (2.5D 스타일링: 테두리 추가)
        notice_bg = "#1E1E1E"
        notice_frame = tk.Frame(left_frame, bg=notice_bg, padx=20, pady=20, highlightbackground="black", highlightthickness=2)
        notice_frame.pack(fill="both", expand=True, pady=(0, 20))

        tk.Label(notice_frame, text="공지사항", font=self.notice_title_font, bg=notice_bg, fg="#FF3333", anchor="w").pack(fill="x", pady=(0, 15))

        self.notice_labels = []
        for _ in range(5):
            lbl = tk.Label(notice_frame, text="Loading...", font=self.text_font, bg=notice_bg, fg="#CCCCCC", anchor="w", cursor="hand2")
            lbl.pack(fill="x", pady=3)
            self.notice_labels.append(lbl)
        
        self.load_notices()

        # 오른쪽: 버튼 영역
        right_frame = tk.Frame(main_container, bg="#121212")
        right_frame.pack(side="right", fill="y", padx=(60, 0))

        # 버튼 생성 헬퍼 함수 (ModernButton 적용)
        def create_btn(text, cmd, primary=False):
            bg_color = "#FF3333" if primary else "#252525"
            hover_color = "#FF5555" if primary else "#353535"
            btn = ModernButton(right_frame, text=text, command=cmd, width=220, height=55, 
                               bg_color=bg_color, hover_color=hover_color, font=self.menu_btn_font)
            btn.pack(pady=8)
            return btn

        self.btn_start = create_btn("게임 시작", self.start_game, primary=True)
        self.btn_nickname = create_btn(f"닉네임 변경", self.open_nickname_window)
        self.btn_settings = create_btn("설정", self.open_settings_window)
        self.btn_editor = create_btn("맵 에디터", self.open_editor)
        self.btn_update = create_btn("업데이트 확인", self.check_update)
        self.btn_exit = create_btn("종료", root.quit)

        # 관리자 기능 (이스터에그): 설정 버튼 위에서 숫자 6 누르기
        self.is_settings_hover = False
        self.btn_settings.bind("<Enter>", lambda e: self._on_settings_hover(True), add="+")
        self.btn_settings.bind("<Leave>", lambda e: self._on_settings_hover(False), add="+")
        self.root.bind("<Key>", self._on_key_press)

        # 하단 버전 정보
        version_label = tk.Label(root, text=f"{version.VERSION} | GameJoyGo", bg="#121212", fg="#333333", font=("Arial", 9))
        version_label.place(relx=0.98, rely=0.98, anchor="se")

    def _on_settings_hover(self, is_hover):
        self.is_settings_hover = is_hover

    def _on_key_press(self, event):
        if self.is_settings_hover and event.char == '6':
            self.open_admin_window()

    def load_notices(self):
        def fetch():
            try:
                url = "https://api.github.com/repos/1048s/gamejoygo/issues?state=open&per_page=5"
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as response:
                    data = json.loads(response.read().decode())
                    self.root.after(0, self.update_notice_ui, data)
            except Exception as e:
                print(f"Notice Error: {e}")
                self.root.after(0, self.update_notice_ui, [])
        threading.Thread(target=fetch, daemon=True).start()

    def update_notice_ui(self, issues):
        for i, lbl in enumerate(self.notice_labels):
            if i < len(issues):
                lbl.config(text=f"• {issues[i]['title']}", fg="white", cursor="hand2")
                lbl.bind("<Button-1>", lambda e, url=issues[i]['html_url']: webbrowser.open(url))
            else:
                lbl.config(text="" if issues else ("공지사항을 불러올 수 없습니다." if i == 0 else ""))

    def load_config(self):
        self.config = {}
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    self.config = json.load(f)
            except: pass

    def save_config(self):
        """tk.Var 변수들의 현재 값을 self.config에 반영하고 파일에 저장합니다."""
        self.config["skip_intro_screen"] = self.skip_var.get()
        self.config["cheat_mode"] = self.cheat_var.get()
        self.config["bgm_volume"] = self.bgm_var.get()
        self.config["sfx_volume"] = self.sfx_var.get()
        self.config["display_mode"] = self.display_var.get()
        self.config["server_ip"] = self.server_ip_var.get()
        try:
            self.config["server_port"] = int(self.server_port_var.get())
        except:
            self.config["server_port"] = 12345
        self.config["nickname"] = self.nickname_var.get()
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            messagebox.showerror("오류", f"설정 저장에 실패했습니다: {e}", parent=self.root)

    def open_settings_window(self):
        """설정 팝업창을 엽니다."""
        settings_win = tk.Toplevel(self.root)
        settings_win.title("설정")
        settings_win.geometry("400x550")
        settings_win.configure(bg="#121212")
        settings_win.resizable(False, False)
        settings_win.transient(self.root)
        settings_win.grab_set()

        # 타이틀
        tk.Label(settings_win, text="설정", font=("Malgun Gothic", 20, "bold"), bg="#121212", fg="#FF3333").pack(pady=(25, 10))

        frame = tk.Frame(settings_win, bg="#121212", padx=30, pady=10)
        frame.pack(fill="both", expand=True)

        # 스타일 상수
        bg_color = "#121212"
        text_color = "#CCCCCC"
        accent_color = "#FF3333"
        rb_style = {"bg": bg_color, "fg": text_color, "selectcolor": "#252525", "activebackground": bg_color, "activeforeground": "white", "font": self.text_font, "relief": "flat"}

        # 섹션 헬퍼
        def add_section(text):
            tk.Label(frame, text=text, font=self.notice_title_font, bg=bg_color, fg=accent_color, anchor="w").pack(fill="x", pady=(15, 5))

        # 1. DISPLAY
        add_section("화면 설정")
        display_frame = tk.Frame(frame, bg=bg_color)
        display_frame.pack(fill='x')
        tk.Radiobutton(display_frame, text="창 모드", variable=self.display_var, value=0, **rb_style).pack(side="left", padx=(0, 15))
        tk.Radiobutton(display_frame, text="전체 화면", variable=self.display_var, value=1, **rb_style).pack(side="left")

        # 2. AUDIO
        add_section("오디오 설정")
        def create_slider(label_text, var):
            f = tk.Frame(frame, bg=bg_color)
            f.pack(fill='x', pady=2)
            tk.Label(f, text=label_text, font=self.text_font, bg=bg_color, fg=text_color, width=8, anchor="w").pack(side="left")
            val_lbl = tk.Label(f, text=f"{int(var.get()*100)}%", font=self.text_font, bg=bg_color, fg=accent_color, width=4)
            val_lbl.pack(side="right")
            def update_lbl(v): val_lbl.config(text=f"{int(float(v)*100)}%")
            tk.Scale(f, from_=0, to=1, resolution=0.1, orient='horizontal', variable=var, 
                     bg=bg_color, fg=text_color, troughcolor="#333333", activebackground=accent_color, 
                     highlightthickness=0, showvalue=0, command=update_lbl, bd=0).pack(fill='x', expand=True, padx=5)

        create_slider("효과음", self.sfx_var)
        create_slider("배경음", self.bgm_var)

        # 3. NETWORK
        add_section("네트워크 설정")
        net_frame = tk.Frame(frame, bg=bg_color)
        net_frame.pack(fill='x', pady=2)
        
        tk.Label(net_frame, text="IP 주소", font=self.text_font, bg=bg_color, fg=text_color, width=8, anchor="w").pack(side="left")
        tk.Entry(net_frame, textvariable=self.server_ip_var, font=self.text_font, bg="#252525", fg="white", insertbackground="white", relief="flat").pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        tk.Label(net_frame, text="포트", font=self.text_font, bg=bg_color, fg=text_color, width=4, anchor="w").pack(side="left")
        tk.Entry(net_frame, textvariable=self.server_port_var, font=self.text_font, bg="#252525", fg="white", insertbackground="white", relief="flat", width=6).pack(side="left")

        # 4. OPTIONS
        add_section("기타 설정")
        tk.Checkbutton(frame, text="치트 모드", variable=self.cheat_var, **rb_style).pack(anchor="w", pady=2)
        tk.Checkbutton(frame, text="인트로 건너뛰기", variable=self.skip_var, **rb_style).pack(anchor="w", pady=2)

        def save_and_close():
            self.save_config()
            settings_win.destroy()

        # 저장 버튼
        btn = ModernButton(settings_win, text="저장하고 닫기", command=save_and_close, width=340, height=50,
                           bg_color=accent_color, hover_color="#FF5555", font=self.btn_font)
        btn.pack(fill="x", padx=30, pady=30)

    def open_nickname_window(self):
        """닉네임 설정 팝업창을 엽니다."""
        nick_win = tk.Toplevel(self.root)
        nick_win.title("닉네임 변경")
        nick_win.geometry("350x200")
        nick_win.configure(bg="#121212")
        nick_win.resizable(False, False)
        nick_win.transient(self.root)
        nick_win.grab_set()

        # 화면 중앙 배치
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 175
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 100
        nick_win.geometry(f"+{x}+{y}")

        tk.Label(nick_win, text="닉네임 설정", font=("Malgun Gothic", 16, "bold"), bg="#121212", fg="#FF3333").pack(pady=(20, 10))
        
        frame = tk.Frame(nick_win, bg="#121212", padx=20)
        frame.pack(fill="x")

        tk.Label(frame, text="사용할 닉네임을 입력하세요:", font=self.text_font, bg="#121212", fg="#CCCCCC").pack(anchor="w", pady=(0, 5))
        
        entry_bg = "#252525"
        entry_fg = "white"
        
        nick_entry = tk.Entry(frame, textvariable=self.nickname_var, font=("Malgun Gothic", 12), bg=entry_bg, fg=entry_fg, insertbackground="white", relief="flat")
        nick_entry.pack(fill="x", ipady=5)
        
        def save_nick():
            self.save_config()
            nick_win.destroy()
            
        btn = ModernButton(nick_win, text="확인", command=save_nick, width=150, height=40,
                           bg_color="#FF3333", hover_color="#FF5555", font=self.btn_font)
        btn.pack(pady=20)
        
        nick_entry.focus_set()
        nick_entry.bind("<Return>", lambda e: save_nick())

    def start_game(self):
        self.should_launch_game = True
        self.root.destroy()

    # ... (inside LauncherApp class methods)
    def open_admin_window(self):
        """관리자 탭(창)을 엽니다. (비밀번호 기능 구현됨)"""
        # 비밀번호 입력 받기
        password = simpledialog.askstring("관리자 인증", "관리자 비밀번호를 입력하세요:", parent=self.root, show="*")
        
        if not password:
            return

        # 1. 패스워드 검증 (data/admin_hash.txt)
        target_pw = ""
        try:
            with open("data/admin_hash.txt", "r") as f:
                target_pw = f.read().strip().upper()
        except: pass
        
        if not target_pw: target_pw = "7FC74A463D290D5B0085818FC9041B6C" # 기본값

        if hashlib.md5(password.encode()).hexdigest().upper() != target_pw:
            messagebox.showerror("인증 실패", "비밀번호가 올바르지 않습니다.", parent=self.root)
            return

        # 1차 인증 성공 알림 및 파일 선택 유도
        if not messagebox.askokcancel("2차 인증", "1차 인증에 성공했습니다.\n확인을 누르면 보안 키 파일(.key 등)을 선택하는 창이 열립니다.\n올바른 키 파일을 선택해주세요.", parent=self.root):
            return

        # 2차 인증: 키 파일 선택 (파일 업로드 창)
        target_key_hash = "76deb49cc2a877d33c64a76b4f11989a"
        
        key_file_path = filedialog.askopenfilename(
            title="보안 키 파일 선택",
            initialdir=os.getcwd(),
            filetypes=[("All Files", "*.*"), ("Key Files", "*.key")]
        )

        if not key_file_path: # 취소함
            return

        try:
            with open(key_file_path, "rb") as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            
            if file_hash != target_key_hash:
                messagebox.showerror("인증 실패", f"선택한 키 파일이 유효하지 않습니다.\n(Hash Mismatch)", parent=self.root)
                return
        except Exception as e:
            messagebox.showerror("오류", f"파일을 읽는 중 오류가 발생했습니다: {e}", parent=self.root)
            return

        # 인증 성공
        self._show_admin_panel()

    def _show_admin_panel(self):
        """실제 관리자 패널을 표시합니다."""
        admin_win = tk.Toplevel(self.root)
        admin_win.title("관리자 대시보드")
        admin_win.geometry("800x600")
        admin_win.configure(bg="#1E1E1E")
        
        # 스타일
        title_font = ("Malgun Gothic", 20, "bold")
        header_font = ("Malgun Gothic", 12, "bold")
        btn_font = ("Malgun Gothic", 10)
        log_font = ("Consolas", 9)
        
        # 1. 헤더
        tk.Label(admin_win, text="관리자 대시보드", font=title_font, bg="#1E1E1E", fg="#FF3333").pack(pady=20)
        
        # 2. 버튼 컨트롤 패널
        control_frame = tk.Frame(admin_win, bg="#1E1E1E")
        control_frame.pack(fill="x", padx=20, pady=10)
        
        def run_build():
            if not messagebox.askyesno("빌드", "게임을 빌드하시겠습니까?\n시간이 다소 소요될 수 있습니다."): return
            self._log_to_admin(log_text, "=== 빌드 시작 ===")
            
            def build_thread():
                try:
                    # sys.stdout을 캡처하여 로그창에 출력하고 싶지만 복잡하므로 subprocess로 실행
                    p = subprocess.Popen([sys.executable, "data/build.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=os.getcwd())
                    
                    while True:
                        line = p.stdout.readline()
                        if not line and p.poll() is not None: break
                        if line: self._log_to_admin(log_text, line.strip())
                    
                    if p.returncode == 0:
                        self._log_to_admin(log_text, "=== 빌드 성공 ===")
                        messagebox.showinfo("완료", "빌드가 완료되었습니다.", parent=admin_win)
                    else:
                        err = p.stderr.read()
                        self._log_to_admin(log_text, f"=== 빌드 실패 ===\n{err}")
                        messagebox.showerror("실패", "빌드 중 오류가 발생했습니다.", parent=admin_win)
                except Exception as e:
                    self._log_to_admin(log_text, f"Error: {e}")

            threading.Thread(target=build_thread, daemon=True).start()

        def run_release():
            # create_release.py 실행
            try:
                subprocess.Popen([sys.executable, "data/create_release.py"], cwd=os.getcwd())
                self._log_to_admin(log_text, "릴리스 매니저 실행됨.")
            except Exception as e:
                self._log_to_admin(log_text, f"릴리스 매니저 실행 실패: {e}")

        def view_error_log():
            log_path = "error_log.txt"
            if os.path.exists(log_path):
                with open(log_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self._log_to_admin(log_text, f"--- {log_path} ---\n{content}\n----------------")
            else:
                self._log_to_admin(log_text, "error_log.txt 파일이 없습니다.")

        ModernButton(control_frame, text="게임 빌드 (Build)", command=run_build, width=200, height=50, bg_color="#0066CC").pack(side="left", padx=10)
        ModernButton(control_frame, text="릴리스 생성 (Release)", command=run_release, width=200, height=50, bg_color="#009900").pack(side="left", padx=10)
        ModernButton(control_frame, text="에러 로그 확인", command=view_error_log, width=200, height=50, bg_color="#CC6600").pack(side="left", padx=10)
        
        # 3. 로그 뷰어
        tk.Label(admin_win, text="실행 로그", font=header_font, bg="#1E1E1E", fg="#CCCCCC").pack(anchor="w", padx=20, pady=(20, 5))
        
        log_frame = tk.Frame(admin_win, bg="#1E1E1E")
        log_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        log_text = scrolledtext.ScrolledText(log_frame, font=log_font, bg="#101010", fg="#00FF00", state="disabled")
        log_text.pack(fill="both", expand=True)
        
        # 닫기 버튼
        ModernButton(admin_win, text="닫기", command=admin_win.destroy, width=150, height=40, bg_color="#333333").pack(side="bottom", pady=10)

        self._log_to_admin(log_text, "관리자 패널이 준비되었습니다.")

    def _log_to_admin(self, widget, message):
        """로그 창에 메시지를 추가합니다. (Thread-safe)"""
        def _update():
            widget.config(state="normal")
            widget.insert("end", f"{message}\n")
            widget.see("end")
            widget.config(state="disabled")
        self.root.after(0, _update)

    def open_editor(self):
        if getattr(sys, 'frozen', False):
            subprocess.Popen([sys.executable, "map_editor"])
        else:
            subprocess.Popen([sys.executable, "map_editor.py"])

    def check_update(self):
        def check():
            try:
                url = "https://api.github.com/repos/1048s/gamejoygo/releases/latest"
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as response:
                    data = json.loads(response.read().decode())
                    latest_tag = data['tag_name']
                    current_version = version.VERSION
                    if latest_tag != current_version:
                        self.root.after(0, lambda: self.show_update_dialog(latest_tag, data['html_url']))
                    else:
                        self.root.after(0, lambda: messagebox.showinfo("업데이트", "현재 최신 버전을 사용 중입니다."))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("오류", f"업데이트 정보를 가져올 수 없습니다.\n{e}"))
        
        threading.Thread(target=check, daemon=True).start()

    def show_update_dialog(self, tag, url):
        if messagebox.askyesno("업데이트", f"새로운 버전 {tag}이 있습니다.\n다운로드 페이지로 이동하시겠습니까?"):
            webbrowser.open(url)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "map_editor":
        map_editor.main()
        sys.exit()

    # 런처는 항상 실행합니다.
    # '건너뛰기' 옵션은 런처 내부의 게임 시작 로직에 영향을 줍니다.
    root = tk.Tk()
    app = LauncherApp(root)
    root.mainloop()
    
    if app.should_launch_game:
        try:
            # 게임 시작 직전에 모듈을 임포트하여 충돌 방지
            import main
            main.main(skip_intro=app.config.get("skip_intro_screen", False))
        except Exception as e:
            # 실행 실패 시 오류 메시지 표시
            messagebox.showerror("실행 오류", f"게임을 시작하는 중 오류가 발생했습니다:\n{e}")