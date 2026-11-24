import pygame
import sys
import random
import ast
from pathlib import Path
from perlin_noise import PerlinNoise
import itertools

import math

pygame.init()
window_size_x = 960
window_size_y = 720

window_size = (window_size_x,window_size_y)
screen = pygame.display.set_mode(window_size)
pygame.display.set_caption("blockgame")

seed = 113

noise = PerlinNoise(octaves=12,seed=seed)

zoom = 100

player_x = 0
player_z = 0
player_y = 0

player_block_x = 0
player_block_z = 0
player_block_y = 0

player_chunk_x = 0
player_chunk_z = 0
player_chunk_y = 0

past_player_chunk_x = None
past_player_chunk_z = None
past_player_chunk_y = None

past_zoom = None

move_w = 0
move_a = 0
move_s = 0
move_d = 0
move_q = 0
move_e = 0

click = 0

block_size = 24

chunk_size_x = 16
chunk_size_z = 16
chunk_size_y = 16

select_block = 0

world_data = []


# Also needs work, gotta make it work
def get_index(local_block_x,local_block_z, local_block_y, chunk_x, chunk_z, chunk_y):
    return local_block_y + (local_block_x*16) + (local_block_z*256)

"""
Needs work, right now the chunk borders are generated no matter what.
Also, I gotta figure out when to update this list. Constantly or 
if certain actions are done
"""
def cull_blocks():
    temp_list = []

    i = 0
    for chunk_z in range(3):
        for chunk_x in range(3):
            for chunk_y in range(3):
                for block_z in range(16):
                    for block_x in range(16):
                        for block_y in range(16):
                            if world_data[i] == 0:
                                temp_list.append(0)
                            else:
                                if block_y == 0 or block_y == 15 or block_x == 0 or block_x == 15 or block_z == 0 or block_z == 15:
                                    temp_list.append(1)
                                elif world_data[i-1] != 0 and world_data[i+1] != 0 and world_data[i-16] != 0 and world_data[i+16] != 0 and world_data[i-256] != 0 and world_data[i+256] != 0:
                                    temp_list.append(0)
                                else:
                                    temp_list.append(1)
                            i += 1
    return temp_list


def get_chunk_data():
    final_list = []
    for chunk_z,chunk_x,chunk_y in itertools.product(range(-1,2),repeat=3):
        chunk_pos = (player_chunk_x+chunk_x,player_chunk_z+chunk_z,player_chunk_y+chunk_y)

        if Path(f"{player_chunk_x+chunk_x},{player_chunk_z+chunk_z},{player_chunk_y+chunk_y}.txt").is_file():
            world_file = open(f"{player_chunk_x+chunk_x},{player_chunk_z+chunk_z},{player_chunk_y+chunk_y}.txt", "r")

            read_list = world_file.read()

            read_list = read_list.strip()

            world_file.close()

            read_list = list(ast.literal_eval(read_list))
        else:
            read_list = []

            # Replaced some nested for-loops with itertools cuz it might be faster 
            for z,x,y in itertools.product(range(chunk_size_z),range(chunk_size_x),range(chunk_size_y)):
                value = noise([(x+((player_chunk_x+chunk_x)*16))/250,(z+((player_chunk_z+chunk_z)*16))/250])

                if y+((player_chunk_y+chunk_y)*16) == round(value*16):
                    read_list.append(1)
                elif y+((player_chunk_y+chunk_y)*16) < round(value*16) and y+((player_chunk_y+chunk_y)*16) >= round(value*16)-2:
                    read_list.append(2)
                elif y+((player_chunk_y+chunk_y)*16) < round(value*16)-2:
                    read_list.append(3)
                else:
                    read_list.append(0)


        final_list.extend(read_list)
    

    return final_list

world_data = get_chunk_data()
cull_list = cull_blocks()

def change_file_data():
    global world_data


    world_file = open(f"{player_chunk_x},{player_chunk_z},{player_chunk_y}.txt", "w")

    world_file.write(str(world_data[53248:57344]))

    world_file.close()


