import pygame
import sys
import math
import os
from modules.mte_config import *
from modules import mte_config
from modules.mte_object import *
from modules import mte_object
import json
import glob
import socket
import socket
import traceback
import threading
from modules import online_client
from modules.mte_shared import MK8Button, draw_text_with_outline, PygameChatBox, GameManager

# --- 상태 정의 ---
STATE_MAP_SELECT = 2
STATE_SETTINGS = 3
STATE_INTRO = -2
STATE_MAIN_MENU = -1
STATE_WAITING = 4
STATE_WIN = 5

# --- 네트워크 설정 ---
SERVER_IP = '127.0.0.1' # 테스트용 로컬 IP (실제 배포 시 서버 IP 입력)
SERVER_PORT = 12345     # server.py의 포트와 같아야 함
NICKNAME = "Player"     # 기본 닉네임

# --- 채팅 관리 클래스 ---
# --- 채팅 관리 클래스는 mte_shared에서 import 함 ---

# --- 게임 상태 관리 클래스 ---
# --- 게임 상태 관리 클래스는 mte_shared에서 import 함 ---

def get_nickname():
    return NICKNAME

# GameManager 초기화 (PygameChatBox 사용)
# PygameChatBox가 이 모듈의 NICKNAME을 참조할 수 있도록 getter 전달
gm = GameManager(chat_class=lambda: PygameChatBox(nickname_getter=get_nickname))

# --- 설정 관리 ---
CONFIG_FILE = "data/launcher_config.json"

display_mode_setting = 0 # 0: 창모드, 1: 전체화면, 2: 전체화면(창)
NATIVE_RESOLUTION = RESOLUTION # mte_config에서 가져온 초기(모니터) 해상도 저장
CHEAT_MODE = False # mte_config.CHEAT_MODE와 동기화 필요

main_bg_image = None

# --- 마리오카트 8 스타일 버튼 클래스 ---
# --- 마리오카트 8 스타일 버튼 클래스는 mte_shared에서 import 함 ---

