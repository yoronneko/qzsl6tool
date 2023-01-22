#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# libcolor.py: library for color decoration
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2022 Satoshi Takahashi
#
# Released under BSD 2-clause license.

import sys


class Color:
    '''
    foreground color (fg):
      black, red, green, yellow, blue, magenta, cyan, white, default
    background color (bg):
      black, red, green, yellow, blue, magenta, cyan, gray, default
    decoration style (dec):
      default, bold, dark, italic, underline, bling, hblink,
      reverse, hide, strike
    '''
    fp = None
    def __init__(self, fp=sys.stdout, is_forced=False):
        if is_forced:
            self.fp = fp
        else:
            self.fp = None if not fp or not fp.isatty() else fp

    def fg(self, color='default'):  # foreground color
        "color: black, red, green, yellow, blue, magenta, cyan, white, default"
        if not self.fp:
            return ''
        result = ''
        if color == "black":     # foreground: black
            result += "\x1b[30m"
        elif color == "red":     # foreground: red
            result += "\x1b[31m"
        elif color == "green":   # foreground: green
            result += "\x1b[32m"
        elif color == "yellow":  # foreground: yellow
            result += "\x1b[33m"
        elif color == "blue":    # foreground: blue
            result += "\x1b[34m"
        elif color == "magenta": # foreground: magenta
            result += "\x1b[35m"
        elif color == "cyan":    # foreground: cyan
            result += "\x1b[36m"
        elif color == "white":   # foreground: white
            result += "\x1b[37m"
        elif color == "default": # foreground: default
            result += "\x1b[39m"
        else:
            print(f"undefined foreground color: {color}", file=sys.stderr)
            sys.exit(1)
        return result

    def bg(self, color='default'):  # background color
        "color: black, red, green, yellow, blue, magenta, cyan, gray, default"
        if not self.fp:
            return ''
        result = ''
        if color == "black":     # background: black
            result += "\x1b[40m"
        elif color == "red":     # background: red
            result += "\x1b[41m"
        elif color == "green":   # background: green
            result += "\x1b[42m"
        elif color == "yellow":  # background: yellow
            result += "\x1b[43m"
        elif color == "blue":    # background: blue
            result += "\x1b[44m"
        elif color == "magenta": # background: magenta
            result += "\x1b[45m"
        elif color == "cyan":    # background: cyan
            result += "\x1b[46m"
        elif color == "gray":    # background: gray
            result += "\x1b[47m"
        elif color == "default": # background: default
            result += "\x1b[49m"
        else:
            print(f"undefined background color: {color}", file=sys.stderr)
            sys.exit(1)
        return result

    def dec(self, style='default'):  # text decoration
        "style: default, bold, dark, italic, underline, bling, hblink, "
        "       reverse, hide, strike"
        if not self.fp:
            return ''
        result = ''
        if style == '':
            pass
        elif style == "default":
            result += "\x1b[0m"
        elif style == "bold":
            result += "\x1b[1m"
        elif style == "dark":
            result += "\x1b[2m"
        elif style == "italic":
            result += "\x1b[3m"
        elif style == "underline":
            result += "\x1b[4m"
        elif style == "blink":
            result += "\x1b[5m"
        elif style == "hblink":
            result += "\x1b[6m"
        elif style == "reverse":
            result += "\x1b[7m"
        elif style == "hide":
            result += "\x1b[8m"
        elif style == "strike":
            result += "\x1b[9m"
        else:
            print(f"undefined decoration style: {style}", file=sys.stderr)
            sys.exit(1)
        return result

    def color(self, fg_color='default', bg_color='default', style='default'):
        if not self.fp:
            return ''
        return self.fg(fg_color) + self.bg(bg_color) + self.dec(style)

    def default(self):
        return self.fg() + self.bg() + self.dec()


if __name__ == '__main__':
    msg_color = Color()
    # msg_color = Color(is_forced=True)  # forced colorization
    msg = ''
    msg = msg_color.fg('red') + 'red\n'
    msg += msg_color.fg('green') + 'green\n'
    msg += msg_color.fg('yellow') + 'yellow\n' + msg_color.default()
    msg += msg_color.dec('bold') + 'bold\n' + msg_color.default()
    msg += msg_color.bg('red') + 'background red'
    msg += msg_color.default() + '\n'
    msg += msg_color.bg('green') + 'background green'
    msg += msg_color.default() + '\n'
    msg += msg_color.bg('yellow') + 'background yellow'
    msg += msg_color.default() + '\n'
    print(msg)

# EOF
