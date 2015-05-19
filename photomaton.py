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
from qrcode import QRCode, constants
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
    return font.render(text, True, color)


def build_qrcode(finalpicname, msg_url, qrcode_name):
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
        screen.blit(countdown_text_show, (100, 400))
        pygame.display.update()
        time.sleep(1)
        screen.blit(countdown_text_clear, (100, 400))
        pygame.display.update()


def setup_gpio():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(11, GPIO.OUT)
    GPIO.setup(15, GPIO.IN, pull_up_down=GPIO.PUD_UP)


def setup_env():
    # Init framebuffer/touchscreen environment variables
    os.putenv('SDL_VIDEODRIVER', 'fbcon')
    os.putenv('SDL_FBDEV', '/dev/fb0')
    os.putenv('SDL_NOMOUSE', '1')


def main(config):
    setup_env()

    # DATA

    cam_video_width, cam_video_height = picamera.PiCamera.MAX_VIDEO_RESOLUTION

    video_surface_width = cam_video_width / 2
    video_surface_height = cam_video_height / 2

    bg_color = pygame.Color(config['pyg']['screen_bg_color'])
    pygame.init()
    pygame.mouse.set_visible(False)
    pygame.mixer.music.load('shot.wav')

    # fullscreen settings :

    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    screen.fill(bg_color)

    url_text_show = create_label(config['msgs']['msg_find_your_pic'],
                                 config['pyg']['font-bold'], 32,
                                 pygame.Color('black'))

    screen.blit(url_text_show, (350, 940))

    setup_gpio()

    camera = picamera.PiCamera()
    pygame.display.flip()

    camera.preview_fullscreen = False
    camera.brightness = 50
    camera.resolution = (video_surface_width, video_surface_height)
    camera.preview_window = (140, 200, video_surface_width,
                             video_surface_height)
    camera.start_preview()

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

        notice_text_show = create_label(config['msgs']['msg_do'],
                                        config['pyg']['font'], 50,
                                        pygame.Color('black'))
        notice_text_clear = create_label(config['msgs']['msg_do'],
                                         config['pyg']['font'], 50,
                                         bg_color)

        screen.blit(notice_text_show, (50, 750))
        pygame.display.update()

        # catch GPIO.input
        if not GPIO.input(15):

            title_text_show = create_label(config['msgs']['msg_title'],
                                           config['pyg']['font'], 50,
                                           pygame.Color('black'))

            title_text_clear = create_label(config['msgs']['msg_title'],
                                            config['pyg']['font'], 50,
                                            bg_color)

            smyle_text_show = create_label(config['msgs']['msg_smile'],
                                           config['pyg']['font'], 100,
                                           pygame.Color('black'))
            smyle_text_clear = create_label(config['msgs']['msg_smile'],
                                            config['pyg']['font'], 100,
                                            bg_color)

            screen.blit(notice_text_clear, (50, 750))
            screen.blit(title_text_show, (50, 750))
            pygame.display.update()
            time.sleep(3)
            screen.blit(title_text_clear, (50, 750))
            pygame.display.update()
            camera.stop_preview()
            camera.resolution = (int(config['cam']['cam_image_width']),
                                 int(config['cam']['cam_image_height']))
            seq_photo = int(config['prog']['seq_photo'])
            # time.sleep(1)
            pic_names = []
            now = datetime.now().strftime(config['prog']['date_fmt'])
            for photo_nb in range(1, seq_photo + 1):
                countdown_timer(screen, config, bg_color)

                screen.blit(smyle_text_show, (510, 40))
                pygame.display.update()
                time.sleep(1)
                switch_light()
                pygame.mixer.music.play()
                fname = '%s_%02d.jpg' % (os.path.join(config['paths']['pics_dir'],
                                                      now),
                                         photo_nb)
                pic_names.append(fname)
                camera.capture(fname)
                state = GPIO.input(11)
                time.sleep(0.5)
                switch_light(state)
                screen.blit(smyle_text_clear, (510, 40))
                pygame.display.update()

            wait_text_show = create_label(config['msgs']['msg_assembly'],
                                          config['pyg']['font'], 70,
                                          pygame.Color('black'))

            screen.blit(wait_text_show, (10, 40))
            pygame.display.update()
            camera.preview_window = (32, 24, video_surface_width,
                                     video_surface_height)
            camera.resolution = (video_surface_width, video_surface_height)
            finalpicname = '%s%s' % (now, config['prog']['pic_name'])
            finalpic = '%s%s' % (os.path.join(config['paths']['pics_dir'], now),
                                 config['prog']['pic_name'])

            # build qrcode
            build_qrcode(finalpicname, config['msgs']['msg_url'],
                         config['qrcode']['qrcode_name'])

            subprocess.call(['nice', '-n -9', config['paths']['convert_path'],
                             '-quality', '90', config['paths']['layout_path'],
                             "-gravity", "southwest", pic_names[0],
                             "-geometry", "+100+1100", "-composite",
                             pic_names[1], "-geometry", "+1030+1100",
                             "-composite", pic_names[2], "-geometry",
                             "+100+400", "-composite", pic_names[3],
                             "-geometry", "+1030+400", "-composite",
                             config['qrcode']['qrcode_name'],
                             '-geometry', '+700+100',
                             '-composite', finalpic])

            layout = pygame.image.load(finalpic)
            # qrcodelayout = pygame.image.load(qrcode_name)
            screen.fill(bg_color)
            screen.blit(pygame.transform.scale(layout, (1920 / 2, 1920 / 2)),
                        (136, 16))
            # screen.blit(pygame.transform.scale(qrcodelayout, (150,150)),
            #             (450,800))
            screen.blit(url_text_show, (350, 950))
            pygame.display.update()
            subprocess.call([config['paths']['convert_path'], finalpic,
                             '-resize', '200x200',
                             finalpic + '.thumbnail.jpg'])
            subprocess.call([config['paths']['rsync_script']])
            time.sleep(18)
            screen.fill(bg_color)
            screen.blit(url_text_show, (350, 940))
            pygame.display.update()
            camera.start_preview()


if __name__ == "__main__":

    args = parser()
    config = get_config(args.config)
    main(config)
