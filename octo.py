#!/usr/bin/env python3
# vim:fileencoding=ISO-8859-1
#
# Title: Octopy
# Description: Multi-channel midi-activated audio player with synchronized midi output on the Raspberry Pi platform
# Author: D Cooper Dalrymple (https://dcdalrymple.com/)
# Created: 2017-10-19
# Updated: 2021-11-16

try:
    import sys
    import getopt
    import time
    import argparse
    import threading

    # Libraries included in other files
    import os
    import configparser
    import subprocess
    import alsaaudio
    import wave
    import time
    import rtmidi
    from rtmidi.midiutil import open_midiinput
    from rtmidi.midiutil import open_midioutput
    from rtmidi.midiconstants import (CHANNEL_PRESSURE, CONTROLLER_CHANGE, NOTE_OFF, NOTE_ON, PITCH_BEND, POLY_PRESSURE, PROGRAM_CHANGE)
    from mido import MidiFile
except ImportError as err:
    print("Could not load {} module.".format(err))
    raise SystemExit

from octosettings import OctoSettings
from octofiles import OctoFiles
from octofiles import OctoUsb
from octofiles import OctoKeymap
from octomidi import OctoMidi
from octoaudio import OctoAudio
from octovideo import OctoVideo
from octomanager import OctoManager
from nullmidi import NullMidi

from getch import _Getch

def handle_midi(note):
    if note > 0 and files.getfiles() and note <= len(files.getfiles()):
        manager.stop()

        file = files.getfiles()[note-1]
        if settings.get_verbose():
            print("File Selected: {}\n".format(file.get_description()))

        manager.load(file)
        manager.start()
        return True # Note processed

    elif note == 0:
        manager.stop()
        return True # Note processed

    return False # Passthrough note

def led_setup(pin=False):
    if pin == False:
        pin = settings.get_statusled()
    if not type(pin) is int or pin <= 0:
        return False

    try:
        import RPi.GPIO
    except ImportError as err:
        print("Could not load {} module.".format(err))
        return False

    RPi.GPIO.setmode(RPi.GPIO.BCM)
    RPi.GPIO.setwarnings(False)
    RPi.GPIO.setup(pin, RPi.GPIO.OUT)
    return True

def led_high(pin=False):
    if pin == False:
        pin = settings.get_statusled()
    if not type(pin) is int or pin <= 0:
        return False

    try:
        import RPi.GPIO
    except ImportError as err:
        return False

    RPi.GPIO.output(pin, RPi.GPIO.HIGH)
    return True

def led_low(pin=False):
    if pin == False:
        pin = settings.get_statusled()
    if not type(pin) is int or pin <= 0:
        return False

    try:
        import RPi.GPIO
    except ImportError as err:
        return False

    RPi.GPIO.output(pin, RPi.GPIO.LOW)
    return True