def iso_coord(block_x,block_z,block_y, chunk_x, chunk_z, chunk_y):
    # raw_x is the x coord of the block without accounting for chunk offset by the player, zoom, or the window
    raw_x = ((((block_x+(chunk_x*16))*(block_size/2))-player_x)+(((block_z+(chunk_z*16))*-(block_size/2))+player_z)-(block_size/2))
    # block_screen_x is the x coord of the block while accounting for the chunk offset
    block_screen_x = (((raw_x)+player_chunk_x*(chunk_size_x*(block_size/2)))-player_chunk_z*(chunk_size_z*(block_size/2)))

    # raw_y is the y coord of the block without accounting for chunk offset by the player, zoom, or the window
    raw_y = ((((block_x+(chunk_x*16))*(block_size/4))-player_x/2)+(((block_z+(chunk_z*16))*(block_size/4))-player_z/2)+(((block_y+(chunk_y*16))*-(block_size/2))+player_y)-(block_size/2))
    # block_screen_y is the y coord of the block while accounting for the chunk offset
    block_screen_y = (((raw_y+player_chunk_x*(chunk_size_x*(block_size/4)))+player_chunk_z*(chunk_size_z*(block_size/4)))-player_chunk_y*(chunk_size_y*(block_size/2)))
    
    return ((block_screen_x*(zoom/100))+(window_size_x/2),(block_screen_y*(zoom/100))+((window_size_y/2)))


block_sheet = pygame.image.load("blocks.png")

# Used for spritesheets and animation (Credits to Coding with Russ)
def get_image(sheet, frame, width, height, scale, color):
	image = pygame.Surface((width, height))
	image.blit(sheet, (0,0), ((frame* width),0, width, height))
	image = pygame.transform.scale(image, (width * scale, height * scale))
	image.set_colorkey(color)

	return image.convert_alpha()

image_list = []
def update_image_cache():
    return [get_image(block_sheet, i, block_size, block_size, zoom/100, (0,0,0)) for i in range(11)]

clock = pygame.time.Clock()

image_list = update_image_cache()

