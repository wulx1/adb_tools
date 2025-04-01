# -*- coding: utf-8 -*-
# @Time : 2025/3/25 19:27
# @Author : longswu
# @File : mtest.py
import pyautogui
import random
import time

def keep_screen_on():
    screen_width, screen_height = pyautogui.size()
    while True:
        x = random.randint(0, screen_width)
        y = random.randint(0, screen_height)
        pyautogui.moveTo(x, y)
        time.sleep(5)  # 每5秒移动一次

keep_screen_on()