import os
import random
import math
import pygame
from os import listdir

#cu ajutorul acestei bibloteci facem split la imaginile din folderul assets
from os.path import isfile, join

pygame.init()

pygame.display.set_caption("Toiagul lui Merlin")

WIDTH, HEIGHT = 1200, 800
FPS = 60
PLAYER_VEL = 5

winodws = pygame.display.set_mode((WIDTH, HEIGHT))

#functia flip imi intoarce imaginea pe axa x (adica ii da flip)
def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]

def load_sprites_sheets(dir1, dir2, width, height, direction = False):
    path = join("assets", dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path, f))]

    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()
        #convert_alpha() este o functie care imi face imaginea transparenta (png)

        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            # SRCALPHA este un flag care imi face imaginea transparenta
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            #blit este o functie care imi copiaza imaginea
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites

def get_block(size):
    path = join("assets", "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(96, 64, size, size)
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)


class Player(pygame.sprite.Sprite):
    #clasa Player mosteneste clasa Sprite pentru a face o coliziune perfecta intre Sprite-uri
    COLOR = (255, 0, 0)
    GRAVITY = 1
    SPRITES = load_sprites_sheets("MainCharacters", "Wizard", 32, 32, True)
    ANIMATION_DELAY = 10

    def __init__(self, x, y, width, height):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        #rect este un box collider - adica un dreptunghi care imi face coliziunea perfecta
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "right"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0
        self.lives = 1
        self.alive = True
        self.tch_hidden = False
        self.finish = False
        self.win = False

    def finished(self):
        self.finish = True

    def won(self):
        self.win = True

    def jump(self):
        self.y_vel = -self.GRAVITY * 8
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def touch_hidden(self):
        self.tch_hidden = True

    def make_hit(self):
        self.hit = True
        if self.lives > 0:
            self.lives -= 1
        if self.lives == 0:
            self.alive = False
        self.hit_count = 0

    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def loop(self, fps):
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)

        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps * 2:
            self.hit = False
            self.hit_count = 0

        self.fall_count += 1
        self.update_sprites()

    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    def hit_head(self):
        self.count = 0
        self.y_vel *= -1


    def update_sprites(self):
        sprite_sheet = "idle"
        if self.hit:
            sprite_sheet = "fall"
        elif self.y_vel < 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "crouch"
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "die"
        elif self.x_vel != 0:
            sprite_sheet = "walk"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    def update(self):
        self.rect = self.sprite.get_rect(topleft = (self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)
        #mask imi modifica dreptunghiul (box collider-ul) in functie de marimea caracterului(sprite-ului)

    def draw(self, window, offset_x, offset_y):
        window.blit(self.sprite, (self.rect.x - offset_x, self.rect.y - offset_y))

class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name = None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, window, offset_x, offset_y):
        window.blit(self.image, (self.rect.x - offset_x, self.rect.y - offset_y))

class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)

class Fire(Object):
    ANIMATION_DELAY = 5

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "fire")
        self.fire = load_sprites_sheets("Traps", "Fire", width, height)
        self.image = self.fire["off"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "off"

    def on(self):
        self.animation_name = "on"

    def off(self):
        self.animation_name = "off"
    
    def loop(self):
        sprites = self.fire[self.animation_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft = (self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0

class Spike(Object):

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "spike")
        self.spike = load_sprites_sheets("Traps", "Spikes", width, height)
        self.image = self.spike["Idle"][0]
        self.mask = pygame.mask.from_surface(self.image)

class Gate(Object):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "gate")
        self.gate = load_sprites_sheets("Terrain", "Blocks", width, height)
        self.image = self.gate["gate"][0]
        self.mask = pygame.mask.from_surface(self.image)

class Staff(Object):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "staff")
        self.staff = load_sprites_sheets("Items", "Staff", width, height)
        self.image = self.staff["toiag"][0]
        self.mask = pygame.mask.from_surface(self.image)

class Chest(Object):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "chest")
        self.chest = load_sprites_sheets("Items", "Chest", width, height)
        self.image = self.chest["chest"][0]
        self.mask = pygame.mask.from_surface(self.image)

class Cube(Object):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "cube")
        self.cube = load_sprites_sheets("Terrain", "Blocks", width, height)
        self.image = self.cube["cube"][0]
        self.mask = pygame.mask.from_surface(self.image)

class HorizontalTile(Object):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "horizontal_tile")
        self.horizontal_tile = load_sprites_sheets("Terrain", "Blocks", width, height)
        self.image = self.horizontal_tile["horizontal_tile"][0]
        self.mask = pygame.mask.from_surface(self.image)

