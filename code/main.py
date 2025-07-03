import pygame
from os.path import join
from random import randint, uniform
import random
import json

# Durée du power-up en millisecondes
RAPID_FIRE_DURATION = 5000
SCORE_FILE = 'scores.json'

class Player(pygame.sprite.Sprite):
    def __init__(self, groups):
        super().__init__(groups)
        self.image = pygame.image.load(join('images', 'player.png')).convert_alpha()
        self.rect = self.image.get_rect(center=(WINDOW_WIDTH / 2, (WINDOW_HEIGHT / 4) * 3))
        self.direction = pygame.math.Vector2(0, 0)
        self.speed = 300

        self.can_shoot = True
        self.laser_shoot_time = 0
        self.cooldown_duration = 400

        self.mask = pygame.mask.from_surface(self.image)

    def laser_timer(self):
        if not self.can_shoot:
            current_time = pygame.time.get_ticks()
            if current_time - self.laser_shoot_time >= self.cooldown_duration:
                self.can_shoot = True

    def update(self, dt):
        keys = pygame.key.get_pressed()
        self.speed = 600 if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] else 300

        self.direction.x = int(keys[pygame.K_RIGHT]) - int(keys[pygame.K_LEFT])
        self.direction.y = int(keys[pygame.K_DOWN]) - int(keys[pygame.K_UP])
        self.direction = self.direction.normalize() if self.direction.length() > 0 else self.direction
        self.rect.centerx += self.direction.x * self.speed * dt
        self.rect.centery += self.direction.y * self.speed * dt

        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > WINDOW_WIDTH:
            self.rect.right = WINDOW_WIDTH
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > WINDOW_HEIGHT:
            self.rect.bottom = WINDOW_HEIGHT

        self.laser_timer()

class Star(pygame.sprite.Sprite):
    def __init__(self, groups, surface):
        super().__init__(groups)
        self.image = surface
        self.rect = self.image.get_rect(center=(randint(0, WINDOW_WIDTH), randint(0, WINDOW_HEIGHT)))

class Laser(pygame.sprite.Sprite):
    def __init__(self, surf, pos, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(midbottom=pos)

    def update(self, dt):
        self.rect.centery -= 400 * dt
        if self.rect.bottom < 0:
            self.kill()

class Meteor(pygame.sprite.Sprite):
    def __init__(self, original_surf, pos, groups):
        super().__init__(groups)
        self.original_surf = original_surf
        self.image = original_surf
        self.rect = self.image.get_rect(center=pos)
        self.start_timer = pygame.time.get_ticks()
        self.life_time = 3000
        self.direction = pygame.math.Vector2(uniform(-0.5, 0.5), 1)
        self.speed = randint(400, 500)
        self.rotation = 0
        self.rotation_speed = randint(50, 150)

    def update(self, dt):
        self.rect.centerx += self.direction.x * self.speed * dt
        self.rect.centery += self.direction.y * self.speed * dt
        if pygame.time.get_ticks() - self.start_timer >= self.life_time:
            self.kill()

        self.rotation += self.rotation_speed * dt
        self.image = pygame.transform.rotozoom(self.original_surf, self.rotation, 1)
        self.rect = self.image.get_rect(center=self.rect.center)

class AnimatedExplosion(pygame.sprite.Sprite):
    def __init__(self, frames, pos, groups):
        super().__init__(groups)
        self.frames = frames
        self.frame_index = 0
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect(center=pos)

    def update(self, dt):
        self.frame_index += 20 * dt
        if self.frame_index < len(self.frames):
            self.image = self.frames[int(self.frame_index) % len(self.frames)]
        else:
            self.kill()

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, pos, groups):
        super().__init__(groups)
        self.image = pygame.image.load(join('images', 'powerup.png')).convert_alpha()
        self.rect = self.image.get_rect(center=pos)
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, dt):
        self.rect.centery += 150 * dt
        if self.rect.top > WINDOW_HEIGHT:
            self.kill()

def title_screen():
    title_font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 80)
    small_font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 30)
    title_text = title_font.render("Le Justicier de la Galaxie", True, (255, 255, 255))
    instruct_text = small_font.render("Appuie sur Entrée pour jouer", True, (200, 200, 200))

    title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50))
    instruct_rect = instruct_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50))

    show_title = True
    while show_title:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    show_title = False

        display_surface.fill('#1f1b24')
        for i in range(100):
            pygame.draw.circle(display_surface, (255, 255, 255), (randint(0, WINDOW_WIDTH), randint(0, WINDOW_HEIGHT)), 1)

        display_surface.blit(title_text, title_rect)
        display_surface.blit(instruct_text, instruct_rect)
        pygame.display.update()
        clock.tick(60)

