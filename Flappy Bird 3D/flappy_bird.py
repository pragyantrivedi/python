import pygame
import sys
import random
import os
from pygame import gfxdraw
import time
import math

pygame.init()

SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
GRAVITY = 0.25
BIRD_JUMP = -5
OBSTACLE_GAP = 150
OBSTACLE_FREQUENCY = 1500
FLOOR_HEIGHT = 100
FPS = 60
LAST_FRAME_TIME = time.time()

DAY_MODE = 0
NIGHT_MODE = 1
MODE_TRANSITION_SPEED = 0.05

DAY_SKY = (135, 206, 235)
NIGHT_SKY = (25, 25, 50)
DAY_GROUND = (139, 69, 19)
NIGHT_GROUND = (50, 25, 0)
DAY_GRASS = (34, 139, 34)
NIGHT_GRASS = (20, 70, 20)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Flappy Bird 3D')
clock = pygame.time.Clock()
font = pygame.font.SysFont('Arial', 30)

SKY_BLUE = (135, 206, 235)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 128, 0)
BROWN = (139, 69, 19)
LIGHT_GREEN = (34, 139, 34)

class Bird:
    def __init__(self):
        self.x = SCREEN_WIDTH // 3
        self.y = SCREEN_HEIGHT // 2
        self.velocity = 0
        self.size = 20
        self.image = pygame.image.load(os.path.join('assets', 'bird.png'))
        self.image = pygame.transform.scale(self.image, (self.size * 2, self.size * 2))
        self.rect = self.image.get_rect(center=(self.x, self.y))
        self.rotation = 0
        self.shadow_offset = 8
    
    def draw(self):
        shadow_image = pygame.transform.rotate(self.image, self.rotation)
        shadow_image.set_alpha(100)
        shadow_rect = shadow_image.get_rect(center=(self.x + self.shadow_offset, self.y + self.shadow_offset))
        screen.blit(shadow_image, shadow_rect)
        
        rotated_image = pygame.transform.rotate(self.image, self.rotation)
        self.rect = rotated_image.get_rect(center=(self.x, self.y))
        screen.blit(rotated_image, self.rect)
    
    def update(self):
        self.velocity += GRAVITY
        self.y += self.velocity
        
        if self.y + self.size > SCREEN_HEIGHT - FLOOR_HEIGHT:
            self.y = SCREEN_HEIGHT - FLOOR_HEIGHT - self.size
            self.velocity = 0
            
        self.rotation = max(-30, min(self.velocity * 3, 70))
    
    def jump(self):
        self.velocity = BIRD_JUMP
    
    def get_mask(self):
        return pygame.Rect(self.x - self.size//2, self.y - self.size//2, 
                          self.size, self.size)

