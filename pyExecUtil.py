#!/usr/bin/env python
# -*- Coding: utf-8 -*-
#
# Copyright (C) 2017 hidenorly
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import signal
import sys
import codecs
import subprocess, threading

cset = 'utf-8'

# for Python 3.x
try:
	reload
except NameError:
	try:
		from importlib import reload
	except ImportError:
		from imp import reload

reload(sys)
try:
	sys.setdefaultencoding(cset)
except AttributeError:
	pass

sys.stdin = codecs.getreader(cset)(sys.stdin)
sys.stdout = codecs.getwriter(cset)(sys.stdout)

class PyExecUtil(object):
	def __init__(self, cmd):
		self.cmd = cmd
		self._process = None
		self._thread = None
		self._callback = None
		self._args = None
		self.stdout_data = None
		self.stderr_data = None

	def onCompletion(self):
		if self._callback:
			self._callback(self._args, self.stdout_data, self.stderr_data)

	def __onExecute(self):
		self._process = subprocess.Popen(self.cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)
		self.stdout_data, self.stderr_data = self._process.communicate()
		self.onCompletion()

	def kill_children_process(self, pid):
		os.killpg(os.getpgid(pid), signal.SIGTERM)

	def terminate(self, killChildrenProcess=True):
		if self._thread.is_alive():
			if self._process!=None:
				if killChildrenProcess:
					self.kill_children_process(self._process.pid)
				self._process.terminate()
			self._thread.join()

	def execute(self, timeout=None, killChildrenProcess=True, onCompletion=None, args=None):
		self._callback = onCompletion
		self._args = args
		self._thread = threading.Thread(target=self.__onExecute)
		self._thread.start()

		self._thread.join(timeout)
		self.terminate(killChildrenProcess)

		return_code = None
		if self._process:
			return_code = self._process.returncode

		return return_code