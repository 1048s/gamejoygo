import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import json
import os

# --- 설정 --- 2026-02-09
# 게임 내 설정과 맞춤 (mte_config.py 참고)
# 에디터 화면에 다 들어오도록 시각적 크기는 절반(40)으로 줄이고, 논리적 좌표는 그대로 사용
VISUAL_GRID_SIZE = 40 
GAME_GRID_COLS = 24  # 1920 / 80
GAME_GRID_ROWS = 14  # 1080 / 80

class MapEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("케인 디펜스 맵 에디터")
        
        self.path = [] # [[x, y], [x, y], ...]
        self.map_name = "새로운 맵"
        
        # 상단 UI 프레임
        self.ui_frame = tk.Frame(root, pady=5)
        self.ui_frame.pack(side=tk.TOP, fill=tk.X)
        
        tk.Label(self.ui_frame, text="맵 이름:").pack(side=tk.LEFT, padx=5)
        self.name_entry = tk.Entry(self.ui_frame, width=20)
        self.name_entry.insert(0, self.map_name)
        self.name_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Button(self.ui_frame, text="불러오기", command=self.load_map).pack(side=tk.LEFT, padx=5)
        tk.Button(self.ui_frame, text="저장하기", command=self.save_map).pack(side=tk.LEFT, padx=5)
        tk.Button(self.ui_frame, text="주꾸다시", command=self.clear_map, fg="red").pack(side=tk.LEFT, padx=5)
        
        tk.Label(self.ui_frame, text="[좌클릭: 조이기] [우클릭: 조이기 취소]").pack(side=tk.RIGHT, padx=10)

        # 캔버스 (맵 영역)
        canvas_w = GAME_GRID_COLS * VISUAL_GRID_SIZE
        canvas_h = GAME_GRID_ROWS * VISUAL_GRID_SIZE
        self.canvas = tk.Canvas(root, width=canvas_w, height=canvas_h, bg="white")
        self.canvas.pack(pady=10, padx=10)
        
        # 이벤트 바인딩
        self.canvas.bind("<Button-1>", self.on_left_click)
        self.canvas.bind("<Button-3>", self.on_right_click)
        
        self.draw_grid()

    def draw_grid(self):
        """격자 무늬 그리기"""
        w = int(self.canvas['width'])
        h = int(self.canvas['height'])
        
        # 수직선
        for x in range(0, w, VISUAL_GRID_SIZE):
            self.canvas.create_line(x, 0, x, h, fill="#ddd")
        # 수평선
        for y in range(0, h, VISUAL_GRID_SIZE):
            self.canvas.create_line(0, y, w, y, fill="#ddd")

    def draw_path(self):
        """현재 경로 그리기"""
        self.canvas.delete("path_element") # 기존 경로 요소 삭제
        
        if not self.path:
            return

        # 선 그리기
        if len(self.path) > 1:
            points = []
            for p in self.path:
                cx = p[0] * VISUAL_GRID_SIZE + VISUAL_GRID_SIZE // 2
                cy = p[1] * VISUAL_GRID_SIZE + VISUAL_GRID_SIZE // 2
                points.extend([cx, cy])
            self.canvas.create_line(points, fill="blue", width=3, tags="path_element", arrow=tk.LAST)

        # 점 그리기
        for i, p in enumerate(self.path):
            cx = p[0] * VISUAL_GRID_SIZE + VISUAL_GRID_SIZE // 2
            cy = p[1] * VISUAL_GRID_SIZE + VISUAL_GRID_SIZE // 2
            r = 6
            
            color = "blue"
            if i == 0: color = "green" # 시작점
            elif i == len(self.path) - 1: color = "red" # 끝점
            
            self.canvas.create_oval(cx-r, cy-r, cx+r, cy+r, fill=color, outline="black", tags="path_element")
            self.canvas.create_text(cx, cy-15, text=str(i), fill="black", font=("Arial", 8), tags="path_element")

    def on_left_click(self, event):
        """경로 추가"""
        gx = event.x // VISUAL_GRID_SIZE
        gy = event.y // VISUAL_GRID_SIZE
        
        # 범위 체크
        if 0 <= gx < GAME_GRID_COLS and 0 <= gy < GAME_GRID_ROWS:
            self.path.append([gx, gy])
            self.draw_path()

    def on_right_click(self, event):
        """마지막 경로 삭제 (Undo)"""
        if self.path:
            self.path.pop()
            self.draw_path()

    def clear_map(self):
        if messagebox.askyesno("확인", "반야맨이야?"):
            self.path = []
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, "새로운 맵")
            self.draw_path()

    def save_map(self):
        if not self.path:
            messagebox.showwarning("경고", "경로가 비어있습니다.")
            return
            
        initial_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "maps")
        if not os.path.exists(initial_dir):
            os.makedirs(initial_dir)
            
        file_path = filedialog.asksaveasfilename(
            initialdir=initial_dir,
            title="맵 저장",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        
        if file_path:
            data = {
                "name": self.name_entry.get(),
                "path": self.path
            }
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                messagebox.showinfo("성공", "맵이 저장되었습니다!")
            except Exception as e:
                messagebox.showerror("오류", f"저장 중 오류 발생: {e}")

    def load_map(self):
        initial_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "maps")
        if not os.path.exists(initial_dir):
            os.makedirs(initial_dir)
            
        file_path = filedialog.askopenfilename(
            initialdir=initial_dir,
            title="맵 불러오기",
            filetypes=[("JSON files", "*.json")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if "path" in data:
                    self.path = data["path"]
                    self.name_entry.delete(0, tk.END)
                    self.name_entry.insert(0, data.get("name", "이름 없음"))
                    self.draw_path()
                else:
                    messagebox.showerror("오류", "유효한 맵 파일 형식이 아닙니다.")
            except Exception as e:
                messagebox.showerror("오류", f"불러오기 중 오류 발생: {e}")

def main():
    root = tk.Tk()
    # 윈도우 크기 및 위치 설정
    root.geometry(f"{GAME_GRID_COLS * VISUAL_GRID_SIZE + 40}x{GAME_GRID_ROWS * VISUAL_GRID_SIZE + 100}")
    app = MapEditor(root)
    try:
        root.mainloop()
    except KeyboardInterrupt:
        root.destroy()

if __name__ == "__main__":
    main()