class Obstacle:
    def __init__(self, x):
        self.x = x
        self.height = random.randint(100, SCREEN_HEIGHT - FLOOR_HEIGHT - OBSTACLE_GAP - 100)
        self.passed = False
        self.width = 60
        
        self.sprite_sheet = pygame.image.load(os.path.join('assets', 'dinosaur.png'))
        
        self.dino_image = pygame.Surface((44, 47), pygame.SRCALPHA)
        self.dino_image.blit(self.sprite_sheet, (0, 0), (848, 2, 44, 47))
        
        black_filter = pygame.Surface(self.dino_image.get_size(), pygame.SRCALPHA)
        black_filter.fill((0, 0, 0, 255))
        
        original_alpha = pygame.surfarray.pixels_alpha(self.dino_image).copy()
        self.dino_image.blit(black_filter, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        pygame.surfarray.pixels_alpha(self.dino_image)[:] = original_alpha
        
        self.dino_size = (50, 50)
        self.dino_image = pygame.transform.scale(self.dino_image, self.dino_size)
        
        self.top_dinos = []
        self.bottom_dinos = []
        
        for i in range(0, self.height, self.dino_size[1]):
            if random.random() > 0.5:
                self.top_dinos.append(i)
        
        bottom_space = SCREEN_HEIGHT - FLOOR_HEIGHT - self.height - OBSTACLE_GAP
        for i in range(0, bottom_space, self.dino_size[1]):
            if random.random() > 0.5:
                self.bottom_dinos.append(i)
    
    def draw(self):
        shadow_offset = 8
        shadow_img = self.dino_image.copy()
        shadow_img.set_alpha(100)
        
        for y_pos in self.top_dinos:
            screen.blit(shadow_img, (self.x + shadow_offset, y_pos + shadow_offset))
            screen.blit(self.dino_image, (self.x, y_pos))
        
        bottom_y_start = self.height + OBSTACLE_GAP
        for y_offset in self.bottom_dinos:
            y_pos = bottom_y_start + y_offset
            screen.blit(shadow_img, (self.x + shadow_offset, y_pos + shadow_offset))
            screen.blit(self.dino_image, (self.x, y_pos))
    
    def update(self):
        self.x -= 3
    
    def collide(self, bird):
        bird_rect = bird.get_mask()
        
        for y_pos in self.top_dinos:
            dino_rect = pygame.Rect(self.x, y_pos, self.dino_size[0], self.dino_size[1])
            if bird_rect.colliderect(dino_rect):
                return True
        
        bottom_y_start = self.height + OBSTACLE_GAP
        for y_offset in self.bottom_dinos:
            y_pos = bottom_y_start + y_offset
            dino_rect = pygame.Rect(self.x, y_pos, self.dino_size[0], self.dino_size[1])
            if bird_rect.colliderect(dino_rect):
                return True
        
        return False

class Background:
    def __init__(self):
        self.cloud_positions = []
        self.cloud_speeds = []
        self.cloud_sizes = []
        self.sun_pos = (SCREEN_WIDTH - 80, 80)
        self.moon_pos = (80, 80)
        self.mountains = []
        self.mountain_details = []
        self.trees = []
        
        for i in range(8):
            mountain_x = random.randint(-100, SCREEN_WIDTH + 100)
            mountain_h = random.randint(100, 250)
            mountain_w = random.randint(200, 350)
            
            detail_points = [(mountain_x - mountain_w//2, SCREEN_HEIGHT - FLOOR_HEIGHT)]
            
            steps = 40
            last_height = 0
            for j in range(1, steps):
                x = mountain_x - mountain_w//2 + (mountain_w * j // steps)
                progress = j / steps
                height_factor = 1.0 - 4 * (progress - 0.5) * (progress - 0.5)
                height_variation = math.sin(j * 0.5) * 15 + random.randint(-8, 8)
                
                height_variation = (height_variation + last_height) / 2
                last_height = height_variation
                
                y = SCREEN_HEIGHT - FLOOR_HEIGHT - mountain_h * height_factor + height_variation
                detail_points.append((x, y))
                
            detail_points.append((mountain_x + mountain_w//2, SCREEN_HEIGHT - FLOOR_HEIGHT))
            
            has_snow = mountain_h > 180
            snow_line = mountain_h * 0.3
            
            snow_points = []
            if has_snow:
                for x, y in detail_points:
                    if y <= SCREEN_HEIGHT - FLOOR_HEIGHT - mountain_h + snow_line:
                        snow_points.append((x, y))
            
            texture_points = []
            for k in range(random.randint(3, 8)):
                tx = random.randint(mountain_x - mountain_w//3, mountain_x + mountain_w//3)
                ty = random.randint(SCREEN_HEIGHT - FLOOR_HEIGHT - mountain_h//2, 
                                  SCREEN_HEIGHT - FLOOR_HEIGHT - mountain_h//5)
                size = random.randint(10, 30)
                texture_points.append((tx, ty, size))
            
            trees_count = random.randint(2, 6)
            mountain_trees = []
            for _ in range(trees_count):
                tree_x = random.randint(mountain_x - mountain_w//3, mountain_x + mountain_w//3)
                tree_y = SCREEN_HEIGHT - FLOOR_HEIGHT - random.randint(20, mountain_h//3)
                tree_height = random.randint(15, 30)
                tree_width = random.randint(8, 15)
                mountain_trees.append((tree_x, tree_y, tree_height, tree_width))
            
            mountain_data = {
                'base': (mountain_x, mountain_h, mountain_w),
                'detail': detail_points,
                'has_snow': has_snow,
                'snow': snow_points,
                'texture': texture_points,
                'trees': mountain_trees
            }
            self.mountains.append(mountain_data)
        
        self.mountains.sort(key=lambda m: m['base'][1])
        
        for _ in range(10):
            tree_x = random.randint(0, SCREEN_WIDTH)
            tree_y = SCREEN_HEIGHT - FLOOR_HEIGHT
            tree_height = random.randint(30, 70)
            tree_width = random.randint(15, 30)
            self.trees.append((tree_x, tree_y, tree_height, tree_width))
        
        self.stars = [(random.randint(0, SCREEN_WIDTH), 
                      random.randint(10, SCREEN_HEIGHT - FLOOR_HEIGHT - 50), 
                      random.random() * 0.8 + 0.2)
                     for _ in range(100)]
        
        for _ in range(10):
            self.cloud_positions.append([random.randint(0, SCREEN_WIDTH), 
                                        random.randint(20, SCREEN_HEIGHT//3)])
            self.cloud_speeds.append(random.uniform(0.2, 0.8))
            self.cloud_sizes.append(random.uniform(0.7, 1.3))
    
    def draw(self, mode_transition=0.0):
        for i in range(SCREEN_HEIGHT - FLOOR_HEIGHT):
            day_color_value = 235 - int(i * 0.2)
            day_color = (135, 206, day_color_value)
            
            night_color_value = max(0, 50 - int(i * 0.15))
            night_color = (25, 25, night_color_value)
            
            r = int(day_color[0] * (1 - mode_transition) + night_color[0] * mode_transition)
            g = int(day_color[1] * (1 - mode_transition) + night_color[1] * mode_transition)
            b = int(day_color[2] * (1 - mode_transition) + night_color[2] * mode_transition)
            
            pygame.draw.line(screen, (r, g, b), (0, i), (SCREEN_WIDTH, i))
        
        for x, y, brightness in self.stars:
            star_alpha = int(255 * mode_transition * brightness)
            if star_alpha > 0:
                star_brightness = min(255, star_alpha)
                if random.random() > 0.99:
                    star_brightness = min(255, star_brightness + 50)
                pygame.draw.circle(screen, (star_brightness, star_brightness, star_brightness), (int(x), int(y)), 1)
        
        sun_alpha = int(255 * (1 - mode_transition))
        moon_alpha = int(255 * mode_transition)
        
        if sun_alpha > 0:
            sun_alpha_safe = min(255, sun_alpha) 
            pygame.draw.circle(screen, (255, 255, 200), (self.sun_pos[0], self.sun_pos[1]), 40)
            
            for i in range(5):
                glow_alpha = max(0, min(255, sun_alpha - i*50))
                if glow_alpha > 10:
                    glow_surface = pygame.Surface((80 + i*10, 80 + i*10), pygame.SRCALPHA)
                    pygame.draw.circle(glow_surface, (255, 255, 150, glow_alpha), 
                                     (40 + i*5, 40 + i*5), 40 + i*5)
                    screen.blit(glow_surface, (self.sun_pos[0] - 40 - i*5, self.sun_pos[1] - 40 - i*5))
        
        if moon_alpha > 0:
            moon_alpha_safe = min(255, moon_alpha)
            pygame.draw.circle(screen, (220, 220, 230), (self.moon_pos[0], self.moon_pos[1]), 30)
            
            if moon_alpha > 100:
                crater_color = (200, 200, 210)
                pygame.draw.circle(screen, crater_color, (self.moon_pos[0] - 10, self.moon_pos[1] - 15), 8)
                pygame.draw.circle(screen, crater_color, (self.moon_pos[0] + 10, self.moon_pos[1] - 5), 6)
                pygame.draw.circle(screen, crater_color, (self.moon_pos[0] - 15, self.moon_pos[1] + 5), 7)
                pygame.draw.circle(screen, crater_color, (self.moon_pos[0] + 5, self.moon_pos[1] + 10), 9)
            
            for i in range(3):
                glow_alpha = max(0, min(255, moon_alpha - i*70))
                if glow_alpha > 10:
                    glow_surface = pygame.Surface((60 + i*10, 60 + i*10), pygame.SRCALPHA)
                    pygame.draw.circle(glow_surface, (220, 220, 240, glow_alpha), 
                                    (30 + i*5, 30 + i*5), 30 + i*5)
                    screen.blit(glow_surface, (self.moon_pos[0] - 30 - i*5, self.moon_pos[1] - 30 - i*5))
        
        for mountain in self.mountains:
            mx, mh, mw = mountain['base']
            mountain_detail = mountain['detail']
            
            shadow_r = int(100 * (1 - mode_transition) + 40 * mode_transition)
            shadow_g = int(70 * (1 - mode_transition) + 30 * mode_transition)
            shadow_b = int(30 * (1 - mode_transition) + 20 * mode_transition)
            shadow_color = (shadow_r, shadow_g, shadow_b)
            
            pygame.draw.polygon(screen, shadow_color, mountain_detail)
            
            for i in range(0, mh, 3):
                ratio = i / mh
                
                if ratio > 0.7:
                    day_r = 139 - int(ratio * 30)
                    day_g = 69 - int(ratio * 20)
                    day_b = 19
                else:
                    green_intensity = int(120 + (1-ratio) * 80)
                    brown_intensity = int(30 + ratio * 70)
                    day_r = brown_intensity
                    day_g = green_intensity
                    day_b = 30
                
                if ratio > 0.7:
                    night_r = 50 - int(ratio * 15)
                    night_g = 50 - int(ratio * 25)
                    night_b = 70 - int(ratio * 30)
                else:
                    night_r = 30 + int(ratio * 20)
                    night_g = 40 + int(ratio * 10)
                    night_b = 60
                
                r = int(day_r * (1 - mode_transition) + night_r * mode_transition)
                g = int(day_g * (1 - mode_transition) + night_g * mode_transition)
                b = int(day_b * (1 - mode_transition) + night_b * mode_transition)
                color = (r, g, b)
                
                height_points = []
                for x, y in mountain_detail:
                    if y <= SCREEN_HEIGHT - FLOOR_HEIGHT - i:
                        height_points.append((x, SCREEN_HEIGHT - FLOOR_HEIGHT - i))
                
                if len(height_points) >= 2:
                    for j in range(len(height_points) - 1):
                        pygame.draw.line(screen, color, height_points[j], height_points[j+1])
            
            for tx, ty, size in mountain['texture']:
                rock_color = (shadow_r - 20, shadow_g - 10, shadow_b - 5)
                pygame.draw.circle(screen, rock_color, (tx, ty), size)
                highlight_color = (shadow_r + 30, shadow_g + 20, shadow_b + 10)
                pygame.draw.circle(screen, highlight_color, (tx - size//3, ty - size//3), size//2)
            
            if mountain['has_snow'] and len(mountain['snow']) >= 3:
                snow_points = mountain['snow'] + [(mountain['snow'][-1][0], mountain['snow'][0][1])]
                
                day_snow = (250, 250, 255)
                night_snow = (200, 210, 255)
                r = int(day_snow[0] * (1 - mode_transition) + night_snow[0] * mode_transition)
                g = int(day_snow[1] * (1 - mode_transition) + night_snow[1] * mode_transition)
                b = int(day_snow[2] * (1 - mode_transition) + night_snow[2] * mode_transition)
                
                pygame.draw.polygon(screen, (r, g, b), snow_points)
            
            for tree_x, tree_y, tree_height, tree_width in mountain['trees']:
                self.draw_tree(tree_x, tree_y, tree_height, tree_width, mode_transition)
        
        for tree_x, tree_y, tree_height, tree_width in self.trees:
            self.draw_tree(tree_x, tree_y, tree_height, tree_width, mode_transition)
        
        cloud_alpha = max(50, int(255 * (1 - mode_transition*0.7)))
        
        for i in range(len(self.cloud_positions)):
            x, y = self.cloud_positions[i]
            size = self.cloud_sizes[i]
            
            cloud_color = (255, 255, 255, cloud_alpha)
            shadow_color = (200, 200, 200, cloud_alpha)
            
            shadow_offset = 5
            
            shadow_surface = pygame.Surface((60 * size, 30 * size), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow_surface, shadow_color, (0, 0, 60 * size, 30 * size))
            screen.blit(shadow_surface, (x + shadow_offset, y + shadow_offset))
            
            main_surface = pygame.Surface((60 * size, 30 * size), pygame.SRCALPHA)
            pygame.draw.ellipse(main_surface, cloud_color, (0, 0, 60 * size, 30 * size))
            screen.blit(main_surface, (x, y))
            
            top_surface = pygame.Surface((40 * size, 25 * size), pygame.SRCALPHA)
            pygame.draw.ellipse(top_surface, cloud_color, (0, 0, 40 * size, 25 * size))
            screen.blit(top_surface, (x + 20 * size, y - 10 * size))
            
            side_surface = pygame.Surface((50 * size, 25 * size), pygame.SRCALPHA)
            pygame.draw.ellipse(side_surface, cloud_color, (0, 0, 50 * size, 25 * size))
            screen.blit(side_surface, (x - 20 * size, y - 5 * size))
    
    def draw_tree(self, x, y, height, width, mode_transition):
        trunk_height = height * 0.4
        trunk_width = width * 0.3
        
        day_trunk = (100, 50, 20)
        night_trunk = (40, 35, 30)
        
        r = int(day_trunk[0] * (1 - mode_transition) + night_trunk[0] * mode_transition)
        g = int(day_trunk[1] * (1 - mode_transition) + night_trunk[1] * mode_transition)
        b = int(day_trunk[2] * (1 - mode_transition) + night_trunk[2] * mode_transition)
        
        trunk_color = (r, g, b)
        pygame.draw.rect(screen, trunk_color, (x - trunk_width//2, y - trunk_height, trunk_width, trunk_height))
        
        tree_top_height = height * 0.6
        
        day_leaf = (30, 120, 30)
        night_leaf = (10, 40, 30)
        
        r = int(day_leaf[0] * (1 - mode_transition) + night_leaf[0] * mode_transition)
        g = int(day_leaf[1] * (1 - mode_transition) + night_leaf[1] * mode_transition)
        b = int(day_leaf[2] * (1 - mode_transition) + night_leaf[2] * mode_transition)
        
        leaf_color = (r, g, b)
        
        for i in range(3):
            offset = i * tree_top_height * 0.3
            layer_height = tree_top_height * 0.7 * (1 - i * 0.2)
            layer_width = width * (1 - i * 0.2)
            
            points = [
                (x, y - trunk_height - offset - layer_height),
                (x - layer_width//2, y - trunk_height - offset),
                (x + layer_width//2, y - trunk_height - offset)
            ]
            
            pygame.draw.polygon(screen, leaf_color, points)
    
    def update(self):
        for i in range(len(self.cloud_positions)):
            self.cloud_positions[i][0] -= self.cloud_speeds[i]
            if self.cloud_positions[i][0] + 100 < 0:
                self.cloud_positions[i][0] = SCREEN_WIDTH
                self.cloud_positions[i][1] = random.randint(20, SCREEN_HEIGHT//3)

def draw_floor(mode_transition=0.0):
    for y in range(FLOOR_HEIGHT):
        day_shade = 139 - int(y * 0.3)
        day_color = (day_shade, day_shade//2, day_shade//3)
        
        night_shade = 50 - int(y * 0.2)
        night_color = (night_shade, night_shade//3, night_shade//6)
        
        r = int(day_color[0] * (1 - mode_transition) + night_color[0] * mode_transition)
        g = int(day_color[1] * (1 - mode_transition) + night_color[1] * mode_transition)
        b = int(day_color[2] * (1 - mode_transition) + night_color[2] * mode_transition)
        
        pygame.draw.line(screen, (r, g, b), 
                        (0, SCREEN_HEIGHT - FLOOR_HEIGHT + y), 
                        (SCREEN_WIDTH, SCREEN_HEIGHT - FLOOR_HEIGHT + y))
    
    for i in range(0, SCREEN_WIDTH, 30):
        for j in range(0, FLOOR_HEIGHT, 20):
            day_shade = random.randint(130, 150)
            day_color = (day_shade, day_shade//2, day_shade//3)
            
            night_shade = random.randint(40, 55)
            night_color = (night_shade, night_shade//2, night_shade//5)
            
            r = int(day_color[0] * (1 - mode_transition) + night_color[0] * mode_transition)
            g = int(day_color[1] * (1 - mode_transition) + night_color[1] * mode_transition)
            b = int(day_color[2] * (1 - mode_transition) + night_color[2] * mode_transition)
            
            pygame.draw.rect(screen, (r, g, b), 
                           (i, SCREEN_HEIGHT - FLOOR_HEIGHT + j, 15, 10))
    
    day_grass = DAY_GRASS
    night_grass = NIGHT_GRASS
    r = int(day_grass[0] * (1 - mode_transition) + night_grass[0] * mode_transition)
    g = int(day_grass[1] * (1 - mode_transition) + night_grass[1] * mode_transition)
    b = int(day_grass[2] * (1 - mode_transition) + night_grass[2] * mode_transition)
    
    pygame.draw.rect(screen, (r, g, b), (0, SCREEN_HEIGHT - FLOOR_HEIGHT, SCREEN_WIDTH, 5))
    
    for i in range(0, SCREEN_WIDTH, 40):
        shadow_r = int(0 * (1 - mode_transition) + 0 * mode_transition)
        shadow_g = int(100 * (1 - mode_transition) + 40 * mode_transition)
        shadow_b = int(0 * (1 - mode_transition) + 20 * mode_transition)
        pygame.draw.ellipse(screen, (shadow_r, shadow_g, shadow_b), 
                          (i+2, SCREEN_HEIGHT - FLOOR_HEIGHT + 3, 20, 7))
        
        tuft_r = int(0 * (1 - mode_transition) + 0 * mode_transition)
        tuft_g = int(200 * (1 - mode_transition) + 80 * mode_transition)
        tuft_b = int(0 * (1 - mode_transition) + 40 * mode_transition)
        pygame.draw.ellipse(screen, (tuft_r, tuft_g, tuft_b), 
                          (i, SCREEN_HEIGHT - FLOOR_HEIGHT, 20, 7))

def calculate_fps():
    global LAST_FRAME_TIME
    current_time = time.time()
    dt = current_time - LAST_FRAME_TIME
    LAST_FRAME_TIME = current_time
    return int(1.0 / dt) if dt > 0 else 0

def game():
    bird = Bird()
    obstacles = []
    score = 0
    game_over = False
    last_obstacle = pygame.time.get_ticks() - OBSTACLE_FREQUENCY
    background = Background()
    
    current_mode = DAY_MODE
    mode_transition = 0.0
    target_mode = DAY_MODE
    last_toggle = 0
    toggle_cooldown = 500
    
    running = True
    while running:
        clock.tick(FPS)
        
        current_time = pygame.time.get_ticks()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not game_over:
                    bird.jump()
                if event.key == pygame.K_r and game_over:
                    return game()
                if event.key == pygame.K_n and current_time - last_toggle > toggle_cooldown:
                    target_mode = NIGHT_MODE if target_mode == DAY_MODE else DAY_MODE
                    last_toggle = current_time
        
        if target_mode == DAY_MODE and mode_transition > 0:
            mode_transition = max(0, mode_transition - MODE_TRANSITION_SPEED)
        elif target_mode == NIGHT_MODE and mode_transition < 1:
            mode_transition = min(1, mode_transition + MODE_TRANSITION_SPEED)
        
        if not game_over and current_time - last_obstacle > OBSTACLE_FREQUENCY:
            obstacles.append(Obstacle(SCREEN_WIDTH))
            last_obstacle = current_time
        
        if not game_over:
            bird.update()
            background.update()
            
            for obstacle in obstacles:
                obstacle.update()
                
                if obstacle.collide(bird):
                    game_over = True
                
                if not obstacle.passed and obstacle.x + obstacle.width < bird.x:
                    obstacle.passed = True
                    score += 1
        
        obstacles = [obstacle for obstacle in obstacles if obstacle.x > -obstacle.width]
        
        day_sky = DAY_SKY
        night_sky = NIGHT_SKY
        sky_r = int(day_sky[0] * (1 - mode_transition) + night_sky[0] * mode_transition)
        sky_g = int(day_sky[1] * (1 - mode_transition) + night_sky[1] * mode_transition)
        sky_b = int(day_sky[2] * (1 - mode_transition) + night_sky[2] * mode_transition)
        
        screen.fill((sky_r, sky_g, sky_b))
        
        background.draw(mode_transition)
        
        for obstacle in obstacles:
            obstacle.draw()
        
        draw_floor(mode_transition)
        
        bird.draw()
        
        shadow_offset = 2
        score_shadow = font.render(f'Score: {score}', True, (20, 20, 20))
        screen.blit(score_shadow, (10 + shadow_offset, 10 + shadow_offset))
        
        score_text = font.render(f'Score: {score}', True, WHITE)
        screen.blit(score_text, (10, 10))
        
        hint_font = pygame.font.SysFont('Arial', 18)
        hint_text = hint_font.render('Press N to toggle day/night', True, WHITE)
        screen.blit(hint_text, (10, 40))
        
        fps = calculate_fps()
        fps_text = pygame.font.SysFont('Arial', 20).render(f'FPS: {fps}', True, WHITE)
        screen.blit(fps_text, (SCREEN_WIDTH - 80, 10))
        
        if game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            screen.blit(overlay, (0, 0))
            
            shadow_offset = 10
            pygame.draw.rect(screen, (20, 20, 20), 
                          (SCREEN_WIDTH // 2 - 150 + shadow_offset, 
                           SCREEN_HEIGHT // 2 - 60 + shadow_offset, 300, 120))
            
            pygame.draw.rect(screen, (70, 70, 70), 
                          (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 60, 300, 120))
            pygame.draw.rect(screen, (100, 100, 100), 
                          (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 60, 300, 5))
            pygame.draw.rect(screen, (50, 50, 50), 
                          (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 60, 5, 120))
            pygame.draw.rect(screen, (30, 30, 30), 
                          (SCREEN_WIDTH // 2 + 145, SCREEN_HEIGHT // 2 - 60, 5, 120))
            pygame.draw.rect(screen, (40, 40, 40), 
                          (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 + 55, 300, 5))
            
            shadow_offset = 2
            game_over_shadow = font.render('Game Over!', True, BLACK)
            restart_shadow = font.render('Press R to restart', True, BLACK)
            final_score_shadow = font.render(f'Final Score: {score}', True, BLACK)
            
            screen.blit(game_over_shadow, 
                      (SCREEN_WIDTH // 2 - game_over_shadow.get_width() // 2 + shadow_offset, 
                       SCREEN_HEIGHT // 2 - 30 + shadow_offset))
            screen.blit(restart_shadow, 
                      (SCREEN_WIDTH // 2 - restart_shadow.get_width() // 2 + shadow_offset, 
                       SCREEN_HEIGHT // 2 + 10 + shadow_offset))
            screen.blit(final_score_shadow,
                     (SCREEN_WIDTH // 2 - final_score_shadow.get_width() // 2,
                      SCREEN_HEIGHT // 2 - 70 + shadow_offset))
            
            game_over_text = font.render('Game Over!', True, WHITE)
            restart_text = font.render('Press R to restart', True, WHITE)
            final_score = font.render(f'Final Score: {score}', True, WHITE)
            
            screen.blit(game_over_text, 
                      (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, 
                       SCREEN_HEIGHT // 2 - 30))
            screen.blit(restart_text, 
                      (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, 
                       SCREEN_HEIGHT // 2 + 10))
            screen.blit(final_score,
                     (SCREEN_WIDTH // 2 - final_score.get_width() // 2,
                      SCREEN_HEIGHT // 2 - 70))
        
        pygame.display.update()
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    game()