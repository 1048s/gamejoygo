import tkinter as tk
from tkinter import filedialog, messagebox, font
import json
import os

# --- 설정 --- 2026-02-09
# 게임 내 설정과 맞춤 (mte_config.py 참고)
# 에디터 화면에 다 들어오도록 시각적 크기는 절반(40)으로 줄이고, 논리적 좌표는 그대로 사용
VISUAL_GRID_SIZE = 40 
GAME_GRID_COLS = 24  # 1920 / 80
GAME_GRID_ROWS = 14  # 1080 / 80

# --- 색상 테마 ---
COLOR_BG_MAIN = "#1E1E1E"       # 윈도우 배경
COLOR_BG_SIDEBAR = "#1E1E1E"    # 사이드바 배경
COLOR_BG_CANVAS = "#252525"     # 캔버스 배경
COLOR_GRID_LINE = "#3A3A3A"     # 그리드 선
COLOR_ACCENT_CYAN = "#00FFFF"   # 강조색 (시안)
COLOR_ACCENT_RED = "#FF3333"    # 강조색 (레드 - 주꾸다시)
COLOR_TEXT_MAIN = "#FFFFFF"     # 메인 텍스트
COLOR_TEXT_SUB = "#AAAAAA"      # 서브 텍스트
COLOR_BTN_NORMAL = "#333333"    # 버튼 기본 배경
COLOR_BTN_HOVER = "#444444"     # 버튼 호버 배경
COLOR_INPUT_BG = "#2C2C2C"      # 입력창 배경

class ModernButton(tk.Frame):
    """스타일리시한 커스텀 버튼"""
    def __init__(self, parent, text, command, width=140, height=40, bg_color=COLOR_BTN_NORMAL, hover_color=COLOR_BTN_HOVER, text_color=COLOR_TEXT_MAIN, accent_color=None):
        super().__init__(parent, bg=parent["bg"])
        self.command = command
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.accent_color = accent_color if accent_color else bg_color
        
        # 캔버스를 이용해 둥근 사각형 느낌 (실제로는 Flat 디자인)
        self.canvas = tk.Canvas(self, width=width, height=height, bg=self.bg_color, highlightthickness=0, cursor="hand2")
        self.canvas.pack()
        
        # 텍스트
        self.text_item = self.canvas.create_text(width/2, height/2, text=text, fill=self.text_color, font=("Malgun Gothic", 10, "bold"))
        
        # 테두리 (accent color가 있을 경우)
        if accent_color:
             self.canvas.create_rectangle(0, height-2, width, height, fill=accent_color, width=0)

        # 이벤트 바인딩
        self.canvas.bind("<Enter>", self.on_enter)
        self.canvas.bind("<Leave>", self.on_leave)
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

    def on_enter(self, e):
        self.canvas.config(bg=self.hover_color)

    def on_leave(self, e):
        self.canvas.config(bg=self.bg_color)

    def on_click(self, e):
        self.canvas.move(self.text_item, 1, 1)

    def on_release(self, e):
        self.canvas.move(self.text_item, -1, -1)
        if self.command:
            self.command()

class ModernEntry(tk.Entry):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.config(
            bg=COLOR_INPUT_BG,
            fg=COLOR_TEXT_MAIN,
            insertbackground=COLOR_TEXT_MAIN, # 커서 색상
            relief=tk.FLAT,
            bd=5 # 내부 여백 느낌
        )

class MapEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("케인 디펜스 맵 에디터")
        self.root.configure(bg=COLOR_BG_MAIN)
        
        self.path = [] # [[x, y], [x, y], ...]
        self.redo_stack = [] # Redo를 위한 스택
        self.map_name = "새로운 맵"
        
        # 폰트 설정
        self.title_font = font.Font(family="Malgun Gothic", size=16, weight="bold")
        self.label_font = font.Font(family="Malgun Gothic", size=10)
        
        # --- 레이아웃 ---
        # 1. 사이드바 (왼쪽)
        self.sidebar = tk.Frame(root, bg=COLOR_BG_SIDEBAR, width=220, padx=20, pady=20)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False) # 너비 고정

        # 타이틀
        tk.Label(self.sidebar, text="GAMEJOYGO\nEDITOR", font=self.title_font, bg=COLOR_BG_SIDEBAR, fg=COLOR_ACCENT_RED, justify=tk.LEFT).pack(anchor="w", pady=(0, 20))
        
        # 맵 이름 입력
        tk.Label(self.sidebar, text="MAP NAME", font=self.label_font, bg=COLOR_BG_SIDEBAR, fg=COLOR_TEXT_SUB).pack(anchor="w", pady=(0, 5))
        self.name_entry = ModernEntry(self.sidebar, width=20)
        self.name_entry.insert(0, self.map_name)
        self.name_entry.pack(fill=tk.X, pady=(0, 20))
        
        # 액션 버튼들
        tk.Label(self.sidebar, text="ACTIONS", font=self.label_font, bg=COLOR_BG_SIDEBAR, fg=COLOR_TEXT_SUB).pack(anchor="w", pady=(0, 5))
        
        ModernButton(self.sidebar, "불러오기 (LOAD)", self.load_map, width=180, hover_color="#555555").pack(pady=5)
        ModernButton(self.sidebar, "저장하기 (SAVE)", self.save_map, width=180, accent_color=COLOR_ACCENT_CYAN).pack(pady=5)
        ModernButton(self.sidebar, "되돌리기 (UNDO)", self.on_undo, width=180, hover_color="#555555").pack(pady=5)
        ModernButton(self.sidebar, "다시 실행 (REDO)", self.on_redo, width=180, hover_color="#555555").pack(pady=5)
        
        # 구분선
        tk.Frame(self.sidebar, height=1, bg="#444444").pack(fill=tk.X, pady=20)
        
        ModernButton(self.sidebar, "주꾸다시 (CLEAR)", self.clear_map, width=180, bg_color="#3E1E1E", hover_color="#5E1E1E", text_color="#FF9999", accent_color=COLOR_ACCENT_RED).pack(pady=5)
        
        # 사용법 안내
        tk.Label(self.sidebar, text="CONTROLS", font=self.label_font, bg=COLOR_BG_SIDEBAR, fg=COLOR_TEXT_SUB).pack(anchor="w", pady=(30, 5))
        info_text = "• 좌클릭: 경로 추가\n• 우클릭: 실행 취소\n• 자동 저장 없음"
        tk.Label(self.sidebar, text=info_text, font=("Malgun Gothic", 9), bg=COLOR_BG_SIDEBAR, fg="#888888", justify=tk.LEFT).pack(anchor="w")


        # 2. 메인 캔버스 영역 (오른쪽)
        self.content_area = tk.Frame(root, bg=COLOR_BG_MAIN, padx=20, pady=20)
        self.content_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 캔버스 테두리 효과를 위한 프레임
        canvas_border = tk.Frame(self.content_area, bg=COLOR_ACCENT_CYAN, padx=1, pady=1)
        canvas_border.pack()

        canvas_w = GAME_GRID_COLS * VISUAL_GRID_SIZE
        canvas_h = GAME_GRID_ROWS * VISUAL_GRID_SIZE
        self.canvas = tk.Canvas(canvas_border, width=canvas_w, height=canvas_h, bg=COLOR_BG_CANVAS, highlightthickness=0)
        self.canvas.pack()
        
        # 이벤트 바인딩
        self.canvas.bind("<Button-1>", self.on_left_click)
        self.canvas.bind("<Button-3>", self.on_right_click)
        
        self.draw_grid()

    def draw_grid(self):
        """격자 무늬 그리기 (다크 테마)"""
        w = int(self.canvas['width'])
        h = int(self.canvas['height'])
        
        self.canvas.delete("grid_line")
        
        # 수직선
        for x in range(0, w, VISUAL_GRID_SIZE):
            self.canvas.create_line(x, 0, x, h, fill=COLOR_GRID_LINE, tags="grid_line")
        # 수평선
        for y in range(0, h, VISUAL_GRID_SIZE):
            self.canvas.create_line(0, y, w, y, fill=COLOR_GRID_LINE, tags="grid_line")

    def draw_path(self):
        """현재 경로 그리기 (네온 스타일)"""
        self.canvas.delete("path_element") # 기존 경로 요소 삭제
        
        if not self.path:
            return

        # 1. 선 그리기 (네온 효과)
        if len(self.path) > 1:
            points = []
            for p in self.path:
                cx = p[0] * VISUAL_GRID_SIZE + VISUAL_GRID_SIZE // 2
                cy = p[1] * VISUAL_GRID_SIZE + VISUAL_GRID_SIZE // 2
                points.extend([cx, cy])
            
            # 발광 효과 (두껍고 반투명한 선을 아래에 깔기) - tkinter canvas는 알파 지원이 제한적이니 두꺼운 어두운 색으로 대체하거나 생략
            # 메인 선
            self.canvas.create_line(points, fill=COLOR_ACCENT_CYAN, width=4, capstyle=tk.ROUND, joinstyle=tk.ROUND, tags="path_element")
            # 화살표 (마지막 두 점만 사용)
            if len(points) >= 4:
                self.canvas.create_line(points[-4:], fill=COLOR_ACCENT_CYAN, width=4, arrow=tk.LAST, tags="path_element")

        # 2. 노드(점) 그리기
        for i, p in enumerate(self.path):
            cx = p[0] * VISUAL_GRID_SIZE + VISUAL_GRID_SIZE // 2
            cy = p[1] * VISUAL_GRID_SIZE + VISUAL_GRID_SIZE // 2
            r = 8
            
            fill_color = COLOR_BG_CANVAS
            outline_color = COLOR_ACCENT_CYAN
            text_color = COLOR_TEXT_MAIN
            
            if i == 0: # 시작점
                outline_color = "#00FF00" 
                fill_color = "#003300"
            elif i == len(self.path) - 1: # 끝점
                outline_color = "#FF3333"
                fill_color = "#330000"
            
            # 노드 원
            self.canvas.create_oval(cx-r, cy-r, cx+r, cy+r, fill=fill_color, outline=outline_color, width=2, tags="path_element")
            
            # 인덱스 텍스트 (원래 위치: 노드 위쪽)
            self.canvas.create_text(cx, cy-15, text=str(i), fill=COLOR_TEXT_MAIN, font=("Arial", 8), tags="path_element")
            
            if i == 0: 
               self.canvas.create_text(cx, cy, text="S", fill=outline_color, font=("Arial", 8, "bold"), tags="path_element")
            elif i == len(self.path) - 1:
               self.canvas.create_text(cx, cy, text="E", fill=outline_color, font=("Arial", 8, "bold"), tags="path_element")

    def on_left_click(self, event):
        """경로 추가"""
        gx = event.x // VISUAL_GRID_SIZE
        gy = event.y // VISUAL_GRID_SIZE
        
        # 범위 체크
        if 0 <= gx < GAME_GRID_COLS and 0 <= gy < GAME_GRID_ROWS:
            self.path.append([gx, gy])
            self.redo_stack.clear() # 새로운 행동 시 레드 스택 초기화
            self.draw_path()

    def on_right_click(self, event):
        self.on_undo()

    def on_undo(self):
        """마지막 경로 삭제 (Undo)"""
        if self.path:
            pos = self.path.pop()
            self.redo_stack.append(pos)
            self.draw_path()

    def on_redo(self):
        """삭제된 경로 복구 (Redo)"""
        if self.redo_stack:
            pos = self.redo_stack.pop()
            self.path.append(pos)
            self.draw_path()

    def clear_map(self):
        # 다크 테마 메시지 박스는 구현이 복잡하므로 기본 메시지 박스 사용
        if messagebox.askyesno("확인", "정말로 모든 경로를 지우시겠습니까?\n(반야맨이야?)"):
            self.path = []
            self.redo_stack = []
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
                messagebox.showinfo("성공", "맵이 쌈@뽕하게 저장되었습니다!")
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
                    self.redo_stack = [] # 불러오기 시 Redo 스택 초기화
                    self.name_entry.delete(0, tk.END)
                    self.name_entry.insert(0, data.get("name", "이름 없음"))
                    self.draw_path()
                else:
                    messagebox.showerror("오류", "유효한 맵 파일 형식이 아닙니다.")
            except Exception as e:
                messagebox.showerror("오류", f"불러오기 중 오류 발생: {e}")

def main():
    root = tk.Tk()
    # 윈도우 크기 자동 계산 (사이드바 220 + 캔버스 너비 + 여백)
    window_w = 220 + (GAME_GRID_COLS * VISUAL_GRID_SIZE) + 60
    window_h = (GAME_GRID_ROWS * VISUAL_GRID_SIZE) + 60
    
    # 화면 중앙 배치
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    x = (screen_w - window_w) // 2
    y = (screen_h - window_h) // 2
    
    root.geometry(f"{window_w}x{window_h}+{x}+{y}")
    root.resizable(False, False)
    
    app = MapEditor(root)
    try:
        root.mainloop()
    except KeyboardInterrupt:
        root.destroy()

if __name__ == "__main__":
    main()