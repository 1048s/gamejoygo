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
from data import version

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

        # 하단 버전 정보
        version_label = tk.Label(root, text=f"{version.VERSION} | GameJoyGo", bg="#121212", fg="#333333", font=("Arial", 9))
        version_label.place(relx=0.98, rely=0.98, anchor="se")

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