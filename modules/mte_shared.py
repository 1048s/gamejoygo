import pygame
import math
import json
import socket
import threading
from .mte_config import *
from . import mte_config
from .mte_object import *
from . import mte_object

# --- 마리오카트 8 스타일 버튼 클래스 ---
class MK8Button:
    def __init__(self, x, y, w, h, text, color, text_color=WHITE):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.base_color = color
        self.text_color = text_color
        self.skew = 30 # 기울기 정도
        self.hover_scale = 1.05
        
    def draw(self, surface, mx, my):
        is_hover = self.rect.collidepoint(mx, my)
        
        # 색상 및 크기 계산
        color = (min(255, self.base_color[0]+40), min(255, self.base_color[1]+40), min(255, self.base_color[2]+40)) if is_hover else self.base_color
        
        # 평행사변형 좌표 계산 (오른쪽으로 기울어짐)
        #  /  /
        points = [
            (self.rect.x + self.skew, self.rect.y),
            (self.rect.x + self.rect.w + self.skew, self.rect.y),
            (self.rect.x + self.rect.w, self.rect.y + self.rect.h),
            (self.rect.x, self.rect.y + self.rect.h)
        ]
        
        # 그림자 (약간 아래로)
        shadow_points = [(p[0]+5, p[1]+5) for p in points]
        pygame.draw.polygon(surface, (0,0,0,100), shadow_points)
        
        # 본체
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, WHITE, points, 3) # 테두리
        
        # 텍스트 (기울기에 맞춰 중앙 정렬 보정)
        txt_surf = get_text_surface(self.text, Fonts.BTN_LARGE, self.text_color)
        center_x = self.rect.x + self.rect.w // 2 + self.skew // 2
        center_y = self.rect.y + self.rect.h // 2
        surface.blit(txt_surf, (center_x - txt_surf.get_width()//2, center_y - txt_surf.get_height()//2))

# --- 유틸리티 함수 ---
def draw_text_with_outline(surface, text, font, pos, text_color, outline_color):
    # [성능 개선] 텍스트와 외곽선을 미리 합성한 후 캐시하여 매 프레임 반복 렌더링 방지
    key = ("outline", text, font, text_color, outline_color)
    if key not in TEXT_CACHE:
        text_surf = get_text_surface(text, font, text_color)
        outline_surf = get_text_surface(text, font, outline_color)
        
        w, h = text_surf.get_size()
        # 외곽선 두께(1px)를 고려하여 2px 더 큰 서피스 생성
        composite_surf = pygame.Surface((w + 2, h + 2), pygame.SRCALPHA)
        
        # 8방향으로 외곽선 blit
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0: continue
                composite_surf.blit(outline_surf, (1 + dx, 1 + dy))
        
        # 중앙에 텍스트 blit
        composite_surf.blit(text_surf, (1, 1))
        TEXT_CACHE[key] = composite_surf

    surface.blit(TEXT_CACHE[key], pos)

# --- 채팅 관리 클래스 (Pygame 기반) ---
class PygameChatBox:
    def __init__(self, nickname_getter=None):
        self.gm = None
        self.width = 400
        self.height = 250
        self.x = 20
        self.messages = [] # (text, color)
        self.input_text = ""
        self.is_active = False
        self.cursor_visible = True
        self.last_cursor_toggle = 0
        self.font = Fonts.BTN_SMALL # 18px
        self.socket = None
        self.connect_thread = None
        self.buffer = ""
        self.nickname_getter = nickname_getter
        
        # 서버 설정 (기본값)
        self.server_ip = '127.0.0.1' 
        self.server_port = 12345

    def set_network_info(self, ip, port):
        self.server_ip = ip
        self.server_port = int(port)

    def get_nickname(self):
         if self.nickname_getter:
             return self.nickname_getter()
         return "Player"

    def connect(self):
        """서버에 연결을 시도합니다."""
        if self.socket: return
        def _connect():
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.server_ip, self.server_port))
                self.add_message("[시스템] 서버에 연결되었습니다.", GREEN)
                self.send_json({"type": "MATCH", "nickname": self.get_nickname()})
                # 수신 스레드 시작
                threading.Thread(target=self.receive_loop, daemon=True).start()
            except Exception as e:
                self.add_message(f"[시스템] 서버 연결 실패: {e}", RED)
                self.socket = None
        self.connect_thread = threading.Thread(target=_connect, daemon=True)
        self.connect_thread.start()

    def receive_loop(self):
        while self.socket:
            try:
                data = self.socket.recv(4096)
                if not data: break
                self.buffer += data.decode('utf-8')
                while '\n' in self.buffer:
                    line, self.buffer = self.buffer.split('\n', 1)
                    if not line.strip(): continue
                    try:
                        pkt = json.loads(line)
                        self.handle_packet(pkt)
                    except json.JSONDecodeError:
                        self.add_message(line, WHITE)
            except:
                break
        self.add_message("[시스템] 서버와 연결이 끊어졌습니다.", RED)
        self.socket = None
        if self.gm and self.gm.is_online:
            self.gm.mode = STATE_MENU # STATE_MAIN_MENU -> STATE_MENU (mte_config safe import)

    def handle_packet(self, pkt):
        ptype = pkt.get("type")
        if ptype == "CHAT":
            self.add_message(pkt.get("msg"), WHITE)
        elif ptype == "START":
            if self.gm: self.gm.start_online_game(pkt.get("map", 0), pkt.get("opponent", "Unknown"))
        elif ptype == "SPAWN":
            if self.gm: self.gm.queue_spawn(pkt.get("mob"))
        elif ptype == "WIN":
            if self.gm: self.gm.mode = STATE_WIN
        elif ptype == "WAIT":
            self.add_message("[시스템] 대전 상대를 찾는 중입니다...", YELLOW)
        elif ptype == "HP":
            if self.gm:
                self.gm.update_opponent_hp(pkt.get("hp"), pkt.get("max_hp"))
        elif ptype == "TIME":
            if self.gm:
                self.gm.sync_time(pkt)

    def disconnect(self):
        if self.socket:
            try:
                self.socket.close()
            except: pass
            self.socket = None

    def send_json(self, data):
        if self.socket:
            try:
                msg = json.dumps(data) + "\n"
                self.socket.send(msg.encode('utf-8'))
            except: pass

    def add_message(self, text, color=WHITE):
        self.messages.append((text, color))
        if len(self.messages) > 10:
            self.messages.pop(0)
            
    def open_chat_popup(self):
        """채팅 입력을 위한 tkinter 팝업을 엽니다."""
        
        try:
            import tkinter as tk
            from tkinter import simpledialog
            
            # tkinter 루트가 없으면 임시 생성
            root = tk.Tk()
            root.withdraw() # 메인 창 숨김
            
            # 화면 중앙 계산
            ws = root.winfo_screenwidth()
            hs = root.winfo_screenheight()
            x = (ws/2) - (300/2)
            y = (hs/2) - (150/2)
            root.geometry(f"+{int(x)}+{int(y)}")

            msg = simpledialog.askstring("채팅 입력", "메시지를 입력하세요:", parent=root)
            root.destroy()
            
            if msg and msg.strip():
                formatted_msg = f"{self.get_nickname()}: {msg}"
                self.add_message(formatted_msg, YELLOW)
                self.send_json({"type": "CHAT", "msg": formatted_msg})
                
        except Exception as e:
            print(f"Chat popup error: {e}")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if self.gm and self.gm.is_online:
                     self.open_chat_popup()
                return True
        return False

    def draw(self, surface):
        current_y = RESOLUTION[1] - self.height - 20
        
        # 메시지 목록
        for i, (msg, color) in enumerate(self.messages):
            msg_y = current_y + self.height - 40 - (len(self.messages) - 1 - i) * 22
            draw_text_with_outline(surface, msg, self.font, (self.x + 5, msg_y), color, BLACK)
            
    def update(self):
        pass # Pygame version doesn't need explicit update in main loop usually, but for API compatibility

    def destroy(self):
        pass # Pygame version doesn't need to destroy window

