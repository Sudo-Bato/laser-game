import pygame
from os.path import join
from random import randint, uniform
import random
import json

# Durée du power-up en millisecondes
RAPID_FIRE_DURATION = 5000
SCORE_FILE = 'scores.json'
PLAYER_DATA_FILE = 'save_data.json'

# --- Player Data Management ---
def load_player_data():
    try:
        with open(PLAYER_DATA_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Default data if file doesn't exist or is corrupted
        return {
            "coins": 0,
            "upgrades": {
                "slower_cooldown": False,
                "faster_movement_speed": False
            },
            "skins": {
                "default": True,
                "yellow_ship": False
            },
            "selected_skin": "default"
        }

def save_player_data(data):
    with open(PLAYER_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# --- Game Classes ---

class Player(pygame.sprite.Sprite):
    def __init__(self, groups, player_data):
        super().__init__(groups)
        self.player_data = player_data
        self.load_skin()

        self.rect = self.image.get_rect(center=(WINDOW_WIDTH / 2, (WINDOW_HEIGHT / 4) * 3))
        self.direction = pygame.math.Vector2(0, 0)

        # Define base attributes BEFORE calling apply_upgrades
        self.base_speed = 300
        self.speed = self.base_speed

        self.can_shoot = True
        self.laser_shoot_time = 0
        self.base_cooldown_duration = 400
        self.cooldown_duration = self.base_cooldown_duration

        self.apply_upgrades() # Now this call is safe

        self.mask = pygame.mask.from_surface(self.image)

    def load_skin(self):
        skin_name = self.player_data["selected_skin"]
        if skin_name == "default":
            self.image = pygame.image.load(join('images', 'player.png')).convert_alpha()
        elif skin_name == "yellow_ship":
            # Ensure you have 'yellow_ship.png' in your 'images' folder
            self.image = pygame.image.load(join('images', 'yellow_ship.png')).convert_alpha()
        # Add more skins here as you create them

    def apply_upgrades(self):
        # Apply movement speed upgrade
        if self.player_data["upgrades"]["faster_movement_speed"]:
            self.speed = self.base_speed * 1.5 # 50% faster
        else:
            self.speed = self.base_speed

        # Apply cooldown upgrade
        if self.player_data["upgrades"]["slower_cooldown"]:
            self.cooldown_duration = self.base_cooldown_duration * 0.5 # 50% faster shooting
        else:
            self.cooldown_duration = self.base_cooldown_duration

    def laser_timer(self):
        if not self.can_shoot:
            current_time = pygame.time.get_ticks()
            if current_time - self.laser_shoot_time >= self.cooldown_duration:
                self.can_shoot = True

    def update(self, dt):
        keys = pygame.key.get_pressed()
        # Apply shift for temporary speed boost on top of upgrades
        current_speed = self.speed * 2 if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] else self.speed

        self.direction.x = int(keys[pygame.K_RIGHT]) - int(keys[pygame.K_LEFT])
        self.direction.y = int(keys[pygame.K_DOWN]) - int(keys[pygame.K_UP])
        self.direction = self.direction.normalize() if self.direction.length() > 0 else self.direction
        self.rect.centerx += self.direction.x * current_speed * dt
        self.rect.centery += self.direction.y * current_speed * dt

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
    def __init__(self, original_surf, pos, groups, is_powerup_carrier=False): # Ajout de is_powerup_carrier
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
        self.is_powerup_carrier = is_powerup_carrier # Stocke l'information

    def update(self, dt):
        self.rect.centerx += self.direction.x * self.speed * dt
        self.rect.centery += self.direction.y * self.speed * dt
        if self.rect.top > WINDOW_HEIGHT or self.rect.left > WINDOW_WIDTH or self.rect.right < 0:
            self.kill()
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

# --- Game Screens ---

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

    options = ["1. Nouvelle Partie", "2. Boutique", "3. Meilleurs Scores", "4. Quitter"]
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

    show_death = True
    while show_death:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    show_death = False

        display_surface.fill('#1f1b24')
        for i in range(100):
            pygame.draw.circle(display_surface, (255, 255, 255), (randint(0, WINDOW_WIDTH), randint(0, WINDOW_HEIGHT)), 1)

        display_surface.blit(title_text, title_rect)
        display_surface.blit(instruct_text, instruct_rect)
        display_surface.blit(score_text, score_rect)
        pygame.display.update()
        clock.tick(60)

def shop_screen():
    global player_data
    shop_font_title = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 60)
    shop_font_item = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 30)
    shop_font_info = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 25)

    title_text = shop_font_title.render("Boutique", True, (240, 240, 240))
    title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, 70))

    items = {
        "upgrades": [
            {"name": "Refroidissement Amélioré", "desc": "Tir plus rapide (Cooldown -50%)", "cost": 100, "key": "slower_cooldown", "type": "upgrade"},
            {"name": "Propulseurs Améliorés", "desc": "Vitesse de déplacement +50%", "cost": 150, "key": "faster_movement_speed", "type": "upgrade"},
        ],
        "skins": [
            {"name": "Vaisseau Standard", "desc": "Le look classique.", "cost": 0, "key": "default", "type": "skin"},
            {"name": "Vaisseau Jaune", "desc": "Change l'apparence de votre vaisseau", "cost": 200, "key": "yellow_ship", "type": "skin"},
        ]
    }

    # Le skin de base est toujours possédé
    player_data["skins"].setdefault("default", True)

    showing_shop = True
    while showing_shop:
        all_available_items = []

        display_surface.fill('#1f1b24')
        for _ in range(100):
            pygame.draw.circle(display_surface, (255, 255, 255), (randint(0, WINDOW_WIDTH), randint(0, WINDOW_HEIGHT)), 1)

        display_surface.blit(title_text, title_text.get_rect(center=(WINDOW_WIDTH // 2, 70)))

        coins_text = shop_font_info.render(f"Vos Pièces: {player_data['coins']}", True, (255, 215, 0))
        display_surface.blit(coins_text, coins_text.get_rect(midtop=(WINDOW_WIDTH // 2, title_rect.bottom + 20)))

        current_y = coins_text.get_rect().bottom + 40
        item_counter = 1

        # --- Upgrades ---
        upgrade_title = shop_font_item.render("--- Améliorations ---", True, (150, 150, 255))
        display_surface.blit(upgrade_title, upgrade_title.get_rect(midleft=(50, current_y)))
        current_y += 50

        for item in items["upgrades"]:
            owned = player_data["upgrades"].get(item["key"], False)
            color = (100, 255, 100) if owned else (200, 200, 200)
            status_text = "(Acheté)" if owned else f"- {item['cost']} pièces"

            all_available_items.append(item)

            item_text = shop_font_item.render(f"{item_counter}. {item['name']} {status_text}", True, color)
            display_surface.blit(item_text, item_text.get_rect(midleft=(50, current_y)))

            desc_text = shop_font_info.render(f"    {item['desc']}", True, (180, 180, 180))
            display_surface.blit(desc_text, desc_text.get_rect(midleft=(50, current_y + 35)))

            item_counter += 1
            current_y += 75

        # --- Skins ---
        skin_title = shop_font_item.render("--- Apparences ---", True, (255, 150, 150))
        display_surface.blit(skin_title, skin_title.get_rect(midleft=(50, current_y)))
        current_y += 50

        for item in items["skins"]:
            owned = player_data["skins"].get(item["key"], False)
            selected = player_data["selected_skin"] == item["key"]
            color = (100, 255, 255) if selected else (100, 255, 100) if owned else (200, 200, 200)
            status_text = "(Sélectionné)" if selected else "(Acheté - Appuyer pour équiper)" if owned else f"- {item['cost']} pièces"

            all_available_items.append(item)

            item_text = shop_font_item.render(f"{item_counter}. {item['name']} {status_text}", True, color)
            display_surface.blit(item_text, item_text.get_rect(midleft=(50, current_y)))

            desc_text = shop_font_info.render(f"    {item['desc']}", True, (180, 180, 180))
            display_surface.blit(desc_text, desc_text.get_rect(midleft=(50, current_y + 35)))

            item_counter += 1
            current_y += 75

        # Instructions
        instruction_text = shop_font_info.render("Appuyez sur un numéro pour acheter/équiper. Échap pour retourner au menu.", True, (200, 200, 200))
        display_surface.blit(instruction_text, instruction_text.get_rect(midbottom=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 30)))

        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    showing_shop = False
                elif pygame.K_1 <= event.key <= pygame.K_9:
                    selected_item_number = event.key - pygame.K_0
                    if 1 <= selected_item_number <= len(all_available_items):
                        chosen_item = all_available_items[selected_item_number - 1]

                        if chosen_item["type"] == "upgrade":
                            already_owned = player_data["upgrades"].get(chosen_item["key"], False)
                            if already_owned:
                                print("Déjà acheté.")
                            elif player_data["coins"] >= chosen_item["cost"]:
                                player_data["coins"] -= chosen_item["cost"]
                                player_data["upgrades"][chosen_item["key"]] = True
                                save_player_data(player_data)
                                print(f"Acheté : {chosen_item['name']}")
                            else:
                                print("Pas assez de pièces.")

                        elif chosen_item["type"] == "skin":
                            owned = player_data["skins"].get(chosen_item["key"], False)
                            if not owned and player_data["coins"] >= chosen_item["cost"]:
                                player_data["coins"] -= chosen_item["cost"]
                                player_data["skins"][chosen_item["key"]] = True
                                player_data["selected_skin"] = chosen_item["key"]
                                save_player_data(player_data)
                                print(f"Acheté et équipé : {chosen_item['name']}")
                            elif owned:
                                player_data["selected_skin"] = chosen_item["key"]
                                save_player_data(player_data)
                                print(f"Apparence équipée : {chosen_item['name']}")
                            else:
                                print("Pas assez de pièces.")
                    else:
                        print("Numéro invalide.")

        pygame.display.update()
        clock.tick(60)


def reset_game():
    global all_sprites, meteor_sprites, laser_sprites, powerup_sprites, player, start_ticks, rapid_fire, last_rapid_fire, rapid_fire_timer, player_data

    all_sprites.empty()
    meteor_sprites.empty()
    laser_sprites.empty()
    powerup_sprites.empty()

    for i in range(20):
        Star(all_sprites, star_surf)
    player = Player(all_sprites, player_data) # Pass player_data to Player constructor

    rapid_fire = False
    last_rapid_fire = 0
    rapid_fire_timer = 0

    start_ticks = pygame.time.get_ticks()

def collisions():
    global running, player_data

    collision_sprites = pygame.sprite.spritecollide(player, meteor_sprites, True, pygame.sprite.collide_mask)
    if collision_sprites:
        damage_soud.play()
        running = False # End game on player collision

    for laser in laser_sprites:
        collided_sprites = pygame.sprite.spritecollide(laser, meteor_sprites, True, pygame.sprite.collide_mask)
        if collided_sprites:
            laser.kill()
            # Explode each collided meteor
            for meteor in collided_sprites:
                AnimatedExplosion(explosion_frames, meteor.rect.center, all_sprites)
                explosion_soud.play()

                # Check if the destroyed meteor was a power-up carrier
                if meteor.is_powerup_carrier:
                    player_data["coins"] += 20  # 20 coins for yellow meteor
                    PowerUp(meteor.rect.center, (all_sprites, powerup_sprites)) # Drop the power-up
                else:
                    player_data["coins"] += 1 # 1 coins for regular meteors

            save_player_data(player_data) # Save coins immediately after destruction


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

# Load assets
meteor_surface = pygame.image.load(join('images', 'meteor.png')).convert_alpha()
# Assurez-vous d'avoir 'yellow_meteor.png' dans votre dossier 'images'
yellow_meteor_surface = pygame.image.load(join('images', 'yellow_meteor.png')).convert_alpha() 
laser_surface = pygame.image.load(join('images', 'laser.png')).convert_alpha()
star_surf = pygame.image.load(join('images', 'star.png')).convert_alpha()

font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 40)
explosion_frames = [pygame.image.load(join('images', 'explosion', f'{i}.png')).convert_alpha() for i in range(21)]

# Load sounds
laser_soud = pygame.mixer.Sound(join('audio', 'laser.wav'))
explosion_soud = pygame.mixer.Sound(join('audio', 'explosion.wav'))
damage_soud = pygame.mixer.Sound(join('audio', 'damage.ogg'))
game_music = pygame.mixer.Sound(join('audio', 'game_music.wav'))
laser_soud.set_volume(0.2)
explosion_soud.set_volume(0.2)
damage_soud.set_volume(0.2)

# Global player data
player_data = load_player_data()

# Sprite groups
all_sprites = pygame.sprite.Group()
meteor_sprites = pygame.sprite.Group()
laser_sprites = pygame.sprite.Group()
powerup_sprites = pygame.sprite.Group()

# Initial setup for player and stars (will be reset by reset_game)
for i in range(20):
    Star(all_sprites, star_surf)
player = Player(all_sprites, player_data) # Initial player creation with loaded data

meteor_event = pygame.event.custom_type()
pygame.time.set_timer(meteor_event, 500)

rapid_fire = False
last_rapid_fire = 0
rapid_fire_timer = 0
rapid_fire_cooldown = 100

def main_game():
    global running, start_ticks, player_data
    global rapid_fire, last_rapid_fire, rapid_fire_timer

    reset_game() # Ensures new player and game state based on current player_data
    start_ticks = pygame.time.get_ticks()
    running = True
    score = 0
    game_music.set_volume(0.7)

    while running:
        dt = clock.tick(60) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == meteor_event:
                x, y = randint(0, WINDOW_WIDTH), randint(-200, -100)
                # Nouvelle logique : 1 chance sur 30 d'avoir un météore jaune
                if random.randint(1, 30) == 1:
                    Meteor(yellow_meteor_surface, (x, y), (all_sprites, meteor_sprites), is_powerup_carrier=True)
                else:
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

# Main game loop
game_music.play(loops=-1)
def game_loop():
    global player_data
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
            shop_screen()
            # After shop, reload player_data and recreate player to apply changes
            player_data = load_player_data() # Ensure player_data is updated
            reset_game() # This will recreate the player with updated data


# Launch the game
game_loop()
pygame.quit()