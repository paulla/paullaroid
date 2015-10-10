#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""PauLLA Photomaton, exposed on THDF 2015."""

import argparse
import picamera
import pygame
import os
import subprocess
import sys
import time
import RPi.GPIO as GPIO

from pygame.locals import KEYDOWN, K_ESCAPE, K_SPACE, K_q, QUIT
from datetime import datetime
from ConfigParser import SafeConfigParser


def parser():
    """Build parser."""
    name = os.path.basename(__file__)
    config = '%s.ini' % os.path.splitext(name)[0]
    argp = argparse.ArgumentParser(description=__doc__)
    argp.add_argument('-c', '--config', default='%s' % config,
                      help='config filename, default is %s' % config)

    return argp.parse_args()


def get_config(filename):
    parser = SafeConfigParser()
    parser.read(filename)
    return parser._sections


def get_font(font, size):
    """Get asked font or pygame.default."""
    available = pygame.font.get_fonts()
    if font.lower() in available:
        return pygame.font.SysFont(font.lower(), size)
    else:
        return pygame.font.Font(None, size)


def create_label(text, font, size, color=pygame.Color('black')):
    """Create pygame label."""
    font = get_font(font, size)
    return font.render(text.decode('utf-8'), 0, color)

def get_text_param(config, text_id):
    """Make dict with all param of a message."""
    text_param = dict()
    text_param['text'] = config['msgs'][text_id]
    text_param['font'] = config['font'][text_id]
    text_param['size'] = int(config['size'][text_id])
    text_param['color'] = config['color'][text_id]
    text_param['positions'] = tuple([int(elt) for elt in config['positions'][text_id].split(',')])

    return text_param

def get_camera_param(config):
    camera_param = dict()
    camera_param['positions'] = config['camera'].get('positions').split(',')
    camera_param['brightness'] = config.get('camera').get('brightness')
    camera_param['cam_image_width'] = config.get('camera').get('cam_image_width')
    camera_param['cam_image_height'] = config.get('camera').get('cam_image_height')
    
    return camera_param

def text_show(screen, text, font, size, color, positions):
    """ show text. """
    
    text_label = create_label(text, font, size, color=pygame.Color('black') )
    screen.blit(text_label, positions)
    pygame.display.update()

def text_clear(screen, bg_color, text, font, size, color, positions):
    """ show text. """
    
    text_label = create_label(text, font, size, bg_color )

    screen.blit(text_label, positions)
    pygame.display.update()



def build_qrcode(finalpicname, msg_url, qrcode_name):
    from qrcode import QRCode, constants
    qr = QRCode(version=1,
                error_correction=constants.ERROR_CORRECT_L,
                box_size=8, border=1, )
    qr.add_data(msg_url + finalpicname)
    qr.make()
    img = qr.make_image()
    img.save(qrcode_name)


def switch_light(state=0):
    """Switch light."""
    GPIO.output(11, not state)


def countdown_timer(screen, config, bg_color, ticks=2):
    """Countdown with final text."""

    for tick in range(ticks, 0, -1):
        countdown_text_show = create_label(str(tick), config['pyg']['font'],
                                           200, pygame.Color('black'))
        countdown_text_clear = create_label(str(tick), config['pyg']['font'],
                                            200, bg_color)
        screen.blit(countdown_text_show, (762, 474))
        pygame.display.update()
        time.sleep(1)
        screen.blit(countdown_text_clear, (762, 474))
        pygame.display.update()

def pics_assembly(config, pic_names, finalpicname, finalpic):
    convert_args = []
    if config['convert'].get('pre_options'):
        convert_args.extend([config['convert'].get('pre_options')])

    convert_args.extend([config['convert'].get('binary_path'),
                '-quality', config['convert'].get('quality'), 
                config['paths'].get('layout_path'),
                 '-gravity', config['convert'].get('gravity')]) 
            
    for photo_id in range(0, int(config['prog']['seq_photo'])):
        convert_args.extend([pic_names[photo_id], "-geometry",
                     config['convert']['position' + str(photo_id)],'-composite'])
            
    if config['qrcode']:
    # build qrcode
        build_qrcode(finalpicname, config['msgs']['msg_url'],
                     config['qrcode']['qrcode_name'])
        convert_args.extend([config['qrcode']['qrcode_name'], '-geometry', 
                      config['qrcode']['position'], '-composite'])

    convert_args.append(finalpicname)
    subprocess.call(convert_args)


def pics_assembly2(config):
    subprocess.call(['nice', '-n -9', config['paths']['convert_path'],
                             '-quality', '90', config['paths']['layout_path'],
                             "-gravity", "southwest", pic_names[0],
                             "-geometry", config['pics']['']+"+100+1100", "-composite",
                             pic_names[1], "-geometry", "+1030+1100",
                             "-composite", pic_names[2], "-geometry",
                             "+100+400", "-composite", pic_names[3],
                             "-geometry", "+1030+400", "-composite",
                             config['qrcode']['qrcode_name'],
                             '-geometry', '+700+100',
                             '-composite', finalpic])

def make_thumbnail(config, finalpic):
    subprocess.call([config['paths']['convert_path'], finalpic,
                     '-resize', config['convert']['thumbnail_size'],
                             finalpic + '.thumbnail.jpg'])

