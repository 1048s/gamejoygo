import random
import pygame
import sys
import math
import os
import argparse
from PIL import Image

# --- 실행 인수 처리 (치트 활성화) ---
parser = argparse.ArgumentParser()
parser.add_argument("--cheat", action="store_true", help="치트 모드를 활성화합니다.")
args = parser.parse_known_args()[0]
CHEAT_MODE = args.cheat

# --- 초기화 ---
pygame.init()
pygame.mixer.init()

# --- 리소스 경로 처리 함수 (빌드 시 필수) ---
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- 설정 및 전역 변수 ---
infoObject = pygame.display.Info()
RESOLUTION = (infoObject.current_w, infoObject.current_h)
FPS = 144
GRID_SIZE = 80 
damage_gold_val = 15
hp_gold_val = 200
range_gold_val = 150

F_DMG_PRINCESS = 10
F_DMG_DUCHESS = 5
F_DMG_CANON = 20
F_DMG_JINUTELLA = 3

BGM_VOL = 0.3
SFX_VOL = 0.5

STATE_START_SCREEN = -1
STATE_PLAYING = 0
STATE_AIGONAN = 1
game_state_mode = STATE_START_SCREEN

WHITE, BLACK, RED, BLUE, GREEN = (255, 255, 255), (0, 0, 0), (255, 0, 0), (0, 0, 255), (0, 255, 0)
YELLOW, PURPLE, CYAN = (255, 255, 0), (128, 0, 128), (0, 255, 255)
DARK_RED, GRAY = (150, 0, 0), (50, 50, 50)
PATH_COLOR = (200, 200, 200)
BROWN_ALPHA = (139, 69, 19, 120) 

# SCALED 플래그를 추가하여 최종 출력을 하드웨어 가속 처리 시도
display_surface = pygame.display.set_mode(RESOLUTION, pygame.FULLSCREEN | pygame.SCALED)
pygame.display.set_caption("케인 디펜스")
clock = pygame.time.Clock()

# --- 폰트 설정 ---
FONT_HP = pygame.font.SysFont("malgungothic", 16, bold=True)
FONT_SHOP_TITLE = pygame.font.SysFont("malgungothic", 30, bold=True) 
FONT_BTN_SMALL = pygame.font.SysFont("malgungothic", 18, bold=True)
FONT_BTN_LARGE = pygame.font.SysFont("malgungothic", 22, bold=True)
# [성능 개선] 게임 루프 내에서 폰트 객체를 생성하는 것을 방지하기 위해 미리 정의
FONT_COOLDOWN = pygame.font.SysFont("malgungothic", 14, bold=True)
FONT_UI = pygame.font.SysFont("malgungothic", 25, bold=True)
FONT_DMG_TEXT = pygame.font.SysFont("malgungothic", 15, bold=True)
FONT_TITLE = pygame.font.SysFont("malgungothic", 60, bold=True)
FONT_HELP = pygame.font.SysFont("malgungothic", 30)
FONT_GAMEOVER = pygame.font.SysFont("malgungothic", 100, bold=True)
FONT_POPUP_TITLE = pygame.font.SysFont("malgungothic", 30, bold=True)
FONT_CLEAR = pygame.font.SysFont("malgungothic", 100, True)

# --- 성능 최적화를 위한 캐시 ---
TEXT_CACHE = {}
RANGE_SURFACE_CACHE = {}

def get_text_surface(text, font, color):
    """렌더링된 텍스트 서피스를 캐시하여 반환합니다. GPU 가속을 위해 convert_alpha()를 사용합니다."""
    key = (text, font, color)
    if key not in TEXT_CACHE:
        TEXT_CACHE[key] = font.render(text, True, color).convert_alpha()
    return TEXT_CACHE[key]

def get_range_surface(radius, color):
    key = (radius, color)
    if key not in RANGE_SURFACE_CACHE:
        s = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
        pygame.draw.circle(s, color, (radius, radius), radius)
        RANGE_SURFACE_CACHE[key] = s
    return RANGE_SURFACE_CACHE[key]

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

def load_smart_image(base_path, size):
    for ext in ['.png', '.PNG', '.jpg', '.JPG']:
        full_path = resource_path(base_path + ext)
        if os.path.exists(full_path):
            try: return pygame.transform.scale(pygame.image.load(full_path).convert_alpha(), size)
            except: continue
    return None

def load_gif_frames_21_9(filename, target_width):
    path = resource_path(f"image/{filename}")
    frames = []
    target_height = int(target_width * 9 / 21)
    size = (target_width, target_height)
    if os.path.exists(path):
        with Image.open(path) as gif:
            for i in range(gif.n_frames):
                gif.seek(i); frame = gif.convert("RGBA")
                pygame_frame = pygame.image.fromstring(frame.tobytes(), frame.size, frame.mode)
                frames.append(pygame.transform.scale(pygame_frame, size))
    return frames

def load_sound(file_path):
    full_path = resource_path(file_path)
    if os.path.exists(full_path): 
        s = pygame.mixer.Sound(full_path); s.set_volume(SFX_VOL)
        return s
    return None

