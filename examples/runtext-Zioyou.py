#!/usr/bin/env python
# Display a runtext with double-buffering.
from samplebase import SampleBase
from rgbmatrix import graphics
import time
import argparse

# python /home/suzukaotto/Project/runtext-ZioYou.py --led-cols=64 --led-rows=32 --led-chain=7 --led-slowdown-gpio=5 --led-pixel-mapper="V-mapper;Rotate:270" --led-pwm-lsb-nanoseconds=120

class RunText(SampleBase):
    def __init__(self, *args, **kwargs):
        super(RunText, self).__init__(*args, **kwargs)
        self.parser.add_argument("-t", "--text", help="The text to scroll on the RGB LED panel", default="협업의 시작 ZioYou")

    def run(self):
        offscreen_canvas = self.matrix.CreateFrameCanvas()
        font = graphics.Font()
        font.LoadFont("/home/suzukaotto/Project/Fonts/Hangul.bdf")
        textColor = graphics.Color(255, 255, 255)
        blueColor = graphics.Color(0, 0, 255)
        pos = offscreen_canvas.width
        my_text = self.args.text

        while True:
            offscreen_canvas.Clear()
            len_white = graphics.DrawText(offscreen_canvas, font, pos, 30, textColor, my_text[:-6])  # "협업의 시작 "
            len_blue = graphics.DrawText(offscreen_canvas, font, pos + len_white, 30, blueColor, my_text[-6:])  # "ZioYou" blue
            pos -= 1
            if (pos + len_white + len_blue < 0):
                pos = offscreen_canvas.width

            time.sleep(0.02)
            offscreen_canvas = self.matrix.SwapOnVSync(offscreen_canvas)


# Main function
if __name__ == "__main__":
    run_text = RunText()
    run_text.process()
