# Adafruit NeoPixel library port to the rpi_ws281x library.
# Author: Tony DiCola (tony@tonydicola.com), Jeremy Garff (jer@jers.net)
import atexit

import _rpi_ws281x as ws


def Color(red, green, blue, white=0):
    """Convert the provided red, green, blue color to a 24-bit color value.
    Each color component should be a value 0-255 where 0 is the lowest intensity
    and 255 is the highest intensity.
    """
    return (white << 24) | (red << 16) | (green << 8) | blue


class _LED_Data(object):
    """Wrapper class which makes a SWIG LED color data array look and feel like
    a Python list of integers.
    """

    def __init__(self, ws2811, channum, channel, size):
        self.size = size
        self.channum = channum
        self.channel = channel
        self.ws2811 = ws2811

    def __getitem__(self, pos):
        """Return the 24-bit RGB color value at the provided position or slice
        of positions.
        """
        # Handle if a slice of positions are passed in by grabbing all the values
        # and returning them in a list.
        if isinstance(pos, slice):
            return [
                ws.ws2811_led_get(self.channel, n)
                for n in range(*pos.indices(self.size))
            ]
        # Else assume the passed in value is a number to the position.
        else:
            return ws.ws2811_led_get(self.channel, pos)

    def __setitem__(self, pos, value):
        """Set the 24-bit RGB color value at the provided position or slice of
        positions.
        """
        # Handle if a slice of positions are passed in by setting the appropriate
        # LED data values to the provided values.
        if isinstance(pos, slice):
            pixels = pos.indices(self.size)
            ws.ws2811_led_set_multi_colors(pixels, value, 0, self.channum)
        # Else assume the passed in value is a number to the position.
        else:
            return ws.ws2811_led_set(pos, value, 0, self.channum)


class Adafruit_NeoPixel(object):
    def __init__(
        self,
        num,
        pin,
        freq_hz=800000,
        dma=10,
        invert=(False, False),
        brightness=(255, 255),
        available_watts=(5.0, 5.0),
        strip_type=(ws.WS2811_STRIP_RGB, ws.WS2811_STRIP_RGB),
    ):
        """Class to represent a NeoPixel/WS281x LED display.  Num should be the
        number of pixels in the display, and pin should be the GPIO pin connected
        to the display signal line (must be a PWM pin like 18!).  Optional
        parameters are freq, the frequency of the display signal in hertz (default
        800khz), dma, the DMA channel to use (default 10), invert, a boolean
        specifying if the signal line should be inverted (default False), and
        channel, the PWM channel to use (defaults to 0).
        """
        # Create ws2811_t structure and fill in parameters.
        self._leds = ws.new_ws2811_t()

        # Initialize the channels to zero
        for channum in range(2):
            chan = ws.ws2811_channel_get(self._leds, channum)
            ws.ws2811_channel_t_count_set(chan, num[channum])
            ws.ws2811_channel_t_gpionum_set(chan, pin[channum])
            ws.ws2811_channel_t_invert_set(chan, 0 if not invert[channum] else 1)
            ws.ws2811_channel_t_brightness_set(chan, brightness[channum])
            ws.ws2811_channel_t_strip_type_set(chan, strip_type[channum])
            ws.ws2811_channel_t_available_watts_set(chan, available_watts[channum])

        self._channel = [
            ws.ws2811_channel_get(self._leds, 0),
            ws.ws2811_channel_get(self._leds, 1),
        ]

        # Initialize the controller
        ws.ws2811_t_freq_set(self._leds, freq_hz)
        ws.ws2811_t_dmanum_set(self._leds, dma)

        # Grab the led data array.
        self._led_data = [
            _LED_Data(self._leds, 0, self._channel[0], num[0]),
            _LED_Data(self._leds, 1, self._channel[1], num[1]),
        ]

        # Substitute for __del__, traps an exit condition and cleans up properly
        atexit.register(self._cleanup)

    def _cleanup(self):
        # Clean up memory used by the library when not needed anymore.
        if self._leds is not None:
            ws.delete_ws2811_t(self._leds)
            self._leds = None
            self._channel = None

    def begin(self):
        """Initialize library, must be called once before other functions are
        called.
        """
        resp = ws.ws2811_init(self._leds)
        if resp != ws.WS2811_SUCCESS:
            message = ws.ws2811_get_return_t_str(resp)
            raise RuntimeError(
                "ws2811_init failed with code {0} ({1})".format(resp, message)
            )
        ws.ws2811_set(self._leds)

    def set_available_watts(self, watts, channel=0):
        chan = ws.ws2811_channel_get(self._leds, channel)
        ws.ws2811_channel_t_available_watts_set(chan, watts)
        self.show()

    def show(self):
        """Update the display with the data from the LED buffer."""
        resp = ws.ws2811_render(self._leds)
        if resp == ws.WS2811_SUCCESS:
            return

        message = ws.ws2811_get_return_t_str(resp)
        raise RuntimeError(
            "ws2811_render failed with code {0} ({1})".format(resp, message)
        )

    def setPixelColor(self, n, color, channel=0):
        """Set LED at position n to the provided 24-bit color value (in RGB order).
        """
        self._led_data[channel][n] = color

    def setPixelColorRGB(self, n, red, green, blue, white=0, channel=0):
        """Set LED at position n to the provided red, green, and blue color.
        Each color component should be a value from 0 to 255 (where 0 is the
        lowest intensity and 255 is the highest intensity).
        """
        self.setPixelColor(n, Color(red, green, blue, white), channel)

    def setBrightness(self, brightness, channel=0):
        """Scale each LED in the buffer by the provided brightness.  A brightness
        of 0 is the darkest and 255 is the brightest.
        """
        ws.ws2811_channel_t_brightness_set(self._channel[channel], brightness)

    def getBrightness(self, channel=0):
        """Get the brightness value for each LED in the buffer. A brightness
        of 0 is the darkest and 255 is the brightest.
        """
        return ws.ws2811_channel_t_brightness_get(self._channel[channel])

    def getPixels(self, channel=0):
        """Return an object which allows access to the LED display data as if
        it were a sequence of 24-bit RGB values.
        """
        return self._led_data[channel]

    def numPixels(self, channel=0):
        """Return the number of pixels in the display."""
        return ws.ws2811_channel_t_count_get(self._channel[channel])

    def getPixelColor(self, n, channel=0):
        """Get the 24-bit RGB color value for the LED at position n."""
        return self._led_data[channel][n]