# --- 게임 상태 관리 클래스 (Shared) ---
class GameManager:
    def __init__(self, chat_class=PygameChatBox):
        self.chat_cls = chat_class
        try:
           self.mode = STATE_MAP_SELECT # mte_config에 정의된 변수가 맞는지 확인 필요 main.py에는 STATE_MAP_SELECT = 2 라고 되어있음
        except:
           # Fallback defaults if constants are not in mte_config
           pass
           
        self.mode = 2 # STATE_MAP_SELECT
        self.gold = 300
        self.damage_level = 1
        self.hp_level = 1
        self.range_level = 1
        self.game_speed = 1
        self.virtual_elapsed_time = 0.0
        self.current_round = 1
        self.selected_tower_type = "PRINCESS"
        self.time_left = 0
        self.gif_frame_idx = 0
        self.round_gold_value = 15
        self.range_gold_val = 150
        self.damage_gold_val = 50
        self.hp_gold_val = 200
        self.enemies_to_spawn_this_round = 0
        self.enemies_spawned_this_round = 0
        self.enemies = []
        self.towers = []
        self.projectiles = []
        self.round_start_time = 0.0
        self.nexus = None
        self.shop_open = False
        self.jukku_confirm_open = False
        self.last_spawn_time = 0
        self.is_break_time = True
        self.shop_pos = [0, 0]
        self.is_dragging_shop = False
        self.drag_offset = [0, 0]
        self.show_skip_button = False
        self.ending_sound_played = False
        self.quit_confirm_open = False
        self.sell_confirm_open = False
        self.tower_to_sell = None
        self.boss_spawn_count = 0
        self.is_overtime = False
        self.overtime_start_time = 0
        self.enemy_path = []
        self.current_map_index = 0
        self.state_before_settings = 0 # STATE_PLAYING
        self.show_save_feedback_timer = 0
        self.save_confirm_open = False
        self.initial_settings = {}
        self.online_popup_timer = 0
        self.chat = None
        self.is_online = False
        self.spawn_queue = []
        self.opponent_hp = 100
        self.opponent_max_hp = 100
        self.opponent_nickname = "Unknown"
        self.last_hp_sent_time = 0
        self.online_confirm_open = False
        
        # available_maps is expected to be populated by main.py or loaded here.
        # It's better to pass maps in valid state or allow external assignment.
        self.available_maps = [] 

    def get_current_damage(self, tower_type):
        d = TOWER_DATA[tower_type]
        dmg = int(d["dmg"] * (1.4 ** (self.damage_level - 1)))
        if self.is_overtime: dmg = int(dmg * 1.5)
        return dmg

    def draw_online_popup(self, surface):
        if pygame.time.get_ticks() - self.online_popup_timer < 1500:
            text = Fonts.POPUP_TITLE.render("아직 조이는 중입니다!", True, RED)
            rect = text.get_rect(center=(RESOLUTION[0]//2, RESOLUTION[1]//2))
            
            # 배경 박스 (검은색 배경 + 흰색 테두리)
            bg_rect = rect.inflate(40, 20)
            pygame.draw.rect(surface, BLACK, bg_rect)
            pygame.draw.rect(surface, WHITE, bg_rect, 2)
            surface.blit(text, rect)

    def reset(self, target_state=0): # STATE_PLAYING
        self.is_online = False
        self.opponent_hp, self.opponent_max_hp = 100, 100
        # 온라인 모드면 치트 강제 비활성화
        is_cheat = mte_config.CHEAT_MODE and not self.is_online
        self.gold = 999999 if is_cheat else 300
        self.round_gold_value = 15
        self.damage_level, self.hp_level, self.range_level, self.game_speed, self.virtual_elapsed_time, self.current_round = 1, 1, 1, 1, 0.0, 1
        self.damage_gold_val, self.hp_gold_val, self.range_gold_val = 50, 200, 150
        self.time_left = 10 + (self.current_round * 5)
        self.round_start_time, self.enemies, self.towers, self.projectiles = 0.0, [], [], []
        self.mode, self.shop_open, self.jukku_confirm_open, self.selected_tower_type, self.gif_frame_idx = target_state, False, False, "PRINCESS", 0
        
        # Cleanup old chat if exists
        if self.chat and hasattr(self.chat, 'destroy'):
            self.chat.destroy()

        # Initialize new ChatBox
        self.chat = self.chat_cls()
        self.chat.gm = self
        
        # 현재 선택된 맵 경로 로드
        if self.available_maps:
            self.current_map_index = self.current_map_index % len(self.available_maps)
            raw_path = self.available_maps[self.current_map_index]["path"]
            
            # Handle different path formats (simple list vs dict)
            self.enemy_path = []
            for p in raw_path:
                if isinstance(p, dict):
                    self.enemy_path.append(p) # Already parsed format ? No, mte_object uses {'pos':..., 'props':...}
                                              # But external raw_path might be [[x,y], [x,y]] or [[x,y,props]]
                elif isinstance(p, list) or isinstance(p, tuple):
                     gx, gy = p[0], p[1]
                     props = p[2] if len(p) > 2 else {"speed": 1.0, "type": "NORMAL"}
                     self.enemy_path.append({"pos": get_c(gx, gy), "props": props})
                
        else:
            self.enemy_path = []
        
        self.last_spawn_time, self.is_break_time = 0, True
        if self.enemy_path:
             # building_image need to be available globally or imported
             # assuming imports are working from mte_object or passed manually. 
             # But Image loading happens in main usually with resource_path. 
             # We might need a placeholder or ensure mte_config/objects has it.
             # Nexus creation usually expects an image.
             try:
                # We try to create Nexus. If image is not passed, it might use rect fallback
                # mte_object.Nexus allows img=None
                self.nexus = Nexus(self.enemy_path[-1]["pos"], None) 
             except:
                self.nexus = None
        else:
             self.nexus = None

        self.shop_pos, self.is_dragging_shop, self.drag_offset = [(RESOLUTION[0] - 650) // 2, int(RESOLUTION[1] * 0.15)], False, [0, 0]
        self.ending_sound_played, self.quit_confirm_open, self.sell_confirm_open, self.tower_to_sell, self.boss_spawn_count = False, False, False, None, 0
        self.is_overtime, self.overtime_start_time, self.show_skip_button, self.enemies_to_spawn_this_round, self.enemies_spawned_this_round = False, 0, False, 0, 0

    def start_online_game(self, map_idx, opponent_name="Unknown"):
        self.reset(STATE_PLAYING)
        self.is_online = True
        self.current_map_index = map_idx
        self.opponent_nickname = opponent_name
        if self.available_maps:
            raw_path = self.available_maps[self.current_map_index]["path"]
            self.enemy_path = []
            for p in raw_path:
                if isinstance(p, dict): self.enemy_path.append(p)
                else:
                    gx, gy = p[0], p[1]
                    props = p[2] if len(p) > 2 else {"speed": 1.0, "type": "NORMAL"}
                    self.enemy_path.append({"pos": get_c(gx, gy), "props": props})

            if self.nexus:
                # 딕셔너리 구조로 변경되었으므로 pos 접근 방식 수정
                self.nexus.rect = pygame.Rect(0,0,120,120)
                self.nexus.rect.center = self.enemy_path[-1]["pos"]
                
        # 치트 모드 재설정 (온라인이라 꺼짐)
        self.gold = 300
        
    def sync_time(self, pkt):
        # 서버로부터 시간 동기화
        self.current_round = pkt.get("round", 1)
        self.is_break_time = pkt.get("is_break", True)
        self.time_left = pkt.get("time_left", 0)
        # 라운드 변경 감지 시 BGM 변경 등 추가 로직 가능

    def queue_spawn(self, mob_type):
        self.spawn_queue.append(mob_type)

    def update_opponent_hp(self, hp, max_hp):
        self.opponent_hp = hp
        self.opponent_max_hp = max_hp

    def send_mob(self, mob_type):
        cost = 0
        if mob_type == "SMALL": cost = 200
        elif mob_type == "LARGE": cost = 500
        elif mob_type == "BOSS": cost = 2000
        
        if self.gold >= cost:
            self.gold -= cost
            if self.chat:
                self.chat.send_json({"type": "SPAWN", "mob": mob_type})
                # Check if ChatBox supports add_message with color (Pygame version does)
                if hasattr(self.chat, 'add_message'):
                     self.chat.add_message(f"[시스템] {mob_type} 공격을 보냈습니다!", CYAN)