def setup_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(11, GPIO.OUT)
    GPIO.setup(15, GPIO.IN, pull_up_down=GPIO.PUD_UP)


def setup_env(config):
    # Init framebuffer/touchscreen environment variables
    os.putenv('SDL_VIDEODRIVER', 'fbcon')
    os.putenv('SDL_FBDEV', '/dev/fb0')
    os.putenv('SDL_NOMOUSE', '1')


    pygame.init()
    pygame.mouse.set_visible(False)

def setup_screen(bg_color):
 
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    screen.fill(bg_color)

    return screen

def setup_camera(bg_color, brightness, screen ):
    camera = picamera.PiCamera()

    cam_video_width, cam_video_height = picamera.PiCamera.MAX_VIDEO_RESOLUTION

    video_surface_width = cam_video_width / 2
    video_surface_height = cam_video_height / 2
    
    camera.preview_fullscreen = False
    camera.brightness = int(brightness)
    camera.resolution = (video_surface_width, video_surface_height)
    width, height = screen.get_size()
    left = (width - video_surface_width) / 2
    top = (height - video_surface_height) / 2

    camera.preview_window = (left, top, video_surface_width,
                             video_surface_height)

    return camera, video_surface_width, video_surface_height

def main(config):
    setup_env(config)

    # DATA
   #pygame.mixer.music.load('shot.wav')

    bg_color = pygame.Color(config['pyg']['screen_bg_color'])
    # fullscreen settings :
    screen = setup_screen(bg_color)

    text_param = {}
    text_param['msg_find_your_pic'] = get_text_param(config, 'msg_find_your_pic')
    text_param['msg_do'] = get_text_param(config, 'msg_do') 
    text_param['msg_title'] = get_text_param(config, 'msg_title') 
    text_param['msg_smile'] = get_text_param(config, 'msg_smile') 
    text_param['msg_assembly'] = get_text_param(config, 'msg_assembly')
    text_param['msg_url']  = get_text_param(config, 'msg_url')

    text_show(screen, **text_param['msg_find_your_pic'] )
    
	
    setup_gpio()
    
    camera_param = get_camera_param(config)

    camera, video_surface_width, video_surface_height = setup_camera(bg_color, camera_param['brightness'], screen )
    camera.start_preview()
    pygame.display.flip()

    loop_value = True
    while loop_value:
        for event in pygame.event.get():
            if event.type == QUIT:
                loop_value = False
            if event.type == KEYDOWN:
                if event.key == K_q or event.key == K_ESCAPE:
                    loop_value = False
                if event.key == K_SPACE:
                    countdown_timer(screen, config, bg_color)

        text_show(screen, **text_param['msg_do'])


        pygame.display.update()
        do = False
      
        # catch GPIO.input
        if not GPIO.input(15) or do:

            do = False


            text_clear(screen, bg_color, **text_param['msg_do'])
            text_show(screen, **text_param['msg_title'])
            time.sleep(3)
            
            text_clear(screen, bg_color, **text_param['msg_title'])
            

            camera.stop_preview()
            camera.resolution = (int(config['camera']['cam_image_width']),
                                 int(config['camera']['cam_image_height']))
            seq_photo = int(config['prog']['seq_photo'])
            # time.sleep(1)
            pic_names = []
            now = datetime.now().strftime(config['prog']['date_fmt'])
            for photo_nb in range(1, seq_photo + 1):
                countdown_timer(screen, config, bg_color)

                text_show(screen, **text_param['msg_smile'])
                time.sleep(1)
                switch_light()
                #pygame.mixer.music.play()
                fname = '%s_%02d.jpg' % (os.path.join(config['paths']['pics_dir'],
                                                      now),
                                         photo_nb)
                pic_names.append(fname)
                camera.capture(fname)
                state = GPIO.input(11)
                time.sleep(0.5)
                switch_light(state)
                text_clear(screen, bg_color, **text_param['msg_smile'])

            text_show(screen, **text_param['msg_assembly'])

            camera.preview_window = (320, 330, video_surface_width,
                                     video_surface_height)
            camera.resolution = (video_surface_width, video_surface_height)
            finalpicname = '%s%s' % (os.path.join(config['paths']['pics_dir'], now), config['prog']['pic_name'])
            finalpic = '%s%s' % (os.path.join(config['paths']['pics_dir'], now),
                                 config['prog']['pic_name'])

	    pics_assembly(config, pic_names, finalpicname, finalpic)
            layout = pygame.image.load(finalpic)
            screen.fill(bg_color)
            screen.blit(pygame.transform.scale(layout, (1920 / 2, 1920 / 2)),
                        (136, 16))
           

            text_show(screen, **text_param['msg_url'])
 
            if config['convert'].get('thumbnail_size'): 
                make_thumbnail(config, finalpic)
            
            if config['paths'].get('rsync_script'):
                subprocess.call([config['paths']['rsync_script']])
    
            time.sleep(18)
            screen.fill(bg_color)
            text_show(screen, **text_param['msg_url'])
            camera.start_preview()


if __name__ == "__main__":

    args = parser()
    config = get_config(args.config)
    main(config)
