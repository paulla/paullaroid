#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""PauLLA Photomaton, exposed on THSF 2015."""

import subprocess
import sys
import time
import os

from collections import namedtuple
from datetime import datetime
from random import randint

import pygame
import RPi.GPIO as GPIO

from picamera import PiCamera
from pygame.locals import KEYDOWN, K_ESCAPE, K_SPACE, K_q, QUIT

from .tools import build_qrcode, parser, get_config

Positions = namedtuple('Positions', ['x', 'y'])


class MsgTexte(object):
    """Took (text, font, size, bg_color, positions = (0,0), color)."""

    def __init__(self, bg_color, text, font, size, positions, color='black', encoding='utf-8'):
        self.encoding = encoding
        self.positions = Positions(*tuple(int(elt) for elt in positions.split(',')))
        self.bg_color = bg_color
        self.color = color
        self.size = int(size)

        self.font = self._get_font(font, self.size)
        self.label_show = self.font.render(text, 0, pygame.Color(self.color))
        self.label_clear = self.font.render(text, 0, pygame.Color(self.bg_color))

    @staticmethod
    def _get_font(font, size):
        """Get asked font or pygame.default."""

        available = pygame.font.get_fonts()
        if font.lower() in available:
            return pygame.font.SysFont(font.lower(), size)
        else:
            return pygame.font.Font(None, size)

    def show(self, screen):
        """Paint text."""

        screen.blit(self.label_show, self.positions)
        pygame.display.update()


    def clear(self, screen):
        """Clear text."""

        screen.blit(self.label_clear, self.positions)
        pygame.display.update()


def switch_light():
    """Switch light."""
    state = GPIO.input(11)
    GPIO.output(11, not state)


class CountdowTimer(object):
    """Countdown with final text."""
    def __init__(self,  bg_color, font, size=200, nombre=2, positions = '0, 0', color='black'):
        self.ticks = []
        for tick in range(int(nombre)): 
            self.ticks.append(MsgTexte(bg_color, str(int(nombre) - tick), font, size, positions, color))


    def show(self, screen):
	
        for tick in self.ticks:
            tick.show(screen)
            time.sleep(1)
            tick.clear(screen)



def make_thumbnail(config, finalpic):
    subprocess.call([config.get('paths', 'convert_path'), finalpic,
                     '-resize', config.get('convert', 'thumbnail_size'),
                             finalpic + '.thumbnail.jpg'])


def setup_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(11, GPIO.OUT)
    GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_UP)


def setup_env(config):
    #  Init framebuffer/touchscreen environment variables
    os.putenv('SDL_VIDEODRIVER', 'fbcon')
    os.putenv('SDL_FBDEV', '/dev/fb0')
    os.putenv('SDL_NOMOUSE', '1')

    pygame.init()
    pygame.mouse.set_visible(False)


def setup_screen(bg_color):

    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    screen.fill(bg_color)

    return screen


def setup_msg(config):
    bg_color =  config.get('pyg','screen_bg_color')


    msg_textes = {}


    msg_textes['find_pic'] = MsgTexte(bg_color = bg_color, **dict(config.items('msg_find_your_pic')))
    msg_textes['do'] = MsgTexte(bg_color = bg_color, **dict(config.items('msg_do')))
    msg_textes['title'] = MsgTexte(bg_color = bg_color, **dict(config.items('msg_title')))
    msg_textes['smile_1'] = MsgTexte(bg_color = bg_color, **dict(config.items('msg_smile_1')))
    msg_textes['smile_2'] = MsgTexte(bg_color = bg_color, **dict(config.items('msg_smile_2')))
    msg_textes['smile_3'] = MsgTexte(bg_color = bg_color, **dict(config.items('msg_smile_3')))
    msg_textes['smile_4'] = MsgTexte(bg_color = bg_color, **dict(config.items('msg_smile_4')))
    msg_textes['assembly'] = MsgTexte(bg_color = bg_color, **dict(config.items('msg_assembly')))
    msg_textes['url']  = MsgTexte(bg_color = bg_color, **dict(config.items('msg_url')))

    return msg_textes


class MyCamera(PiCamera):

    def __init__(self, brightness, screen, image_width,
                    image_height, positions):

        super(MyCamera, self).__init__()

        cam_video_width, cam_video_height = PiCamera.MAX_VIDEO_RESOLUTION

        self.video_surface_width = int(cam_video_width / 2)
        self.video_surface_height = int(cam_video_height / 2)
        self.rotation = 90
        self.preview_fullscreen = False
        self.brightness = int(brightness)
        self.width, self.height = screen.get_size()
        left = int((self.width - self.video_surface_width) / 2)
        top = int((self.height - self.video_surface_height) / 2)

        self.preview_window = (left, top, self.video_surface_width,
                             self.video_surface_height)

    def start_preview(self):
        super(MyCamera, self).start_preview()
        pygame.display.flip()


    def set_video_resolution(self):
         self.resolution = (self.video_surface_width, self.video_surface_height)

    def set_resolution(self, width, height):
         self.resolution = (int(width), int(height))

    #def resize(self):
    #    self.preview_window = (320, 330, self.video_surface_width,
    #                                 self.video_surface_height)
    #    self.resolution()


