#!/usr/bin/env python
# -*- coding: utf_8 -*-


"""
 Modbus TestKit: Implementation of Fisher ROC protocol in python
 This is distributed under GNU LGPL license, see license.txt
"""


import socket
import select
import struct

import crc



class TcpMaster(object):
	
	def __init__(self, server="127.0.0.1", port=4000, host_group=3, host_address=1, timeout_in_sec=5.0):
		self.timeout_in_sec = timeout_in_sec
		self._server = server
		self._port = port
		self._sock = None
		self._host_group = host_group
		self._host_address = host_address
		
	def _do_open(self):
		"""Connect to the Modbus slave"""
		if self._sock:
			self._sock.close()
		self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.set_timeout(self.timeout_in_sec)
		self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self._sock.connect((self._server, self._port))

	def _do_close(self):
		"""Close the connection with the Modbus Slave"""
		if self._sock:
			self._sock.close()
			self._sock = None
		return True
	
	def _send(self, request):
		"""Send request to the slave"""
		try:
			flush_socket(self._sock, 3)
		except Exception as msg:
			#if we can't flush the socket successfully: a disconnection may happened
			#try to reconnect
			self._do_open()
		self._sock.send(request)
	
	def _recv(self, expected_length=-1):
		"""
		Receive the response from the slave
		"""
		response = []
		length = 255
		while len(response) < length:
			rcv_byte = self._sock.recv(1)
			if rcv_byte:
				response.append(struct.unpack('B',rcv_byte)[0])
				#response += rcv_byte
				if len(response) == 6:
					to_be_recv_length = struct.unpack('B',rcv_byte)[0]
					length = to_be_recv_length + 6 + 2
			else:
				break
		return response
	
	
	
	
	def set_timeout(self, timeout_in_sec):
		if self._sock:
			self._sock.setblocking(timeout_in_sec > 0)
			if timeout_in_sec:
				self._sock.settimeout(timeout_in_sec)
	
	#=============================================================================================================
	# OPCODE 128 Read Daily History
	#=============================================================================================================
	def opcode128(self, address, group, point, day, month, expected_length=-1):
		data = [address, group, self._host_address, self._host_group, 128, 3, point, day, month]
		request = ""
		for i in data:
			request += struct.pack('B',i)
		for i in crc.crc16(request):
			request += struct.pack('B',i)
		self._send(request)
		data = self._recv()
		responsecrc = data[-2:]
		data = data[:-2]
		response = ""
		for i in data:
			response += struct.pack('B',i)
		
		if not(crc.crc16(response) == responsecrc):
			raise RuntimeError('CRC Error')
		if not(data[0] == self._host_address) or not(data[1] == self._host_group):
			raise RuntimeError('Incorrect Host Address in Response')
		
		if not(data[2] == address) or not(data[3] == group):
			raise RuntimeError('Incorrect Device Address in Response')
		
		if not(data[4] == 128):
			raise RuntimeError('Incorrect OPCode in Response')
		
		if not(data[7] == month) or not(data[8] == day):
			raise RuntimeError('Incorrect Date in Response')
		
		value = ''
		value += struct.pack('B',data[109])
		value += struct.pack('B',data[110])
		value += struct.pack('B',data[111])
		value += struct.pack('B',data[112])
		return struct.unpack('f',value)
		
	#=============================================================================================================
	# OPCODE 180 Read TLP
	#=============================================================================================================
	def opcode180(self, address, group, TLP, data_format=[], expected_length=-1):
		data = [address, group, self._host_address, self._host_group, 180, (len(TLP)*3)+1, len(TLP)]
		self.data_format = data_format
		length = 1
		regs = 0
		for t,l,p in TLP:
			length += 3
			regs += 1
			data.append(t)
			data.append(l)
			data.append(p)
			
		request = ""
		for i in data:
			request += struct.pack('B',i)
		for i in crc.crc16(request):
			request += struct.pack('B',i)
		
		self._send(request)
		
		data = self._recv()
		responsecrc = data[-2:]
		data = data[:-2]
		response = ""
		for i in data:
			response += struct.pack('B',i)
		
		if not(crc.crc16(response) == responsecrc):
			raise RuntimeError('CRC Error')
		if not(data[0] == self._host_address) or not(data[1] == self._host_group):
			raise RuntimeError('Incorrect Host Address in Response')
		
		if not(data[2] == address) or not(data[3] == group):
			raise RuntimeError('Incorrect Device Address in Response')
		
		if not(data[4] == 180):
			raise RuntimeError('Incorrect OPCode in Response')
		
		tlplength = data[6]
		data = data[7:]
		value = ''
		for i in range(len(TLP)):
			t,l,p = TLP[i]
			if not(data[0] == t) or not(data[1] == l) or not(data[2] == p):
				raise RuntimeError('TLP Recieved is not TLP Requested')
			if data_format[i] in ['f','q','L','l','i']:
				value += struct.pack('B',data[3])
				value += struct.pack('B',data[4])
				value += struct.pack('B',data[5])
				value += struct.pack('B',data[6])
				data = data[7:]
			elif data_format[i] in ['h','H']:
				value += struct.pack('B',data[3])
				value += struct.pack('B',data[4])
				data = data[5:]
			elif data_format[i] in ['b','B']:
				value += struct.pack('B',data[3])
				data = data[4:]
			else:
				#MUST BE A STRING (c)
				stringlength = int(data_format[i].replace('c',''))
				dataformat = ''
				for x in range(stringlength):
					dataformat += 'c'
					value += struct.pack('B',data[3+x])
				data = data[3+stringlength:]
				data_format[i] = dataformat
		return struct.unpack(''.join(data_format),value)
	
	
	#=============================================================================================================
	# OPCODE 181 WRITE TLP
	#=============================================================================================================
	def opcode181(self, address, group, TLP, data_format, values, expected_length=-1):
		data = [address, group, self._host_address, self._host_group, 181,0,0]
		length = 1
		regs = 0
		for i in range(len(TLP)):
			t,l,p = TLP[i]
			length += 3
			regs += 1
			data.append(t)
			data.append(l)
			data.append(p)
			if data_format[i] in ['f','q','L','l','i']:
				length += 4
				for byte in struct.pack(data_format[i], values[i]):
					data.append(struct.unpack('B',byte)[0])
			elif data_format[i] in ['h','H']:
				length += 2
				for byte in struct.pack(data_format[i], values[i]):
					data.append(struct.unpack('B',byte)[0])
			elif data_format[i] in ['b','B']:
				length += 1
				for byte in struct.pack(data_format[i], values[i]):
					data.append(struct.unpack('B',byte)[0])
			else:
				#Must be a string
				stringlength = int(data_format[i].replace('c',''))
				data_format = ''
				for x in range(stringlength):
					length += 1
					data_format += 'c'
					data.append(struct.unpack('B',values[x])[0])
				
		data[5] = length
		data[6] = regs
		
		request = ""
		for i in data:
			request += struct.pack('B',i)
		for i in crc.crc16(request):
			request += struct.pack('B',i)
		
		self._send(request)
		data = self._recv()
		responsecrc = data[-2:]
		data = data[:-2]
		
		response = ""
		for i in data:
			response += struct.pack('B',i)
			
		if not(crc.crc16(response) == responsecrc):
			raise RuntimeError('CRC Error')
		
		if not(data[0] == self._host_address) or not(data[1] == self._host_group):
			raise RuntimeError('Incorrect Host Address in Response')
		
		if not(data[2] == address) or not(data[3] == group):
			raise RuntimeError('Incorrect Device Address in Response')
		
		if not(data[4] == 181):
			raise RuntimeError('Incorrect OPCode in Response')
		
		if (data[5] == 0):
			#Good Response
			return tuple(values)
		
	
	
		


