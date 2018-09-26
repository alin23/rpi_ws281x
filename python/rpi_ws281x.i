// SWIG interface file to define rpi_ws281x library python wrapper.
// Author: Tony DiCola (tony@tonydicola.com), Jeremy Garff (jer@jers.net)

// Define module name rpi_ws281x.  This will actually be imported under
// the name _rpi_ws281x following the SWIG & Python conventions.
%module rpi_ws281x

// Include standard SWIG types & array support for support of uint32_t
// parameters and arrays.
%include "stdint.i"
%include "carrays.i"
%array_class(int, intArray);

// Declare functions which will be exported as anything in the ws2811.h header.
%{
#define SWIG_FILE_WITH_INIT
#include "../ws2811.h"
%}

%include "numpy.i"

%init %{
import_array();
%}

%apply (int* IN_ARRAY1, int DIM1) {(int* leds, int ledcount), (int* colors, int colorcount)};
%apply (int* IN_ARRAY1, int DIM1) {(int* leds, int ledcount)};

// Process ws2811.h header and export all included functions.
%include "../ws2811.h"

%inline %{
    ws2811_t* ledstrip;
    int ledchannel;

    uint32_t ws2811_led_get(ws2811_channel_t *channel, int lednum)
    {
        if (lednum >= channel->count)
        {
            return -1;
        }

        return channel->leds[lednum];
    }

    int ws2811_set(ws2811_t *ws2811, int channum) {
        ledstrip = ws2811;
        ledchannel = channum;
        return 0;
    }

    int ws2811_led_set(int lednum, uint32_t color, int render)
    {
        ws2811_channel_t *channel = &ledstrip->channel[ledchannel];
        if (lednum >= channel->count)
        {
            return -1;
        }

        channel->leds[lednum] = color;

        if (render == 1)
        {
            ws2811_render(ledstrip);
        }

        return 0;
    }

    int ws2811_led_set_all(uint32_t color, int render)
    {
        ws2811_channel_t *channel = &ledstrip->channel[ledchannel];
        for (int i = 0; i < channel->count; ++i)
        {
            channel->leds[i] = color;
        }

        if (render == 1)
        {
            ws2811_render(ledstrip);
        }
        return 0;
    }

    int ws2811_led_set_brightness(uint8_t brightness, int render)
    {
        ws2811_channel_t *channel = &ledstrip->channel[ledchannel];
        channel->brightness = brightness;
        if (render == 1)
        {
            ws2811_render(ledstrip);
        }
        return 0;
    }

    int ws2811_led_set_multi_colors(int* leds, int ledcount, int* colors, int colorcount, int render)
    {
        ws2811_channel_t *channel = &ledstrip->channel[ledchannel];
        uint32_t* colors32 = (uint32_t*)colors;
        int lednum = 0;
        for (int i = 0; i < ledcount; ++i)
        {
            lednum = leds[i];
            if (lednum < channel->count) {
                channel->leds[lednum] = colors32[i];
            }
        }

        if (render == 1)
        {
            ws2811_render(ledstrip);
        }

        return 0;
    }

    int ws2811_led_set_multi_color(int* leds, int ledcount, uint32_t color, int render)
    {
        ws2811_channel_t *channel = &ledstrip->channel[ledchannel];
        int lednum = 0;
        for (int i = 0; i < ledcount; ++i)
        {
            lednum = leds[i];
            if (lednum < channel->count) {
                channel->leds[lednum] = color;
            }
        }

        if (render == 1)
        {
            ws2811_render(ledstrip);
        }

        return 0;
    }

    ws2811_channel_t *ws2811_channel_get(ws2811_t *ws, int channelnum)
    {
        return &ws->channel[channelnum];
    }
%}