class Photos:

    def __init__(self, cam, timer, image_width, image_height, pics_dir, seq_photo, convert, date_fmt='%Y-%m-%d_%H-%M-%S'):
        self.seq_photo = int(seq_photo)
        self.pic_names = []
        self.date_fmt = date_fmt
        self.pics_dir = pics_dir
        self.cam = cam
        self.image_width = int(image_width)
        self.image_height = int(image_height)
        self.timer = timer 
        self.convert = convert

    def take(self, messages, screen):
        nombre = len([key for key in messages.keys() if key.startswith('smile_')])
        self.now = datetime.now().strftime(self.date_fmt)
        self.cam.stop_preview()
        self.cam.set_resolution(int(self.image_width), int(self.image_height))
        for photo_nb in range(1, self.seq_photo+1):
            num = str(randint(1,nombre)) 
            self.timer.show(screen)
            messages['smile_'+num].show(screen)
            time.sleep(1)
            switch_light()
            #pygame.mixer.music.play()
            fname = '%s_%02d.jpg' % (os.path.join(self.pics_dir, self.now), photo_nb)
            self.pic_names.append(fname)
            self.cam.capture(fname)
            time.sleep(0.5)
            switch_light()
            messages['smile_'+num].clear(screen)


    def pics_assembly(self):
        finalpic = '%s_THSF2016.jpg' % (os.path.join(self.pics_dir, self.now))

        convert_args = []
        if self.convert.get('pre_options'):
            convert_args.append(self.convert.get('pre_options'))
    
        convert_args.extend([self.convert.get('binary_path'),
                    '-quality', self.convert.get('quality'),
                    self.convert.get('layout_path'),
                     '-gravity', self.convert.get('gravity','northwest')])
    
        for photo_id in range(0, self.seq_photo):
            convert_args.extend([self.pic_names.pop(0), "-geometry",
                         self.convert.get('position' + str(photo_id)),'-composite'])
    
        if self.convert.get('qrcode_position'):
            url = self.convert.get('qrcode_url') + self.now + 'jpg'
            build_qrcode(url, 'qrcode_image.png')
            convert_args.extend(['qrcode_image.png', '-geometry',
                          self.convert.get('qrcode_position'), '-composite'])
    
        convert_args.append(finalpic)
        subprocess.call(convert_args)
        return finalpic


def play(config):
    setup_env(config)
    setup_gpio()
    msg_textes = setup_msg(config)

    build_qrcode(config.get('defaults', 'url'), 'qrcode_site.png')

    bg_color_text =  config.get('pyg','screen_bg_color')
    bg_color = pygame.Color(bg_color_text)
    timer = CountdowTimer(bg_color_text, **dict(config.items('countdown')))

    screen = setup_screen(bg_color)


    msg_textes['find_pic'].show(screen)
    my_cam = MyCamera(screen = screen, **dict(config.items('camera')))
    photo = Photos(my_cam, timer, convert = dict(config.items('convert')), **dict(config.items('image')))


    my_cam.start_preview()

    loop_value = True
    while loop_value:
        for event in pygame.event.get():
            if event.type == QUIT:
                loop_value = False
            if event.type == KEYDOWN:
                if event.key == K_q or event.key == K_ESCAPE:
                    loop_value = False

        msg_textes['do'].show(screen)

        pygame.display.update()
        do = False

        if not GPIO.input(4) or do:

            do = False


            msg_textes['do'].clear(screen)
            msg_textes['title'].show(screen)
            time.sleep(3)

            msg_textes['title'].clear(screen)
	
            photo.take(msg_textes,  screen)

            msg_textes['assembly'].show(screen)

            finalpic = photo.pics_assembly()
            layout = pygame.image.load(finalpic)
            screen.fill(bg_color)
            screen.blit(pygame.transform.scale(layout, (int(1920 / 2), int(1920 / 2))), (136, 16))

            msg_textes['find_pic'].show(screen)

            if config.get('convert', 'thumbnail_size'):
                make_thumbnail(config, finalpic)

            if config.get('paths', 'rsync_script'):
                subprocess.call([config.get('paths', 'rsync_script')])

            time.sleep(10)
            screen.fill(bg_color)
            msg_textes['find_pic'].show(screen)
            my_cam.start_preview()
            layout_qrcode = pygame.image.load('qrcode_site.png')
            screen.blit( layout_qrcode, (1136, 16))

            pygame.display.update()


def main():
    args = parser()
    config = get_config(args.config)
    play(config)
