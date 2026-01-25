import pygame
import random
from mte_config import *

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
    def __init__(self, pos, img):
        self.image = img; self.rect = img.get_rect(center=pos) if img else pygame.Rect(pos[0]-60, pos[1]-60, 120, 120)
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
                self.target_idx += 1
                move_step -= dist
            else:
                if dist > 0: self.pos += dir_vec.normalize() * move_step
                move_step = 0
        self.rect.center = (int(self.pos.x), int(self.pos.y))
    def draw(self, surface):
        if self.image: surface.blit(self.image, self.rect)
        pygame.draw.rect(surface, RED, (self.rect.x, self.rect.y-10, self.rect.width, 4))
        pygame.draw.rect(surface, GREEN, (self.rect.x, self.rect.y-10, self.rect.width*(max(0, self.hp)/self.max_hp), 4))
        hp_text = f"{int(self.hp)}"
        txt_surf = get_text_surface(hp_text, FONT_HP, WHITE)
        shadow_surf = get_text_surface(hp_text, FONT_HP, BLACK)
        txt_pos_x = self.rect.centerx - txt_surf.get_width() // 2
        surface.blit(shadow_surf, (txt_pos_x + 1, self.rect.y - 29))
        surface.blit(txt_surf, (txt_pos_x, self.rect.y - 30))

class Projectile:
    def __init__(self, start_pos, target_enemy, dmg, img_key, p_images, speed=15):
        self.pos, self.target_enemy, self.dmg, self.speed, self.reached = pygame.Vector2(start_pos), target_enemy, dmg, speed, False
        self.image = p_images.get(img_key)
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
    def draw(self, surface, range_level):
        if self.type == "JINUTELLA" and self.effect_timer > 0:
            rv = TOWER_DATA[self.type]["range"] + (range_level - 1) * 20
            es = get_range_surface(rv, BROWN_ALPHA)
            surface.blit(es, (self.rect.centerx-rv, self.rect.centery-rv))
        if self.image: surface.blit(self.image, self.rect)
        else: pygame.draw.rect(surface, TOWER_DATA[self.type]["color"], self.rect.inflate(-20,-20), border_radius=5)
        if self.attack_timer > 0:
            bw = GRID_SIZE * 0.8; fw = bw * (self.attack_timer / TOWER_DATA[self.type]["cd"])
            pygame.draw.rect(surface, GRAY, (self.rect.x + (GRID_SIZE-bw)//2, self.rect.y+5, bw, 6))
            pygame.draw.rect(surface, YELLOW, (self.rect.x + (GRID_SIZE-bw)//2, self.rect.y+5, fw, 6))
            cd_txt = get_text_surface(f"{self.attack_timer/60:.1f}s", FONT_COOLDOWN, BLACK)
            surface.blit(cd_txt, (self.rect.centerx - cd_txt.get_width()//2, self.rect.y + 12))