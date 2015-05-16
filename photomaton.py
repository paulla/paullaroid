# -*- coding: UTF-8 -*-

import picamera
import pygame
import os
import subprocess
import sys
import time
import RPi.GPIO as GPIO

from pygame.locals import *
from datetime import datetime
from qrcode import QRCode, constants

msg_url = "http://photomaton.thsf.net/photomaton/"
msg_title = "Une serie de 4 photos va etre prise "
msg_find_your_pic = "Retrouvez la photo sur %s " % msg_url
msg_do = 'Appuie sur le bouton ! '
msg_assembly = "J'assemble vos photos ..."

rsync_script = '/home/pi/photomaton/_data/rsync.sh'


def switch_light(state=0):
    if state == 0:
        GPIO.output(11, 1)
    else:
        GPIO.output(11, 0)


def countdown_timer(ticks=2):
    '''
    Countdown with final text
    '''
    countdownFont = pygame.font.SysFont("monospace", 200)
    for tick in range(ticks, 0, -1):
        countdownTextShow = countdownFont.render(str(tick), 0,
                                                 pygame.Color('black'))
        countdownTextClear = countdownFont.render(str(tick), 0, bgColor)
        screen.blit(countdownTextShow, (100, 400))
        pygame.display.update()
        time.sleep(1)
        screen.blit(countdownTextClear, (100, 400))
        pygame.display.update()
    return


