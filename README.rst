.. contents::

Introduction
============

Photomaton by PauLLA and MIPS-LAB


Le photomaton est une super machine qui vous prend en photo, à base de Rpi.
Merci à Xel (https://github.com/XeL64) pour le lancement du projet !

INSTALL
=======

 python bootstrap-buildout.py

 bin/buildout 


USAGE
=====

bin/paullaroid -c photomaton.ini 

NOTES
======
>>> Notes concernant le photomaton version PyConFr

- Coordonnées des photos dans le background du photomaton pour la PyConFr :
    
* Photo Haut Gauche : 27,27
* Photo Haut Droit  : 1083,90
* Photo Bas Droit   : 27,850
* Photo Bas gauche  : 1105, 773

- Couleur pour afficher URL et date
    gris : Héxa #808080 / RGB 128,128,128