while True:
    #print(clock.get_fps())
    mouse = pygame.mouse.get_pos()
    mouse_x, mouse_y = mouse[0]-(window_size_x/2), mouse[1]-(window_size_y/2)

    iso_mouse_block_x = round((((mouse_x/2) + mouse_y)/(block_size/2))/(zoom/100))+round(player_x/(block_size/2))-(player_chunk_x*chunk_size_x)
    iso_mouse_block_z = round((((-mouse_x/2) + mouse_y)/(block_size/2))/(zoom/100))+round(player_z/(block_size/2))-(player_chunk_z*chunk_size_z)
    iso_mouse_block_y = round(player_y/(block_size/2))-(player_chunk_y*chunk_size_y)

    player_block_x = round(player_x/(block_size/2))
    player_block_z = round(player_z/(block_size/2))
    player_block_y = round(player_y/(block_size/2))

    player_chunk_x = player_block_x//chunk_size_x
    player_chunk_z = player_block_z//chunk_size_z
    player_chunk_y = player_block_y//chunk_size_y


    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w:
                move_w = 1
            if event.key == pygame.K_a:
                move_a = 1
            if event.key == pygame.K_s:
                move_s = 1
            if event.key == pygame.K_d:
                move_d = 1
            if event.key == pygame.K_q:
                move_q = 1
            if event.key == pygame.K_e:
                move_e = 1
            if event.key == pygame.K_RIGHT:
                select_block += 1
            if event.key == pygame.K_LEFT:
                select_block -= 1
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_w:
                move_w = 0
            if event.key == pygame.K_a:
                move_a = 0
            if event.key == pygame.K_s:
                move_s = 0
            if event.key == pygame.K_d:
                move_d = 0
            if event.key == pygame.K_q:
                move_q = 0
            if event.key == pygame.K_e:
                move_e = 0
        if event.type == pygame.MOUSEBUTTONDOWN:
            click = 1
        if event.type == pygame.MOUSEBUTTONUP:
            click = 0
        if event.type == pygame.MOUSEWHEEL:
            if event.y > 0 and zoom > 75:
                zoom -= round(zoom/10)
            if event.y < 0 and zoom < 1000:
                zoom += round(zoom/10)

    if move_w == 1:
        player_x -=1
        player_z -=1
    if move_a == 1:
        player_x -=1
        player_z +=1
    if move_s == 1:
        player_x +=1
        player_z +=1
    if move_d == 1:
        player_x +=1
        player_z -=1
    if move_q == 1:
        player_y -= 1
    if move_e == 1:
        player_y += 1

    if player_chunk_x != past_player_chunk_x or player_chunk_z != past_player_chunk_z or player_chunk_y != past_player_chunk_y:
        past_player_chunk_x = int(player_chunk_x)
        past_player_chunk_z = int(player_chunk_z)
        past_player_chunk_y = int(player_chunk_y)

        world_data = get_chunk_data()
        cull_list = cull_blocks()

    if click == 1:
        if iso_mouse_block_x > -1 and iso_mouse_block_x < chunk_size_x and iso_mouse_block_z > -1 and iso_mouse_block_z < chunk_size_z and iso_mouse_block_y > -1 and iso_mouse_block_y < chunk_size_y:
            if world_data[iso_mouse_block_y+((iso_mouse_block_x)*chunk_size_x)+((iso_mouse_block_z)*chunk_size_x*chunk_size_z)+53248] != select_block:
                world_data[iso_mouse_block_y+((iso_mouse_block_x)*chunk_size_x)+((iso_mouse_block_z)*chunk_size_x*chunk_size_z)+53248] = select_block
                change_file_data()
                cull_list = cull_blocks()


    if select_block > 8:
        select_block = 0
    if select_block < 0:
        select_block = 8

    if zoom < 75:
        zoom = 75
    if zoom > 1000:
        zoom = 1000
    
    if past_zoom != zoom:
        past_zoom = zoom
        image_list = update_image_cache()


    screen.fill((50,100,255))


    
    chunk_i = 0
    for chunk_z,chunk_x,chunk_y in itertools.product(range(-1,2),repeat=3):
        block_i = 0

        for block_z,block_x,block_y in itertools.product(range(chunk_size_z),range(chunk_size_x),range(chunk_size_y)):
            # Generates Block
            if cull_list[block_i+(chunk_i*4096)] == 1:
                sliced_block = image_list[world_data[block_i+(chunk_i*4096)]]
                screen.blit(sliced_block, iso_coord(block_x, block_z, block_y, chunk_x, chunk_z, chunk_y))
            # Generates the player's mouse tip
            if block_x+(chunk_x*16) == iso_mouse_block_x and block_y+(chunk_y*16) == iso_mouse_block_y and block_z+(chunk_z*16) == iso_mouse_block_z:
                if world_data[block_i+(chunk_i*4096)] == 0:
                    mouse_block = image_list[8]
                else:
                    mouse_block = image_list[9]
                screen.blit(mouse_block, iso_coord(block_x, block_z, block_y, chunk_x, chunk_z, chunk_y))
            # Generates the player at a certain block pos
            if block_x+(chunk_x*16) == player_block_x-(player_chunk_x*chunk_size_x) and block_y+(chunk_y*16) == player_block_y-(player_chunk_y*chunk_size_y) and block_z+(chunk_z*16) == player_block_z-(player_chunk_z*chunk_size_z):
                player_block = image_list[10]
                screen.blit(player_block, iso_coord(block_x, block_z, block_y, chunk_x, chunk_z, chunk_y))

            block_i += 1

        chunk_i += 1
    

    # Generates the block selection in the corner
    selected_block = get_image(block_sheet, select_block, block_size, block_size, 3, (0,0,0))
    screen.blit(selected_block, (0, 0))

    pygame.display.flip()

    clock.tick(60)

