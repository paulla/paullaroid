#!/usr/bin/python
# -*- coding: UTF-8 -*-

"""Photomaton tools:
 - qrcode
 - parser
 - get_config"""

import argparse
import os

from configparser import SafeConfigParser
from configparser import ExtendedInterpolation

from qrcode import QRCode
from qrcode import constants

def build_qrcode(url, qrcode_name):
    qr = QRCode(version=1,
                error_correction=constants.ERROR_CORRECT_L,
                box_size=8, border=1, )
    qr.add_data(url)
    qr.make()
    img = qr.make_image()
    img.save(qrcode_name)


def parser():
    """Build parser."""

    name = os.path.basename(__file__)
    config = '%s.ini' % os.path.splitext(name)[0]
    argp = argparse.ArgumentParser(description=__doc__)
    argp.add_argument('-c', '--config', default='%s' % config,
                      help='config filename, default is %s' % config)

    return argp.parse_args()


def get_config(filename):

    parser = SafeConfigParser(interpolation=ExtendedInterpolation())
    parser.read(filename)

    return parser