def main_menu_screen():
    small_font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 50)
    menu_font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 30)

    options = ["1. Nouvelle Partie", "2. Boutique (à venir)", "3. Meilleurs Scores",  "4. Quitter"]
    option_surfaces = [menu_font.render(opt, True, (240, 240, 240)) for opt in options]
    option_rects = [surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + i * 60)) for i, surf in enumerate(option_surfaces)]

    title_text = small_font.render("Menu Principal", True, (200, 200, 200))
    title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 100))

    selected = False
    choice = None

    while not selected:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    choice = "play"
                    selected = True
                elif event.key == pygame.K_2:
                    choice = "shop"
                    selected = True
                elif event.key == pygame.K_3:
                    choice = "high_scores"
                    selected = True
                elif event.key == pygame.K_4 or event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    exit()

        display_surface.fill('#1f1b24')
        for i in range(100):
            pygame.draw.circle(display_surface, (255, 255, 255), (randint(0, WINDOW_WIDTH), randint(0, WINDOW_HEIGHT)), 1)

        display_surface.blit(title_text, title_rect)
        for surf, rect in zip(option_surfaces, option_rects):
            display_surface.blit(surf, rect)

        pygame.display.update()
        clock.tick(60)

    return choice    

def death_screen(score):
    title_font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 80)
    small_font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 30)
    title_text = title_font.render("Vous êtes mort", True, (220, 20, 60))
    score_text = small_font.render(f"Score : {score}", True, (240, 240, 240))
    score_rect = score_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 120))
    instruct_text = small_font.render("Appuie sur Entrée pour continuer", True, (200, 200, 200))

    title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50))
    instruct_rect = instruct_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50))

    show_title = True
    while show_title:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    show_title = False

        display_surface.fill('#1f1b24')
        for i in range(100):
            pygame.draw.circle(display_surface, (255, 255, 255), (randint(0, WINDOW_WIDTH), randint(0, WINDOW_HEIGHT)), 1)

        display_surface.blit(title_text, title_rect)
        display_surface.blit(instruct_text, instruct_rect)
        display_surface.blit(score_text, score_rect)
        pygame.display.update()
        clock.tick(60)

def reset_game():
    global all_sprites, meteor_sprites, laser_sprites, powerup_sprites, player, start_ticks, rapid_fire, last_rapid_fire, rapid_fire_timer

    all_sprites.empty()
    meteor_sprites.empty()
    laser_sprites.empty()
    powerup_sprites.empty()

    for i in range(20):
        Star(all_sprites, star_surf)
    player = Player(all_sprites)

    rapid_fire = False
    last_rapid_fire = 0
    rapid_fire_timer = 0

    start_ticks = pygame.time.get_ticks()

def collisions():
    global running

    collision_sprites = pygame.sprite.spritecollide(player, meteor_sprites, True, pygame.sprite.collide_mask)
    if collision_sprites:
        damage_soud.play()
        running = False

    for laser in laser_sprites:
        collided_sprites = pygame.sprite.spritecollide(laser, meteor_sprites, True, pygame.sprite.collide_mask)
        if collided_sprites:
            laser.kill()
            AnimatedExplosion(explosion_frames, laser.rect.midtop, all_sprites)
            explosion_soud.play()

            if random.randint(1, 30) == 1:
                meteor_pos = collided_sprites[0].rect.center
                PowerUp(meteor_pos, (all_sprites, powerup_sprites))

def display_score(score):
    text_surf = font.render(str(score), True, (240, 240, 240))
    text_rect = text_surf.get_rect(midbottom=(WINDOW_WIDTH / 2, WINDOW_HEIGHT - 50))

    pygame.draw.rect(display_surface, (240, 240, 240), text_rect.inflate(20, 10).move(0,-6), 5, 10)
    display_surface.blit(text_surf, text_rect)

