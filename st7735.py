"""Minimal ST7735 SPI TFT driver for MicroPython.

Published from Open Maker Studio's own reference driver for the ST7735 TFT
Display Blockly block. Talks to the chip over a plain `machine.SPI`
instance, drives an optional PWM backlight pin, and renders text via
`framebuf.FrameBuffer` — no other dependency needed.
"""
import time
import framebuf
from machine import PWM


class ST7735:
    def __init__(self, spi, cs, dc, rst, blk=None, width=128, height=160, rot=0):
        self.spi = spi; self.cs = cs; self.dc = dc; self.rst = rst; self.blk = blk
        self._w_phys = width; self._h_phys = height
        self.width = width; self.height = height
        self.cs.init(cs.OUT, value=1); self.dc.init(dc.OUT, value=0); self.rst.init(rst.OUT, value=0)
        if self.blk:
            self.pwm = PWM(self.blk); self.pwm.freq(1000); self.pwm.duty_u16(65535)
        self.reset(); self._init_display(); self.rotation(rot)

    def write_cmd(self, cmd): self.dc(0); self.cs(0); self.spi.write(bytearray([cmd])); self.cs(1)
    def write_data(self, buf): self.dc(1); self.cs(0); self.spi.write(buf); self.cs(1)
    def reset(self): self.rst(0); time.sleep_ms(50); self.rst(1); time.sleep_ms(50)

    def _init_display(self):
        self.write_cmd(0x01); time.sleep_ms(150); self.write_cmd(0x11); time.sleep_ms(255)
        self.write_cmd(0x3A); self.write_data(bytearray([0x05])); self.write_cmd(0x29); time.sleep_ms(10)

    def rotation(self, r):
        self.write_cmd(0x36)
        val = 0x00
        if r == 0: val = 0x00; self.width = self._w_phys; self.height = self._h_phys
        elif r == 1: val = 0xA0; self.width = self._h_phys; self.height = self._w_phys
        elif r == 2: val = 0xC0; self.width = self._w_phys; self.height = self._h_phys
        elif r == 3: val = 0x60; self.width = self._h_phys; self.height = self._w_phys
        self.write_data(bytearray([val]))

    def fill(self, color):
        self._set_window(0, 0, self.width-1, self.height-1)
        chunk_size = 4096; wb = bytearray(chunk_size * 2)
        c_hi = (color >> 8) & 0xFF; c_lo = color & 0xFF
        for i in range(0, chunk_size * 2, 2): wb[i] = c_hi; wb[i+1] = c_lo
        pixels = self.width * self.height
        while pixels > 0:
            count = min(pixels, chunk_size); self.write_data(wb[:count*2]); pixels -= count

    def pixel(self, x, y, color):
        if not (0 <= x < self.width and 0 <= y < self.height): return
        self._set_window(x, y, x, y); self.write_data(bytearray([(color >> 8) & 0xFF, color & 0xFF]))

    def line(self, x0, y0, x1, y1, color):
        dx = abs(x1 - x0); dy = abs(y1 - y0); sx = 1 if x0 < x1 else -1; sy = 1 if y0 < y1 else -1; err = dx - dy
        while True:
            self.pixel(x0, y0, color)
            if x0 == x1 and y0 == y1: break
            e2 = 2 * err
            if e2 > -dy: err -= dy; x0 += sx
            if e2 < dx: err += dx; y0 += sy

    def rect(self, x, y, w, h, color):
        self.line(x, y, x+w-1, y, color); self.line(x, y+h-1, x+w-1, y+h-1, color)
        self.line(x, y, x, y+h-1, color); self.line(x+w-1, y, x+w-1, y+h-1, color)

    def fill_rect(self, x, y, w, h, color):
        if w < 0 or h < 0 or x >= self.width or y >= self.height: return
        x2 = min(x + w - 1, self.width - 1); y2 = min(y + h - 1, self.height - 1)
        self._set_window(x, y, x2, y2); count = (x2 - x + 1) * (y2 - y + 1)
        chunk_size = 512; wb = bytearray(chunk_size * 2); c_hi = (color >> 8) & 0xFF; c_lo = color & 0xFF
        for i in range(0, chunk_size * 2, 2): wb[i] = c_hi; wb[i+1] = c_lo
        while count > 0: n = min(count, chunk_size); self.write_data(wb[:n*2]); count -= n

    def text(self, s, x, y, color, bg_color=0):
        width = len(s) * 8; height = 8; buf = bytearray(width * height * 2)
        fbuf = framebuf.FrameBuffer(buf, width, height, framebuf.RGB565)
        fbuf.fill(bg_color); fbuf.text(s, 0, 0, color)
        if x + width > self.width: width = self.width - x
        if y + height > self.height: height = self.height - y
        if width > 0 and height > 0:
            self._set_window(x, y, x + width - 1, y + height - 1); self.write_data(buf)

    def _set_window(self, x0, y0, x1, y1):
        self.write_cmd(0x2A); self.write_data(bytearray([0, x0, 0, x1]))
        self.write_cmd(0x2B); self.write_data(bytearray([0, y0, 0, y1]))
        self.write_cmd(0x2C)

    def invert_color(self, invert): self.write_cmd(0x21 if invert else 0x20)

    def brightness(self, value):
        if hasattr(self, 'pwm'):
            duty = int(value) * 64
            if duty > 65535: duty = 65535
            self.pwm.duty_u16(duty)
