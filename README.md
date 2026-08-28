# ST7735 MicroPython Driver

Driver for ST7735-based color SPI TFT displays (commonly sold as 1.8" 128x160 modules). Handles the chip init sequence and gives you drawing primitives — pixels, lines, rectangles, and text — plus screen rotation, color inversion, and PWM backlight brightness control if you've wired the backlight pin.

## Install

Copy `st7735.py` onto your board's filesystem (e.g. via [Open Maker Studio](https://openmakerstudio.com)'s Library Manager, Thonny, or `mpremote cp`).

## Usage

```python
from machine import Pin, SPI
from st7735 import ST7735

spi = SPI(1, baudrate=20_000_000, sck=Pin(18), mosi=Pin(23))
tft = ST7735(spi, cs=Pin(5), dc=Pin(2), rst=Pin(4), blk=Pin(15))

tft.fill(0x0000)                       # black
tft.text("Hello!", 10, 10, 0xFFFF)     # white text
```

## License

MIT — see [LICENSE](LICENSE).
