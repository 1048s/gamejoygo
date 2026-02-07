import tkinter as tk
from tkinter import messagebox
import os
import json
import sys
import urllib.request
import urllib.error
import subprocess
import threading

# --- 설정 ---
REPO_OWNER = "1048s"
REPO_NAME = "gamejoygo"
TARGET_BRANCH = "main"

class ReleaseManager:
    def __init__(self, root):
        self.root = root
        self.root.title("GameJoyGo 배포 관리자")
        self.root.geometry("500x480")
        self.root.configure(bg="#f0f0f0")

        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.version_file = os.path.join(self.script_dir, "version.py")

        self.github_ver = "확인 중..."
        self.local_ver = self.get_local_version()
        
        self.setup_ui()
        self.root.after(100, self.fetch_github_info)

    def get_local_version(self):
        try:
            # 모듈 캐시 문제 방지를 위해 직접 파일 읽기
            if os.path.exists(self.version_file):
                with open(self.version_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    # VERSION = "v1.0.1" 형태 파싱
                    if 'VERSION = "' in content:
                        return content.split('VERSION = "')[1].split('"')[0]
            return "없음"
        except:
            return "오류"

    def setup_ui(self):
        lbl_font = ("Malgun Gothic", 10)
        val_font = ("Malgun Gothic", 12, "bold")
        p = 20
        
        # 1. 정보 섹션
        info_frame = tk.LabelFrame(self.root, text="버전 정보", font=("Malgun Gothic", 11, "bold"), bg="#f0f0f0", padx=10, pady=10)
        info_frame.pack(fill="x", padx=p, pady=p)
        
        tk.Label(info_frame, text="GitHub 최신 버전:", font=lbl_font, bg="#f0f0f0").grid(row=0, column=0, sticky="w")
        self.lbl_gh_ver = tk.Label(info_frame, text=self.github_ver, font=val_font, fg="#0055aa", bg="#f0f0f0")
        self.lbl_gh_ver.grid(row=0, column=1, sticky="w", padx=10)
        
        tk.Label(info_frame, text="로컬 현재 버전:", font=lbl_font, bg="#f0f0f0").grid(row=1, column=0, sticky="w", pady=(5,0))
        self.lbl_local_ver = tk.Label(info_frame, text=self.local_ver, font=val_font, fg="#333333", bg="#f0f0f0")
        self.lbl_local_ver.grid(row=1, column=1, sticky="w", padx=10, pady=(5,0))

        # 2. 입력 섹션
        input_frame = tk.LabelFrame(self.root, text="새 버전 배포", font=("Malgun Gothic", 11, "bold"), bg="#f0f0f0", padx=10, pady=10)
        input_frame.pack(fill="x", padx=p, pady=0)
        
        tk.Label(input_frame, text="새 버전 입력 (예: v1.0.2):", font=lbl_font, bg="#f0f0f0").pack(anchor="w")
        self.entry_ver = tk.Entry(input_frame, font=("Arial", 12))
        self.entry_ver.pack(fill="x", pady=5)
        self.entry_ver.insert(0, self.local_ver)
        
        self.var_git_push = tk.BooleanVar(value=True)
        tk.Checkbutton(input_frame, text="Git Commit & Push 자동 수행", variable=self.var_git_push, bg="#f0f0f0", font=lbl_font).pack(anchor="w", pady=5)

        # 3. 실행 버튼
        btn_frame = tk.Frame(self.root, bg="#f0f0f0")
        btn_frame.pack(fill="x", padx=p, pady=20)
        
        tk.Button(btn_frame, text="배포 시작 (Release)", command=self.start_release, bg="#007acc", fg="white", font=("Malgun Gothic", 12, "bold"), height=2).pack(fill="x")
        
        self.lbl_status = tk.Label(self.root, text="대기 중...", bg="#f0f0f0", fg="#666666")
        self.lbl_status.pack(side="bottom", pady=10)

    def fetch_github_info(self):
        def _fetch():
            try:
                url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
                req = urllib.request.Request(url, headers={'User-Agent': 'GameJoyGo-Release-Manager'})
                with urllib.request.urlopen(req) as response:
                    data = json.loads(response.read().decode())
                    self.github_ver = data.get('tag_name', '알 수 없음')
            except urllib.error.HTTPError as e:
                self.github_ver = "릴리스 없음" if e.code == 404 else f"오류: {e.code}"
            except Exception:
                self.github_ver = "연결 실패"
            self.lbl_gh_ver.config(text=self.github_ver)
        threading.Thread(target=_fetch, daemon=True).start()

    def start_release(self):
        new_ver = self.entry_ver.get().strip()
        if not new_ver:
            messagebox.showwarning("경고", "버전을 입력해주세요.")
            return
            
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            messagebox.showerror("오류", "GITHUB_TOKEN 환경변수가 없습니다.\n환경 변수를 설정해주세요.")
            return

        if not messagebox.askyesno("확인", f"버전: {new_ver}\n\n정말로 배포하시겠습니까?"):
            return

        self.lbl_status.config(text="작업 진행 중...", fg="blue")
        self.root.update()

        try:
            # 1. version.py 업데이트
            with open(self.version_file, "w", encoding="utf-8") as f:
                f.write(f'VERSION = "{new_ver}"\n')
            
            # 2. Git 작업 (선택 시)
            if self.var_git_push.get():
                self.lbl_status.config(text="Git Push 중...")
                self.root.update()
                subprocess.run(["git", "add", "version.py"], check=True)
                subprocess.run(["git", "commit", "-m", f"Release {new_ver}"], check=True)
                subprocess.run(["git", "push", "origin", TARGET_BRANCH], check=True)

            # 3. GitHub Release 생성
            self.lbl_status.config(text="GitHub Release 생성 중...")
            self.root.update()
            
            url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases"
            payload = {"tag_name": new_ver, "target_commitish": TARGET_BRANCH, "name": f"Release {new_ver}", "body": f"GameJoyGo {new_ver} 업데이트", "generate_release_notes": True}
            headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json", "User-Agent": "GameJoyGo-Release-Manager"}
            
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
            with urllib.request.urlopen(req) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                
            self.lbl_status.config(text="완료!", fg="green")
            messagebox.showinfo("성공", f"릴리스 생성 완료!\n{res_data.get('html_url')}")
            self.root.destroy()

        except Exception as e:
            self.lbl_status.config(text="오류 발생", fg="red")
            messagebox.showerror("오류", f"작업 중 오류가 발생했습니다.\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ReleaseManager(root)
    root.mainloop()