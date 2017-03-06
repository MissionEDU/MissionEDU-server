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

logo = "\
                    ````````````````      ```````````````` \n\
                    `````````````````    ````````````````` \n\
                    ``````````````````  `````````````````` \n\
                    `````````````````````````````````````` \n\
                    `````````````````````````````````````` \n\
                    ````        ``````````````        ```` \n\
                    ````        ``````````````        ```` \n\
                    ````        ``````````````        ```` \n\
                    ````        ``````````````        ```` \n\
                    ````        ``````````````        ```` \n\
                    ````        ``````````````        ```` \n\
                    ````        ``````````````        ```` \n\
                    ````        ``````````````        ```` \n\
                    `````````````````````````````````````` \n\
                    `````````````````````````````````````` \n\
                                                           \n\
                    +oooooooooooooooooooooooooooooooooooo/ \n\
                   ``````````--------------------``````````\n\
                   ````````` ````````    ```````` `````````\n\
                   ````````` ``````        `````` `````````\n\
                   ````````` `````          ````` `````````\n\
                   ````````` ````            ```` `````````\n\
                   ````````` ```              ``` `````````\n\
                   ````````` `                  ` `````````\n\
                   `````````                      `````````\n\
                   `````````                      `````````\n\
\n\
\n\
oy:     /y+  /-                o.                   `y++++:  so++++/`  .y`    -s\n\
y+h-   :yos  /- `////- `////:  +.  -////-  .+://+:  .d.      h:   `:h. .d`    :h\n\
y:-h. -y`os  y+ :y:.`` -y:-``  d: :h.  .h: -m-  `d- .m+///.  h:     h+ .d`    :h\n\
y: :y-y. os  y+  `.:+o  `.:+s` d: +y    y+ -d    h: .d`      h:    :d- `d.    +y\n\
s:  /h-  +o  s/ -+//++ -+//++  y- `+o//o+` -h    y: .h++++:  yo++++/.   -o+++o+\n\
"


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
import hashlib
import copy

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
		fprint("Client disconnected")
		if self.confMode:
			self.confMode = False
			self.start_ars()
			self.ars = ARS()
			self.ars.connect()

	def build_ars(self):
		ars_gen.build_ars("example.cdef")
		
	def start_ars(self):
		try:
			self.ars_p = subprocess.Popen("./ars.o")
		except:
			print "Compiling"
			self.build_ars()
			self.ars_p = subprocess.Popen(self.cdef["run"]["path"])
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
		#dprint(message)
		if message["MessageType"] == "DSC":
			disconnect(sock)
		elif not self.confMode:
			if self.execution_mode:
				if message["MessageType"] == "SEC":
					result = self.exec_cmd(message["Payload"]["CommandName"], message["Payload"]["CommandParams"][0]["CommandParam"])
					if result == "failed" or not result:
						self.sock.send(self.generate_err_message('ECE', 'Command could not be executed'), sock, sock.sock)
					else:
						self.sock.send(pack_message("ECR", result), sock, sock.sock)
				elif message["MessageType"] == "EEM":
					self.execution_mode = False
				else:
					self.sock.send(self.generate_err_message('CER', 'Cannot use standard commands in execution mode'), sock, sock.sock)

			elif message["MessageType"] == "SEM":
				self.execution_mode = True
			else:
				self.sock.send(self.generate_err_message('CER', 'Invalid command'), sock, sock.sock)
		else:
			if message["MessageType"] == "CTS":
				if int(message["Payload"]["TaskUID"]) < 0:
					tse = pack_message("TSE", {"ErrorDescription" : "Pre defined tasks cannot be altered!"})
					self.sock.send(tse, sock, sock.sock)
				else:
					self.change_task(message["Payload"])
					tsl = pack_message("TSL", self.generate_task_list())
					self.sock.send(tsl, sock, sock.sock)
			elif message["MessageType"] == "ATS":
				self.add_task(message["Payload"])
				tsl = pack_message("TSL", self.generate_task_list())
				self.sock.send(tsl, sock, sock.sock)
			elif message["MessageType"] == "DTS":
				if int(message["Payload"]["TaskUID"]) < 0:
					tse = pack_message("TSE", {"ErrorDescription" : "Pre defined tasks cannot be delteded!"})
					self.sock.send(tse, sock, sock.sock)
				else:
					self.delete_task(message["Payload"])
					tsl = pack_message("TSL", self.generate_task_list())
					self.sock.send(tsl, sock, sock.sock)
			elif message["MessageType"] == "ACM":
				if self.add_command(message["Payload"]):
					cml = pack_message("CML", self.generate_command_list())
					self.sock.send(cml, sock, sock.sock)
				else: 
					CER = pack_message("CER", {"ErrorDescription" : "Command did not compile! Removed command"})
					self.sock.send(CER, sock, sock.sock)
			elif message["MessageType"] == "CCM":
				if self.change_command(message["Payload"]):
					cml = pack_message("CML", self.generate_command_list())
					self.sock.send(cml, sock, sock.sock)
				else: 
					CER = pack_message("CER", {"ErrorDescription" : "Command did not compile! Reverted state!"})
					self.sock.send(CER, sock, sock.sock)
			elif message["MessageType"] == "DCM":
				if self.delete_command(message["Payload"]):
					cml = pack_message("CML", self.generate_command_list())
					self.sock.send(cml, sock, sock.sock)
				else: 
					CER = pack_message("CER", {"ErrorDescription" : "Deletion unsuccessful!"})
					self.sock.send(CER, sock, sock.sock)
			elif message["MessageType"] == "RAL":
				self.sock.send(pack_message("SAL", cdef))
			elif message["MessageType"] == "UAL":
				self.update_ars(message["Payload"])
			else:
				fprint("error executing command")
				self.sock.send(self.generate_err_message('CER', 'Invalid command'), sock, sock.sock)



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
				self.ars.send("shutdown")
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
		elif command == "mode":
			if self.confMode:
				fprint("Conf Mode")
			else:
				fprint("Client Mode")
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
			command_params = {"CommandParamDataType":method["param_type"]}
			if method["param_type"] != "void":
				command_params["CommandParamName"] = method["param_name"]
				if "min" in method:
					command_params["CommandParamRanges"] = {"min":method["min"],"max":method["max"]} 
			if self.confMode:
				command["CommandCode"] = method["code"]
			command["CommandParams"].append(command_params)
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

	"""
	Change the task file for the given task
	"""
	def change_task(self, task):
		os.remove('tasks/'+task["TaskUID"]+'.tdef')
		file = open('tasks/'+str(task["TaskUID"])+'.tdef', 'w+')
		file.write(json.dumps(task))

	"""
	Add a task and a task file
	"""
	def add_task(self, task):
		try:
			task_id = int(hashlib.sha1(str(time.time())+task["TaskName"]+task["TaskDesc"]["ShortDesc"]).hexdigest(), 16)
		except UnicodeEncodeError:
			task_id = int(hashlib.sha1(str(time.time())).hexdigest(), 16)
		task["TaskUID"] = str(task_id)
		file = open('tasks/'+str(task_id)+'.tdef', 'w+')
		file.write(json.dumps(task))

	"""
	Delete a task file
	"""
	def delete_task(self, task):
		os.remove('tasks/'+task["TaskUID"]+'.tdef')

	"""
	Change a given command
	"""
	def change_command(self, command):
		fprint("Change Command")
		old_cdef = copy.deepcopy(self.cdef)

		index = -1
		counter = 0
		for method in self.cdef["methods"]:
			if method["name"] == command["CommandName"]:
				index = counter
			counter+=1

		if index >= 0:
			self.cdef["methods"][0]["name"] = command["CommandName"]
			self.cdef["methods"][0]["return_type"] = command["CommandReturn"]
			self.cdef["methods"][0]["param_type"] = command["CommandParams"][0]["CommandParamDataType"]
			self.cdef["methods"][0]["code"] = command["Code"]

			if command["CommandParams"][0]["CommandParamDataType"] != "void":
				self.cdef["methods"][0]["param_name"] = command["CommandParams"][0]["CommandParamName"]
				if command["CommandParams"][0]["CommandParamDataType"] == "double" or \
					command["CommandParams"][0]["CommandParamDataType"] == "int":
					
					self.cdef["methods"][0]["min"] = command["CommandParams"][0]["CommandParamRanges"]["min"]
					self.cdef["methods"][0]["max"] = command["CommandParams"][0]["CommandParamRanges"]["max"]

			f = open('ars/cdef/'+'example.cdef', 'w')
			f.write(json.dumps(self.cdef, indent=4, sort_keys=True))
			f.close()

			if not ars_gen.build_ars("example.cdef"):
				fprint("Error Updating ARS")
				self.cdef = old_cdef
				f = open('ars/cdef/'+'example.cdef', 'w')
				f.write(json.dumps(self.cdef, indent=4, sort_keys=True))
				f.close() 
				ars_gen.build_ars("example.cdef")
				fprint("Reverted ARS")
				return False
			else:
				fprint("Updated ARS")
				return True
		else:
			return False

	"""
	Add a command
	"""
	def add_command(self, command):
		fprint("Add Command")
		old_cdef = copy.deepcopy(self.cdef)

		method = {
			"name" : command["CommandName"],
			"return_type" :  command["CommandReturn"],
			"param_type" : command["CommandParams"][0]["CommandParamDataType"],
			"code" : command["Code"]
		}

		if command["CommandParams"][0]["CommandParamDataType"] != "void":
			method["param_name"] = command["CommandParams"][0]["CommandParamName"]
			if command["CommandParams"][0]["CommandParamDataType"] == "double" or \
				command["CommandParams"][0]["CommandParamDataType"] == "int":
				
				method["min"] = command["CommandParams"][0]["CommandParamRanges"]["min"]
				method["max"] = command["CommandParams"][0]["CommandParamRanges"]["max"]
		self.cdef["methods"].append(method)
		f = open('ars/cdef/'+'example.cdef', 'w')
		f.write(json.dumps(self.cdef, indent=4, sort_keys=True))
		f.close()
		try:
			if not ars_gen.build_ars("example.cdef"):
				fprint("Error Updating ARS")
				self.cdef = old_cdef
				f = open('ars/cdef/'+'example.cdef', 'w')
				f.write(json.dumps(self.cdef, indent=4, sort_keys=True))
				f.close() 
				ars_gen.build_ars("example.cdef")
				fprint("Reverted ARS")
				return False
			else:
				fprint("Updated ARS")
				return True
		except UnicodeEncodeError:
			fprint("Error Updating ARS")
			self.cdef = old_cdef
			f = open('ars/cdef/'+'example.cdef', 'w')
			f.write(json.dumps(self.cdef, indent=4, sort_keys=True))
			f.close() 
			ars_gen.build_ars("example.cdef")
			fprint("Reverted ARS")
			return False

	"""
	Delete a command
	"""
	def delete_command(self, command):
		fprint("Delete Command")
		old_cdef = copy.deepcopy(self.cdef)
		index = -1
		counter = 0
		for method in self.cdef["methods"]:
			if method["name"] == command["CommandName"]:
				index = counter
			counter+=1

		if index >= 0:
			self.cdef["methods"].pop(index)

		f = open('ars/cdef/'+'example.cdef', 'w')
		f.write(json.dumps(self.cdef, indent=4, sort_keys=True))
		f.close()

		if not ars_gen.build_ars("example.cdef"):
			fprint("Error Updating ARS")
			self.cdef = old_cdef
			f = open('ars/cdef/'+'example.cdef', 'w')
			f.write(json.dumps(self.cdef, indent=4, sort_keys=True))
			f.close() 
			ars_gen.build_ars("example.cdef")
			fprint("Reverted ARS")
			return False
		else:
			fprint("Updated ARS")
			return True

	"""
	Update the ars and compile it
	"""
	def update_ars(self, ars):
		fprint("Updating ars")
		self.build_ars();

	"""""""""""""""""""""""""""""""""""""""""""""""""""
	Main program
	"""""""""""""""""""""""""""""""""""""""""""""""""""
	def main(self):
		self.ars = ARS()
		self.start_ars()
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

print logo
print "Server Version 1.0 - (C) 2017 MissionEDU.org - Daniel Swoboda"
server = server()
server.main()
