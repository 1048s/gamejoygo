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

class LauncherApp:
    def __init__(self, root):
        self.root = root
        self.config_file = "launcher_config.json"
        self.load_config()
        self.should_launch_game = False

        # Initialize tk variables from loaded config
        self.display_var = tk.IntVar(value=self.config.get("display_mode", 0))
        self.sfx_var = tk.DoubleVar(value=self.config.get("sfx_volume", 0.5))
        self.bgm_var = tk.DoubleVar(value=self.config.get("bgm_volume", 0.3))
        self.cheat_var = tk.BooleanVar(value=self.config.get("cheat_mode", False))
        self.skip_var = tk.BooleanVar(value=self.config.get("skip_intro_screen", False))

        self.root.title("Kane Defense Launcher")
        self.root.geometry("800x500")
        self.root.configure(bg="#1e1e1e")
        self.root.resizable(False, False)

        # 폰트 설정 (시스템에 맑은 고딕이 없으면 기본 폰트 사용)
        try:
            self.title_font = font.Font(family="Malgun Gothic", size=30, weight="bold")
            self.btn_font = font.Font(family="Malgun Gothic", size=12, weight="bold")
            self.text_font = font.Font(family="Malgun Gothic", size=10)
        except:
            self.title_font = font.Font(family="Helvetica", size=30, weight="bold")
            self.btn_font = font.Font(family="Helvetica", size=12, weight="bold")
            self.text_font = font.Font(family="Helvetica", size=10)

        # 메인 프레임
        main_frame = tk.Frame(root, bg="#1e1e1e")
        main_frame.pack(fill="both", expand=True, padx=40, pady=40)

        # 왼쪽: 타이틀 및 정보
        left_frame = tk.Frame(main_frame, bg="#1e1e1e")
        left_frame.pack(side="left", fill="both", expand=True)

        title_label = tk.Label(left_frame, text="케인 디펜스 실행기", font=self.title_font, bg="#1e1e1e", fg="#ff3333", anchor="w")
        title_label.pack(fill="x", pady=(0, 10))

        desc_label = tk.Label(left_frame, text="실행파일이란 맨이야 \n지금 바로 조이기->", font=self.text_font, bg="#1e1e1e", fg="#cccccc", justify="left", anchor="w")
        desc_label.pack(fill="x", pady=(0, 30))

        # 공지사항 박스 (더미 데이터)
        notice_frame = tk.LabelFrame(left_frame, text="공지사항", font=self.text_font, bg="#1e1e1e", fg="#aaaaaa", bd=1, relief="solid")
        notice_frame.pack(fill="both", expand=True, pady=(0, 20))

        self.notice_labels = []
        for _ in range(4):
            lbl = tk.Label(notice_frame, text="로딩 중...", font=self.text_font, bg="#1e1e1e", fg="#aaaaaa", anchor="w", padx=10, pady=5)
            lbl.pack(fill="x")
            self.notice_labels.append(lbl)
        
        self.load_notices()

        # 오른쪽: 버튼 영역
        right_frame = tk.Frame(main_frame, bg="#1e1e1e")
        right_frame.pack(side="right", fill="y", padx=(40, 0))

        # 버튼 생성 헬퍼 함수
        def create_btn(text, cmd, color="#333333", text_color="white"):
            btn = tk.Button(right_frame, text=text, font=self.btn_font, bg=color, fg=text_color, 
                            activebackground="#555555", activeforeground="white", 
                            relief="flat", width=20, height=2, command=cmd, cursor="hand2")
            btn.pack(pady=10)
            return btn

        self.btn_start = create_btn("게임 시작", self.start_game, color="#cc0000")
        self.btn_settings = create_btn("설정", self.open_settings_window)
        self.btn_editor = create_btn("맵 에디터", self.open_editor)
        self.btn_update = create_btn("업데이트 확인", self.check_update)
        self.btn_exit = create_btn("종료", root.quit)

        # 하단 버전 정보
        version_label = tk.Label(root, text="Version 1.0.0 | GameJoyGo", bg="#1e1e1e", fg="#666666", font=("Arial", 8))
        version_label.pack(side="bottom", pady=10)

    def load_notices(self):
        def fetch():
            try:
                url = "https://api.github.com/repos/1048s/gamejoygo/issues?state=open&per_page=4"
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
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            messagebox.showerror("오류", f"설정 저장에 실패했습니다: {e}", parent=self.root)

    def open_settings_window(self):
        """설정 팝업창을 엽니다."""
        settings_win = tk.Toplevel(self.root)
        settings_win.title("설정")
        settings_win.geometry("350x320")
        settings_win.configure(bg="#1e1e1e")
        settings_win.resizable(False, False)
        settings_win.transient(self.root)
        settings_win.grab_set()

        frame = tk.Frame(settings_win, bg="#1e1e1e", padx=20, pady=20)
        frame.pack(fill="both", expand=True)

        # 화면 설정
        display_frame = tk.Frame(frame, bg="#1e1e1e")
        display_frame.pack(fill='x', pady=5)
        tk.Label(display_frame, text="화면", font=self.text_font, bg="#1e1e1e", fg="#aaaaaa", width=8, anchor="w").pack(side="left")
        tk.Radiobutton(display_frame, text="창", variable=self.display_var, value=0, bg="#1e1e1e", fg="#aaaaaa", selectcolor="#1e1e1e", activebackground="#1e1e1e", activeforeground="white").pack(side="left")
        tk.Radiobutton(display_frame, text="전체", variable=self.display_var, value=1, bg="#1e1e1e", fg="#aaaaaa", selectcolor="#1e1e1e", activebackground="#1e1e1e", activeforeground="white").pack(side="left")

        # SFX 볼륨
        sfx_frame = tk.Frame(frame, bg="#1e1e1e")
        sfx_frame.pack(fill='x', pady=5)
        tk.Label(sfx_frame, text="효과음", font=self.text_font, bg="#1e1e1e", fg="#aaaaaa", width=8, anchor="w").pack(side="left")

        sfx_percent_label = tk.Label(sfx_frame, text=f"{int(self.sfx_var.get()*100)}%", font=self.text_font, bg="#1e1e1e", fg="#aaaaaa", width=4)
        sfx_percent_label.pack(side="right", padx=(5,0))

        def update_sfx_label(val):
            sfx_percent_label.config(text=f"{int(float(val)*100)}%")

        tk.Scale(sfx_frame, from_=0, to=1, resolution=0.1, orient='horizontal', variable=self.sfx_var, bg="#1e1e1e", fg="#aaaaaa", troughcolor="#333333", activebackground="#555555", highlightthickness=0, showvalue=0, command=update_sfx_label).pack(fill='x', expand=True)

        # BGM 볼륨
        bgm_frame = tk.Frame(frame, bg="#1e1e1e")
        bgm_frame.pack(fill='x', pady=5)
        tk.Label(bgm_frame, text="배경음", font=self.text_font, bg="#1e1e1e", fg="#aaaaaa", width=8, anchor="w").pack(side="left")

        bgm_percent_label = tk.Label(bgm_frame, text=f"{int(self.bgm_var.get()*100)}%", font=self.text_font, bg="#1e1e1e", fg="#aaaaaa", width=4)
        bgm_percent_label.pack(side="right", padx=(5,0))

        def update_bgm_label(val):
            bgm_percent_label.config(text=f"{int(float(val)*100)}%")

        tk.Scale(bgm_frame, from_=0, to=1, resolution=0.1, orient='horizontal', variable=self.bgm_var, bg="#1e1e1e", fg="#aaaaaa", troughcolor="#333333", activebackground="#555555", highlightthickness=0, showvalue=0, command=update_bgm_label).pack(fill='x', expand=True)

        # 치트 모드
        tk.Checkbutton(frame, text="치트 모드 활성화", variable=self.cheat_var, bg="#1e1e1e", fg="#aaaaaa", activebackground="#1e1e1e", activeforeground="#aaaaaa", font=self.text_font, selectcolor="#1e1e1e").pack(pady=5, anchor="w")

        # 시작 화면 건너뛰기
        tk.Checkbutton(frame, text="시작 화면 건너뛰기", variable=self.skip_var, bg="#1e1e1e", fg="#aaaaaa", activebackground="#1e1e1e", activeforeground="#aaaaaa", font=self.text_font, selectcolor="#1e1e1e").pack(pady=5, anchor="w")

        def save_and_close():
            self.save_config()
            messagebox.showinfo("저장 완료", "설정이 저장되었습니다.", parent=settings_win)
            settings_win.destroy()

        tk.Button(frame, text="저장하고 닫기", font=self.btn_font, bg="#333333", fg="white", 
                  activebackground="#555555", activeforeground="white", 
                  relief="flat", command=save_and_close, cursor="hand2").pack(side="bottom", fill="x", pady=(15, 0))

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
                    # 현재 버전 하드코딩 (실제로는 변수로 관리 권장)
                    current_version = "v1.0.0" 
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