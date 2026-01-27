import tkinter as tk
from tkinter import font, messagebox
import subprocess
import sys
import webbrowser
import urllib.request
import json
import threading
import os

class LauncherApp:
    def __init__(self, root):
        self.root = root
        self.config_file = "launcher_config.json"
        self.load_config()

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
        
        self.skip_var = tk.BooleanVar()
        self.chk_skip = tk.Checkbutton(right_frame, text="시작 화면 보지 않기", variable=self.skip_var,
                                       bg="#1e1e1e", fg="#aaaaaa",
                                       activebackground="#1e1e1e", activeforeground="#aaaaaa",
                                       font=self.text_font)
        self.chk_skip.pack(pady=(0, 10))

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

    def start_game(self, save=True):
        if save and hasattr(self, 'skip_var') and self.skip_var.get():
            self.config["skip_launcher"] = True
            try:
                with open(self.config_file, "w") as f:
                    json.dump(self.config, f)
            except: pass
            
        self.root.destroy()
        subprocess.Popen([sys.executable, "main.py"])

    def open_editor(self):
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
                        if messagebox.askyesno("업데이트", f"새로운 버전 {latest_tag}이 있습니다.\n다운로드 페이지로 이동하시겠습니까?"):
                            webbrowser.open(data['html_url'])
                    else:
                        messagebox.showinfo("업데이트", "현재 최신 버전을 사용 중입니다.")
            except Exception as e:
                messagebox.showerror("오류", f"업데이트 정보를 가져올 수 없습니다.\n{e}")
        
        threading.Thread(target=check, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = LauncherApp(root)
    root.mainloop()