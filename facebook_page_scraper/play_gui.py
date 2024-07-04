"""Play mouse/keyboard recording as recorded using:
https://github.com/george-jensen/record-and-play-pynput
"""
import random
from typing import Callable, Tuple

import numpy as np
from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Key, Controller as KeyboardController
import time
import json
import sys

special_keys = {"Key.shift": Key.shift, "Key.tab": Key.tab, "Key.caps_lock": Key.caps_lock, "Key.ctrl": Key.ctrl,
                "Key.alt": Key.alt, "Key.cmd": Key.cmd, "Key.cmd_r": Key.cmd_r, "Key.alt_r": Key.alt_r,
                "Key.ctrl_r": Key.ctrl_r, "Key.shift_r": Key.shift_r, "Key.enter": Key.enter,
                "Key.backspace": Key.backspace, "Key.f19": Key.f19, "Key.f18": Key.f18, "Key.f17": Key.f17,
                "Key.f16": Key.f16, "Key.f15": Key.f15, "Key.f14": Key.f14, "Key.f13": Key.f13,
                "Key.media_volume_up": Key.media_volume_up, "Key.media_volume_down": Key.media_volume_down,
                "Key.media_volume_mute": Key.media_volume_mute, "Key.media_play_pause": Key.media_play_pause,
                "Key.f6": Key.f6, "Key.f5": Key.f5, "Key.right": Key.right, "Key.down": Key.down, "Key.left": Key.left,
                "Key.up": Key.up, "Key.page_up": Key.page_up, "Key.page_down": Key.page_down, "Key.home": Key.home,
                "Key.end": Key.end, "Key.delete": Key.delete, "Key.space": Key.space}

mouse = MouseController()
keyboard = KeyboardController()


def play_recording(name_of_recording,
                   random_start=False, max_execute_sec: Tuple[int, int] = None,
                   stop_condition: Callable[[], bool] = lambda: False,
                   pause_condition: Callable[[], bool] = lambda: False):
    with open(name_of_recording) as json_file:
        data = json.load(json_file)

    if random_start:
        start_index = random.randint(0, len(data) - 1)
    else:
        start_index = 0

    rec_executed_time = 0
    to_execute_sec = random.uniform(*max_execute_sec) if max_execute_sec else np.inf
    for index in range(start_index, len(data)):
        obj = data[index]
        while pause_condition():
            time.sleep(random.uniform(0.1, 0.5))
            if stop_condition():
                return
        if stop_condition():
            return
        if rec_executed_time > to_execute_sec:
            return

        action, _time = obj['action'], obj['_time']
        try:
            next_movement = data[index + 1]['_time']
            pause_time = next_movement - _time
            rec_executed_time += pause_time
        except IndexError as e:
            pause_time = 1

        if action == "pressed_key" or action == "released_key":
            key = obj['key'] if 'Key.' not in obj['key'] else special_keys[obj['key']]
            print("action: {0}, time: {1}, key: {2}".format(action, _time, str(key)))
            if action == "pressed_key":
                keyboard.press(key)
            else:
                keyboard.release(key)
            time.sleep(pause_time)

        else:
            move_for_scroll = True
            x, y = obj['x'], obj['y']
            if action == "scroll" and index > 0 and (
                    data[index - 1]['action'] == "pressed" or data[index - 1]['action'] == "released"):
                if x == data[index - 1]['x'] and y == data[index - 1]['y']:
                    move_for_scroll = False
            print("x: {0}, y: {1}, action: {2}, time: {3}".format(x, y, action, _time))
            mouse.position = (x, y)
            if action == "pressed" or action == "released" or action == "scroll" and move_for_scroll == True:
                time.sleep(0.1)
            if action == "pressed":
                mouse.press(Button.left if obj['button'] == "Button.left" else Button.right)
            elif action == "released":
                mouse.release(Button.left if obj['button'] == "Button.left" else Button.right)
            elif action == "scroll":
                horizontal_direction, vertical_direction = obj['horizontal_direction'], obj['vertical_direction']
                mouse.scroll(horizontal_direction, vertical_direction)
            time.sleep(pause_time)


if __name__ == "__main__":
    n = len(sys.argv)

    if n < 3:
        exit("Takes two arguments - name of recording to play and number of times to play it")

    if n > 3:
        exit("Only takes two argument - name of recording to play and number of times to play it")

    if n == 3:
        name_of_recording = "data/" + str(sys.argv[1]) + '.txt'
        number_of_plays = int(sys.argv[2])