def main():
    # Init framebuffer/touchscreen environment variables
    os.putenv('SDL_VIDEODRIVER', 'fbcon')
    os.putenv('SDL_FBDEV', '/dev/fb0')
    os.putenv('SDL_NOMOUSE', '1')

    #DATA
    cameraImageWidth = 800
    cameraImageHeight = 600
    cameraVideoWidth, cameraVideoHeight = \
        picamera.PiCamera.MAX_VIDEO_RESOLUTION

    pathFile = '/home/pi/photomaton/_data/_pics'
    textFinal = 'Souriez ;)'
    global screenWidth
    screenWidth = 1232
    global screenHeight
    screenHeight = 992

    videoSurfaceWidth = cameraVideoWidth / 2
    videoSurfaceHeight = cameraVideoHeight / 2

    photoWidth = cameraImageWidth / 4
    photoHeight = cameraImageHeight / 4

    pygame.init()
    pygame.mouse.set_visible(False)
    pygame.mixer.music.load('shot.wav')
    #Ouverture de la fenêtre Pygame
    global bgColor
    bgColor = pygame.Color('ivory')
    #fullscreen settings :
    global screen
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    urlFont = pygame.font.SysFont("monospace-bold", 32)
    urlTextShow = urlFont.render('msg_find_your_pic/', 0,
                                 pygame.Color('black'))
    urlTextClear = urlFont.render('msg_find_your_pic/', 0, bgColor)
    screen.fill(bgColor)
    screen.blit(urlTextShow, (350, 940))

    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(11, GPIO.OUT)
    GPIO.setup(15, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    #Rafraîchissement de l'écran
    camera = picamera.PiCamera()
    pygame.display.flip()
    #~ camera = picamera.PiCamera()
    camera.preview_fullscreen = False
    #~ camera.vflip = True
    camera.brightness = 50
    camera.resolution = (videoSurfaceWidth, videoSurfaceHeight)
    camera.preview_window = (140, 200, videoSurfaceWidth, videoSurfaceHeight)
    camera.start_preview()
    loopValue = True
    while loopValue:
        for event in pygame.event.get():
            if event.type == QUIT:
                loopValue = False
            if event.type == KEYDOWN:
                if event.key == K_q or event.key == K_ESCAPE:
                    loopValue = False
                if event.key == K_SPACE:
                    countdown_timer()
        smyleFont2 = pygame.font.SysFont("monospace", 50)
        NoticeTextShow = smyleFont2.render(msg_do, 0, pygame.Color('black'))
        NoticeTextClear = smyleFont2.render(msg_do, 0, bgColor)
        screen.blit(NoticeTextShow, (50, 750))
        pygame.display.update()
        if GPIO.input(15) == False:
            smyleFont = pygame.font.SysFont("monospace", 100)
            smyleFont2 = pygame.font.SysFont("monospace", 50)
            wifiTextShow = smyleFont2.render(msg_title, 0,
                                             pygame.Color('black'))
            wifiTextClear = smyleFont2.render(msg_title, 0, bgColor)
            screen.blit(NoticeTextClear, (50, 750))
            screen.blit(wifiTextShow, (50, 750))
            pygame.display.update()
            time.sleep(3)
            screen.blit(wifiTextClear, (50, 750))
            pygame.display.update()
            frame = nb = 4
            camera.stop_preview()
            camera.resolution = (cameraImageWidth, cameraImageHeight)
            sequencePhoto = 4
            #~ time.sleep(1)
            picNames = []
            now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            for photoNb in range(1, sequencePhoto + 1, 1):
                countdown_timer()
                smyleTextShow = smyleFont.render(textFinal, 0,
                                                 pygame.Color('black'))
                smyleTextClear = smyleFont.render(textFinal, 0, bgColor)
                screen.blit(smyleTextShow, (510, 40))
                pygame.display.update()
                time.sleep(1)
                switch_light()
                pygame.mixer.music.play()
                filename = '%s_%02d.jpg' % (os.path.join(pathFile, now),
                                            photoNb)
                picNames.append(filename)
                camera.capture(filename)
                state = GPIO.input(11)
                time.sleep(0.5)
                switch_light(state)
                screen.blit(smyleTextClear, (510, 40))
                pygame.display.update()
            assembleFont = pygame.font.SysFont("monospace", 70)
            waitTextShow = assembleFont.render(msg_assembly, 0,
                                               pygame.Color('black'))
            waitTextClear = assembleFont.render(msg_assembly, 0, bgColor)
            screen.blit(waitTextShow, (10, 40))
            pygame.display.update()
            camera.preview_window = (32, 24, videoSurfaceWidth,
                                     videoSurfaceHeight)
            camera.resolution = (videoSurfaceWidth, videoSurfaceHeight)
            finalpicname = '%sTHSF.jpg' % (now)
            finalpic = '%sTHSF.jpg' % (os.path.join(pathFile, now))
            qr = QRCode(version=1,
                        error_correction=constants.ERROR_CORRECT_L,
                        box_size=8, border=1,)
            qr.add_data(msg_url + finalpicname)
            qr.make()
            img = qr.make_image()
            img.save('qrcode.png')
            subprocess.call(['nice', '-n -9', '/usr/bin/convert', '-quality',
                             '90', '/home/pi/photomaton/layout_THSF.png',
                             "-gravity", "southwest", picNames[0],
                             "-geometry", "+100+1100", "-composite",
                             picNames[1], "-geometry", "+1030+1100",
                             "-composite", picNames[2], "-geometry",
                             "+100+400", "-composite", picNames[3],
                             "-geometry", "+1030+400", "-composite",
                             'qrcode.png', '-geometry', '+700+100',
                             '-composite', finalpic])
            layout = pygame.image.load(finalpic)
            qrcodelayout = pygame.image.load('qrcode.png')
            screen.fill(bgColor)
            screen.blit(pygame.transform.scale(layout, (1920 / 2, 1920 / 2)),
                                               (136, 16))
            screen.blit(urlTextShow, (350, 950))
            pygame.display.update()
            subprocess.call(['/usr/bin/convert', finalpic,
                             '-resize', '200x200',
                             finalpic + '.thumbnail.jpg'])
            subprocess.call([rsync_script])
            time.sleep(18)
            screen.fill(bgColor)
            screen.blit(urlTextShow, (350, 940))
            pygame.display.update()
            camera.start_preview()


if __name__ == "__main__":
    try:
        main()
    except:
        print 'Unexpected error : ', sys.exc_info()[0], sys.exc_info()[1]
