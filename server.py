"""""""""""""""""""""""""""""""""""""""""""""""""""
"""""""""""""""""""""""""""""""""""""""""""""""""""
#server.py 
#Author: Daniel Swoboda
#License: MIT
#Copyright: Daniel Swoboda, MissionEDU Project
#Last edited: 02/02/2017
#Description: MissionEDU server program
"""""""""""""""""""""""""""""""""""""""""""""""""""
"""""""""""""""""""""""""""""""""""""""""""""""""""

"""""""""""""""""""""""""""""""""""""""""""""""""""
Imports
"""""""""""""""""""""""""""""""""""""""""""""""""""
from ars import ARS
from swockets import swockets, SwocketError, SwocketClientSocket, SwocketHandler
import time
import sys
import json
import subprocess
import ars_gen
import os
import glob
import socket

"""""""""""""""""""""""""""""""""""""""""""""""""""
Class helper methods
"""""""""""""""""""""""""""""""""""""""""""""""""""

"""
Packs a message into the MiRACLE format
"""
def pack_message(m_type, m_payload):
	message = {}
	message["MessageType"] = m_type
	message["Payload"] = m_payload
	return message


def fprint(content):
	print '\r'+content+'\n>',
	sys.stdout.flush()
def dprint(content):
	print '\r',
	sys.stdout.flush()
	print content
	print '>',

"""
server for MissionEDU
"""
class server(SwocketHandler):
	"""""""""""""""""""""""""""""""""""""""""""""""""""
	Class variables
	"""""""""""""""""""""""""""""""""""""""""""""""""""
	execution_mode = False
	running = True
	confMode = False
	cdef = json.loads(open('ars/cdef/'+'example.cdef', 'r').read())

	def __init__(self):
		SwocketHandler.__init__(self)
		self.connected = True

	def disconnect(self, sock):
		self.connected = False
		fprint("Server disconnected")
		if self.confMode:
			self.confMode = False
			#restart the ars process here

	"""
	sends list of commands and list of tasks
	"""
	def connect(self, sock):
		cml = pack_message("CML", self.generate_command_list())
		tsl = pack_message("TSL", self.generate_task_list())

		self.sock.send(cml, sock, sock)
		self.sock.send(tsl, sock, sock)

	"""
	called if handshake is unsuccessful
	"""
	def handshake_unsuccessful(self):
		self.connected = False
		fprint("Handshake unsuccessful")

	"""
	called whenever a message is received
	"""
	def recv(self, message, sock):
		dprint(message)
		if message["MessageType"] == "DSC":
			disconnect(sock)
		elif not self.confMode:
			if self.execution_mode:
				if message["MessageType"] == "SEC":
					result = self.exec_cmd(message["Payload"]["CommandName"], message["Payload"]["CommandParams"][0]["CommandParam"])
					if result == "failed" or not result:
						self.sock.send(self.generate_err_message('ECE', 'Command could not be executed'), sock, sock)
					else:
						self.sock.send(pack_message("ECR", result), sock, sock)
				elif message["MessageType"] == "EEM":
					self.execution_mode = False
				else:
					self.sock.send(self.generate_err_message('CER', 'Cannot use standard commands in execution mode'), sock, sock)

			elif message["MessageType"] == "SEM":
				self.execution_mode = True
			else:
				self.sock.send(self.generate_err_message('CER', 'Invalid command'), sock, sock)
		else:
			if message["MessageType"] == "CTS":
				self.change_task(message["Payload"])
				#send to all clients new task list
			elif message["MessageType"] == "ATS":
				self.add_task(message["Payload"])
				#send to all clients new task list
			elif message["MessageType"] == "DTS":
				self.delete_task(message["Payload"])
				#send to all clients new task list
			elif message["MessageType"] == "RAL":
				self.sock.send(pack_message("SAL", cdef))
			elif message["MessageType"] == "UAL":
				self.update_ars(message["Payload"])
			else:
				print "fake news"
				self.sock.send(self.generate_err_message('CER', 'Invalid command'), sock, sock)



	"""
	Performs the MiRACLE handshake
	"""
	def handshake(self, sock):
		ack = pack_message("ACK", {})
		ref = pack_message("REF", {})

		req = self.sock.receive_one_message(sock, sock)

		if not self.confMode:
			self.sock.send(ack, sock, sock)
		else:
			self.sock.send(ref, sock, sock)
			return False

		ack_cl = self.sock.receive_one_message(sock, sock)
		if ack_cl["MessageType"] == "ACK":
			fprint("Client connected")
			if req["Payload"]["ClientType"] == "config":
				#TODO disconnect all other
				#TODO kill the subprocess, stop the ars
				self.confMode = True
				fprint("Config Mode activated")
			return True
		else:
			return False

	"""
	Executes a command on the ARS
	"""
	def exec_cmd(self, cmd, param = None):
		for method in self.cdef["methods"]:
			if method["name"] == cmd:
				self.ars.send(cmd)
				self.ars.send(method["param_type"])
				
				if method["param_type"] != "void":
					self.ars.send(param)

				result = self.ars.receive()
				return result


	"""
	Executes a command on the ARS from terminal
	"""
	def exec_cmd_term(self, cmd):
		for method in self.cdef["methods"]:
			if method["name"] == cmd:
				self.ars.send(cmd)
				self.ars.send(method["param_type"])
				
				if method["param_type"] != "void":
					self.ars.send(raw_input(">par:"))

				return self.ars.receive()

	"""
	Parse the console input
	"""
	def parse_command(self, command):
		if command == "shutdown":
			self.running = False
			self.ars.send(command)
		else:
			result = self.exec_cmd_term(command)
			if result == "failed" or not result:
				fprint("command failed, please repeat")
			else:
				fprint(result)

	"""
	Generate the command list from the cdef file
	"""
	def generate_command_list(self):
		command_list = []
		for method in self.cdef["methods"]:
			command = {"CommandName":method["name"], "CommandReturn":method["return_type"], "CommandParams":[]}
			command["CommandParams"].append({"CommandParamDataType":method["param_type"]})
			if method["param_type"] != "void":
				command["CommandParamName"] = method["param_name"]
				if "min" in method:
					command["CommmandParamRanges"] = {"min":method["min"],"max":method["max"]} 
			command_list.append(command)
		return command_list

	"""
	Generate the task list from all the tdef files
	"""
	def generate_task_list(self):
		task_list = []
		for task_file in glob.glob('tasks/*.tdef'):
			task = json.loads(open(task_file, 'r').read())
			task_list.append(task)
		return task_list

	"""
	Generate Error Message
	"""
	def generate_err_message(self, etype, desc):
		return pack_message(etype, desc)


	def change_task(self, task):
		fprint("change task")
	def add_task(self, task):
		fprint("adding task")
	def delete_task(self, task):
		fprint("deleting task")
	def update_ars(self, ars):
		fprint("Updating ars")

	"""""""""""""""""""""""""""""""""""""""""""""""""""
	Main program
	"""""""""""""""""""""""""""""""""""""""""""""""""""
	def main(self):
		self.ars = ARS()
		try:
			self.ars_p = subprocess.Popen("./ars.o")
		except:
			print "Compiling"
			ars_gen.build_ars("example.cdef")
			self.ars_p = subprocess.Popen(self.cdef["run"]["path"])
		self.ars.connect()

		server = swockets(swockets.ISSERVER, self)
		self.sock = server

		print ">",
		while self.running:
			command = raw_input("")
			try:
				self.parse_command(command)
			except socket.error:
				fprint("Retrying")
				self.parse_command(command)
			#except
			#	fprint("error while executing command")


server = server()
server.main()