# --- 리소스 로드 ---
background_image = load_smart_image("image/yousuck", RESOLUTION)
building_image = load_smart_image("image/building", (120, 120))
mte21_image = load_smart_image("image/mte21", (800, 800))
mte22_image = load_smart_image("image/mte22", (800, 800))
aigonan_gif_frames = load_gif_frames_21_9("mte21.gif", RESOLUTION[0])
projectile_images = {
    "mte23": load_smart_image("image/mte23", (40, 40)),
    "mte24": load_smart_image("image/mte24", (40, 40)),
    "mte25": load_smart_image("image/mte25", (60, 60))
}
bgm_file = resource_path("sound/bgm.mp3")
if os.path.exists(bgm_file):
    pygame.mixer.music.load(bgm_file); pygame.mixer.music.set_volume(BGM_VOL); pygame.mixer.music.play(-1)
aigonan_sound, oh_sound, bbolong_sound = load_sound("sound/aigonan.mp3"), load_sound("sound/oh.mp3"), load_sound("sound/bbolong.mp3")

# --- 데이터 ---
TOWER_DATA = {
    "PRINCESS": {"name": "이걸 왜쏴 ㅋㅋ", "cost": 100, "range": 300, "dmg": F_DMG_PRINCESS, "cd": 20, "color": BLUE, "image_path": "image/uring1", "p_img": "mte23"},
    "DUCHESS": {"name": "집게이사장", "cost": 250, "range": 200, "dmg": F_DMG_DUCHESS, "cd": 5, "color": PURPLE, "image_path": "image/uring2", "p_img": "mte24"},
    "CANON": {"name": "-3000로베로스", "cost": 400, "range": 400, "dmg": F_DMG_CANON, "cd": 60, "color": CYAN, "image_path": "image/uring3", "p_img": "mte25"},
    "JINUTELLA": {"name": "지누텔라", "cost": 500, "range": 160, "dmg": F_DMG_JINUTELLA, "cd": 15, "color": YELLOW, "image_path": "image/mte20", "p_img": None}
}

def get_current_damage(tower_type):
    d = TOWER_DATA[tower_type]
    dmg = int(d["dmg"] * (1.4 ** (damage_level - 1)))
    if is_overtime: dmg = int(dmg * 1.5)
    return dmg

