import pygame
import os
import sys
import argparse
from PIL import Image

# --- 실행 인수 처리 ---
parser = argparse.ArgumentParser()
parser.add_argument("--cheat", action="store_true", help="치트 모드를 활성화합니다.")
args = parser.parse_known_args()[0]
CHEAT_MODE = args.cheat

# --- 초기화 ---
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)

# --- 리소스 경로 처리 ---
def resource_path(relative_path):
    # 1. 로컬 파일 우선 확인 (모딩 및 개발 편의성)
    if os.path.exists(relative_path):
        return os.path.abspath(relative_path)
    # 2. PyInstaller 임시 폴더 확인
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# --- 설정 및 전역 변수 ---
infoObject = pygame.display.Info()
RESOLUTION = (infoObject.current_w, infoObject.current_h)
FONT_SCALE = max(0.5, min(2.5, RESOLUTION[1] / 1080.0))
FPS = 144
GRID_SIZE = 80 
damage_gold_val = 50
hp_gold_val = 200
range_gold_val = 150

F_DMG_PRINCESS = 10
F_DMG_DUCHESS = 4
F_DMG_CANON = 20
F_DMG_JINUTELLA = 2

BGM_VOL = 0.3
SFX_VOL = 0.5

STATE_INTRO = -2
STATE_MENU = -1
STATE_PLAYING = 0
STATE_AIGONAN = 1

WHITE, BLACK, RED, BLUE, GREEN = (255, 255, 255), (0, 0, 0), (255, 0, 0), (0, 0, 255), (0, 255, 0)
YELLOW, PURPLE, CYAN, BROWN = (255, 255, 0), (128, 0, 128), (0, 255, 255), (139, 69, 19)
DARK_RED, GRAY = (150, 0, 0), (50, 50, 50)
PATH_COLOR = (200, 200, 200)
BROWN_ALPHA = (139, 69, 19, 120) 

# --- 폰트 및 캐시 ---
FONT_FILE = resource_path("font/D2Coding.ttf")
TEXT_CACHE = {}
RANGE_SURFACE_CACHE = {}

class GameFonts:
    pass
Fonts = GameFonts()

def create_font(size, bold=False, italic=False):
    scaled_size = int(size * FONT_SCALE)
    if os.path.exists(FONT_FILE):
        try:
            font = pygame.font.Font(FONT_FILE, scaled_size)
            font.set_bold(bold)
            font.set_italic(italic)
            return font
        except Exception: pass
    return pygame.font.SysFont("malgungothic", scaled_size, bold, italic)

def init_fonts(screen_height):
    global FONT_SCALE
    FONT_SCALE = max(0.5, min(2.5, screen_height / 1080.0))
    TEXT_CACHE.clear() # 폰트 변경 시 캐시 초기화
    
    Fonts.HP = create_font(16, bold=True)
    Fonts.SHOP_TITLE = create_font(30, bold=True)
    Fonts.BTN_SMALL = create_font(18, bold=True)
    Fonts.BTN_LARGE = create_font(22, bold=True)
    Fonts.COOLDOWN = create_font(14, bold=True)
    Fonts.UI = create_font(25, bold=True)
    Fonts.DMG_TEXT = create_font(15, bold=True)
    Fonts.TITLE = create_font(60, bold=True)
    Fonts.HELP = create_font(30)
    Fonts.GAMEOVER = create_font(100, bold=True)
    Fonts.POPUP_TITLE = create_font(30, bold=True)
    Fonts.CLEAR = create_font(100, bold=True)

init_fonts(RESOLUTION[1])

# --- 리소스 로더 함수 ---
def get_text_surface(text, font, color):
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
        try:
            s = pygame.mixer.Sound(full_path); s.set_volume(SFX_VOL)
            return s
        except: return None
    return None

# --- 데이터 ---
TOWER_DATA = {
    "PRINCESS": {"name": "이걸 왜쏴 ㅋㅋ", "cost": 100, "range": 300, "dmg": F_DMG_PRINCESS, "cd": 20, "color": BLUE, "image_path": "image/uring1", "p_img": "mte23"},
    "DUCHESS": {"name": "집게이사장", "cost": 250, "range": 200, "dmg": F_DMG_DUCHESS, "cd": 5, "color": PURPLE, "image_path": "image/uring2", "p_img": "mte24"},
    "CANON": {"name": "-3000로베로스", "cost": 400, "range": 400, "dmg": F_DMG_CANON, "cd": 60, "color": CYAN, "image_path": "image/uring3", "p_img": "mte25"},
    "JINUTELLA": {"name": "지누텔라", "cost": 500, "range": 160, "dmg": F_DMG_JINUTELLA, "cd": 15, "color": YELLOW, "image_path": "image/mte20", "p_img": None}
}