if __name__ == '__main__':

    settings = OctoSettings()

    parser = argparse.ArgumentParser(description="Octopy")

    parser.add_argument('--verbose', action='store_true', default=settings.get('verbose'), help='Display console output.')

    parser.add_argument('--audiodevice', type=str, default=settings.get('audiodevice'), metavar='Audio Device Index')
    parser.add_argument('--buffersize', type=int, default=settings.get('buffersize'), metavar='Buffer Size')

    parser.add_argument('--localmedia', type=str, default=settings.get('localmedia'), metavar='Relative Media Directory')
    parser.add_argument('--storagemedia', type=str, default=settings.get('storagemedia'), metavar='External Storage Media Directory')

    parser.add_argument('--midiindevice', type=str, default=settings.get('midiindevice'), metavar='Midi Input Device')
    parser.add_argument('--midiinchannel', type=int, default=settings.get('midiinchannel'), metavar='Midi Input Channel Filter', help='Used for selecting song playback')
    parser.add_argument('--midioutdevice', type=str, default=settings.get('midioutdevice'), metavar='Midi Output Device')
    parser.add_argument('--midioutchannel', type=int, default=settings.get('midioutchannel'), metavar='Midi Output Channel', help='When > 0, force a midi channel. Otherwise, use original midi message channels.')

    parser.add_argument('--midiclock', action='store_true', default=settings.get('midiclock'), help='Output midi clock messages. Is set to selected song midi file bpm.')
    parser.add_argument('--midisong', action='store_true', default=settings.get('midisong'), help='Output song start and stop midi messages.')

    parser.add_argument('--midipanic_alloff', action='store_true', default=settings.get('midipanic_alloff'), help='Send MIDI All Off (CC 120) on panic/stop.')
    parser.add_argument('--keymapfile', type=str, default=settings.get('keymapfile'), metavar='Keymap CSV File', help='Path to CSV file mapping keyboard keys to files.')

    parser.add_argument('--videoenabled', action='store_true', default=settings.get('videoenabled'), help='Enable video output. Requires pygame.')
    parser.add_argument('--videobgcolor', type=str, default=settings.get('videobgcolor'), metavar='Video Background Color', help='Use hexadecimal encoded rgb color value (ie: #000000).')
    parser.add_argument('--videobgimage', type=str, default=settings.get('videobgimage'), metavar='Video Background Image', help='Path to image to use as video background. Supports PNG, JPG, GIF, and BMP formats.')
    parser.add_argument('--videoplayer', type=str, default=settings.get('videoplayer'), metavar='Desired Video Player', help='Select your preferred video playback handler. Available options: pyvidplayer, OMX, MPV, FFmpeg, and hello_video.')

    settings.set(parser.parse_args())

    # Only import pygame if video output is enabled
    if settings.get_videoenabled():
        try:
            os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
            import pygame
        except ImportError as err:
            print("Could not load {} module.".format(err))
            raise SystemExit

    # Configure LED if enabled
    if not led_setup() and settings.get_statusled() > 0:
        settings.set_statusled(0)
        if settings.get_verbose():
            print("Could not initialize status LED.")

    # LED high to indicate we're loading
    led_high()

    # Initialize and build file list (local and storage)
    files = OctoFiles(settings)
    if settings.get_storagemedia():
        usb = OctoUsb(settings)
        if usb.getpath():
            files.append(usb.getfiles())
    files.sort()

    if settings.get_verbose():
        files.print()

    # Initialize keymap with file list
    keymap = OctoKeymap(settings, files)

    # Preload Files
    if settings.get_preloadmedia():
        files.loadfiles()

    # Initialize Audio
    audio = OctoAudio(settings)

    # Initialize Midi
    # Check if null MIDI device requested (for testing without ALSA)
    if settings.get_midiindevice() == 'null' and settings.get_midioutdevice() == 'null':
        midi = NullMidi()
        if settings.get_verbose():
            print("Using null MIDI device (no actual MIDI I/O).\n")
    else:
        midi = OctoMidi(settings)
        midi.set_callback(handle_midi)
        midi.open()

    # Initialize Video
    video = OctoVideo(settings)
    video.init()

    # Setup Audio/Midi Manager
    manager = OctoManager(settings, audio, midi, video, led_high, led_low)

    # Turn off LED to indicate loading completion
    led_low()

    # Wait for keyboard interrupt
    if settings.get_verbose():
        if settings.get_keyboardcontrol():
            print("Entering main loop. Press 1-9 to play file. Press 0 to stop. Press Q or Control-C to exit.\n")
        else:
            print("Entering main loop. Press Control-C to exit.\n")
    try:
        getch = False
        if settings.get_keyboardcontrol() and not settings.get_videoenabled():
            getch = _Getch()

        while True:
            if settings.get_videoenabled():
                # Pygame focus
                if settings.get_keyboardcontrol():
                    pygame_break = False
                    for event in pygame.event.get():
                        if event.type == pygame.KEYDOWN:
                            key_char = chr(event.key) if event.key < 128 else ''
                            # Check keymap first, then fallback to numeric keys
                            file_index = keymap.get_file_index(key_char)
                            if file_index is not None:
                                handle_midi(file_index)
                            elif key_char.isnumeric():
                                handle_midi(int(key_char))
                            elif event.key in [pygame.K_q, pygame.K_ESCAPE] or (event.key == pygame.K_c and pygame.key.get_mods() & pygame.KMOD_CTRL):
                                pygame_break = True
                                break
                        elif event.type == pygame.QUIT:
                            pygame_break = True
                            break
                    if pygame_break:
                        break

                video.update()

            # Console focus
            elif settings.get_keyboardcontrol():
                ch = getch()
                # Check keymap first, then fallback to numeric keys
                file_index = keymap.get_file_index(ch)
                if file_index is not None:
                    handle_midi(file_index)
                elif ch.isnumeric():
                    handle_midi(int(ch))
                elif ch == "q" or ord(ch) in [3,26]: # 3=Ctrl+C, 26=Ctrl+Z
                    break

            else:
                time.sleep(1)

    except KeyboardInterrupt:
        if settings.get_verbose():
            print()
    finally:
        if settings.get_verbose():
            print("Exiting Octopy.")

        manager.stop()
        audio.close()
        midi.close()
        video.close()
