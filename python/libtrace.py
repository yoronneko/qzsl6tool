#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# libtrace.py: library for trace function
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2022-2026 Satoshi Takahashi
#
# Released under BSD 2-clause license.

import sys
from typing import TextIO

def fg_color(color: str ='default') -> str:  # foreground color
    '''
    color:
        black, red, green, yellow, blue, magenta, cyan, white, default
    '''
    if   color == "black"  : return "\x1b[30m"
    elif color == "red"    : return "\x1b[31m"
    elif color == "green"  : return "\x1b[32m"
    elif color == "yellow" : return "\x1b[33m"
    elif color == "blue"   : return "\x1b[34m"
    elif color == "magenta": return "\x1b[35m"
    elif color == "cyan"   : return "\x1b[36m"
    elif color == "white"  : return "\x1b[37m"
    elif color == "default": return "\x1b[39m"
    else:
        print(f"undefined foreground color: {color}", file=sys.stderr)
        sys.exit(1)

def bg_color(color: str ='default') -> str:  # background color
    '''
    color:
        black, red, green, yellow, blue, magenta, cyan, gray, default
    '''
    if   color == "black"  : return "\x1b[40m"
    elif color == "red"    : return "\x1b[41m"
    elif color == "green"  : return "\x1b[42m"
    elif color == "yellow" : return "\x1b[43m"
    elif color == "blue"   : return "\x1b[44m"
    elif color == "magenta": return "\x1b[45m"
    elif color == "cyan"   : return "\x1b[46m"
    elif color == "gray"   : return "\x1b[47m"
    elif color == "default": return "\x1b[49m"
    else:
        print(f"undefined background color: {color}", file=sys.stderr)
        sys.exit(1)

def text_dec(style: str ='default') -> str:  # text decoration
    '''
    style:
        default, bold, dark, italic, underline, bling, hblink, reverse, hide, strike
    '''
    if   style == "default"  : return "\x1b[0m"
    elif style == "bold"     : return "\x1b[1m"
    elif style == "dark"     : return "\x1b[2m"
    elif style == "italic"   : return "\x1b[3m"
    elif style == "underline": return "\x1b[4m"
    elif style == "blink"    : return "\x1b[5m"
    elif style == "hblink"   : return "\x1b[6m"
    elif style == "reverse"  : return "\x1b[7m"
    elif style == "hide"     : return "\x1b[8m"
    elif style == "strike"   : return "\x1b[9m"
    else:
        print(f"undefined decoration style: {style}", file=sys.stderr)
        sys.exit(1)
    return result

def err(*args: object) -> None:
    print(fg_color('red'), end='', file=sys.stderr)
    for arg in args:
        print(arg, end='', file=sys.stderr)
    print(fg_color(), file=sys.stderr)

def warn(*args: object) -> None:
    print(fg_color('yellow'), end='', file=sys.stderr)
    for arg in args:
        print(arg, end='', file=sys.stderr)
    print(fg_color(), file=sys.stderr)

def info(*args: object) -> None:
    print(fg_color('green'), end='', file=sys.stderr)
    for arg in args:
        print(arg, end='', file=sys.stderr)
    print(fg_color(), file=sys.stderr)

class Trace:
    def __init__(self, fp: TextIO | None = sys.stdout, t_level: int = 0, is_forced: bool = False) -> None:
        self.fp     : TextIO | None = fp
        self.t_level: int           = t_level
        self.colored: bool          = False
        if fp and (is_forced or fp.isatty()):
            self.colored = True

    def msg(self, level: int, arg: str, fg: str ='', bg: str ='', dec: str ='') -> str:
        '''
        returns colorize argument when level is lower than t_level
        arg: string to be output to self.fp
        fg:  foreground color
        bg:  background color
        dec: decoration color
        end: termination character
        '''
        if self.t_level < level or not self.fp or not arg:
            return ''
        message = ''
        if self.colored:
            if fg : message += fg_color( fg)
            if bg : message += bg_color( bg)
            if dec: message += text_dec(dec)
        if arg:
            message += arg
        if self.colored:
            if dec: message += text_dec()
            if bg : message += bg_color()
            if fg : message += fg_color()
        return message

    def show(self, level: int, arg: str, fg: str ='', bg: str ='', dec: str ='', end: str ='\n') -> None:
        '''
        prints colorize argument when level is lower than t_level
        arg: string to be output to self.fp
        fg:  foreground color
        bg:  background color
        dec: decoration color
        end: termination character
        '''
        if self.t_level < level or not self.fp:
            return
        print(self.msg(level, arg, fg, bg, dec), end=end, file=self.fp)
        self.fp.flush()

if __name__ == '__main__':
    trace = Trace()
    # trace = Trace(is_forced=True)  # forced colorization
    trace.show(0, 'red', fg='red')
    trace.show(0, 'green', fg='green')
    trace.show(0, 'yellow', fg='yellow')
    trace.show(0, 'bold', dec='bold')
    trace.show(0, 'background red', bg='red')
    trace.show(0, 'background green', bg='green')
    trace.show(0, 'background yellown', bg='yellow')
    msg = trace.msg(0, 'red', fg='red') + '\n'
    msg += trace.msg(0, 'green', fg='green') + '\n'
    msg += trace.msg(0, 'yellow', fg='yellow') + '\n'
    msg += trace.msg(0, 'bold', dec='bold')+ '\n'
    msg += trace.msg(0, 'background red', bg='red') + '\n'
    msg += trace.msg(0, 'background green', bg='green') + '\n'
    msg += trace.msg(0, 'background yellown', bg='yellow')
    trace.show(0, msg)

# EOF

