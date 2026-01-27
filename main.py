import pygame
import sys
import math
import os
from mte_config import *
import mte_config
from mte_object import *
import mte_object
import json
import glob

game_state_mode = STATE_START_SCREEN
STATE_MAP_SELECT = 2
display_mode_setting = 0 # 0: 창모드, 1: 전체화면, 2: 전체화면(창)
NATIVE_RESOLUTION = RESOLUTION # mte_config에서 가져온 초기(모니터) 해상도 저장

def init_ui():
    """현재 해상도(RESOLUTION)에 맞춰 UI 요소들의 위치를 초기화합니다."""
    global start_btn, map_prev_btn, map_next_btn, map_select_confirm_btn, map_select_back_btn
    global open_shop_btn, open_settings_btn, speed_btn, quit_btn, retry_btn, next_round_btn
    global display_mode_window_btn, display_mode_borderless_btn, display_mode_fullscreen_btn

    s = RESOLUTION[1] / 1080.0 # UI 크기 비율

    # 메인 화면 버튼
    start_btn = Button(RESOLUTION[0]//2 - int(150*s), int(RESOLUTION[1] * 0.85), int(300*s), int(80*s), "게 이 시 작 !", BLUE)
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
    quit_btn = Button(RESOLUTION[0]-int(180*s), int(RESOLUTION[1] * 0.02), int(160*s), int(50*s), "게이 종료", DARK_RED)
    retry_btn = Button(RESOLUTION[0]//2 - int(150*s), int(RESOLUTION[1] * 0.8), int(300*s), int(80*s), "다시 조이기", BLUE)
    next_round_btn = Button(RESOLUTION[0]//2 - int(150*s), RESOLUTION[1]//2 + int(60*s), int(300*s), int(80*s), "다음라운드", BLUE)

def update_display_mode():
    """현재 display_mode_setting에 따라 화면 모드를 변경합니다."""
    global display_surface, RESOLUTION, background_image, aigonan_gif_frames, shop_pos, settings_pos
    global GRID_SIZE, building_image, mte21_image, mte22_image, projectile_images, enemy_path
    
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
    
    # 그리드 사이즈 및 전역 변수 업데이트 (해상도 너비 기준 24등분)
    GRID_SIZE = int(RESOLUTION[0] / 24)
    mte_config.GRID_SIZE = GRID_SIZE
    mte_object.GRID_SIZE = GRID_SIZE

    display_surface = pygame.display.set_mode(RESOLUTION, flags)
    
    # 해상도 변경에 따른 리소스 및 UI 업데이트
    scale = RESOLUTION[1] / 1080.0
    background_image = load_smart_image("image/yousuck", RESOLUTION)
    building_image = load_smart_image("image/building", (int(120*scale), int(120*scale)))
    mte21_image = load_smart_image("image/mte21", (int(800*scale), int(800*scale)))
    mte22_image = load_smart_image("image/mte22", (int(800*scale), int(800*scale)))
    projectile_images["mte23"] = load_smart_image("image/mte23", (int(40*scale), int(40*scale)))
    projectile_images["mte24"] = load_smart_image("image/mte24", (int(40*scale), int(40*scale)))
    projectile_images["mte25"] = load_smart_image("image/mte25", (int(60*scale), int(60*scale)))
    aigonan_gif_frames = load_gif_frames_21_9("mte21.gif", RESOLUTION[0])
    init_fonts(RESOLUTION[1])
    init_ui()
    
    # 게임 중 해상도 변경 시 팝업 위치 재조정
    try:
        shop_pos[0] = (RESOLUTION[0] - 650) // 2
        shop_pos[1] = int(RESOLUTION[1] * 0.15)
        settings_pos[0] = (RESOLUTION[0] - 450) // 2
        settings_pos[1] = (RESOLUTION[1] - 450) // 2
    except: pass # 게임 시작 전이라 변수가 없을 경우 무시

    # 게임 진행 중일 경우 엔티티 위치 및 크기 재조정
    if game_state_mode == STATE_PLAYING:
        # 경로 업데이트
        raw_path = available_maps[current_map_index]["path"]
        enemy_path = [get_c(p[0], p[1]) for p in raw_path]
        
        # 넥서스 업데이트
        if nexus: nexus.image = building_image; nexus.rect = nexus.image.get_rect(center=enemy_path[-1])
        
        # 타워 업데이트
        for t in towers:
            gx, gy = round(t.rect.x / old_grid_size), round(t.rect.y / old_grid_size)
            t.rect = pygame.Rect(gx * GRID_SIZE, gy * GRID_SIZE, GRID_SIZE, GRID_SIZE)
            t.image = load_smart_image(TOWER_DATA[t.type]["image_path"], (GRID_SIZE, GRID_SIZE))
            
        # 적 업데이트
        for e in enemies:
            e.path = enemy_path
            e.pos = e.pos * (GRID_SIZE / old_grid_size)
            w, h = (100, 100) if e.is_boss else (70, 70)
            size = (int(w * scale), int(h * scale))
            e.image = load_smart_image(e.image_path, size); e.rect = e.image.get_rect(center=(int(e.pos.x), int(e.pos.y)))
            
        # 투사체 업데이트
        for p in projectiles: p.pos = p.pos * (GRID_SIZE / old_grid_size)

projectile_images = {}
update_display_mode() # 프로그램 시작 시 기본 화면 모드(창 모드)로 설정
pygame.display.set_caption("케인 디펜스")

# 현재 사용 중인 비디오 드라이버 출력 (예: windows, x11, cocoa 등 - 하드웨어 가속 백엔드 확인용)
print(f"Video Driver: {pygame.display.get_driver()}")

clock = pygame.time.Clock()

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

def get_current_damage(tower_type):
    d = TOWER_DATA[tower_type]
    dmg = int(d["dmg"] * (1.4 ** (damage_level - 1)))
    if is_overtime: dmg = int(dmg * 1.5)
    return dmg

# --- 유틸리티 및 경로 ---
def get_c(gx, gy): return (gx * GRID_SIZE + GRID_SIZE // 2, gy * GRID_SIZE + GRID_SIZE // 2)
def is_on_path(pos, path, threshold=45):
    for i in range(len(path)-1):
        p1, p2, p3 = pygame.Vector2(path[i]), pygame.Vector2(path[i+1]), pygame.Vector2(pos); lp = p2-p1
        if lp.length() == 0: continue
        t = max(0, min(1, (p3-p1).dot(lp)/lp.length_squared()))
        if p3.distance_to(p1 + t*lp) < threshold: return True
    return False

# --- 맵 시스템 ---
MAPS_DIR = "maps"
available_maps = []
current_map_index = 0
enemy_path = []

def load_maps():
    global available_maps
    maps_path = resource_path(MAPS_DIR)
    # 맵 폴더가 없으면 생성하고 기본 맵 파일 생성
    if not os.path.exists(maps_path):
        try:
            os.makedirs(maps_path)
            default_map = {
                "name": "기본 맵",
                "path": [[1,13], [1,1], [3,1], [3,12], [5,12], [5,1], [22,1], [22,12], [7,12], [7,3], [20,3], [20,10], [9,10], [9,5], [18,5], [18,8], [11,8]]
            }
            with open(os.path.join(maps_path, "default.json"), "w", encoding="utf-8") as f:
                json.dump(default_map, f, ensure_ascii=False, indent=4)
        except: pass
    
    for f in glob.glob(os.path.join(maps_path, "*.json")):
        try:
            with open(f, "r", encoding="utf-8") as file:
                d = json.load(file)
                if "name" in d and "path" in d: available_maps.append(d)
        except: continue
    
    if not available_maps:
        available_maps.append({"name": "기본 맵", "path": [[1,13], [1,1], [3,1], [3,12], [5,12], [5,1], [22,1], [22,12], [7,12], [7,3], [20,3], [20,10], [9,10], [9,5], [18,5], [18,8], [11,8]]})

load_maps()

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
        
        p_surf = get_text_surface(prompt, FONT_UI, BLACK); surface.blit(p_surf, (box_rect.centerx - p_surf.get_width()//2, box_rect.y + 40))
        p_surf = get_text_surface(prompt, Fonts.UI, BLACK); surface.blit(p_surf, (box_rect.centerx - p_surf.get_width()//2, box_rect.y + 40))
        i_surf = get_text_surface(input_str + "_", Fonts.TITLE, BLUE); surface.blit(i_surf, (box_rect.centerx - i_surf.get_width()//2, box_rect.y + 100))
        pygame.display.update()
        
    try: return int(input_str)
    except: return None

# --- 게임 리셋 ---
def reset_game(target_state=STATE_PLAYING):
    global gold, damage_level, hp_level, range_level, game_speed, virtual_elapsed_time, current_round, selected_tower_type, time_left, gif_frame_idx, round_gold_value, range_gold_val, enemies_to_spawn_this_round, enemies_spawned_this_round
    global enemies, towers, projectiles, round_start_time, game_state_mode, nexus, shop_open, jukku_confirm_open, last_spawn_time, is_break_time, shop_pos, is_dragging_shop, drag_offset, settings_open, settings_pos, is_dragging_settings, drag_offset_settings, show_skip_button
    global ending_sound_played, quit_confirm_open, sell_confirm_open, tower_to_sell, boss_spawn_count
    global is_overtime, overtime_start_time, enemy_path
    gold = 999999 if CHEAT_MODE else 300
    round_gold_value = 15  # [복리 시스템] 마리당 지급 골드 초기값
    damage_level, hp_level, range_level, game_speed, virtual_elapsed_time, current_round = 1, 1, 1, 1, 0.0, 1
    range_gold_val = 150
    time_left = 10 + (current_round * 5)
    round_start_time, enemies, towers, projectiles = 0.0, [], [], []
    game_state_mode, shop_open, settings_open, jukku_confirm_open, selected_tower_type, gif_frame_idx = target_state, False, False, False, "PRINCESS", 0
    
    # 현재 선택된 맵 경로 로드
    raw_path = available_maps[current_map_index]["path"]
    enemy_path = [get_c(p[0], p[1]) for p in raw_path]
    
    last_spawn_time, is_break_time, nexus = 0, True, Nexus(enemy_path[-1], building_image)
    shop_pos, is_dragging_shop, drag_offset = [(RESOLUTION[0] - 650) // 2, int(RESOLUTION[1] * 0.15)], False, [0, 0]
    settings_pos, is_dragging_settings, drag_offset_settings = [(RESOLUTION[0] - 450) // 2, (RESOLUTION[1] - 450) // 2], False, [0, 0]
    ending_sound_played, quit_confirm_open, sell_confirm_open, tower_to_sell, boss_spawn_count = False, False, False, None, 0
    is_overtime, overtime_start_time, show_skip_button, enemies_to_spawn_this_round, enemies_spawned_this_round = False, 0, False, 0, 0

reset_game(STATE_START_SCREEN)

# --- 메인 루프 ---
running = True
while running:
    dt = clock.tick(FPS) / 1000.0; dt = min(dt, 0.1) # [버그 수정] 렉 걸릴 때 순간이동 방지
    mx, my = pygame.mouse.get_pos(); gmx, gmy = (mx//GRID_SIZE)*GRID_SIZE, (my//GRID_SIZE)*GRID_SIZE
    can_place = (not is_on_path((gmx+GRID_SIZE//2, gmy+GRID_SIZE//2), enemy_path)) and (not any(t.rect.topleft == (gmx, gmy) for t in towers))
    
    shop_rect = pygame.Rect(shop_pos[0], shop_pos[1], 650, 500); sdb = pygame.Rect(shop_pos[0], shop_pos[1], 650, 60)
    close_shop_btn = Button(shop_pos[0] + 580, shop_pos[1] + 10, 60, 40, "X", GRAY)
    tower_btns = [Button(shop_pos[0]+25, shop_pos[1]+100, 140, 50, "이걸 왜쏴 ㅋㅋ", BLUE, "PRINCESS"), Button(shop_pos[0]+175, shop_pos[1]+100, 140, 50, "집게이사장", PURPLE, "DUCHESS"), Button(shop_pos[0]+325, shop_pos[1]+100, 140, 50, "-3000로베로스", BLACK, "CANON"), Button(shop_pos[0]+475, shop_pos[1]+100, 140, 50, "지누텔라", BROWN, "JINUTELLA")]
    up_dmg_btn = Button(shop_pos[0]+30, shop_pos[1]+220, 280, 60, f"공격 강화 ({damage_gold_val}G)", RED)
    up_hp_btn = Button(shop_pos[0]+340, shop_pos[1]+220, 280, 60, f"체력 UP ({hp_gold_val}G)", GREEN)
    up_range_btn = Button(shop_pos[0]+30, shop_pos[1]+300, 590, 60, f"사거리 증가 ({range_gold_val}G)", CYAN)
    settings_rect = pygame.Rect(settings_pos[0], settings_pos[1], 450, 520)
    sdb_settings = pygame.Rect(settings_pos[0], settings_pos[1], 450, 60)
    close_settings_btn = Button(settings_pos[0] + 380, settings_pos[1] + 10, 60, 40, "X", GRAY)
    bgm_vol_down_btn = Button(settings_pos[0] + 240, settings_pos[1] + 80, 50, 50, "-", BLUE)
    bgm_vol_up_btn = Button(settings_pos[0] + 320, settings_pos[1] + 80, 50, 50, "+", RED)
    sfx_vol_down_btn = Button(settings_pos[0] + 240, settings_pos[1] + 150, 50, 50, "-", BLUE)
    sfx_vol_up_btn = Button(settings_pos[0] + 320, settings_pos[1] + 150, 50, 50, "+", RED)
    
    display_mode_y = settings_pos[1] + 260
    display_mode_window_btn = Button(settings_pos[0] + 30, display_mode_y, 185, 50, "창 모드", GRAY)
    display_mode_fullscreen_btn = Button(settings_pos[0] + 235, display_mode_y, 185, 50, "전체화면", GRAY)

    settings_jukku_btn = Button(settings_pos[0] + 30, settings_pos[1] + 340, 390, 60, "주꾸다시 (자폭)", DARK_RED)
    settings_quit_btn = Button(settings_pos[0] + 30, settings_pos[1] + 410, 390, 60, "게이 종료", DARK_RED)
    
    # 설정창 내 텍스트 클릭을 위한 Rect 미리 계산
    bgm_text_rect = get_text_surface(f"BGM 볼륨: {int(BGM_VOL * 100)}%", Fonts.BTN_LARGE, BLACK).get_rect(topleft=(settings_pos[0] + 40, settings_pos[1] + 95))
    sfx_text_rect = get_text_surface(f"효과음 볼륨: {int(SFX_VOL * 100)}%", Fonts.BTN_LARGE, BLACK).get_rect(topleft=(settings_pos[0] + 40, settings_pos[1] + 165))

    # --- 이벤트 처리 ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        if event.type == pygame.VIDEORESIZE:
            if display_mode_setting == 0:
                RESOLUTION = (event.w, event.h)
                display_surface = pygame.display.set_mode(RESOLUTION, pygame.DOUBLEBUF | pygame.RESIZABLE)
                background_image = load_smart_image("image/yousuck", RESOLUTION)
                aigonan_gif_frames = load_gif_frames_21_9("mte21.gif", RESOLUTION[0])
                init_fonts(RESOLUTION[1])
                init_ui()
        
        if CHEAT_MODE and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F1: gold += 10000000
            if event.key == pygame.K_F2: damage_level += 5
            if event.key == pygame.K_F3: nexus.hp = nexus.max_hp
            if event.key == pygame.K_F4: enemies = []
            if event.key == pygame.K_F5: is_break_time = not is_break_time; current_round = current_round+1 if not is_break_time else current_round; round_start_time = virtual_elapsed_time; enemies = []

        if event.type == pygame.MOUSEBUTTONDOWN:
            # --- 최상위 팝업 및 패널 처리 (클릭 이벤트 선점) ---
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
            if jukku_confirm_open:
                px, py = (RESOLUTION[0]-500)//2, (RESOLUTION[1]-250)//2
                if pygame.Rect(px+60, py+140, 160, 60).collidepoint(mx, my): pygame.mixer.music.stop(); game_state_mode = STATE_AIGONAN; jukku_confirm_open = False; (aigonan_sound.play() if aigonan_sound else None)
                elif pygame.Rect(px+280, py+140, 160, 60).collidepoint(mx, my): jukku_confirm_open = False
                continue
            
            if settings_open:
                if close_settings_btn.rect.collidepoint(mx, my): settings_open = False; continue
                if sdb_settings.collidepoint(mx, my): is_dragging_settings, drag_offset_settings = True, [settings_pos[0]-mx, settings_pos[1]-my]; continue
                if bgm_vol_down_btn.rect.collidepoint(mx, my): BGM_VOL = max(0.0, BGM_VOL - 0.1); pygame.mixer.music.set_volume(BGM_VOL)
                if bgm_vol_up_btn.rect.collidepoint(mx, my): BGM_VOL = min(1.0, BGM_VOL + 0.1); pygame.mixer.music.set_volume(BGM_VOL)
                if sfx_vol_down_btn.rect.collidepoint(mx, my): SFX_VOL = max(0.0, SFX_VOL - 0.1); [s.set_volume(SFX_VOL) for s in [aigonan_sound, oh_sound, bbolong_sound] if s]
                if sfx_vol_up_btn.rect.collidepoint(mx, my): SFX_VOL = min(1.0, SFX_VOL + 0.1); [s.set_volume(SFX_VOL) for s in [aigonan_sound, oh_sound, bbolong_sound] if s]
                if bgm_text_rect.collidepoint(mx, my):
                    val = show_input_dialog(display_surface, "BGM 볼륨 (0-100)");
                    if val is not None: BGM_VOL = max(0.0, min(1.0, val / 100.0)); pygame.mixer.music.set_volume(BGM_VOL)
                if sfx_text_rect.collidepoint(mx, my):
                    val = show_input_dialog(display_surface, "SFX 볼륨 (0-100)");
                    if val is not None: SFX_VOL = max(0.0, min(1.0, val / 100.0)); [s.set_volume(SFX_VOL) for s in [aigonan_sound, oh_sound, bbolong_sound] if s]
                if display_mode_window_btn.rect.collidepoint(mx, my) and display_mode_setting != 0: display_mode_setting = 0; update_display_mode()
                if display_mode_fullscreen_btn.rect.collidepoint(mx, my) and display_mode_setting != 1: display_mode_setting = 1; update_display_mode()
                if settings_jukku_btn.rect.collidepoint(mx, my): jukku_confirm_open = True
                if settings_quit_btn.rect.collidepoint(mx, my): quit_confirm_open = True
                if settings_rect.collidepoint(mx, my): continue

            if open_settings_btn.rect.collidepoint(mx, my): settings_open = not settings_open; continue

            # --- 게임 상태별 처리 ---
            if game_state_mode == STATE_START_SCREEN and start_btn.rect.collidepoint(mx, my):
                game_state_mode = STATE_MAP_SELECT
            elif game_state_mode == STATE_MAP_SELECT:
                if map_prev_btn.rect.collidepoint(mx, my):
                    current_map_index = (current_map_index - 1) % len(available_maps)
                elif map_next_btn.rect.collidepoint(mx, my):
                    current_map_index = (current_map_index + 1) % len(available_maps)
                elif map_select_confirm_btn.rect.collidepoint(mx, my):
                    reset_game(STATE_PLAYING)
                    play_round_music(current_round)
                elif map_select_back_btn.rect.collidepoint(mx, my):
                    game_state_mode = STATE_START_SCREEN

            elif game_state_mode == STATE_PLAYING:
                if show_skip_button and next_round_btn.rect.collidepoint(mx, my):
                    enemies.clear() # 타임아웃 등으로 남은 적이 있다면 제거
                    is_break_time, current_round, round_start_time, gold = True, current_round + 1, virtual_elapsed_time, gold + (100 * (current_round + 1))
                    play_round_music(current_round)
                    show_skip_button = False
                    continue
                if current_round > 40 and quit_btn.rect.collidepoint(mx, my): quit_confirm_open = True; continue
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
                if open_shop_btn.rect.collidepoint(mx, my): shop_open = not shop_open; continue
                if speed_btn.rect.collidepoint(mx, my): game_speed = 2 if game_speed==1 else (4 if game_speed==2 else 1); speed_btn.text = f"배속: {game_speed}x"
                elif can_place and gold >= TOWER_DATA[selected_tower_type]["cost"]: 
                    towers.append(Tower(mx, my, selected_tower_type)); gold -= TOWER_DATA[selected_tower_type]["cost"]
            elif game_state_mode == STATE_AIGONAN and retry_btn.rect.collidepoint(mx, my):
                reset_game()
                play_round_music(current_round)
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
                    is_break_time, round_start_time, last_spawn_time, boss_spawn_count, show_skip_button = False, virtual_elapsed_time, virtual_elapsed_time, 0, False
                    if current_round > 1: round_gold_value = int(round_gold_value * 1.5) # [복리] 라운드 시작 시 가치 상승
                    
                    # 현재 라운드에 스폰할 몬스터 수 계산
                    enemies_spawned_this_round = 0
                    if current_round == 40:
                        enemies_to_spawn_this_round = 10
                    else:
                        spawn_interval_secs = max(0.4, 1.5 - current_round*0.05)
                        enemies_to_spawn_this_round = math.floor(45 / spawn_interval_secs) if spawn_interval_secs > 0 else 50

            elif is_overtime:
                time_left = 0
                if not enemies:
                    is_overtime = False
                    show_skip_button = True
                elif (virtual_elapsed_time - overtime_start_time >= 60):
                    # 60초 초과 시에도 버튼을 표시하여 수동으로 넘어가도록 변경
                    is_overtime = False
                    show_skip_button = True
            else:
                time_left = max(0, 45 - c_time)
                all_spawned = enemies_spawned_this_round >= enemies_to_spawn_this_round
                
                if not all_spawned:
                    if current_round == 40:
                        if boss_spawn_count < 10 and virtual_elapsed_time - last_spawn_time > 2.0: enemies.append(Enemy(enemy_path, 40, True)); boss_spawn_count += 1; enemies_spawned_this_round += 1; last_spawn_time = virtual_elapsed_time
                    elif virtual_elapsed_time - last_spawn_time > max(0.4, 1.5 - current_round*0.05):
                        enemies.append(Enemy(enemy_path, current_round, (current_round%5==0 and not any(e.is_boss for e in enemies)))); enemies_spawned_this_round += 1; last_spawn_time = virtual_elapsed_time
                
                if all_spawned and not enemies and not is_overtime:
                    show_skip_button = True

                if time_left <= 0:
                    if not all_spawned:
                        pass
                    elif enemies:
                        is_overtime = True
                        overtime_start_time = virtual_elapsed_time
        
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
                        else: projectiles.append(Projectile(t.rect.center, e, get_current_damage(t.type), d["p_img"], projectile_images))
                        t.attack_timer = d["cd"]; break
        if nexus.attack_timer > 0: nexus.attack_timer -= 1 * game_speed * (dt * 144)
        else:
            eff_range = 300 + (range_level - 1) * 20
            for e in enemies:
                if math.hypot(e.rect.centerx-nexus.rect.centerx, e.rect.centery-nexus.rect.centery) <= eff_range:
                    projectiles.append(Projectile(nexus.rect.center, e, get_current_damage("PRINCESS") * 2, "mte23", projectile_images))
                    nexus.attack_timer = nexus.cd; break
        for e in enemies[:]:
            e.move(dt, game_speed)
            if e.hp <= 0: 
                gold += round_gold_value * (5 if e.is_boss else 1) # [복리] 적용된 골드 지급
                if e.is_boss:
                    if aigonan_sound: aigonan_sound.play()
                elif bbolong_sound: bbolong_sound.play()
                enemies.remove(e)
            elif e.target_idx >= len(enemy_path): 
                nexus.hp -= 2000 if e.is_boss else 1000; enemies.remove(e)
                if nexus.hp <= 0: pygame.mixer.music.stop(); game_state_mode = STATE_AIGONAN; (aigonan_sound.play() if aigonan_sound else None)

    # --- 그리기 ---
    display_surface.blit(background_image, (0, 0)) if background_image else display_surface.fill(BLACK)
    if game_state_mode == STATE_START_SCREEN:
        overlay = pygame.Surface(RESOLUTION, pygame.SRCALPHA); overlay.fill((0,0,0,220)); display_surface.blit(overlay, (0,0))
        panel_w, panel_h = int(RESOLUTION[0] * 0.8), int(RESOLUTION[1] * 0.8)
        h_rect = pygame.Rect((RESOLUTION[0] - panel_w)//2, (RESOLUTION[1] - panel_h)//2, panel_w, panel_h)
        pygame.draw.rect(display_surface, WHITE, h_rect, border_radius=30)
        title_surf = get_text_surface("케인 디펜스 - GayDefense", Fonts.TITLE, BLACK)
        display_surface.blit(title_surf, (h_rect.centerx - title_surf.get_width() // 2, h_rect.y + int(panel_h * 0.1)))
        helps = [f"● 치트(헉) 상태: {'활성' if CHEAT_MODE else '비활성'}", f"● 자! 처치골드: {round_gold_value}G만큼 시작!(1.5배))", "● 40라운드 까지 조이면 최종보스, ", "● 지(으악)라는 광역 공격", "● 방음부스 체력 0 되면 게이ㅁ 종료", "● 타워 우클릭시 70% 가격으로 판매"]
        for i, txt in enumerate(helps):
            display_surface.blit(get_text_surface(txt, Fonts.HELP, BLACK), (h_rect.x + int(panel_w * 0.1), h_rect.y + int(panel_h * 0.25) + i * int(panel_h * 0.08)))
        start_btn.draw(display_surface)
        
    elif game_state_mode == STATE_MAP_SELECT:
        overlay = pygame.Surface(RESOLUTION, pygame.SRCALPHA); overlay.fill((0,0,0,220)); display_surface.blit(overlay, (0,0))
        
        # 맵 선택 UI
        map_name = available_maps[current_map_index]["name"]
        map_surf = get_text_surface(f"MAP: {map_name}", Fonts.UI, WHITE)
        display_surface.blit(map_surf, (RESOLUTION[0]//2 - map_surf.get_width()//2, int(RESOLUTION[1] * 0.2)))
        
        # 미리보기
        preview_rect = pygame.Rect(0, 0, 600, 350)
        preview_rect.center = (RESOLUTION[0]//2, RESOLUTION[1]//2)
        pygame.draw.rect(display_surface, WHITE, preview_rect)
        pygame.draw.rect(display_surface, BLACK, preview_rect, 3)
        
        p_path = available_maps[current_map_index]["path"]
        if p_path:
            scaled_path = [(preview_rect.x + p[0]*(preview_rect.width/24) + (preview_rect.width/48), preview_rect.y + p[1]*(preview_rect.height/14) + (preview_rect.height/28)) for p in p_path]
            if len(scaled_path) > 1: pygame.draw.lines(display_surface, BLUE, False, scaled_path, 5)
            pygame.draw.circle(display_surface, GREEN, (int(scaled_path[0][0]), int(scaled_path[0][1])), 8)
            pygame.draw.circle(display_surface, RED, (int(scaled_path[-1][0]), int(scaled_path[-1][1])), 8)
            
        map_prev_btn.draw(display_surface)
        map_next_btn.draw(display_surface)
        map_select_confirm_btn.draw(display_surface)
        map_select_back_btn.draw(display_surface)
        
    elif game_state_mode == STATE_PLAYING:
        pygame.draw.lines(display_surface, PATH_COLOR, False, enemy_path, 50)
        if shop_open and not (shop_rect.collidepoint(mx, my)) and current_round <= 40:
            ps = pygame.Surface((GRID_SIZE, GRID_SIZE), pygame.SRCALPHA); pygame.draw.rect(ps, (0,255,0,100) if can_place else (255,0,0,100), (0,0,GRID_SIZE,GRID_SIZE)); display_surface.blit(ps, (gmx, gmy))
            rv = TOWER_DATA[selected_tower_type]["range"] + (range_level - 1) * 20; rs = pygame.Surface((rv*2, rv*2), pygame.SRCALPHA); pygame.draw.circle(rs, (255,255,255,60), (rv,rv), rv); display_surface.blit(rs, (gmx+GRID_SIZE//2-rv, gmy+GRID_SIZE//2-rv))
        for t in towers: t.draw(display_surface, range_level)
        for e in enemies: e.draw(display_surface)
        for p in projectiles: p.draw(display_surface)
        nexus.draw(display_surface); open_shop_btn.draw(display_surface); speed_btn.draw(display_surface)
        display_surface.blit(get_text_surface(f"GOLD: {gold} (마리당: {round_gold_value}G) | 공격 Lv: {damage_level} | HP Lv: {hp_level} | 사거리 Lv: {range_level}", Fonts.UI, BLACK), (int(RESOLUTION[0]*0.02), int(RESOLUTION[1]*0.03)))
        display_surface.blit(get_text_surface(f"{f'라운드 {current_round} 조이고 ' if not is_break_time else '정리좀하고(%s초쯤)' % int(time_left)}| 남은 시간: {int(time_left)}초", Fonts.UI, DARK_RED), (int(RESOLUTION[0]*0.02), int(RESOLUTION[1]*0.08)))
        if shop_open:
            pygame.draw.rect(display_surface, (230,230,230), shop_rect, border_radius=20); pygame.draw.rect(display_surface, (150,150,150), sdb, border_radius=20); close_shop_btn.draw(display_surface)
            draw_text_with_outline(display_surface, "★ 타워조이고 ★", Fonts.SHOP_TITLE, (shop_pos[0]+20, shop_pos[1]+15), WHITE, BLACK)
            for b in tower_btns:
                b.draw(display_surface, selected_tower_type == b.val)
                dmg_txt = get_text_surface(f"공격력: {get_current_damage(b.val)}", Fonts.DMG_TEXT, BLACK)
                display_surface.blit(dmg_txt, (b.rect.centerx - dmg_txt.get_width()//2, b.rect.bottom + 5))
            up_dmg_btn.draw(display_surface); up_hp_btn.draw(display_surface); up_range_btn.draw(display_surface)
        if current_round > 40:
            if not ending_sound_played: pygame.mixer.music.stop(); pygame.mixer.stop(); (oh_sound.play() if oh_sound else None); ending_sound_played = True
            if mte22_image:
                m_rect = mte22_image.get_rect(center=(RESOLUTION[0]//2, RESOLUTION[1]//2)); display_surface.blit(mte22_image, m_rect)
                txt = get_text_surface("클(로버핏)리어!", Fonts.CLEAR, YELLOW); display_surface.blit(txt, txt.get_rect(center=m_rect.center))
                quit_btn.rect.midtop = (m_rect.centerx, m_rect.bottom + 50); quit_btn.draw(display_surface)
        if show_skip_button:
            overlay = pygame.Surface(RESOLUTION, pygame.SRCALPHA); overlay.fill((0,0,0,150)); display_surface.blit(overlay, (0,0))
            reward_txt = get_text_surface(f"라운드 클리어 보상: {100 * (current_round + 1)}G", Fonts.TITLE, YELLOW)
            display_surface.blit(reward_txt, (RESOLUTION[0]//2 - reward_txt.get_width()//2, RESOLUTION[1]//2 - int(50 * (RESOLUTION[1]/1080.0))))
            next_round_btn.draw(display_surface)
    elif game_state_mode == STATE_AIGONAN:
        display_surface.fill((20, 0, 0))
        if aigonan_gif_frames:
            gif_frame_idx = (gif_frame_idx + 1) % len(aigonan_gif_frames)
            img = aigonan_gif_frames[gif_frame_idx]; display_surface.blit(img, img.get_rect(center=(RESOLUTION[0]//2, RESOLUTION[1]//2)))
        elif mte21_image: display_surface.blit(mte21_image, mte21_image.get_rect(center=(RESOLUTION[0]//2, RESOLUTION[1]//2 - 50)))
        display_surface.blit(get_text_surface("아이고난!", Fonts.GAMEOVER, RED), (RESOLUTION[0]//2-200, int(RESOLUTION[1]*0.15))); retry_btn.draw(display_surface)
    
    # --- 전역 UI 및 팝업 그리기 (항상 위에 표시) ---
    open_settings_btn.draw(display_surface)
    if settings_open:
        pygame.draw.rect(display_surface, (230, 230, 230), settings_rect, border_radius=20)
        pygame.draw.rect(display_surface, (150, 150, 150), sdb_settings, border_radius=20)
        close_settings_btn.draw(display_surface)
        draw_text_with_outline(display_surface, "★ 설정조이고 ★", Fonts.SHOP_TITLE, (settings_pos[0] + 20, settings_pos[1] + 15), WHITE, BLACK)
        display_surface.blit(get_text_surface(f"BGM 볼륨: {int(BGM_VOL * 100)}%", Fonts.BTN_LARGE, BLACK), bgm_text_rect)
        bgm_vol_down_btn.draw(display_surface); bgm_vol_up_btn.draw(display_surface)
        display_surface.blit(get_text_surface(f"효과음 볼륨: {int(SFX_VOL * 100)}%", Fonts.BTN_LARGE, BLACK), sfx_text_rect)
        sfx_vol_down_btn.draw(display_surface); sfx_vol_up_btn.draw(display_surface)
        display_surface.blit(get_text_surface("화면 설정", Fonts.BTN_LARGE, BLACK), (settings_pos[0] + 40, settings_pos[1] + 225))
        display_mode_window_btn.draw(display_surface, display_mode_setting == 0)
        display_mode_fullscreen_btn.draw(display_surface, display_mode_setting == 1)
        settings_jukku_btn.draw(display_surface); settings_quit_btn.draw(display_surface)

    if sell_confirm_open:
        sx, sy = (RESOLUTION[0]-500)//2, (RESOLUTION[1]-250)//2; pygame.draw.rect(display_surface, WHITE, (sx, sy, 500, 250), border_radius=20)
        display_surface.blit(get_text_surface(f"이 타워를 {int(tower_to_sell.cost*0.7)}G에 파냐맨이야?", Fonts.UI, BLACK), (sx+80, sy+60))
        Button(sx+60, sy+140, 160, 60, "조이기", RED).draw(display_surface); Button(sx+280, sy+140, 160, 60, "안조이기", GRAY).draw(display_surface)
    if jukku_confirm_open:
        px, py = (RESOLUTION[0]-500)//2, (RESOLUTION[1]-250)//2; pygame.draw.rect(display_surface, WHITE, (px, py, 500, 250), border_radius=20); display_surface.blit(get_text_surface("정말 자폭하시겠습니까?", Fonts.UI, BLACK), (px+120, py+50))
        Button(px+60, py+140, 160, 60, "조이기", RED).draw(display_surface); Button(px+280, py+140, 160, 60, "안조이기", GRAY).draw(display_surface)
    if quit_confirm_open:
        qx, qy = (RESOLUTION[0]-500)//2, (RESOLUTION[1]-250)//2; pygame.draw.rect(display_surface, WHITE, (qx, qy, 500, 250), border_radius=20)
        display_surface.blit(get_text_surface("정말 종료하시겠습니까?", Fonts.POPUP_TITLE, BLACK), (qx+100, qy+60))
        Button(qx+60, qy+140, 160, 60, "조이기", RED).draw(display_surface); Button(qx+280, qy+140, 160, 60, "안조이기", GRAY).draw(display_surface)
    pygame.display.update()
pygame.quit(); sys.exit()