# --- 클래스 정의 ---
class Button:
    def __init__(self, x, y, w, h, text, color, val=None):
        self.rect = pygame.Rect(x, y, w, h); self.text, self.color, self.val = text, color, val
    def draw(self, surface, is_selected=False):
        pygame.draw.rect(surface, self.color, self.rect, border_radius=10)
        if is_selected: pygame.draw.rect(surface, WHITE, self.rect, 4, border_radius=10)
        font = FONT_BTN_SMALL if self.val else FONT_BTN_LARGE
        txt_surf = get_text_surface(self.text, font, WHITE)
        surface.blit(txt_surf, (self.rect.centerx - txt_surf.get_width()//2, self.rect.centery - txt_surf.get_height()//2))

class Nexus:
    def __init__(self, pos):
        self.image = building_image; self.rect = building_image.get_rect(center=pos) if building_image else pygame.Rect(pos[0]-60, pos[1]-60, 120, 120)
        self.max_hp = 10000; self.hp = 10000
        self.attack_timer = 0
        self.cd = int(TOWER_DATA["DUCHESS"]["cd"] / 0.7)
    def draw(self, surface):
        if self.image: surface.blit(self.image, self.rect)
        pygame.draw.rect(surface, RED, (self.rect.x, self.rect.y-30, 120, 10))
        pygame.draw.rect(surface, GREEN, (self.rect.x, self.rect.y-30, 120*(max(0, self.hp)/self.max_hp), 10))

class Enemy:
    def __init__(self, path, round_num, is_boss=False):
        self.path, self.target_idx, self.is_boss = path, 0, is_boss
        base_img = "image/mte2" if is_boss else f"image/mte{random.randint(2,15)}"
        size = (100, 100) if is_boss else (70, 70)
        self.image = load_smart_image(base_img, size); self.rect = pygame.Rect(0, 0, size[0], size[1]); self.rect.center = path[0]
        self.pos = pygame.Vector2(path[0])
        self.max_hp = (3000 if is_boss else 100) * (1.3**(round_num-1)); self.hp = self.max_hp; self.speed = 0.5 if is_boss else 1
    def move(self, dt, speed_mult):
        move_step = self.speed * speed_mult * (dt * 144)
        while move_step > 0 and self.target_idx < len(self.path):
            target = pygame.Vector2(self.path[self.target_idx])
            dir_vec = target - self.pos
            dist = dir_vec.length()
            if dist <= move_step:
                self.pos = target
                move_step -= dist
                self.target_idx += 1
            else:
                if dist > 0: self.pos += dir_vec.normalize() * move_step
                move_step = 0
        self.rect.center = (int(self.pos.x), int(self.pos.y))
    def draw(self, surface):
        if self.image: surface.blit(self.image, self.rect)
        pygame.draw.rect(surface, RED, (self.rect.x, self.rect.y-10, self.rect.width, 4))
        pygame.draw.rect(surface, GREEN, (self.rect.x, self.rect.y-10, self.rect.width*(max(0, self.hp)/self.max_hp), 4))
        hp_text = f"{int(self.hp)}"
        # [성능 개선] 텍스트 렌더링 결과를 캐시하여 사용
        txt_surf = get_text_surface(hp_text, FONT_HP, WHITE)
        shadow_surf = get_text_surface(hp_text, FONT_HP, BLACK)
        txt_pos_x = self.rect.centerx - txt_surf.get_width() // 2
        surface.blit(shadow_surf, (txt_pos_x + 1, self.rect.y - 29))
        surface.blit(txt_surf, (txt_pos_x, self.rect.y - 30))

class Projectile:
    def __init__(self, start_pos, target_enemy, dmg, img_key, speed=15):
        self.pos, self.target_enemy, self.dmg, self.speed, self.reached = pygame.Vector2(start_pos), target_enemy, dmg, speed, False
        self.image = projectile_images.get(img_key)
    def move(self, dt, game_speed):
        if not self.target_enemy or self.target_enemy.hp <= 0: self.reached = True; return
        tp = pygame.Vector2(self.target_enemy.rect.center); dir = (tp - self.pos); dist = dir.length()
        move_step = self.speed * game_speed * (dt * 144)
        if dist < move_step: self.target_enemy.hp -= self.dmg; self.reached = True
        elif dist > 0: self.pos += dir.normalize() * move_step
    def draw(self, surface):
        if self.image: surface.blit(self.image, self.image.get_rect(center=(int(self.pos.x), int(self.pos.y))))
        else: pygame.draw.circle(surface, YELLOW, (int(self.pos.x), int(self.pos.y)), 6)

class Tower:
    def __init__(self, x, y, tower_type):
        d = TOWER_DATA[tower_type]; self.type, self.cost = tower_type, d["cost"]
        self.image = load_smart_image(d["image_path"], (GRID_SIZE, GRID_SIZE))
        self.rect = pygame.Rect((x//GRID_SIZE)*GRID_SIZE, (y//GRID_SIZE)*GRID_SIZE, GRID_SIZE, GRID_SIZE)
        self.attack_timer, self.effect_timer = 0, 0 
    def draw(self, surface):
        if self.type == "JINUTELLA" and self.effect_timer > 0:
            rv = TOWER_DATA[self.type]["range"] + (range_level - 1) * 20
            es = get_range_surface(rv, BROWN_ALPHA) # [최적화] 매 프레임 Surface 생성 방지
            surface.blit(es, (self.rect.centerx-rv, self.rect.centery-rv))
        if self.image: surface.blit(self.image, self.rect)
        else: pygame.draw.rect(surface, TOWER_DATA[self.type]["color"], self.rect.inflate(-20,-20), border_radius=5)
        if self.attack_timer > 0:
            bw = GRID_SIZE * 0.8; fw = bw * (self.attack_timer / TOWER_DATA[self.type]["cd"])
            pygame.draw.rect(surface, GRAY, (self.rect.x + (GRID_SIZE-bw)//2, self.rect.y+5, bw, 6))
            pygame.draw.rect(surface, YELLOW, (self.rect.x + (GRID_SIZE-bw)//2, self.rect.y+5, fw, 6))
            # [성능 개선] 루프 내에서 폰트 객체 생성 및 렌더링 대신 캐시 사용
            cd_txt = get_text_surface(f"{self.attack_timer/60:.1f}s", FONT_COOLDOWN, BLACK)
            surface.blit(cd_txt, (self.rect.centerx - cd_txt.get_width()//2, self.rect.y + 12))

# --- 유틸리티 및 경로 ---
def get_c(gx, gy): return (gx * GRID_SIZE + GRID_SIZE // 2, gy * GRID_SIZE + GRID_SIZE // 2)
def is_on_path(pos, path, threshold=45):
    for i in range(len(path)-1):
        p1, p2, p3 = pygame.Vector2(path[i]), pygame.Vector2(path[i+1]), pygame.Vector2(pos); lp = p2-p1
        if lp.length() == 0: continue
        t = max(0, min(1, (p3-p1).dot(lp)/lp.length_squared()))
        if p3.distance_to(p1 + t*lp) < threshold: return True
    return False

enemy_path = [get_c(1,13), get_c(1,1), get_c(3,1), get_c(3,12), get_c(5,12), get_c(5,1), get_c(22,1), get_c(22,12), get_c(7,12), get_c(7,3), get_c(20,3), get_c(20,10), get_c(9,10), get_c(9,5), get_c(18,5), get_c(18,8), get_c(11,8)]

# --- 게임 리셋 ---
def reset_game():
    global gold, damage_level, hp_level, range_level, game_speed, virtual_elapsed_time, current_round, selected_tower_type, time_left, gif_frame_idx, round_gold_value, range_gold_val
    global enemies, towers, projectiles, round_start_time, game_state_mode, nexus, shop_open, jukku_confirm_open, last_spawn_time, is_break_time, shop_pos, is_dragging_shop, drag_offset, settings_open, settings_pos, is_dragging_settings, drag_offset_settings
    global ending_sound_played, quit_confirm_open, sell_confirm_open, tower_to_sell, boss_spawn_count
    global is_overtime, overtime_start_time
    gold = 999999 if CHEAT_MODE else 300
    round_gold_value = 15  # [복리 시스템] 마리당 지급 골드 초기값
    damage_level, hp_level, range_level, game_speed, virtual_elapsed_time, current_round = 1, 1, 1, 1, 0.0, 1
    range_gold_val = 150
    time_left = 10 + (current_round * 5)
    round_start_time, enemies, towers, projectiles = 0.0, [], [], []
    game_state_mode, shop_open, settings_open, jukku_confirm_open, selected_tower_type, gif_frame_idx = STATE_PLAYING, False, False, False, "PRINCESS", 0
    last_spawn_time, is_break_time, nexus = 0, True, Nexus(enemy_path[-1])
    shop_pos, is_dragging_shop, drag_offset = [(RESOLUTION[0] - 650) // 2, 100], False, [0, 0]
    settings_pos, is_dragging_settings, drag_offset_settings = [(RESOLUTION[0] - 450) // 2, (RESOLUTION[1] - 450) // 2], False, [0, 0]
    ending_sound_played, quit_confirm_open, sell_confirm_open, tower_to_sell, boss_spawn_count = False, False, False, None, 0
    is_overtime, overtime_start_time = False, 0
    if os.path.exists(bgm_file): pygame.mixer.music.load(bgm_file); pygame.mixer.music.set_volume(BGM_VOL); pygame.mixer.music.play(-1)

reset_game(); game_state_mode = STATE_START_SCREEN

start_btn = Button(RESOLUTION[0]//2 - 150, RESOLUTION[1]-150, 300, 80, "게 이 시 작 !", BLUE)

# --- 해상도 반응형 UI 위치 설정 ---
margin = 20
settings_btn_w, speed_btn_w, shop_btn_w = 160, 120, 180

settings_btn_x = RESOLUTION[0] - settings_btn_w - margin
speed_btn_x = settings_btn_x - speed_btn_w - margin
shop_btn_x = speed_btn_x - shop_btn_w - margin

open_shop_btn = Button(shop_btn_x, 20, shop_btn_w, 50, "상점 열기", BLUE)
open_settings_btn = Button(settings_btn_x, 20, settings_btn_w, 50, "설정 열기", GRAY)
speed_btn = Button(speed_btn_x, 20, speed_btn_w, 50, "배속: 1x", BLACK)

quit_btn = Button(RESOLUTION[0]-180, 20, 160, 50, "게이 종료", DARK_RED) # 엔딩 화면용
retry_btn = Button(RESOLUTION[0]//2 - 150, RESOLUTION[1]-180, 300, 80, "다시 조이기", BLUE)

# --- 메인 루프 ---
running = True
while running:
    dt = clock.tick(FPS) / 1000.0; dt = min(dt, 0.1) # [버그 수정] 렉 걸릴 때 순간이동 방지
    mx, my = pygame.mouse.get_pos(); gmx, gmy = (mx//GRID_SIZE)*GRID_SIZE, (my//GRID_SIZE)*GRID_SIZE
    can_place = (not is_on_path((gmx+GRID_SIZE//2, gmy+GRID_SIZE//2), enemy_path)) and (not any(t.rect.topleft == (gmx, gmy) for t in towers))
    
    shop_rect = pygame.Rect(shop_pos[0], shop_pos[1], 650, 500); sdb = pygame.Rect(shop_pos[0], shop_pos[1], 650, 60)
    close_shop_btn = Button(shop_pos[0] + 580, shop_pos[1] + 10, 60, 40, "X", GRAY)
    tower_btns = [Button(shop_pos[0]+25, shop_pos[1]+100, 140, 50, "이걸 왜쏴 ㅋㅋ", BLUE, "PRINCESS"), Button(shop_pos[0]+175, shop_pos[1]+100, 140, 50, "집게이사장", PURPLE, "DUCHESS"), Button(shop_pos[0]+325, shop_pos[1]+100, 140, 50, "-3000로베로스", BLACK, "CANON"), Button(shop_pos[0]+475, shop_pos[1]+100, 140, 50, "지누텔라", YELLOW, "JINUTELLA")]
    up_dmg_btn = Button(shop_pos[0]+30, shop_pos[1]+220, 280, 60, f"공격 강화 ({damage_gold_val}G)", RED)
    up_hp_btn = Button(shop_pos[0]+340, shop_pos[1]+220, 280, 60, f"체력 UP ({hp_gold_val}G)", GREEN)
    up_range_btn = Button(shop_pos[0]+30, shop_pos[1]+300, 590, 60, f"사거리 증가 ({range_gold_val}G)", CYAN)
    settings_rect = pygame.Rect(settings_pos[0], settings_pos[1], 450, 450)
    sdb_settings = pygame.Rect(settings_pos[0], settings_pos[1], 450, 60)
    close_settings_btn = Button(settings_pos[0] + 380, settings_pos[1] + 10, 60, 40, "X", GRAY)
    bgm_vol_down_btn = Button(settings_pos[0] + 240, settings_pos[1] + 80, 50, 50, "-", BLUE)
    bgm_vol_up_btn = Button(settings_pos[0] + 320, settings_pos[1] + 80, 50, 50, "+", RED)
    sfx_vol_down_btn = Button(settings_pos[0] + 240, settings_pos[1] + 150, 50, 50, "-", BLUE)
    sfx_vol_up_btn = Button(settings_pos[0] + 320, settings_pos[1] + 150, 50, 50, "+", RED)
    settings_jukku_btn = Button(settings_pos[0] + 30, settings_pos[1] + 230, 390, 60, "주꾸다시 (자폭)", DARK_RED)
    settings_quit_btn = Button(settings_pos[0] + 30, settings_pos[1] + 310, 390, 60, "게이 종료", DARK_RED)
    

    # --- 이벤트 처리 ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        if CHEAT_MODE and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F1: gold += 10000000
            if event.key == pygame.K_F2: damage_level += 5
            if event.key == pygame.K_F3: nexus.hp = nexus.max_hp
            if event.key == pygame.K_F4: enemies = []
            if event.key == pygame.K_F5: is_break_time = not is_break_time; current_round = current_round+1 if not is_break_time else current_round; round_start_time = virtual_elapsed_time; enemies = []

        if event.type == pygame.MOUSEBUTTONDOWN:
            if quit_confirm_open:
                qx, qy = (RESOLUTION[0]-500)//2, (RESOLUTION[1]-250)//2
                if pygame.Rect(qx+60, qy+140, 160, 60).collidepoint(mx, my): running = False
                elif pygame.Rect(qx+280, qy+140, 160, 60).collidepoint(mx, my): quit_confirm_open = False
                continue
            if sell_confirm_open:
                sx, sy = (RESOLUTION[0]-500)//2, (RESOLUTION[1]-250)//2
                if pygame.Rect(sx+60, sy+140, 160, 60).collidepoint(mx, my): 
                    if tower_to_sell in towers: gold += int(tower_to_sell.cost * 0.7); towers.remove(tower_to_sell)
                    sell_confirm_open, tower_to_sell = False, None
                elif pygame.Rect(sx+280, sy+140, 160, 60).collidepoint(mx, my): sell_confirm_open, tower_to_sell = False, None
                continue
            if game_state_mode == STATE_START_SCREEN and start_btn.rect.collidepoint(mx, my): game_state_mode = STATE_PLAYING; round_start_time = virtual_elapsed_time
            elif game_state_mode == STATE_PLAYING:
                if current_round > 40 and quit_btn.rect.collidepoint(mx, my): quit_confirm_open = True; continue
                if jukku_confirm_open:
                    px, py = (RESOLUTION[0]-500)//2, (RESOLUTION[1]-250)//2
                    if pygame.Rect(px+60, py+140, 160, 60).collidepoint(mx, my): pygame.mixer.music.stop(); game_state_mode = STATE_AIGONAN; jukku_confirm_open = False; (aigonan_sound.play() if aigonan_sound else None)
                    elif pygame.Rect(px+280, py+140, 160, 60).collidepoint(mx, my): jukku_confirm_open = False
                    continue
                if event.button == 3:
                    for t in towers:
                        if t.rect.collidepoint(mx, my): tower_to_sell, sell_confirm_open = t, True; break
                    continue
                if shop_open:
                    if close_shop_btn.rect.collidepoint(mx, my): shop_open = False; continue
                    if sdb.collidepoint(mx, my): is_dragging_shop, drag_offset = True, [shop_pos[0]-mx, shop_pos[1]-my]; continue
                    for b in tower_btns:
                        if b.rect.collidepoint(mx, my): selected_tower_type = b.val
                    if up_dmg_btn.rect.collidepoint(mx, my) and gold >= damage_gold_val: gold -= damage_gold_val; damage_level += 1; damage_gold_val = int(15 + damage_gold_val * 1.5)
                    if up_hp_btn.rect.collidepoint(mx, my) and gold >= hp_gold_val: gold -= hp_gold_val; hp_level += 1; nexus.max_hp += 5000; nexus.hp += 5000; hp_gold_val = int(200 + hp_gold_val * 1.5)
                    if up_range_btn.rect.collidepoint(mx, my) and gold >= range_gold_val: gold -= range_gold_val; range_level += 1; range_gold_val = int(150 + range_gold_val * 1.5)
                    if shop_rect.collidepoint(mx, my): continue
                if settings_open:
                    if close_settings_btn.rect.collidepoint(mx, my): settings_open = False; continue
                    if sdb_settings.collidepoint(mx, my): is_dragging_settings, drag_offset_settings = True, [settings_pos[0]-mx, settings_pos[1]-my]; continue
                    if bgm_vol_down_btn.rect.collidepoint(mx, my):
                        BGM_VOL = max(0.0, BGM_VOL - 0.1); pygame.mixer.music.set_volume(BGM_VOL)
                    if bgm_vol_up_btn.rect.collidepoint(mx, my):
                        BGM_VOL = min(1.0, BGM_VOL + 0.1); pygame.mixer.music.set_volume(BGM_VOL)
                    if sfx_vol_down_btn.rect.collidepoint(mx, my):
                        SFX_VOL = max(0.0, SFX_VOL - 0.1); [s.set_volume(SFX_VOL) for s in [aigonan_sound, oh_sound, bbolong_sound] if s]
                    if sfx_vol_up_btn.rect.collidepoint(mx, my):
                        SFX_VOL = min(1.0, SFX_VOL + 0.1); [s.set_volume(SFX_VOL) for s in [aigonan_sound, oh_sound, bbolong_sound] if s]
                    if settings_jukku_btn.rect.collidepoint(mx, my): jukku_confirm_open = True
                    if settings_quit_btn.rect.collidepoint(mx, my): quit_confirm_open = True
                    if settings_rect.collidepoint(mx, my): continue
                if open_shop_btn.rect.collidepoint(mx, my): shop_open = not shop_open
                elif open_settings_btn.rect.collidepoint(mx, my): settings_open = not settings_open
                elif speed_btn.rect.collidepoint(mx, my): game_speed = 2 if game_speed==1 else (4 if game_speed==2 else 1); speed_btn.text = f"배속: {game_speed}x"
                elif can_place and gold >= TOWER_DATA[selected_tower_type]["cost"]: towers.append(Tower(mx, my, selected_tower_type)); gold -= TOWER_DATA[selected_tower_type]["cost"]
            elif game_state_mode == STATE_AIGONAN and retry_btn.rect.collidepoint(mx, my): reset_game()
        if event.type == pygame.MOUSEBUTTONUP: is_dragging_shop, is_dragging_settings = False, False
        if event.type == pygame.MOUSEMOTION:
            if is_dragging_shop: shop_pos[0], shop_pos[1] = mx + drag_offset[0], my + drag_offset[1]
            if is_dragging_settings: settings_pos[0], settings_pos[1] = mx + drag_offset_settings[0], my + drag_offset_settings[1]

    # --- 업데이트 로직 ---
    if game_state_mode == STATE_PLAYING and not any([jukku_confirm_open, quit_confirm_open, sell_confirm_open]):
        virtual_elapsed_time += dt * game_speed; c_time = virtual_elapsed_time - round_start_time
        if current_round <= 40:
            if is_break_time:
                time_left = max(0, 15 - c_time)
                if time_left <= 0: 
                    is_break_time, round_start_time, last_spawn_time, boss_spawn_count = False, virtual_elapsed_time, virtual_elapsed_time, 0
                    if current_round > 1: round_gold_value = int(round_gold_value * 1.5) # [복리] 라운드 시작 시 가치 상승
            elif is_overtime:
                time_left = 0
                if not enemies or (virtual_elapsed_time - overtime_start_time >= 60):
                    is_overtime = False
                    is_break_time, current_round, round_start_time, gold = True, current_round+1, virtual_elapsed_time, gold+(100 * current_round)
            else:
                time_left = max(0, 45 - c_time)
                if current_round == 40:
                    if boss_spawn_count < 10 and virtual_elapsed_time - last_spawn_time > 2.0: enemies.append(Enemy(enemy_path, 40, True)); boss_spawn_count += 1; last_spawn_time = virtual_elapsed_time
                elif virtual_elapsed_time - last_spawn_time > max(0.4, 1.5 - current_round*0.05):
                    enemies.append(Enemy(enemy_path, current_round, (current_round%5==0 and not any(e.is_boss for e in enemies)))); last_spawn_time = virtual_elapsed_time
                if time_left <= 0:
                    if enemies:
                        is_overtime = True
                        overtime_start_time = virtual_elapsed_time
                    else:
                        is_break_time, current_round, round_start_time, gold = True, current_round+1, virtual_elapsed_time, gold+(100 * current_round)
                if not enemies and (virtual_elapsed_time - round_start_time > 2.0):
                    if current_round != 40 or (current_round == 40 and boss_spawn_count >= 10):
                        round_start_time = virtual_elapsed_time - 45
        
        for p in projectiles[:]:
            p.move(dt, game_speed)
            if p.reached: projectiles.remove(p)
        for t in towers:
            if t.effect_timer > 0: t.effect_timer -= 1 * game_speed * (dt * 144)
            if t.attack_timer > 0: t.attack_timer -= 1 * game_speed * (dt * 144)
            else:
                d = TOWER_DATA[t.type]
                eff_range = d["range"] + (range_level - 2) * 40
                for e in enemies:
                    if math.hypot(e.rect.centerx-t.rect.centerx, e.rect.centery-t.rect.centery) <= eff_range:
                        if t.type == "JINUTELLA":
                            t.effect_timer = 12
                            for e2 in enemies:
                                if math.hypot(e2.rect.centerx-t.rect.centerx, e2.rect.centery-t.rect.centery) <= eff_range: e2.hp -= get_current_damage(t.type)
                        else: projectiles.append(Projectile(t.rect.center, e, get_current_damage(t.type), d["p_img"]))
                        t.attack_timer = d["cd"]; break
        if nexus.attack_timer > 0: nexus.attack_timer -= 1 * game_speed * (dt * 144)
        else:
            eff_range = 300 + (range_level - 1) * 20
            for e in enemies:
                if math.hypot(e.rect.centerx-nexus.rect.centerx, e.rect.centery-nexus.rect.centery) <= eff_range:
                    projectiles.append(Projectile(nexus.rect.center, e, get_current_damage("PRINCESS") * 2, "mte23"))
                    nexus.attack_timer = nexus.cd; break
        for e in enemies[:]:
            e.move(dt, game_speed)
            if e.hp <= 0: 
                gold += round_gold_value * (5 if e.is_boss else 1) # [복리] 적용된 골드 지급
                if bbolong_sound: bbolong_sound.play(); 
                elif e.is_boss and oh_sound: oh_sound.play()
                enemies.remove(e)
            elif e.target_idx >= len(enemy_path): 
                nexus.hp -= 2000 if e.is_boss else 1000; enemies.remove(e)
                if nexus.hp <= 0: pygame.mixer.music.stop(); game_state_mode = STATE_AIGONAN; (aigonan_sound.play() if aigonan_sound else None)

    # --- 그리기 ---
    display_surface.blit(background_image, (0, 0)) if background_image else display_surface.fill(BLACK)
    if game_state_mode == STATE_START_SCREEN:
        overlay = pygame.Surface(RESOLUTION, pygame.SRCALPHA); overlay.fill((0,0,0,220)); display_surface.blit(overlay, (0,0))
        h_rect = pygame.Rect(RESOLUTION[0]//2-500, 50, 1000, 750); pygame.draw.rect(display_surface, WHITE, h_rect, border_radius=30)
        title_surf = get_text_surface("케인(한화) 디펜스(수비)", FONT_TITLE, BLACK)
        display_surface.blit(title_surf, (h_rect.centerx - title_surf.get_width() // 2, 100))
        helps = [f"● 치트(헉) 상태: {'활성화' if CHEAT_MODE else '비활성'}", f"● 자! 처치골드: {round_gold_value}G만큼 시작!(1.5배))", "● 40라운드 최종 보스전 (보스 10마리)", "● 지누텔라 타워: 광역 갈색 이펙트 공격", "● 방음부스 체력 0 되면 게임 종료", "● 타워 우클릭: 판매 확인창"]
        for i, txt in enumerate(helps):
            display_surface.blit(get_text_surface(txt, FONT_HELP, BLACK), (h_rect.x+100, 250 + i*70))
        start_btn.draw(display_surface)
    elif game_state_mode == STATE_PLAYING:
        pygame.draw.lines(display_surface, PATH_COLOR, False, enemy_path, 50)
        if shop_open and not (shop_rect.collidepoint(mx, my)) and current_round <= 40:
            ps = pygame.Surface((GRID_SIZE, GRID_SIZE), pygame.SRCALPHA); pygame.draw.rect(ps, (0,255,0,100) if can_place else (255,0,0,100), (0,0,GRID_SIZE,GRID_SIZE)); display_surface.blit(ps, (gmx, gmy))
            rv = TOWER_DATA[selected_tower_type]["range"] + (range_level - 1) * 20; rs = pygame.Surface((rv*2, rv*2), pygame.SRCALPHA); pygame.draw.circle(rs, (255,255,255,60), (rv,rv), rv); display_surface.blit(rs, (gmx+GRID_SIZE//2-rv, gmy+GRID_SIZE//2-rv))
        for t in towers: t.draw(display_surface)
        for e in enemies: e.draw(display_surface)
        for p in projectiles: p.draw(display_surface)
        nexus.draw(display_surface); open_shop_btn.draw(display_surface); open_settings_btn.draw(display_surface); speed_btn.draw(display_surface)
        display_surface.blit(get_text_surface(f"GOLD: {gold} (마리당: {round_gold_value}G) | 공격 Lv: {damage_level} | HP Lv: {hp_level} | 사거리 Lv: {range_level}", FONT_UI, BLACK), (30, 30))
        display_surface.blit(get_text_surface(f"{f'라운드 {current_round} 조이고 ' if not is_break_time else '정리좀하고(%s초쯤)' % int(time_left)}| 남은 시간: {int(time_left)}초", FONT_UI, DARK_RED), (30, 70))
        if shop_open:
            pygame.draw.rect(display_surface, (230,230,230), shop_rect, border_radius=20); pygame.draw.rect(display_surface, (150,150,150), sdb, border_radius=20); close_shop_btn.draw(display_surface)
            draw_text_with_outline(display_surface, "★ 타워조이고 ★", FONT_SHOP_TITLE, (shop_pos[0]+20, shop_pos[1]+15), WHITE, BLACK)
            for b in tower_btns:
                b.draw(display_surface, selected_tower_type == b.val)
                dmg_txt = get_text_surface(f"공격력: {get_current_damage(b.val)}", FONT_DMG_TEXT, BLACK)
                display_surface.blit(dmg_txt, (b.rect.centerx - dmg_txt.get_width()//2, b.rect.bottom + 5))
            up_dmg_btn.draw(display_surface); up_hp_btn.draw(display_surface); up_range_btn.draw(display_surface)
        if settings_open:
            pygame.draw.rect(display_surface, (230, 230, 230), settings_rect, border_radius=20)
            pygame.draw.rect(display_surface, (150, 150, 150), sdb_settings, border_radius=20)
            close_settings_btn.draw(display_surface)
            draw_text_with_outline(display_surface, "★ 설정조이고 ★", FONT_SHOP_TITLE, (settings_pos[0] + 20, settings_pos[1] + 15), WHITE, BLACK)
            bgm_text = get_text_surface(f"BGM 볼륨: {int(BGM_VOL * 100)}%", FONT_BTN_LARGE, BLACK)
            display_surface.blit(bgm_text, (settings_pos[0] + 40, settings_pos[1] + 95))
            bgm_vol_down_btn.draw(display_surface); bgm_vol_up_btn.draw(display_surface)
            sfx_text = get_text_surface(f"효과음 볼륨: {int(SFX_VOL * 100)}%", FONT_BTN_LARGE, BLACK)
            display_surface.blit(sfx_text, (settings_pos[0] + 40, settings_pos[1] + 165))
            sfx_vol_down_btn.draw(display_surface); sfx_vol_up_btn.draw(display_surface)
            settings_jukku_btn.draw(display_surface); settings_quit_btn.draw(display_surface)
        if jukku_confirm_open:
            px, py = (RESOLUTION[0]-500)//2, (RESOLUTION[1]-250)//2; pygame.draw.rect(display_surface, WHITE, (px, py, 500, 250), border_radius=20); display_surface.blit(get_text_surface("정말 자폭하시겠습니까?", FONT_UI, BLACK), (px+120, py+50))
            Button(px+60, py+140, 160, 60, "조이기", RED).draw(display_surface); Button(px+280, py+140, 160, 60, "안조이기", GRAY).draw(display_surface)
        if current_round > 40:
            if not ending_sound_played: pygame.mixer.music.stop(); pygame.mixer.stop(); (oh_sound.play() if oh_sound else None); ending_sound_played = True
            if mte22_image:
                m_rect = mte22_image.get_rect(center=(RESOLUTION[0]//2, RESOLUTION[1]//2)); display_surface.blit(mte22_image, m_rect)
                txt = get_text_surface("클(로버핏)리어!", FONT_CLEAR, YELLOW); display_surface.blit(txt, txt.get_rect(center=m_rect.center))
                quit_btn.rect.midtop = (m_rect.centerx, m_rect.bottom + 50); quit_btn.draw(display_surface)
    elif game_state_mode == STATE_AIGONAN:
        display_surface.fill((20, 0, 0))
        if aigonan_gif_frames:
            gif_frame_idx = (gif_frame_idx + 1) % len(aigonan_gif_frames)
            img = aigonan_gif_frames[gif_frame_idx]; display_surface.blit(img, img.get_rect(center=(RESOLUTION[0]//2, RESOLUTION[1]//2)))
        elif mte21_image: display_surface.blit(mte21_image, mte21_image.get_rect(center=(RESOLUTION[0]//2, RESOLUTION[1]//2 - 50)))
        display_surface.blit(get_text_surface("아이고난!", FONT_GAMEOVER, RED), (RESOLUTION[0]//2-200, 100)); retry_btn.draw(display_surface)
    if sell_confirm_open:
        sx, sy = (RESOLUTION[0]-500)//2, (RESOLUTION[1]-250)//2; pygame.draw.rect(display_surface, WHITE, (sx, sy, 500, 250), border_radius=20)
        display_surface.blit(get_text_surface(f"이 타워를 {int(tower_to_sell.cost*0.7)}G에 파냐맨이야?", FONT_UI, BLACK), (sx+80, sy+60))
        Button(sx+60, sy+140, 160, 60, "조이기", RED).draw(display_surface); Button(sx+280, sy+140, 160, 60, "안조이기", GRAY).draw(display_surface)
    if quit_confirm_open:
        qx, qy = (RESOLUTION[0]-500)//2, (RESOLUTION[1]-250)//2; pygame.draw.rect(display_surface, WHITE, (qx, qy, 500, 250), border_radius=20)
        display_surface.blit(get_text_surface("정말 종료하시겠습니까?", FONT_POPUP_TITLE, BLACK), (qx+100, qy+60))
        Button(qx+60, qy+140, 160, 60, "조이기", RED).draw(display_surface); Button(qx+280, qy+140, 160, 60, "안조이기", GRAY).draw(display_surface)
    pygame.display.update()
pygame.quit(); sys.exit()