def load_scores():
    try:
        with open(SCORE_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_score(score):
    scores = load_scores()
    scores.append(score)
    scores = sorted(scores, reverse=True)[:10]
    with open(SCORE_FILE, 'w') as f:
        json.dump(scores, f, indent=4)

def show_high_scores():
    high_scores = load_scores()
    font_title = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 60)
    font_entry = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 40)

    title_text = font_title.render("Meilleurs Scores", True, (240, 240, 240))
    title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, 100))

    showing = True
    while showing:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                    showing = False

        display_surface.fill('#1f1b24')
        display_surface.blit(title_text, title_rect)

        for i in range(100):
            pygame.draw.circle(display_surface, (255, 255, 255), (randint(0, WINDOW_WIDTH), randint(0, WINDOW_HEIGHT)), 1)

        for i, score in enumerate(high_scores):
            text = f"{i+1}. {score} pts"
            entry_surf = font_entry.render(text, True, (200, 200, 200))
            entry_rect = entry_surf.get_rect(center=(WINDOW_WIDTH // 2, 180 + i * 50))
            display_surface.blit(entry_surf, entry_rect)

        pygame.display.update()
        clock.tick(60)

# Setup pygame
pygame.init()
WINDOW_WIDTH, WINDOW_HEIGHT = 1280, 720
display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Le Justicier de la Galaxie")
pygame.display.set_icon(pygame.image.load(join('images', 'player.png')).convert_alpha())
clock = pygame.time.Clock()
running = True

meteor_surface = pygame.image.load(join('images', 'meteor.png')).convert_alpha()
laser_surface = pygame.image.load(join('images', 'laser.png')).convert_alpha()
star_surf = pygame.image.load(join('images', 'star.png')).convert_alpha()
font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 40)
explosion_frames = [pygame.image.load(join('images', 'explosion', f'{i}.png')).convert_alpha() for i in range(21)]

laser_soud = pygame.mixer.Sound(join('audio', 'laser.wav'))
explosion_soud = pygame.mixer.Sound(join('audio', 'explosion.wav'))
damage_soud = pygame.mixer.Sound(join('audio', 'damage.ogg'))
game_music = pygame.mixer.Sound(join('audio', 'game_music.wav'))
title_screen_music = pygame.mixer.Sound(join('audio', '8bit-spaceshooter.mp3'))
laser_soud.set_volume(0.2)
explosion_soud.set_volume(0.2)
damage_soud.set_volume(0.2)
game_music.play(loops=-1)
game_music.set_volume(0.7)

all_sprites = pygame.sprite.Group()
meteor_sprites = pygame.sprite.Group()
laser_sprites = pygame.sprite.Group()
powerup_sprites = pygame.sprite.Group()

for i in range(20):
    Star(all_sprites, star_surf)
player = Player(all_sprites)

meteor_event = pygame.event.custom_type()
pygame.time.set_timer(meteor_event, 500)

rapid_fire = False
last_rapid_fire = 0
rapid_fire_timer = 0
rapid_fire_cooldown = 100

def main_game():
    global running, start_ticks
    global rapid_fire, last_rapid_fire, rapid_fire_timer

    reset_game()
    start_ticks = pygame.time.get_ticks()
    running = True
    score = 0

    while running:
        dt = clock.tick(60) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == meteor_event:
                x, y = randint(0, WINDOW_WIDTH), randint(-200, -100)
                Meteor(meteor_surface, (x, y), (all_sprites, meteor_sprites))
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and not rapid_fire:
                if player.can_shoot:
                    Laser(laser_surface, player.rect.midtop, (all_sprites, laser_sprites))
                    player.can_shoot = False
                    player.laser_shoot_time = pygame.time.get_ticks()
                    laser_soud.play()

        all_sprites.update(dt)
        collisions()

        # Check for power-up collection
        collected = pygame.sprite.spritecollide(player, powerup_sprites, True, pygame.sprite.collide_mask)
        if collected:
            rapid_fire = True
            rapid_fire_timer = pygame.time.get_ticks()

        if rapid_fire and pygame.time.get_ticks() - rapid_fire_timer > RAPID_FIRE_DURATION:
            rapid_fire = False

        keys = pygame.key.get_pressed()
        if rapid_fire and keys[pygame.K_SPACE]:
            current_time = pygame.time.get_ticks()
            if current_time - last_rapid_fire > rapid_fire_cooldown:
                Laser(laser_surface, player.rect.midtop, (all_sprites, laser_sprites))
                laser_soud.play()
                last_rapid_fire = current_time

        display_surface.fill('#3a2e3f')
        all_sprites.draw(display_surface)

        score = (pygame.time.get_ticks() - start_ticks) // 100
        display_score(score)
        pygame.display.update()

    return score

# Boucle principale du jeu
def game_loop():
    title_screen()
    while True:
        choice = main_menu_screen()

        if choice == "play":
            score = main_game()
            save_score(score)
            death_screen(score)
        elif choice == "high_scores":
            show_high_scores()
        elif choice == "shop":
            print("Boutique")
            pygame.time.wait(1000)


# On lance le jeu
game_loop()
pygame.quit()
