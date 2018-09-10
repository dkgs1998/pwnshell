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

term_attr = termios.tcgetattr(0)

def exit_handler():
	global term_attr
	global termios

	termios.tcsetattr(0, termios.TCSANOW, term_attr)

def child_die(sig_num, frame):
	exit(0)

atexit.register(exit_handler)
signal.signal(signal.SIGCHLD, child_die)

ret = pty.fork()
if ret[0] == 0:
	os.execv("/bin/bash", ["bash"])
else:
	tty.setraw(0)
	pty=ret[1]
	while True:
		pending_fds = select.select([0, pty],[], [])
		if pending_fds[0][0] == 0:
			received_str = os.read(0, 0x1000000)

			little_endian_macros = re.findall("{{L?0x[A-Z|a-z|0-9]*}}", received_str)
			for macro in little_endian_macros:
				if macro[2] == "L":
					print 
					received_str = received_str.replace(macro, macro.strip("{}")[3:].decode("hex")[::-1])
				else:
					received_str = received_str.replace(macro, macro.strip("{}")[2:].decode("hex"))

			if len(little_endian_macros) != 0:
				temp_attr = termios.tcgetattr(pty)
				tty.setraw(pty, termios.TCSANOW)
				os.write(pty, received_str)
				time.sleep(0.1)
				termios.tcsetattr(pty, termios.TCSANOW, temp_attr)
			else:
				os.write(pty, received_str)
		else:
			os.write(1, os.read(pty, 0x1000000))