class MiniCube(Object):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "mini_cube")
        self.mini_cube = load_sprites_sheets("Terrain", "Blocks", width, height)
        self.image = self.mini_cube["mini_cube"][0]
        self.mask = pygame.mask.from_surface(self.image)


class InvisibleBlock(Object):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "invisible_block")
        self.inv_block = load_sprites_sheets("Terrain", "Blocks", width, height)
        self.image = self.inv_block["Dark_blue"][0]
        self.mask = pygame.mask.from_surface(self.image)

def get_background(name):
    image = pygame.image.load(join("assets", "Background", name))
    _, _, width, height = image.get_rect()
    # x, y, width, height, dar pe mine nu ma intereseaza x si y
    tiles = []
    #tiles este o lista de pozitii

    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = (i * width, j * height)
            # ma pozitioneaza in coltul din stanga sus, pos primeste coordonatele
            tiles.append(pos)

    return tiles, image


def draw(window, background, bg_image, player, objects, offset_x, offset_y):
    for tile in background:
        window.blit(bg_image, tile)
        # tile reprezinta pozitia

    for obj in objects:
        obj.draw(window, offset_x, offset_y)

    player.draw(window, offset_x, offset_y)

    if player.tch_hidden == True:
        font_h = pygame.font.Font("Grand9K Pixel.ttf", 32)
        text_h = font_h.render("Nu totul este ceea ce pare a fi", 1, (255, 255, 255))
        window.blit(text_h, (400, 10))

    if player.alive == False:
        pygame.time.delay(10)
        window.fill((0, 0, 0))
        font = pygame.font.Font("Grand9K Pixel.ttf", 32)
        text = font.render("GAME OVER! Press R to RESTART", 1, (255, 255, 255))
        textRect = text.get_rect()
        textRect.center = (WIDTH // 2, HEIGHT // 2)
        window.blit(text, textRect)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_r]:
            player.alive = True
            player.lives = 1
            main(window)

    if player.rect.colliderect(objects[len(objects) - 1].rect): #de adaugat pozitia portii sau pun poarta ultima
        font_in = pygame.font.Font("Grand9K Pixel.ttf", 32)
        text_in = font_in.render("Apasa S pentru a intra", 1, (255, 255, 255))
        window.blit(text_in, (100, 100))
    
    if player.rect.colliderect(objects[len(objects) - 3].rect): 
        font_in = pygame.font.Font("Grand9K Pixel.ttf", 32)
        text_in = font_in.render("Apasa S pentru a revendica Toiagul", 1, (255, 255, 255))
        window.blit(text_in, (300, 100))

    if player.rect.colliderect(objects[len(objects) - 4].rect): 
        font_in = pygame.font.Font("Grand9K Pixel.ttf", 32)
        text_in = font_in.render("Felicitari, ai gasit comoara ascunsa!", 1, (255, 255, 255))
        window.blit(text_in, (300, 100))
    
    if player.rect.colliderect(objects[len(objects) - 2].rect):
        font_sec = pygame.font.Font("Grand9K Pixel.ttf", 32)
        text_sec = font_sec.render("-->", 1, (255, 255, 255))
        window.blit(text_sec, (998, 180))

    font = pygame.font.Font("Grand9K Pixel.ttf", 32)
    text = font.render("Lives: " + str(player.lives), 1, (255, 255, 255))
    window.blit(text, (10, 10))

    if player.finish == True:
        pygame.time.delay(10)
        window.fill((0, 0, 0))
        font = pygame.font.Font("Grand9K Pixel.ttf", 32)
        text = font.render("Felicitari, ai ajuns la final dar nu ai gasit Toiagul!", 1, (255, 255, 255))
        text2 = font.render("Apasa R pentru a reveni la inceput", 1, (255, 255, 255))
        textRect = text.get_rect()
        textRect2 = text2.get_rect()
        textRect.center = (WIDTH // 2, HEIGHT // 2)
        textRect2.center = (WIDTH // 2, HEIGHT // 2 + 64)
        window.blit(text, textRect)
        window.blit(text2, textRect2)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_r]:
            player.alive = True
            player.lives = 1
            player.finish = False
            main(window)

    if player.win == True:
        pygame.time.delay(10)
        window.fill((0, 0, 0))
        font = pygame.font.Font("Grand9K Pixel.ttf", 32)
        text = font.render("Felicitari, ai gasit Toiagul lui Merlin", 1, (255, 255, 255))
        text2 = font.render("Apasa R pentru a juca din nou nivelul", 1, (255, 255, 255))
        textRect = text.get_rect()
        textRect2 = text2.get_rect()
        textRect.center = (WIDTH // 2, HEIGHT // 2)
        textRect2.center = (WIDTH // 2, HEIGHT // 2 + 64)
        window.blit(text, textRect)
        window.blit(text2, textRect2)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_r]:
            player.alive = True
            player.lives = 1
            player.finish = False
            main(window)

    pygame.display.update()

def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            if dy > 0:
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0:
                player.rect.top = obj.rect.bottom
                player.hit_head()

            collided_objects.append(obj)

    return collided_objects

def collide(player, objects, dx):
    player.move(dx, 0)
    player.update()
    collided_object = None
    for obj in objects:
        if pygame.sprite.collide_mask(player,obj):
            collided_object = obj
            break
    
    player.move(-dx, 0)
    player.update()
    return collided_object

def is_fall_from_map(player):
    if player.rect.top > HEIGHT:
        player.make_hit()

def handle_movement(player, objects):
    keys = pygame.key.get_pressed()

    player.x_vel = 0
    #am pus valoarea 0 pentru ca daca nu apasam nimic, player-ul sa nu se miste
    collide_left = collide(player, objects, -PLAYER_VEL * 2)
    collide_right = collide(player, objects, PLAYER_VEL * 2)
    
    if (keys[pygame.K_a] or keys[pygame.K_LEFT]) and not collide_left:
        player.move_left(PLAYER_VEL)
    if (keys[pygame.K_d] or keys[pygame.K_RIGHT]) and not collide_right:
        player.move_right(PLAYER_VEL)

    vertical_collide = handle_vertical_collision(player, objects, player.y_vel)
    to_check = [collide_left, collide_right, *vertical_collide]
    for obj in to_check:
        if obj and (obj.name == "fire" or obj.name == "spike"):
            player.make_hit()

def main(window):
    clock = pygame.time.Clock()
    # setez background-ul
    background, bg_image = get_background("Dark_blue.png")

    block_size = 96

    player = Player(block_size, HEIGHT - block_size, 50, 50)
    fire = Fire(block_size * 12 + 32, HEIGHT - block_size - 64, 16, 32)
    fire.on()
    mini_wall = [Block(block_size * 4, HEIGHT - block_size * i, block_size) for i in range(2, 4)]
    mini_wall.append(Block(block_size * 5, HEIGHT - block_size * 3, block_size))
    mini_wall2 = [Block(block_size * 10, HEIGHT - block_size * i, block_size) for i in range(3, 7)]
    mini_wall3 = [Block(block_size * 17, HEIGHT - block_size * i, block_size) for i in range(2, 7)]
    mini_wall4 = [Block(block_size * 18, HEIGHT - block_size * i, block_size) for i in range(2, 7)]
    mini_wall5 = [Block(block_size * 19, HEIGHT - block_size * i, block_size) for i in range(2, 7)]
    terrain = [Block(block_size * 2, HEIGHT - block_size * 2, block_size),
               Block(block_size * 7, HEIGHT - block_size * 4, block_size),
               Block(block_size * 8, HEIGHT - block_size * 4, block_size),
               Spike(block_size * 6 + 13, HEIGHT - block_size - 14, 15, 7),
               Spike(block_size * 6 + 30 + 15, HEIGHT - block_size - 14, 15, 7),
               Spike(block_size * 7 + 3, HEIGHT - block_size * 4 - 14, 15, 7),
               Spike(block_size * 5 + 13, HEIGHT - block_size * 3 - 14, 15, 7),
               Spike(block_size * 5 + 30 + 15, HEIGHT - block_size * 3 - 14, 15, 7),
               Spike(block_size * 10 + 30 + 33, HEIGHT - block_size - 14, 15, 7),
               Block(block_size * 14, HEIGHT - block_size * 5, block_size),
               Spike(block_size * 12 + 3 + 30, HEIGHT - block_size * 2 - 14, 15, 7),
               Block(block_size * 14, HEIGHT - block_size * 3, block_size)]
    golden_path =  [HorizontalTile(block_size * i, HEIGHT - block_size * 11 - 32, 48, 16) for i in range(-1, 20)]
    secret_terrain = [HorizontalTile(block_size * 28, HEIGHT - block_size - 32, 48, 16),
                      MiniCube(block_size * 30 + 32, HEIGHT - block_size * 2 - 32, 16, 16),
                      HorizontalTile(block_size * 28, HEIGHT + 32 - block_size * 4 - 32, 48, 16),
                      HorizontalTile(block_size * 30, HEIGHT - block_size * 6, 48, 16),
                      HorizontalTile(block_size * 27, HEIGHT - block_size * 8, 48, 16),
                      MiniCube(block_size * 25, HEIGHT - block_size * 9 - 32, 16, 16),
                      HorizontalTile(block_size * 22, HEIGHT - block_size * 10, 48, 16),
                      HorizontalTile(block_size * 20, HEIGHT - block_size * 11, 48, 16),
                      *golden_path]
    inv_block = InvisibleBlock(block_size * 9 + 1, HEIGHT - block_size - 64, 32, 32)
    inv_block2 = Block(block_size * 16, HEIGHT - block_size * 4, block_size)
    secret_path = InvisibleBlock(block_size * 16 + 32, HEIGHT - block_size * 4 - 64, 32, 32)
    inv_spike = InvisibleBlock(block_size * 10 + 30, HEIGHT - block_size - 64, 32, 32)
    inv_spike2 = InvisibleBlock(block_size * 12 + 30, HEIGHT - block_size * 2 - 64, 32, 32)
    touchable_spike = [Spike(block_size * 10 + 13, HEIGHT - block_size * 6 - 14, 15, 7), 
                       Spike(block_size * 10 + 30 + 15, HEIGHT - block_size * 6  - 14, 15, 7)]
    touchable_fire = Fire(block_size * 14 + 32, HEIGHT - block_size - 64, 16, 32)
    touchable_fire.on()
    floor = [Block(i * block_size, HEIGHT - block_size, block_size) for i in range(-2, (WIDTH * 2) // block_size - 5)]
    floor2 = [Block(i * block_size, HEIGHT - block_size, block_size) for i in range((WIDTH * 2) // block_size - 3, (WIDTH * 2) // block_size + 6)]
    wall1 = [Block(0, HEIGHT - i * block_size, block_size) for i in range(12)]
    wall2 = [Block(-block_size, HEIGHT - i * block_size, block_size) for i in range(12)]
    wall3 = [Block(-block_size * 2, HEIGHT - i * block_size, block_size) for i in range(18)]
    wall4 = [Block(block_size * 10, HEIGHT - block_size * i, block_size) for i in range(8, 12)]
    mini_floor = [Block(i * block_size, HEIGHT - block_size * 4, block_size) for i in range(12,15)]
    wall5 = [Block(block_size * 17, HEIGHT - i * block_size, block_size) for i in range(8,12)]
    wall6 = [Block(block_size * 18, HEIGHT - i * block_size, block_size) for i in range(8,12)]
    wall7 = [Block(block_size * 19, HEIGHT - i * block_size, block_size) for i in range(8,12)]
    touchable_wall = [Block(block_size * i, HEIGHT - block_size * 7, block_size) for i in range(17, 20)]
    objects = [*wall1, *wall2, *wall3, *floor, *floor2, fire, *terrain, *mini_wall, *mini_wall2, *wall4, *mini_floor, *wall5, *wall6, *wall7,
               *mini_wall3, *mini_wall4, *mini_wall5, *secret_terrain]
    poarta = [Gate(block_size * 13 - 3, HEIGHT - block_size - 112, 51, 56)] # pozitia pe axa y se calculeaza dubland inaltimea
    staff = [Staff(block_size * 27 - 60, HEIGHT - block_size - 100, 10, 45)]
    chest = [Chest(27, HEIGHT - block_size * 11 - 72, 23, 20)]

    offset_x = 0
    offset_y = 0
    scroll_area_width = 200
    scroll_area_height = 90

    run = True
    while run:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

            if event.type == pygame.KEYDOWN:
                if (event.key == pygame.K_w or event.key == pygame.K_UP) and player.jump_count < 2:
                    player.jump()
                if player.rect.colliderect(poarta[0].rect):
                    if (event.key == pygame.K_s or event.key == pygame.K_DOWN):
                        player.finished()
                if player.rect.colliderect(staff[0].rect):
                    if (event.key == pygame.K_s or event.key == pygame.K_DOWN):
                        player.won()
                
        if player.rect.colliderect(inv_block.rect) or player.rect.colliderect(inv_spike.rect):
            player.touch_hidden()
        is_fall_from_map(player)
        player.loop(FPS)
        fire.loop()
        touchable_fire.loop()
        handle_movement(player, objects + [inv_block2])
        draw(window, background, bg_image, player, objects + touchable_wall + [touchable_fire] + touchable_spike + [inv_block] + [inv_spike] + [inv_spike2] + chest +staff + [secret_path] + poarta, offset_x, offset_y)

        if (player.rect.right - offset_x >= WIDTH - scroll_area_width and player.x_vel > 0) or (player.rect.left - offset_x <= scroll_area_width and player.x_vel < 0):
            offset_x += player.x_vel
        if (player.rect.bottom - offset_y >= HEIGHT - scroll_area_height and player.y_vel > 0) or (player.rect.top - offset_y <= scroll_area_height and player.y_vel < 0):
            offset_y += player.y_vel

    pygame.quit()
    quit()

if __name__ == "__main__":
    main(winodws)



