#!/usr/bin/python
import signal
import pty
import os
import select
import tty
import re
import atexit
import termios
import subprocess
import time
import readline

PLUS = "[\x1b[32m+\x1b[0m]"
MINUS = "[\x1b[31m-\x1b[0m]"
ASTERIX = "[\x1b[33m*\x1b[0m]"

term_attr = termios.tcgetattr(0)
def exit_handler():
	global term_attr
	global termios
	os.write(1, "\r{0} pwnshell out\n\r\n".format(MINUS))
	termios.tcsetattr(0, termios.TCSANOW, term_attr)

def child_die(sig_num, frame):
	exit(0)


NORMAL_OUTPUT_MODE = 0
HEX_OUTPUT_MODE_MIXED = 1
HEX_OUTPUT_MODE_FULL = 2
raw_output_mode = NORMAL_OUTPUT_MODE
def raw_output_mode_toggle():
	global raw_output_mode
	raw_output_mode += 1
	raw_output_mode %= 3
	if raw_output_mode == NORMAL_OUTPUT_MODE:
		os.write(1, "\r\n{0} normal output mode\r\n".format(MINUS))
	elif raw_output_mode == HEX_OUTPUT_MODE_MIXED:
		os.write(1, "\r\n{0} raw (mixed) output mode\r\n".format(PLUS))
	elif raw_output_mode == HEX_OUTPUT_MODE_FULL:
		os.write(1, "\r\n{0} raw (full) output mode\r\n".format(PLUS))

atexit.register(exit_handler)
signal.signal(signal.SIGCHLD, child_die)

os.write(1, "\n\r{0} welcome to pwnshell! ctrl+s to enter raw input mode, ctrl+c in raw input mode to cancel raw input mode and discard changes.".format(PLUS))
os.write(1, "\r\n{0} ctrl+q to toggle raw output mode between normal, mixed hex and ascii mode or full hex mode.\r\n".format(PLUS))
ret = pty.fork()
if ret[0] == 0:
	os.execv("/bin/bash", ["bash"])
else:
	tty.setraw(0)
	pty=ret[1]
	while True:
		pending_fds = select.select([0, pty],[], [])
		if pending_fds[0][0] == 0:
			input_str = os.read(0, 0x1000000)
			if "\x13" in input_str: # ctrl+S
				termios.tcsetattr(0, termios.TCSANOW, term_attr)
				try:
					in_buf = raw_input("\n\r{0} raw input mode:\n\r".format(PLUS))
				except KeyboardInterrupt:
					os.write(1, "\r{0} normal input mode, changes discarded\n\r".format(ASTERIX))
					tty.setraw(0)
					continue
				os.write(1, "\r{0} normal input mode\n\r".format(MINUS))
				tty.setraw(0)
				time.sleep(0.1)
				temp_attr = termios.tcgetattr(pty)
				tty.setraw(pty, termios.TCSANOW)
				os.write(pty, in_buf.decode("string_escape"))
				time.sleep(0.1)
				termios.tcsetattr(pty, termios.TCSANOW, temp_attr)
			elif "\x11" in input_str:
				raw_output_mode_toggle()
			else:
				os.write(pty, input_str)
		else:
			output_str = os.read(pty, 0x1000000)
			if raw_output_mode == HEX_OUTPUT_MODE_MIXED:
				output_str = output_str.encode("string_escape")
			elif raw_output_mode == HEX_OUTPUT_MODE_FULL:
				output_str = "\\x".join("{:02x}".format(ord(c)) for c in output_str)
				output_str = "\\x" + output_str
			os.write(1,output_str)
			
