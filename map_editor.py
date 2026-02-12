import tkinter as tk
from tkinter import filedialog, messagebox, font
import json
import os

# --- 설정 --- 2026-02-09
# 게임 내 설정과 맞춤 (mte_config.py 참고)
# 논리적 좌표는 그대로 사용, 시각적 크기는 동적으로 계산
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
        
        self.cell_size = 40 # 기본 셀 크기 (동적으로 변경됨)

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
        canvas_border.pack(fill=tk.BOTH, expand=True) # 채우기

        # 캔버스 생성 (초기 크기는 임의 지정, 나중에 resize 이벤트로 조정됨)
        self.canvas = tk.Canvas(canvas_border, bg=COLOR_BG_CANVAS, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 이벤트 바인딩
        self.canvas.bind("<Configure>", self.on_resize)
        self.canvas.bind("<Button-1>", self.on_left_click)
        self.canvas.bind("<ButtonRelease-1>", self.on_left_release) # 드래그 등 방지용, 혹은 확장을 위해
        self.canvas.bind("<Button-3>", self.on_right_click)
        
        self.draw_grid()

        # 3. 속성 편집 패널 (사이드바 하단에 추가)
        # 평소엔 숨겨져 있다가 노드 선택 시 표시
        self.props_frame = tk.Frame(self.sidebar, bg=COLOR_BG_SIDEBAR)
        self.props_frame.pack(fill=tk.X, pady=20)
        
        tk.Frame(self.props_frame, height=1, bg="#444444").pack(fill=tk.X, pady=(0, 10))
        tk.Label(self.props_frame, text="NODE PROPERTIES", font=self.label_font, bg=COLOR_BG_SIDEBAR, fg=COLOR_ACCENT_CYAN).pack(anchor="w", pady=(0, 5))
        
        # 속도 입력
        tk.Label(self.props_frame, text="Speed Multiplier:", font=("Malgun Gothic", 9), bg=COLOR_BG_SIDEBAR, fg=COLOR_TEXT_SUB).pack(anchor="w")
        self.speed_entry = ModernEntry(self.props_frame)
        self.speed_entry.pack(fill=tk.X, pady=(0, 10))
        
        # 타입 선택 (Radio Button 스타일 대신 버튼으로 구현하거나 콤보박스 사용)
        # 여기서는 간단히 텍스트 입력으로 처리하거나 토글 버튼 사용
        
        # 적용 버튼
        ModernButton(self.props_frame, "APPLY", self.apply_props, width=180, bg_color="#004444", hover_color="#006666", text_color="#00FFFF").pack(pady=5)

        self.props_frame.pack_forget() # 초기엔 숨김
        self.selected_node_index = -1

    def on_resize(self, event):
        """창 크기 변경 시 호출"""
        w = event.width
        h = event.height
        
        if w < 10 or h < 10: return

        # 그리드 셀 크기 재계산 (화면에 꽉 차게)
        # 가로, 세로 비율 중 더 타이트한 쪽을 기준으로 맞춤 (비율 유지)
        cell_w = w / GAME_GRID_COLS
        cell_h = h / GAME_GRID_ROWS
        
        self.cell_size = min(cell_w, cell_h)
        
        self.draw_grid()
        self.draw_path()

    def draw_grid(self):
        """격자 무늬 그리기 (다크 테마)"""
        self.canvas.delete("grid_line")
        
        w = GAME_GRID_COLS * self.cell_size
        h = GAME_GRID_ROWS * self.cell_size
        
        # 수직선
        for x in range(GAME_GRID_COLS + 1):
            px = x * self.cell_size
            self.canvas.create_line(px, 0, px, h, fill=COLOR_GRID_LINE, tags="grid_line")
            
        # 수평선
        for y in range(GAME_GRID_ROWS + 1):
            py = y * self.cell_size
            self.canvas.create_line(0, py, w, py, fill=COLOR_GRID_LINE, tags="grid_line")

    def draw_path(self):
        """현재 경로 그리기 (네온 스타일)"""
        self.canvas.delete("path_element") # 기존 경로 요소 삭제
        
        if not self.path:
            return

        # 1. 선 그리기 (네온 효과)
        if len(self.path) > 1:
            points = []
            for p in self.path:
                cx = p[0] * self.cell_size + self.cell_size // 2
                cy = p[1] * self.cell_size + self.cell_size // 2
                points.extend([cx, cy])
            
            # 메인 선
            self.canvas.create_line(points, fill=COLOR_ACCENT_CYAN, width=4, capstyle=tk.ROUND, joinstyle=tk.ROUND, tags="path_element")
            # 화살표 (마지막 두 점만 사용)
            if len(points) >= 4:
                self.canvas.create_line(points[-4:], fill=COLOR_ACCENT_CYAN, width=4, arrow=tk.LAST, tags="path_element")

        # 2. 노드(점) 그리기
        for i, p in enumerate(self.path):
            cx = p[0] * self.cell_size + self.cell_size // 2
            cy = p[1] * self.cell_size + self.cell_size // 2
            r = self.cell_size * 0.25 # 약간 키움
            
            # 속성 읽기 (하위 호환성)
            props = p[2] if len(p) > 2 else {"speed": 1.0, "type": "NORMAL"}
            
            fill_color = COLOR_BG_CANVAS
            outline_color = COLOR_ACCENT_CYAN
            text_color = COLOR_TEXT_MAIN
            width = 2
            
            # 속성에 따른 시각화
            if props.get("speed", 1.0) > 1.0: # 가속
                outline_color = "#FFFF00" # 노랑
                text_color = "#FFFF00"
            elif props.get("speed", 1.0) < 1.0: # 감속
                outline_color = "#0088FF" # 파랑
                text_color = "#0088FF"
                
            if i == 0: # 시작점
                outline_color = "#00FF00" 
                fill_color = "#003300"
            elif i == len(self.path) - 1: # 끝점
                outline_color = "#FF3333"
                fill_color = "#330000"
            
            # 선택된 노드 하이라이트
            if hasattr(self, 'selected_node_index') and self.selected_node_index == i:
                fill_color = "#FFFFFF"
                width = 4
                r *= 1.2
            
            # 노드 원
            self.canvas.create_oval(cx-r, cy-r, cx+r, cy+r, fill=fill_color, outline=outline_color, width=width, tags="path_element")
            
            # 정보 표시 (속성 등)
            info_txt = str(i)
            if props.get("speed", 1.0) != 1.0:
                info_txt += f"\n(x{props['speed']})"
                
            font_size = int(max(8, self.cell_size * 0.25))
            self.canvas.create_text(cx, cy - r - 10, text=info_txt, fill=text_color, font=("Arial", font_size), tags="path_element", justify=tk.CENTER)
            
            if i == 0: 
               self.canvas.create_text(cx, cy, text="S", fill=outline_color, font=("Arial", font_size, "bold"), tags="path_element")
            elif i == len(self.path) - 1:
               self.canvas.create_text(cx, cy, text="E", fill=outline_color, font=("Arial", font_size, "bold"), tags="path_element")

    def on_left_click(self, event):
        """경로 추가 또는 노드 선택"""
        if self.cell_size <= 0: return
        gx = int(event.x // self.cell_size)
        gy = int(event.y // self.cell_size)
        
        # 범위 체크
        if 0 <= gx < GAME_GRID_COLS and 0 <= gy < GAME_GRID_ROWS:
            # 기존 노드 선택 확인 (노드 위에 클릭했는지)
            for i, p in enumerate(self.path):
                if p[0] == gx and p[1] == gy:
                    self.select_node(i)
                    return

            # 새 노드 추가 (속성 포함: [x, y, props])
            default_props = {"speed": 1.0, "type": "NORMAL"}
            self.path.append([gx, gy, default_props])
            self.redo_stack.clear() # 새로운 행동 시 레드 스택 초기화
            self.select_node(len(self.path) - 1) # 방금 추가한 노드 선택
            self.draw_path()

    def select_node(self, index):
        """노드 선택 및 속성 표시"""
        self.selected_node_index = index
        self.update_sidebar_props()
        self.draw_path()

    def update_sidebar_props(self):
        """사이드바에 현재 선택된 노드의 속성 표시"""
        if 0 <= self.selected_node_index < len(self.path):
            p = self.path[self.selected_node_index]
            props = p[2] if len(p) > 2 else {"speed": 1.0, "type": "NORMAL"}
            
            self.props_frame.pack(fill=tk.X, pady=20) # 패널 보이기
            
            self.speed_entry.delete(0, tk.END)
            self.speed_entry.insert(0, str(props.get("speed", 1.0)))
        else:
            self.props_frame.pack_forget()

    def apply_props(self):
        """입력된 속성을 선택된 노드에 적용"""
        if 0 <= self.selected_node_index < len(self.path):
            try:
                speed = float(self.speed_entry.get())
                # 값 검증
                speed = max(0.1, min(speed, 5.0)) # 0.1 ~ 5.0 배속 제한
                
                p = self.path[self.selected_node_index]
                
                # 기존 속성 가져오기 (없으면 생성)
                if len(p) < 3: p.append({})
                
                p[2]["speed"] = speed
                # p[2]["type"] = ... (추후 확장)
                
                self.draw_path() # 다시 그리기 (색상 등 업데이트)
                messagebox.showinfo("알림", "속성이 적용되었습니다.")
                
            except ValueError:
                messagebox.showerror("오류", "유효한 숫자를 입력하세요.")

    def on_left_release(self, event):
        pass

    def on_right_click(self, event):
        self.on_undo()

    def on_undo(self):
        """마지막 경로 삭제 (Undo)"""
        if self.path:
            pos = self.path.pop()
            self.redo_stack.append(pos)
            self.selected_node_index = len(self.path) - 1 # 이전 노드 선택
            if self.selected_node_index < 0:
                self.selected_node_index = -1
            self.update_sidebar_props()
            self.draw_path()

    def on_redo(self):
        """삭제된 경로 복구 (Redo)"""
        if self.redo_stack:
            pos = self.redo_stack.pop()
            self.path.append(pos)
            self.select_node(len(self.path) - 1)
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
    # 초기 윈도우 크기 (약간 넉넉하게)
    initial_cell_size = 40
    window_w = 220 + (GAME_GRID_COLS * initial_cell_size) + 40
    window_h = (GAME_GRID_ROWS * initial_cell_size) + 40
    
    # 화면 중앙 배치
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    x = (screen_w - window_w) // 2
    y = (screen_h - window_h) // 2
    
    root.geometry(f"{window_w}x{window_h}+{x}+{y}")
    root.resizable(True, True) # 창 크기 조절 가능하게 변경
    root.minsize(800, 600) # 최소 크기 지정
    
    app = MapEditor(root)
    try:
        root.mainloop()
    except KeyboardInterrupt:
        root.destroy()

if __name__ == "__main__":
    main()