def init_ui():
    """현재 해상도(RESOLUTION)에 맞춰 UI 요소들의 위치를 초기화합니다."""
    global mk8_play_btn, mk8_online_btn, mk8_settings_btn, mk8_quit_btn
    global map_prev_btn, map_next_btn, map_select_confirm_btn, map_select_back_btn
    global open_shop_btn, open_settings_btn, speed_btn, quit_btn, retry_btn, next_round_btn
    global settings_back_btn, settings_save_btn, bgm_vol_down_btn, bgm_vol_up_btn, sfx_vol_down_btn, sfx_vol_up_btn
    global display_mode_window_btn, display_mode_fullscreen_btn, settings_jukku_btn, settings_quit_btn, settings_ip_btn, settings_port_btn, settings_nickname_btn

    s = RESOLUTION[1] / 1080.0 # UI 크기 비율
    s_w, s_h = RESOLUTION[0], RESOLUTION[1]

    # --- 메인 메뉴 버튼 (MK8 스타일) ---
    # 화면 왼쪽 하단에 배치
    btn_w, btn_h = int(350*s), int(70*s)
    start_x = int(100*s)
    start_y = s_h // 2
    gap = int(20*s)

    mk8_play_btn = MK8Button(start_x, start_y, btn_w, btn_h, "싱글 플레이", BLUE)
    mk8_online_btn = MK8Button(start_x + int(20*s), start_y + btn_h + gap, btn_w, btn_h, "온라인 대전", (255, 140, 0)) # 오렌지색
    mk8_settings_btn = MK8Button(start_x + int(40*s), start_y + (btn_h + gap)*2, btn_w, btn_h, "설 정", GRAY)
    mk8_quit_btn = MK8Button(start_x + int(60*s), start_y + (btn_h + gap)*3, btn_w, btn_h, "종 료", DARK_RED)

    # 맵 선택 화면 버튼
    map_prev_btn = Button(RESOLUTION[0]//2 - int(220*s), int(RESOLUTION[1] * 0.75), int(60*s), int(60*s), "<", GRAY)
    map_next_btn = Button(RESOLUTION[0]//2 + int(160*s), int(RESOLUTION[1] * 0.75), int(60*s), int(60*s), ">", GRAY)
    map_select_confirm_btn = Button(RESOLUTION[0]//2 - int(150*s), int(RESOLUTION[1] * 0.85), int(300*s), int(80*s), "전투 시작", RED)
    map_select_back_btn = Button(int(50*s), int(50*s), int(100*s), int(50*s), "뒤로", GRAY)

    # 상단 UI 버튼
    margin = int(20*s)
    settings_btn_w, speed_btn_w, shop_btn_w = int(160*s), int(120*s), int(180*s)
    settings_btn_x = RESOLUTION[0] - settings_btn_w - margin
    speed_btn_x = settings_btn_x - speed_btn_w - margin
    shop_btn_x = speed_btn_x - shop_btn_w - margin

    open_shop_btn = Button(shop_btn_x, int(RESOLUTION[1] * 0.02), shop_btn_w, int(50*s), "상점 열기", BLUE)
    open_settings_btn = Button(settings_btn_x, int(RESOLUTION[1] * 0.02), settings_btn_w, int(50*s), "설정 열기", GRAY)
    speed_btn = Button(speed_btn_x, int(RESOLUTION[1] * 0.02), speed_btn_w, int(50*s), "배속: 1x", BLACK)

    # 기타 버튼
    quit_btn = Button(RESOLUTION[0]-int(180*s), int(RESOLUTION[1] * 0.02), int(160*s), int(50*s), "게임 종료", DARK_RED)
    retry_btn = Button(RESOLUTION[0]//2 - int(150*s), int(RESOLUTION[1] * 0.8), int(300*s), int(80*s), "다시 조이기", BLUE)
    next_round_btn = Button(RESOLUTION[0]//2 - int(150*s), RESOLUTION[1]//2 + int(60*s), int(300*s), int(80*s), "다음라운드", BLUE)
    
    # 설정 화면 버튼
    btn_size = int(50 * s)
    btn_w_small = int(185 * s)
    btn_h = int(50 * s)
    btn_w_large = int(390 * s)
    btn_h_large = int(60 * s)

    settings_back_btn = Button(s_w//2 + int(10*s), s_h * 0.85, int(140*s), int(80*s), "돌아가기", GRAY)
    settings_save_btn = Button(s_w//2 - int(150*s), s_h * 0.85, int(140*s), int(80*s), "저장하기", BLUE)

    bgm_vol_down_btn = Button(s_w//2 + int(10*s), s_h * 0.20, btn_size, btn_size, "-", BLUE)
    bgm_vol_up_btn = Button(s_w//2 + int(90*s), s_h * 0.20, btn_size, btn_size, "+", RED)
    sfx_vol_down_btn = Button(s_w//2 + int(10*s), s_h * 0.28, btn_size, btn_size, "-", BLUE)
    sfx_vol_up_btn = Button(s_w//2 + int(90*s), s_h * 0.28, btn_size, btn_size, "+", RED)
    
    display_mode_window_btn = Button(s_w//2 - int(195*s), s_h * 0.36, btn_w_small, btn_h, "창 모드", GRAY)
    display_mode_fullscreen_btn = Button(s_w//2 + int(10*s), s_h * 0.36, btn_w_small, btn_h, "전체화면", GRAY)
    
    settings_ip_btn = Button(s_w//2 + int(10*s), s_h * 0.44, btn_w_small, btn_h, "변경", GRAY)
    settings_port_btn = Button(s_w//2 + int(10*s), s_h * 0.52, btn_w_small, btn_h, "변경", GRAY)
    settings_nickname_btn = Button(s_w//2 + int(10*s), s_h * 0.60, btn_w_small, btn_h, "변경", GRAY)
    
    settings_jukku_btn = Button(s_w//2 - int(195*s), s_h * 0.72, btn_w_large, btn_h_large, "주꾸다시 (자폭)", DARK_RED)
    settings_quit_btn = Button(s_w//2 - int(195*s), s_h * 0.82, btn_w_large, btn_h_large, "메인 메뉴로 이동", GRAY)
    
    settings_back_btn.rect.y = int(s_h * 0.88)
    settings_save_btn.rect.y = int(s_h * 0.88)

def _update_all_sizes(old_grid_size):
    """해상도 변경에 따라 모든 게임 요소의 크기와 위치를 업데이트합니다."""
    global background_image, main_bg_image, aigonan_gif_frames, building_image, mte21_image, mte22_image, projectile_images

    # 캐시 초기화 (init_fonts가 TEXT_CACHE를 처리)
    mte_config.RANGE_SURFACE_CACHE.clear()

    # 해상도 변경에 따른 리소스 및 UI 업데이트
    scale = RESOLUTION[1] / 1080.0
    background_image = load_smart_image("image/yousuck", RESOLUTION)
    main_bg_image = load_smart_image("image/uring5", RESOLUTION) # 메인 메뉴 배경
    building_image = load_smart_image("image/building", (int(120*scale), int(120*scale)))
    mte21_image = load_smart_image("image/mte21", (int(800*scale), int(800*scale)))
    mte22_image = load_smart_image("image/mte22", (int(800*scale), int(800*scale)))
    projectile_images["mte23"] = load_smart_image("image/mte23", (int(40*scale), int(40*scale)))
    projectile_images["mte24"] = load_smart_image("image/mte24", (int(40*scale), int(40*scale)))
    projectile_images["mte25"] = load_smart_image("image/mte25", (int(60*scale), int(60*scale)))
    aigonan_gif_frames = load_gif_frames_21_9("mte21.gif", RESOLUTION[0])
    init_fonts(RESOLUTION[1])
    init_ui()

    # 게임 진행 중일 경우 엔티티 위치 및 크기 재조정
    if gm.mode == STATE_PLAYING and old_grid_size > 0:
        raw_path = available_maps[gm.current_map_index]["path"]
        
        gm.enemy_path = []
        for i, p in enumerate(raw_path):
            gx, gy = p[0], p[1]
            props = p[2] if len(p) > 2 else {"speed": 1.0, "type": "NORMAL"}
            gm.enemy_path.append({"pos": get_c(gx, gy), "props": props})

        if gm.nexus: gm.nexus.image = building_image; gm.nexus.rect = gm.nexus.image.get_rect(center=gm.enemy_path[-1]["pos"])

        for t in gm.towers:
            gx, gy = round(t.rect.x / old_grid_size), round(t.rect.y / old_grid_size)
            t.rect = pygame.Rect(gx * GRID_SIZE, gy * GRID_SIZE, GRID_SIZE, GRID_SIZE)
            t.image = load_smart_image(TOWER_DATA[t.type]["image_path"], (GRID_SIZE, GRID_SIZE))

        for e in gm.enemies:
            e.path = gm.enemy_path
            e.pos = e.pos * (GRID_SIZE / old_grid_size)
            w, h = (100, 100) if e.is_boss else (70, 70)
            size = (int(w * scale), int(h * scale))
            e.image = load_smart_image(e.image_path, size); e.rect = e.image.get_rect(center=(int(e.pos.x), int(e.pos.y)))

        for p in gm.projectiles: p.pos = p.pos * (GRID_SIZE / old_grid_size)

def update_display_mode():
    """현재 display_mode_setting에 따라 화면 모드를 변경합니다."""
    global display_surface, RESOLUTION, background_image, aigonan_gif_frames
    global GRID_SIZE, building_image, mte21_image, mte22_image, projectile_images
    
    old_grid_size = GRID_SIZE
    flags = pygame.DOUBLEBUF

    if display_mode_setting == 0: # 창 모드
        # 모니터 해상도의 85% 크기 (최대 1600x900)로 설정하여 화면 잘림 방지
        target_w = min(1600, int(NATIVE_RESOLUTION[0] * 0.85))
        target_h = int(target_w * 9 / 16) # 16:9 비율 유지
        RESOLUTION = (target_w, target_h)
        flags |= pygame.RESIZABLE
    elif display_mode_setting == 1: # 전체화면
        RESOLUTION = NATIVE_RESOLUTION
        flags |= pygame.FULLSCREEN
    
    # 그리드 사이즈 및 전역 변수 업데이트 (가로 24칸, 세로 14칸 비율 유지)
    grid_w = RESOLUTION[0] / 24
    grid_h = RESOLUTION[1] / 14
    GRID_SIZE = max(1, int(min(grid_w, grid_h)))
    
    mte_config.GRID_SIZE = GRID_SIZE
    mte_object.GRID_SIZE = GRID_SIZE

    display_surface = pygame.display.set_mode(RESOLUTION, flags)
    _update_all_sizes(old_grid_size)

projectile_images = {}

# --- 유틸리티 함수 ---
# --- draw_text_with_outline은 mte_shared로 이동됨 ---

# --- 리소스 로드 ---
aigonan_sound, oh_sound, bbolong_sound = load_sound("sound/aigonan.mp3"), load_sound("sound/oh.mp3"), load_sound("sound/bbolong.mp3")

# --- 음악 관련 변수 및 함수 ---
TOTAL_MUSIC_COUNT = 5 # 사용 가능한 BGM 파일 개수 (mte1.mp3, mte2.mp3, ...)

def play_round_music(round_num):
    """라운드에 맞는 배경음악을 재생합니다."""
    if round_num > 40: # 40 라운드 클리어 시 음악 중지
        pygame.mixer.music.stop()
        return

    # 5개의 음악을 40라운드 동안 순환 (1~5번 음악)
    music_index = ((round_num - 1) % TOTAL_MUSIC_COUNT) + 1
    
    # 파일 확장자 유연성 및 경로 안전성 확보
    music_file = None
    for ext in ['.mp3', '.ogg', '.wav']:
        path = resource_path(os.path.join("sound", f"mte{music_index}{ext}"))
        if os.path.exists(path): 
            music_file = path
            break
            
    if music_file:
        try:
            pygame.mixer.music.load(music_file)
            pygame.mixer.music.set_volume(BGM_VOL)
            pygame.mixer.music.play(-1) # 라운드 동안 무한 반복
        except pygame.error as e:
            print(f"음악 파일 로드/재생 오류 ({music_file}): {e}")
    else:
        print(f"BGM 파일을 찾을 수 없습니다: sound/mte{music_index}.[mp3/ogg/wav]")

# --- 유틸리티 및 경로 ---
def get_c(gx, gy): return (gx * GRID_SIZE + GRID_SIZE // 2, gy * GRID_SIZE + GRID_SIZE // 2)
def is_on_path(pos, path, threshold=None):
    if threshold is None: threshold = GRID_SIZE * 0.6 # 그리드 크기에 비례하여 판정
    
    # path가 딕셔너리 리스트일 경우 좌표만 추출
    points = [p["pos"] if isinstance(p, dict) else p for p in path]
    
    for i in range(len(points)-1):
        p1, p2, p3 = pygame.Vector2(points[i]), pygame.Vector2(points[i+1]), pygame.Vector2(pos); lp = p2-p1
        if lp.length() == 0: continue
        t = max(0, min(1, (p3-p1).dot(lp)/lp.length_squared()))
        if p3.distance_to(p1 + t*lp) < threshold: return True
    return False

# --- 맵 시스템 ---
MAPS_DIR = "maps"
available_maps = []

def load_maps():
    global available_maps
    available_maps = [] # 중복 방지를 위해 초기화
    
    search_paths = []
    
    # 1. 번들된 맵 경로 (PyInstaller _MEIPASS 대응)
    if hasattr(sys, '_MEIPASS'):
        search_paths.append(os.path.join(sys._MEIPASS, MAPS_DIR))
    else:
        search_paths.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), MAPS_DIR))
        
    # 2. 로컬 맵 경로 (사용자 추가 맵)
    local_path = os.path.join(os.getcwd(), MAPS_DIR)
    if os.path.abspath(local_path) not in [os.path.abspath(p) for p in search_paths]:
        search_paths.append(local_path)

    # 로컬 맵 폴더가 없으면 생성 (기본 맵 파일 생성은 아래 fallback에서 처리됨)
    if not os.path.exists(local_path):
        try:
            os.makedirs(local_path)
        except: pass
    
    for path in search_paths:
        if not os.path.exists(path): continue
        for f in glob.glob(os.path.join(path, "*.json")):
            try:
                with open(f, "r", encoding="utf-8") as file:
                    d = json.load(file)
                    # path가 비어있으면 Nexus 생성 시 크래시 발생하므로 체크
                    if "name" in d and "path" in d and d["path"]: 
                        available_maps.append(d)
            except: continue
    
    if not available_maps:
        available_maps.append({"name": "기본 맵", "path": [[1,13], [1,1], [3,1], [3,12], [5,12], [5,1], [22,1], [22,12], [7,12], [7,3], [20,3], [20,10], [9,10], [9,5], [18,5], [18,8], [11,8]]})

# GameManager에 맵 리스트 전달
gm.available_maps = available_maps

# --- 입력 팝업 함수 ---
def show_input_dialog(surface, prompt):
    """사용자로부터 숫자를 입력받는 모달 대화상자를 표시합니다."""
    bg_snapshot = surface.copy() # 현재 화면 저장
    input_str = ""
    running_dialog = True
    
    while running_dialog:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN: running_dialog = False
                elif event.key == pygame.K_ESCAPE: return None
                elif event.key == pygame.K_BACKSPACE: input_str = input_str[:-1]
                elif event.unicode.isdigit():
                    if len(input_str) < 3: input_str += event.unicode # 최대 3자리
        
        surface.blit(bg_snapshot, (0,0)) # 배경 복구
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA); overlay.fill((0,0,0,150)); surface.blit(overlay, (0,0)) # 어두운 배경
        
        cw, ch = surface.get_size()
        box_rect = pygame.Rect(0, 0, 400, 200); box_rect.center = (cw//2, ch//2)
        pygame.draw.rect(surface, WHITE, box_rect, border_radius=20)
        pygame.draw.rect(surface, BLACK, box_rect, 4, border_radius=20)
        
        p_surf = get_text_surface(prompt, Fonts.UI, BLACK); surface.blit(p_surf, (box_rect.centerx - p_surf.get_width()//2, box_rect.y + 40))
        i_surf = get_text_surface(input_str + "_", Fonts.TITLE, BLUE); surface.blit(i_surf, (box_rect.centerx - i_surf.get_width()//2, box_rect.y + 100))
        pygame.display.update()
        
    try: return int(input_str)
    except: return None

def show_text_input_dialog(surface, prompt, initial_text):
    """사용자로부터 텍스트를 입력받는 모달 대화상자를 표시합니다."""
    bg_snapshot = surface.copy()
    input_str = str(initial_text)
    running_dialog = True
    
    pygame.key.set_repeat(500, 50) # 키 반복 활성화

    while running_dialog:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN: running_dialog = False
                elif event.key == pygame.K_ESCAPE: pygame.key.set_repeat(0); return None
                elif event.key == pygame.K_BACKSPACE: input_str = input_str[:-1]
                elif len(input_str) < 20 and (event.unicode.isalnum() or event.unicode in ".:"):
                    input_str += event.unicode
        
        surface.blit(bg_snapshot, (0,0))
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA); overlay.fill((0,0,0,150)); surface.blit(overlay, (0,0))
        
        cw, ch = surface.get_size()
        box_rect = pygame.Rect(0, 0, 500, 250); box_rect.center = (cw//2, ch//2)
        pygame.draw.rect(surface, WHITE, box_rect, border_radius=20)
        pygame.draw.rect(surface, BLACK, box_rect, 4, border_radius=20)
        
        p_surf = get_text_surface(prompt, Fonts.UI, BLACK); surface.blit(p_surf, (box_rect.centerx - p_surf.get_width()//2, box_rect.y + 40))
        i_surf = get_text_surface(input_str + "_", Fonts.TITLE, BLUE); surface.blit(i_surf, (box_rect.centerx - i_surf.get_width()//2, box_rect.y + 100))
        pygame.display.update()
    
    pygame.key.set_repeat(0) # 키 반복 비활성화
    return input_str

# --- 게임 리셋 ---
def reset_game(target_state=STATE_PLAYING):
    gm.reset(target_state)

def load_game_config():
    """게임 설정을 JSON 파일에서 불러옵니다."""
    global BGM_VOL, SFX_VOL, display_mode_setting, CHEAT_MODE, SERVER_IP, SERVER_PORT, NICKNAME
    
    defaults = {"bgm_volume": 0.3, "sfx_volume": 0.5, "display_mode": 0, "cheat_mode": False, "server_ip": "127.0.0.1", "server_port": 12345}
    config = defaults.copy()

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                loaded_config = json.load(f)
                config.update(loaded_config)
        except:
            pass

    BGM_VOL = config.get("bgm_volume", 0.3)
    SFX_VOL = config.get("sfx_volume", 0.5)
    display_mode_setting = config.get("display_mode", 0)
    CHEAT_MODE = config.get("cheat_mode", False)
    SERVER_IP = config.get("server_ip", "127.0.0.1")
    SERVER_PORT = config.get("server_port", 12345)
    NICKNAME = config.get("nickname", "Player")
    
    mte_config.CHEAT_MODE = CHEAT_MODE
    if pygame.mixer.get_init():
        pygame.mixer.music.set_volume(BGM_VOL)

    # GameManager에 네트워크 정보 및 닉네임 설정
    if gm.chat:
        gm.chat.set_network_info(SERVER_IP, SERVER_PORT)

def save_game_config():
    """현재 게임 설정을 JSON 파일에 저장합니다."""
    config_to_save = {
        "bgm_volume": BGM_VOL,
        "sfx_volume": SFX_VOL,
        "display_mode": display_mode_setting,
        "server_ip": SERVER_IP,
        "server_ip": SERVER_IP,
        "server_port": SERVER_PORT,
        "nickname": NICKNAME,
        "cheat_mode": CHEAT_MODE
    }
    existing_config = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                existing_config = json.load(f)
        except: pass
    
    existing_config.update(config_to_save)
    
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(existing_config, f, indent=4)
    except Exception as e:
        print(f"Error saving config: {e}")

def main(skip_intro=False):
    global running, clock
    global BGM_VOL, SFX_VOL, display_mode_setting, RESOLUTION, background_image, aigonan_gif_frames, display_surface, GRID_SIZE
    global SERVER_IP, SERVER_PORT, NICKNAME, CHEAT_MODE

    # Pygame 및 믹서 재초기화 (런처 종료 후 안전한 상태 확보)
    if not pygame.get_init():
        pygame.init()
    if not pygame.mixer.get_init():
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)

    load_game_config()
    load_maps()
    update_display_mode() # 프로그램 시작 시 기본 화면 모드(창 모드)로 설정
    pygame.display.set_caption("케인 디펜스")

    # 현재 사용 중인 비디오 드라이버 출력 (예: windows, x11, cocoa 등 - 하드웨어 가속 백엔드 확인용)
    print(f"Video Driver: {pygame.display.get_driver()}")

    clock = pygame.time.Clock()
    
    initial_state = STATE_MAIN_MENU if skip_intro else STATE_INTRO
    reset_game(initial_state)

    # --- 메인 루프 ---
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0; dt = min(dt, 0.1) # [버그 수정] 렉 걸릴 때 순간이동 방지
        
        if gm.show_save_feedback_timer > 0:
            gm.show_save_feedback_timer -= dt

        mx, my = pygame.mouse.get_pos(); gmx, gmy = (mx//GRID_SIZE)*GRID_SIZE, (my//GRID_SIZE)*GRID_SIZE
        can_place = (not is_on_path((gmx+GRID_SIZE//2, gmy+GRID_SIZE//2), gm.enemy_path)) and (not any(t.rect.topleft == (gmx, gmy) for t in gm.towers))
        
        shop_rect = pygame.Rect(gm.shop_pos[0], gm.shop_pos[1], 650, 500); sdb = pygame.Rect(gm.shop_pos[0], gm.shop_pos[1], 650, 60)
        close_shop_btn = Button(gm.shop_pos[0] + 580, gm.shop_pos[1] + 10, 60, 40, "X", GRAY)
        tower_btns = [Button(gm.shop_pos[0]+25, gm.shop_pos[1]+100, 140, 50, "이걸 왜쏴 ㅋㅋ", BLUE, "PRINCESS"), Button(gm.shop_pos[0]+175, gm.shop_pos[1]+100, 140, 50, "집게이사장", PURPLE, "DUCHESS"), Button(gm.shop_pos[0]+325, gm.shop_pos[1]+100, 140, 50, "-3000로베로스", BLACK, "CANON"), Button(gm.shop_pos[0]+475, gm.shop_pos[1]+100, 140, 50, "지누텔라", BROWN, "JINUTELLA")]
        up_dmg_btn = Button(gm.shop_pos[0]+30, gm.shop_pos[1]+220, 280, 60, f"공격 강화 ({gm.damage_gold_val}G)", RED)
        up_hp_btn = Button(gm.shop_pos[0]+340, gm.shop_pos[1]+220, 280, 60, f"체력 UP ({gm.hp_gold_val}G)", GREEN)
        up_range_btn = Button(gm.shop_pos[0]+30, gm.shop_pos[1]+300, 590, 60, f"사거리 증가 ({gm.range_gold_val}G)", CYAN)
        
        # 온라인 공격 버튼
        atk_btns = [Button(gm.shop_pos[0]+30 + i*200, gm.shop_pos[1]+380, 190, 60, txt, col, val) for i, (txt, col, val) in enumerate([("짤짤이(200G)", GREEN, "SMALL"), ("중간몹(500G)", YELLOW, "LARGE"), ("보스(2000G)", RED, "BOSS")])]

        # --- 이벤트 처리 ---
        for event in pygame.event.get():
            # 채팅 입력 중일 때는 다른 키 입력을 막음
            if gm.chat.handle_event(event): continue

            if event.type == pygame.QUIT: running = False
            if event.type == pygame.VIDEORESIZE:
                if display_mode_setting == 0:
                    old_grid_size = GRID_SIZE
                    RESOLUTION = (event.w, event.h)
                    display_surface = pygame.display.set_mode(RESOLUTION, pygame.DOUBLEBUF | pygame.RESIZABLE)

                    # 동적 그리드 스케일링 (가로 24, 세로 14 비율 맞춤)
                    grid_w = RESOLUTION[0] / 24
                    grid_h = RESOLUTION[1] / 14
                    GRID_SIZE = max(1, int(min(grid_w, grid_h)))
                    
                    mte_config.GRID_SIZE = GRID_SIZE
                    mte_object.GRID_SIZE = GRID_SIZE
                    
                    _update_all_sizes(old_grid_size)

            if CHEAT_MODE and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F1: gm.gold += 10000000
                if event.key == pygame.K_F2: gm.damage_level += 5
                if event.key == pygame.K_F3: gm.nexus.hp = gm.nexus.max_hp
                if event.key == pygame.K_F4: gm.enemies = []
                if event.key == pygame.K_F5: gm.is_break_time = not gm.is_break_time; gm.current_round = gm.current_round+1 if not gm.is_break_time else gm.current_round; gm.round_start_time = gm.virtual_elapsed_time; gm.enemies = []

            if event.type == pygame.MOUSEBUTTONDOWN:
                # --- 최상위 팝업 및 패널 처리 (클릭 이벤트 선점) ---
                if gm.save_confirm_open:
                    sc_w, sc_h = 600, 250
                    sc_x, sc_y = (RESOLUTION[0]-sc_w)//2, (RESOLUTION[1]-sc_h)//2

                    save_btn_rect = pygame.Rect(sc_x + 100, sc_y + 150, 180, 60)
                    dont_save_btn_rect = pygame.Rect(sc_x + 320, sc_y + 150, 180, 60)
                    if event.button == 1:
                        if save_btn_rect.collidepoint(mx, my):
                            save_game_config()
                            gm.mode = gm.state_before_settings
                            gm.save_confirm_open = False
                        elif dont_save_btn_rect.collidepoint(mx, my):
                            # 설정 화면 진입 시점의 설정으로 되돌림
                            BGM_VOL = gm.initial_settings.get("bgm_volume", 0.3)
                            SFX_VOL = gm.initial_settings.get("sfx_volume", 0.5)
                            pygame.mixer.music.set_volume(BGM_VOL)
                            if display_mode_setting != gm.initial_settings.get("display_mode", 0):
                                display_mode_setting = gm.initial_settings.get("display_mode", 0)
                                update_display_mode() # 화면 모드 변경 적용
                            gm.mode = gm.state_before_settings
                            gm.save_confirm_open = False
                            continue # 상태 변경 후 즉시 루프 재시작하여 오류 방지
                    continue
                if gm.quit_confirm_open:
                    qx, qy = (RESOLUTION[0]-500)//2, (RESOLUTION[1]-250)//2
                    if pygame.Rect(qx+60, qy+140, 160, 60).collidepoint(mx, my): running = False
                    elif pygame.Rect(qx+280, qy+140, 160, 60).collidepoint(mx, my): gm.quit_confirm_open = False
                    continue
                if gm.sell_confirm_open:
                    sx, sy = (RESOLUTION[0]-500)//2, (RESOLUTION[1]-250)//2
                    if pygame.Rect(sx+60, sy+140, 160, 60).collidepoint(mx, my): 
                        if gm.tower_to_sell in gm.towers: gm.gold += int(gm.tower_to_sell.cost * 0.7); gm.towers.remove(gm.tower_to_sell)
                        gm.sell_confirm_open, gm.tower_to_sell = False, None
                    elif pygame.Rect(sx+280, sy+140, 160, 60).collidepoint(mx, my): gm.sell_confirm_open, gm.tower_to_sell = False, None
                    continue
                if gm.jukku_confirm_open:
                    px, py = (RESOLUTION[0]-500)//2, (RESOLUTION[1]-250)//2
                    if pygame.Rect(px+60, py+140, 160, 60).collidepoint(mx, my): pygame.mixer.music.stop(); gm.mode = STATE_AIGONAN; gm.jukku_confirm_open = False; (aigonan_sound.play() if aigonan_sound else None)
                    elif pygame.Rect(px+280, py+140, 160, 60).collidepoint(mx, my): gm.jukku_confirm_open = False
                    continue
                
                if gm.mode != STATE_SETTINGS and open_settings_btn.rect.collidepoint(mx, my):
                    gm.state_before_settings = gm.mode
                    gm.mode = STATE_SETTINGS
                    # 설정 화면 진입 시 현재 설정값 저장
                    gm.initial_settings = {
                        "bgm_volume": BGM_VOL,
                        "sfx_volume": SFX_VOL,
                        "display_mode": display_mode_setting,
                        "server_ip": SERVER_IP,
                        "server_port": SERVER_PORT,
                        "nickname": NICKNAME
                    }
                    continue

                # --- 게임 상태별 처리 ---
                if gm.mode == STATE_INTRO:
                    # 인트로에서는 아무 키나 누르면 메인 메뉴로
                    gm.mode = STATE_MAIN_MENU
                    
                elif gm.mode == STATE_MAIN_MENU:
                    if mk8_play_btn.rect.collidepoint(mx, my):
                        gm.mode = STATE_MAP_SELECT
                        gm.chat.disconnect()
                    elif mk8_online_btn.rect.collidepoint(mx, my):
                        # 온라인 모드 실행 (모듈 함수 호출)
                        should_exit = online_client.run_online(auto_start=True)
                        if should_exit:
                            running = False
                            break
                        
                        # 온라인 모드 종료 후 복귀 처리
                        update_display_mode() # 화면 모드 재설정
                        gm.mode = STATE_MAIN_MENU
                        pygame.mixer.stop(); pygame.mixer.music.stop() # 온라인 소리 정지
                    elif mk8_settings_btn.rect.collidepoint(mx, my):
                        gm.state_before_settings = STATE_MAIN_MENU
                        gm.mode = STATE_SETTINGS
                        gm.initial_settings = {
                            "bgm_volume": BGM_VOL,
                            "sfx_volume": SFX_VOL,
                            "display_mode": display_mode_setting,
                            "server_ip": SERVER_IP,
                            "server_port": SERVER_PORT,
                            "nickname": NICKNAME
                        }
                    elif mk8_quit_btn.rect.collidepoint(mx, my):
                        gm.quit_confirm_open = True
                        
                elif gm.mode == STATE_MAP_SELECT:
                    if map_prev_btn.rect.collidepoint(mx, my):
                        gm.current_map_index = (gm.current_map_index - 1) % len(available_maps)
                    elif map_next_btn.rect.collidepoint(mx, my):
                        gm.current_map_index = (gm.current_map_index + 1) % len(available_maps)
                    elif map_select_confirm_btn.rect.collidepoint(mx, my):
                        reset_game(STATE_PLAYING)
                        play_round_music(gm.current_round)
                    elif map_select_back_btn.rect.collidepoint(mx, my):
                        gm.mode = STATE_MAIN_MENU

                elif gm.mode == STATE_WAITING:
                    if quit_btn.rect.collidepoint(mx, my): gm.mode = STATE_MAIN_MENU; gm.chat.disconnect()

                elif gm.mode == STATE_PLAYING:
                    if gm.show_skip_button and next_round_btn.rect.collidepoint(mx, my):
                        gm.enemies.clear() # 타임아웃 등으로 남은 적이 있다면 제거
                        gm.is_break_time, gm.current_round, gm.round_start_time, gm.gold = True, gm.current_round + 1, gm.virtual_elapsed_time, gm.gold + (100 * (gm.current_round + 1))
                        play_round_music(gm.current_round)
                        gm.show_skip_button = False
                        continue
                    if gm.current_round > 40 and quit_btn.rect.collidepoint(mx, my): gm.quit_confirm_open = True; continue
                    if event.button == 3:
                        for t in gm.towers:
                            if t.rect.collidepoint(mx, my): gm.tower_to_sell, gm.sell_confirm_open = t, True; break
                        continue
                    if gm.shop_open:
                        if close_shop_btn.rect.collidepoint(mx, my): gm.shop_open = False; continue
                        if sdb.collidepoint(mx, my): gm.is_dragging_shop, gm.drag_offset = True, [gm.shop_pos[0]-mx, gm.shop_pos[1]-my]; continue
                        for b in tower_btns:
                            if b.rect.collidepoint(mx, my): gm.selected_tower_type = b.val
                        if up_dmg_btn.rect.collidepoint(mx, my) and gm.gold >= gm.damage_gold_val: gm.gold -= gm.damage_gold_val; gm.damage_level += 1; gm.damage_gold_val = int(15 + gm.damage_gold_val * 1.5)
                        if up_hp_btn.rect.collidepoint(mx, my) and gm.gold >= gm.hp_gold_val: gm.gold -= gm.hp_gold_val; gm.hp_level += 1; gm.nexus.max_hp += 5000; gm.nexus.hp += 5000; gm.hp_gold_val = int(200 + gm.hp_gold_val * 1.5)
                        if up_range_btn.rect.collidepoint(mx, my) and gm.gold >= gm.range_gold_val: gm.gold -= gm.range_gold_val; gm.range_level += 1; gm.range_gold_val = int(150 + gm.range_gold_val * 1.5)
                        if gm.is_online:
                            for b in atk_btns:
                                if b.rect.collidepoint(mx, my): gm.send_mob(b.val)
                        if shop_rect.collidepoint(mx, my): continue
                    if open_shop_btn.rect.collidepoint(mx, my): gm.shop_open = not gm.shop_open; continue
                    if speed_btn.rect.collidepoint(mx, my): gm.game_speed = 2 if gm.game_speed==1 else (4 if gm.game_speed==2 else 1); speed_btn.text = f"배속: {gm.game_speed}x"
                    elif can_place and gm.gold >= TOWER_DATA[gm.selected_tower_type]["cost"]: 
                        gm.towers.append(Tower(mx, my, gm.selected_tower_type)); gm.gold -= TOWER_DATA[gm.selected_tower_type]["cost"]
                elif gm.mode == STATE_AIGONAN and retry_btn.rect.collidepoint(mx, my):
                    gm.chat.disconnect()
                    reset_game()
                    play_round_music(gm.current_round)
                elif gm.mode == STATE_WIN and retry_btn.rect.collidepoint(mx, my):
                    gm.chat.disconnect()
                    gm.mode = STATE_MAIN_MENU
                    play_round_music(gm.current_round)
                elif gm.mode == STATE_SETTINGS:
                    if settings_back_btn.rect.collidepoint(mx, my):
                        # 변경사항이 있는지 확인
                        has_changes = (
                            gm.initial_settings.get("bgm_volume") != BGM_VOL or
                            gm.initial_settings.get("sfx_volume") != SFX_VOL or
                            gm.initial_settings.get("display_mode") != display_mode_setting or
                            gm.initial_settings.get("server_ip") != SERVER_IP or
                            gm.initial_settings.get("server_port") != SERVER_PORT or
                            gm.initial_settings.get("server_port") != SERVER_PORT or
                            gm.initial_settings.get("nickname") != NICKNAME or
                            gm.initial_settings.get("cheat_mode") != CHEAT_MODE
                        )
                        if has_changes:
                            gm.save_confirm_open = True
                        else:
                            gm.mode = gm.state_before_settings
                    elif settings_save_btn.rect.collidepoint(mx, my):
                        save_game_config()
                        # 저장 후, 현재 설정을 "초기 설정"으로 업데이트하여 불필요한 팝업 방지
                        gm.initial_settings = {
                            "bgm_volume": BGM_VOL,
                            "sfx_volume": SFX_VOL,
                            "display_mode": display_mode_setting,
                            "server_ip": SERVER_IP,
                            "server_port": SERVER_PORT,
                            "nickname": NICKNAME
                        }
                        gm.show_save_feedback_timer = 2 # 2초 동안 피드백 표시
                    elif bgm_vol_down_btn.rect.collidepoint(mx, my): BGM_VOL = max(0.0, round(BGM_VOL - 0.1, 1)); pygame.mixer.music.set_volume(BGM_VOL)
                    elif bgm_vol_up_btn.rect.collidepoint(mx, my): BGM_VOL = min(1.0, round(BGM_VOL + 0.1, 1)); pygame.mixer.music.set_volume(BGM_VOL)
                    elif sfx_vol_down_btn.rect.collidepoint(mx, my): SFX_VOL = max(0.0, round(SFX_VOL - 0.1, 1)); [s.set_volume(SFX_VOL) for s in [aigonan_sound, oh_sound, bbolong_sound] if s]
                    elif sfx_vol_up_btn.rect.collidepoint(mx, my): SFX_VOL = min(1.0, round(SFX_VOL + 0.1, 1)); [s.set_volume(SFX_VOL) for s in [aigonan_sound, oh_sound, bbolong_sound] if s]
                    elif display_mode_window_btn.rect.collidepoint(mx, my) and display_mode_setting != 0: display_mode_setting = 0; update_display_mode()
                    elif display_mode_fullscreen_btn.rect.collidepoint(mx, my) and display_mode_setting != 1: display_mode_setting = 1; update_display_mode()
                    elif settings_ip_btn.rect.collidepoint(mx, my):
                        new_ip = show_text_input_dialog(display_surface, "서버 IP 주소 입력", SERVER_IP)
                        if new_ip is not None: SERVER_IP = new_ip
                        if gm.chat: gm.chat.set_network_info(SERVER_IP, SERVER_PORT)
                    elif settings_port_btn.rect.collidepoint(mx, my):
                        new_port = show_text_input_dialog(display_surface, "서버 포트 입력", str(SERVER_PORT))
                        if new_port is not None and new_port.isdigit(): SERVER_PORT = int(new_port)
                        if gm.chat: gm.chat.set_network_info(SERVER_IP, SERVER_PORT)
                    elif settings_nickname_btn.rect.collidepoint(mx, my):
                        new_nick = show_text_input_dialog(display_surface, "닉네임 입력", NICKNAME)
                        if new_nick is not None: NICKNAME = new_nick
                    elif settings_jukku_btn.rect.collidepoint(mx, my): gm.jukku_confirm_open = True
                    elif settings_quit_btn.rect.collidepoint(mx, my): gm.mode = STATE_MAIN_MENU

            if event.type == pygame.MOUSEBUTTONUP: gm.is_dragging_shop = False
            if event.type == pygame.MOUSEMOTION:
                if gm.is_dragging_shop: gm.shop_pos[0], gm.shop_pos[1] = mx + gm.drag_offset[0], my + gm.drag_offset[1]

        # --- 업데이트 로직 ---
        if gm.mode == STATE_PLAYING and not any([gm.jukku_confirm_open, gm.quit_confirm_open, gm.sell_confirm_open]):
            gm.virtual_elapsed_time += dt * gm.game_speed; c_time = gm.virtual_elapsed_time - gm.round_start_time
            if gm.current_round <= 40:
                # 온라인 모드 스폰 처리
                if gm.is_online and gm.spawn_queue:
                    mob_type = gm.spawn_queue.pop(0)
                    is_boss = (mob_type == "BOSS")
                    gm.enemies.append(Enemy(gm.enemy_path, gm.current_round, is_boss))
                    gm.enemies_spawned_this_round += 1

                    # 내 HP 정보를 1초마다 전송
                    now = pygame.time.get_ticks()
                    if now - gm.last_hp_sent_time > 1000 and gm.nexus:
                        gm.chat.send_json({"type": "HP", "hp": gm.nexus.hp, "max_hp": gm.nexus.max_hp})
                        gm.last_hp_sent_time = now

                if gm.is_break_time:
                    # 온라인 모드일 때는 서버 시간이 절대적임
                    if not gm.is_online:
                        gm.time_left = max(0, 15 - c_time)
                        if gm.time_left <= 0: 
                            gm.is_break_time, gm.round_start_time, gm.last_spawn_time, gm.boss_spawn_count, gm.show_skip_button, gm.enemies_spawned_this_round = False, gm.virtual_elapsed_time, gm.virtual_elapsed_time, 0, False, 0
                            if gm.current_round > 1: gm.round_gold_value = int(gm.round_gold_value * 1.5) # [복리] 라운드 시작 시 가치 상승
                    
                    # 공통 로직 (몬스터 스폰 수 계산 등)
                    # 서버에서 동기화된 round 정보를 사용
                    if gm.current_round == 40:
                        gm.enemies_to_spawn_this_round = 10
                    else:
                        spawn_interval_secs = max(0.4, 1.5 - gm.current_round*0.05)
                        gm.enemies_to_spawn_this_round = math.floor(45 / spawn_interval_secs) if spawn_interval_secs > 0 else 50

                elif gm.is_overtime:
                    gm.time_left = 0
                    if not gm.enemies:
                        gm.is_overtime = False
                        gm.show_skip_button = True
                    elif (gm.virtual_elapsed_time - gm.overtime_start_time >= 60):
                        # 60초 초과 시에도 버튼을 표시하여 수동으로 넘어가도록 변경
                        gm.is_overtime = False
                        gm.show_skip_button = True
                else:
                    if not gm.is_online:
                        gm.time_left = max(0, 45 - c_time)
                    
                    all_spawned = gm.enemies_spawned_this_round >= gm.enemies_to_spawn_this_round
                    
                    if not all_spawned:
                        if gm.current_round == 40:
                            if gm.boss_spawn_count < 10 and gm.virtual_elapsed_time - gm.last_spawn_time > 2.0: gm.enemies.append(Enemy(gm.enemy_path, 40, True)); gm.boss_spawn_count += 1; gm.enemies_spawned_this_round += 1; gm.last_spawn_time = gm.virtual_elapsed_time
                        elif gm.virtual_elapsed_time - gm.last_spawn_time > max(0.4, 1.5 - gm.current_round*0.05):
                            gm.enemies.append(Enemy(gm.enemy_path, gm.current_round, (gm.current_round%5==0 and not any(e.is_boss for e in gm.enemies)))); gm.enemies_spawned_this_round += 1; gm.last_spawn_time = gm.virtual_elapsed_time
                    
                    if all_spawned and not gm.enemies and not gm.is_overtime:
                        gm.show_skip_button = True

                    if gm.time_left <= 0:
                        if not all_spawned:
                            pass
                        elif gm.enemies:
                            gm.is_overtime = True
                            gm.overtime_start_time = gm.virtual_elapsed_time
            
            for p in gm.projectiles[:]:
                p.move(dt, gm.game_speed)
                if p.reached: gm.projectiles.remove(p)
            for t in gm.towers:
                if t.effect_timer > 0: t.effect_timer -= 1 * gm.game_speed * (dt * 144)
                if t.attack_timer > 0: t.attack_timer -= 1 * gm.game_speed * (dt * 144)
                else:
                    d = TOWER_DATA[t.type]
                    eff_range = d["range"] + (gm.range_level - 2) * 40
                    eff_range_sq = eff_range * eff_range # [최적화] 사거리 제곱 미리 계산
                    for e in gm.enemies: # [최적화] 제곱근(sqrt) 연산이 없는 거리 제곱 비교
                        dx = e.rect.centerx - t.rect.centerx
                        dy = e.rect.centery - t.rect.centery
                        if dx*dx + dy*dy <= eff_range_sq:
                            if t.type == "JINUTELLA":
                                t.effect_timer = 12
                                for e2 in gm.enemies:
                                    if (e2.rect.centerx-t.rect.centerx)**2 + (e2.rect.centery-t.rect.centery)**2 <= eff_range_sq:
                                        e2.hp -= gm.get_current_damage(t.type)
                            else: gm.projectiles.append(Projectile(t.rect.center, e, gm.get_current_damage(t.type), d["p_img"], projectile_images))
                            t.attack_timer = d["cd"]; break
            if gm.nexus.attack_timer > 0: gm.nexus.attack_timer -= 1 * gm.game_speed * (dt * 144)
            else:
                eff_range = 300 + (gm.range_level - 1) * 20
                eff_range_sq = eff_range * eff_range
                for e in gm.enemies:
                    if (e.rect.centerx-gm.nexus.rect.centerx)**2 + (e.rect.centery-gm.nexus.rect.centery)**2 <= eff_range_sq:
                        gm.projectiles.append(Projectile(gm.nexus.rect.center, e, gm.get_current_damage("PRINCESS") * 2, "mte23", projectile_images))
                        gm.nexus.attack_timer = gm.nexus.cd; break
            for e in gm.enemies[:]:
                e.move(dt, gm.game_speed)
                if e.hp <= 0: 
                    gm.gold += gm.round_gold_value * (5 if e.is_boss else 1) # [복리] 적용된 골드 지급
                    if e.is_boss:
                        if aigonan_sound: aigonan_sound.play()
                    elif bbolong_sound: bbolong_sound.play()
                    gm.enemies.remove(e)
                elif e.target_idx >= len(gm.enemy_path): 
                    gm.nexus.hp -= 2000 if e.is_boss else 1000; gm.enemies.remove(e)
                    if gm.nexus.hp <= 0: 
                        pygame.mixer.music.stop(); gm.mode = STATE_AIGONAN; (aigonan_sound.play() if aigonan_sound else None)
                        if gm.is_online:
                            gm.chat.send_json({"type": "DIE"})

        # --- 그리기 ---
        display_surface.blit(background_image, (0, 0)) if background_image else display_surface.fill(BLACK)
        
        if gm.mode == STATE_INTRO:
            # 인트로 화면: 원래 디자인(흰색 패널 + 도움말)으로 롤백
            overlay = pygame.Surface(RESOLUTION, pygame.SRCALPHA); overlay.fill((0,0,0,220)); display_surface.blit(overlay, (0,0))
            panel_w, panel_h = int(RESOLUTION[0] * 0.8), int(RESOLUTION[1] * 0.8)
            h_rect = pygame.Rect((RESOLUTION[0] - panel_w)//2, (RESOLUTION[1] - panel_h)//2, panel_w, panel_h)
            pygame.draw.rect(display_surface, WHITE, h_rect, border_radius=30)
            title_surf = get_text_surface("케인 디펜스 - GayDefense", Fonts.TITLE, BLACK)
            display_surface.blit(title_surf, (h_rect.centerx - title_surf.get_width() // 2, h_rect.y + int(panel_h * 0.1)))
            helps = [f"● 치트(헉) 상태: {'활성' if CHEAT_MODE else '비활성'}", f"● 자! 처치골드: {gm.round_gold_value}G만큼 시작!(1.5배))", "● 온라인 대전 채팅기능 사용시 창모드 사용 권장", "● 지(으악)라는 광역 공격", "● 방음부스 체력 0 되면 게이ㅁ 종료", "● 타워 우클릭시 70% 가격으로 판매", "", ">>> 아무 키나 눌러서 시작 <<<"]
            for i, txt in enumerate(helps):
                color = RED if ">>>" in txt and (pygame.time.get_ticks() // 500) % 2 == 0 else BLACK
                display_surface.blit(get_text_surface(txt, Fonts.HELP, color), (h_rect.x + int(panel_w * 0.1), h_rect.y + int(panel_h * 0.25) + i * int(panel_h * 0.08)))

        elif gm.mode == STATE_MAIN_MENU:
            # 메인 메뉴: uring5 배경 + MK8 스타일 버튼
            if main_bg_image: display_surface.blit(main_bg_image, (0,0))
            mk8_play_btn.draw(display_surface, mx, my)
            mk8_online_btn.draw(display_surface, mx, my)
            mk8_settings_btn.draw(display_surface, mx, my)
            mk8_quit_btn.draw(display_surface, mx, my)
            gm.draw_online_popup(display_surface)
            
        elif gm.mode == STATE_MAP_SELECT:
            overlay = pygame.Surface(RESOLUTION, pygame.SRCALPHA); overlay.fill((0,0,0,220)); display_surface.blit(overlay, (0,0))
            
            # 맵 선택 UI
            map_name = available_maps[gm.current_map_index]["name"]
            map_surf = get_text_surface(f"MAP: {map_name}", Fonts.UI, WHITE)
            display_surface.blit(map_surf, (RESOLUTION[0]//2 - map_surf.get_width()//2, int(RESOLUTION[1] * 0.2)))
            
            # 미리보기
            preview_rect = pygame.Rect(0, 0, 600, 350)
            preview_rect.center = (RESOLUTION[0]//2, RESOLUTION[1]//2)
            pygame.draw.rect(display_surface, WHITE, preview_rect)
            pygame.draw.rect(display_surface, BLACK, preview_rect, 3)
            
            p_path = available_maps[gm.current_map_index]["path"]
            if p_path:
                scaled_path = [(preview_rect.x + p[0]*(preview_rect.width/24) + (preview_rect.width/48), preview_rect.y + p[1]*(preview_rect.height/14) + (preview_rect.height/28)) for p in p_path]
                if len(scaled_path) > 1: pygame.draw.lines(display_surface, BLUE, False, scaled_path, 5)
                pygame.draw.circle(display_surface, GREEN, (int(scaled_path[0][0]), int(scaled_path[0][1])), 8)
                pygame.draw.circle(display_surface, RED, (int(scaled_path[-1][0]), int(scaled_path[-1][1])), 8)
                
            map_prev_btn.draw(display_surface)
            map_next_btn.draw(display_surface)
            map_select_confirm_btn.draw(display_surface)
            map_select_back_btn.draw(display_surface)
            
        elif gm.mode == STATE_WAITING:
            overlay = pygame.Surface(RESOLUTION, pygame.SRCALPHA); overlay.fill((0,0,0,220)); display_surface.blit(overlay, (0,0))
            txt = get_text_surface("대전 상대를 찾는 중입니다...", Fonts.TITLE, WHITE)
            display_surface.blit(txt, (RESOLUTION[0]//2 - txt.get_width()//2, RESOLUTION[1]//2 - 50))
            quit_btn.rect.center = (RESOLUTION[0]//2, RESOLUTION[1]//2 + 100)
            quit_btn.draw(display_surface)

        elif gm.mode == STATE_PLAYING:
            # 경로 그리기 (딕셔너리 구조 대응)
            path_points = [p["pos"] for p in gm.enemy_path]
            if len(path_points) > 1:
                pygame.draw.lines(display_surface, PATH_COLOR, False, path_points, 50)
            
            if gm.shop_open and not (shop_rect.collidepoint(mx, my)) and gm.current_round <= 40:
                ps = pygame.Surface((GRID_SIZE, GRID_SIZE), pygame.SRCALPHA); pygame.draw.rect(ps, (0,255,0,100) if can_place else (255,0,0,100), (0,0,GRID_SIZE,GRID_SIZE)); display_surface.blit(ps, (gmx, gmy))
                rv = TOWER_DATA[gm.selected_tower_type]["range"] + (gm.range_level - 1) * 20; rs = pygame.Surface((rv*2, rv*2), pygame.SRCALPHA); pygame.draw.circle(rs, (255,255,255,60), (rv,rv), rv); display_surface.blit(rs, (gmx+GRID_SIZE//2-rv, gmy+GRID_SIZE//2-rv))
            for t in gm.towers: t.draw(display_surface, gm.range_level)
            for e in gm.enemies: e.draw(display_surface)
            for p in gm.projectiles: p.draw(display_surface)
            gm.nexus.draw(display_surface); open_shop_btn.draw(display_surface); speed_btn.draw(display_surface)
            display_surface.blit(get_text_surface(f"GOLD: {gm.gold} (마리당: {gm.round_gold_value}G) | 공격 Lv: {gm.damage_level} | HP Lv: {gm.hp_level} | 사거리 Lv: {gm.range_level}", Fonts.UI, BLACK), (int(RESOLUTION[0]*0.02), int(RESOLUTION[1]*0.03)))
            display_surface.blit(get_text_surface(f"{f'라운드 {gm.current_round} 조이고 ' if not gm.is_break_time else '정리좀하고(%s초쯤)' % int(gm.time_left)}| 남은 시간: {int(gm.time_left)}초", Fonts.UI, DARK_RED), (int(RESOLUTION[0]*0.02), int(RESOLUTION[1]*0.08)))
            if gm.shop_open:
                pygame.draw.rect(display_surface, (230,230,230), shop_rect, border_radius=20); pygame.draw.rect(display_surface, (150,150,150), sdb, border_radius=20); close_shop_btn.draw(display_surface)
                draw_text_with_outline(display_surface, "★ 타워조이고 ★", Fonts.SHOP_TITLE, (gm.shop_pos[0]+20, gm.shop_pos[1]+15), WHITE, BLACK)
                for b in tower_btns:
                    b.draw(display_surface, gm.selected_tower_type == b.val)
                    dmg_txt = get_text_surface(f"공격력: {gm.get_current_damage(b.val)}", Fonts.DMG_TEXT, BLACK)
                    display_surface.blit(dmg_txt, (b.rect.centerx - dmg_txt.get_width()//2, b.rect.bottom + 5))
                up_dmg_btn.draw(display_surface); up_hp_btn.draw(display_surface); up_range_btn.draw(display_surface)
                if gm.is_online:
                    for b in atk_btns: b.draw(display_surface)
            
            # 온라인 모드일 때 상대방 HP 표시
            if gm.is_online:
                opp_hp_ratio = max(0, gm.opponent_hp / gm.opponent_max_hp) if gm.opponent_max_hp > 0 else 0
                bar_w, bar_h = 300, 30
                bar_x, bar_y = RESOLUTION[0] - bar_w - 20, 80
                pygame.draw.rect(display_surface, BLACK, (bar_x, bar_y, bar_w, bar_h))
                pygame.draw.rect(display_surface, RED, (bar_x, bar_y, int(bar_w * opp_hp_ratio), bar_h))
                pygame.draw.rect(display_surface, WHITE, (bar_x, bar_y, bar_w, bar_h), 2)
                draw_text_with_outline(display_surface, f"{gm.opponent_nickname}: {gm.opponent_hp}", Fonts.UI, (bar_x + 10, bar_y + 2), WHITE, BLACK)

            if gm.current_round > 40:
                if not gm.ending_sound_played: pygame.mixer.music.stop(); pygame.mixer.stop(); (oh_sound.play() if oh_sound else None); gm.ending_sound_played = True
                if mte22_image:
                    m_rect = mte22_image.get_rect(center=(RESOLUTION[0]//2, RESOLUTION[1]//2)); display_surface.blit(mte22_image, m_rect)
                    txt = get_text_surface("클(로버핏)리어!", Fonts.CLEAR, YELLOW); display_surface.blit(txt, txt.get_rect(center=m_rect.center))
                    quit_btn.rect.midtop = (m_rect.centerx, m_rect.bottom + 50); quit_btn.draw(display_surface)
            if gm.show_skip_button:
                overlay = pygame.Surface(RESOLUTION, pygame.SRCALPHA); overlay.fill((0,0,0,150)); display_surface.blit(overlay, (0,0))
                reward_txt = get_text_surface(f"라운드 클리어 보상: {100 * (gm.current_round + 1)}G", Fonts.TITLE, YELLOW)
                display_surface.blit(reward_txt, (RESOLUTION[0]//2 - reward_txt.get_width()//2, RESOLUTION[1]//2 - int(50 * (RESOLUTION[1]/1080.0))))
                next_round_btn.draw(display_surface)
            gm.chat.draw(display_surface)
        elif gm.mode == STATE_AIGONAN:
            display_surface.fill((20, 0, 0))
            if aigonan_gif_frames:
                gm.gif_frame_idx = (gm.gif_frame_idx + 1) % len(aigonan_gif_frames)
                img = aigonan_gif_frames[gm.gif_frame_idx]; display_surface.blit(img, img.get_rect(center=(RESOLUTION[0]//2, RESOLUTION[1]//2)))
            elif mte21_image: display_surface.blit(mte21_image, mte21_image.get_rect(center=(RESOLUTION[0]//2, RESOLUTION[1]//2 - 50)))
            display_surface.blit(get_text_surface("아이고난!", Fonts.GAMEOVER, RED), (RESOLUTION[0]//2-200, int(RESOLUTION[1]*0.15))); retry_btn.draw(display_surface)
        elif gm.mode == STATE_WIN:
            display_surface.fill((0, 0, 50))
            txt = get_text_surface("승리했습니다!", Fonts.GAMEOVER, YELLOW)
            display_surface.blit(txt, (RESOLUTION[0]//2 - txt.get_width()//2, RESOLUTION[1]//2 - 50))
            retry_btn.draw(display_surface)
        elif gm.mode == STATE_SETTINGS:
            overlay = pygame.Surface(RESOLUTION, pygame.SRCALPHA); overlay.fill((0,0,0,220)); display_surface.blit(overlay, (0,0))
            s_w, s_h = RESOLUTION[0], RESOLUTION[1]
            s = s_h / 1080.0 # UI 크기 비율
            
            title_surf = get_text_surface("설정 조이기", Fonts.TITLE, WHITE)
            display_surface.blit(title_surf, (s_w//2 - title_surf.get_width()//2, s_h * 0.1))

            def draw_setting_item(y, label, value_text, btn1, btn2):
                label_surf = get_text_surface(label, Fonts.UI, WHITE)
                # 스케일링 팩터 's'를 사용하여 위치를 동적으로 계산
                label_x = s_w//2 - int(220 * s) - label_surf.get_width()
                display_surface.blit(label_surf, (label_x, y + int(10 * s)))

                value_surf = get_text_surface(value_text, Fonts.UI, WHITE)
                # 볼륨 숫자와 버튼이 겹치지 않도록 왼쪽으로 이동
                display_surface.blit(value_surf, (s_w//2 - value_surf.get_width()//2 - int(60*s), y + int(10 * s)))
                btn1.draw(display_surface); btn2.draw(display_surface)

            draw_setting_item(s_h * 0.20, "BGM 볼륨", f"{int(BGM_VOL*100)}%", bgm_vol_down_btn, bgm_vol_up_btn)
            draw_setting_item(s_h * 0.28, "효과음 볼륨", f"{int(SFX_VOL*100)}%", sfx_vol_down_btn, sfx_vol_up_btn)

            label_surf = get_text_surface("화면 설정", Fonts.UI, WHITE)
            label_x = s_w//2 - int(220 * s) - label_surf.get_width()
            display_surface.blit(label_surf, (label_x, s_h * 0.36 + int(10 * s)))
            display_mode_window_btn.draw(display_surface, display_mode_setting == 0)
            display_mode_fullscreen_btn.draw(display_surface, display_mode_setting == 1)

            draw_setting_item(s_h * 0.44, "서버 IP", SERVER_IP, settings_ip_btn, Button(0,0,0,0,"",BLACK)) # Dummy button for layout
            settings_ip_btn.draw(display_surface) # Redraw over dummy
            draw_setting_item(s_h * 0.52, "서버 포트", str(SERVER_PORT), settings_port_btn, Button(0,0,0,0,"",BLACK))
            settings_port_btn.draw(display_surface)
            draw_setting_item(s_h * 0.60, "닉네임", NICKNAME, settings_nickname_btn, Button(0,0,0,0,"",BLACK))
            draw_setting_item(s_h * 0.60, "닉네임", NICKNAME, settings_nickname_btn, Button(0,0,0,0,"",BLACK))
            settings_nickname_btn.draw(display_surface)



            settings_jukku_btn.draw(display_surface); settings_quit_btn.draw(display_surface)
            settings_back_btn.draw(display_surface)
            settings_save_btn.draw(display_surface)

            if gm.show_save_feedback_timer > 0:
                save_surf = get_text_surface("저장 완료!", Fonts.UI, GREEN)
                pos = (settings_save_btn.rect.centerx - save_surf.get_width() // 2, settings_save_btn.rect.y - save_surf.get_height() - 10)
                display_surface.blit(save_surf, pos)
        
        # --- 전역 UI 및 팝업 그리기 (항상 위에 표시) ---
        if gm.mode not in [STATE_SETTINGS, STATE_MAIN_MENU, STATE_INTRO]:
            open_settings_btn.draw(display_surface)
        if gm.save_confirm_open:
            sc_w, sc_h = 600, 250
            sc_x, sc_y = (RESOLUTION[0]-sc_w)//2, (RESOLUTION[1]-sc_h)//2
            pygame.draw.rect(display_surface, WHITE, (sc_x, sc_y, sc_w, sc_h), border_radius=20)
            
            prompt_surf = get_text_surface("저장하지 않은 변경사항이 있습니다.", Fonts.UI, BLACK)
            display_surface.blit(prompt_surf, (sc_x + (sc_w - prompt_surf.get_width())//2, sc_y + 40))
            prompt_surf2 = get_text_surface("저장하시겠습니까?", Fonts.UI, BLACK)
            display_surface.blit(prompt_surf2, (sc_x + (sc_w - prompt_surf2.get_width())//2, sc_y + 80))

            save_btn = Button(sc_x + 100, sc_y + 150, 180, 60, "저장하고 닫기", BLUE)
            dont_save_btn = Button(sc_x + 320, sc_y + 150, 180, 60, "저장 안하고 닫기", RED)
            save_btn.draw(display_surface); dont_save_btn.draw(display_surface)

        if gm.sell_confirm_open:
            sx, sy = (RESOLUTION[0]-500)//2, (RESOLUTION[1]-250)//2; pygame.draw.rect(display_surface, WHITE, (sx, sy, 500, 250), border_radius=20)
            display_surface.blit(get_text_surface(f"이 타워를 {int(gm.tower_to_sell.cost*0.7)}G에 파냐맨이야?", Fonts.UI, BLACK), (sx+80, sy+60))
            Button(sx+60, sy+140, 160, 60, "조이기", RED).draw(display_surface); Button(sx+280, sy+140, 160, 60, "안조이기", GRAY).draw(display_surface)
        if gm.jukku_confirm_open:
            px, py = (RESOLUTION[0]-500)//2, (RESOLUTION[1]-250)//2; pygame.draw.rect(display_surface, WHITE, (px, py, 500, 250), border_radius=20); display_surface.blit(get_text_surface("정말 자폭하시겠습니까?", Fonts.UI, BLACK), (px+120, py+50))
            Button(px+60, py+140, 160, 60, "조이기", RED).draw(display_surface); Button(px+280, py+140, 160, 60, "안조이기", GRAY).draw(display_surface)
        if gm.quit_confirm_open:
            qx, qy = (RESOLUTION[0]-500)//2, (RESOLUTION[1]-250)//2; pygame.draw.rect(display_surface, WHITE, (qx, qy, 500, 250), border_radius=20)
            display_surface.blit(get_text_surface("정말 종료하시겠습니까?", Fonts.POPUP_TITLE, BLACK), (qx+100, qy+60))
            Button(qx+60, qy+140, 160, 60, "조이기", RED).draw(display_surface); Button(qx+280, qy+140, 160, 60, "안조이기", GRAY).draw(display_surface)

        pygame.display.update()
    pygame.quit(); sys.exit()

if __name__ == "__main__":
    try:
        main()
    except Exception:
        with open("error_log.txt", "w") as f:
            f.write(traceback.format_exc())
        traceback.print_exc()