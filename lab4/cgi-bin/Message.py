import ctypes 
from ctypes import *
import struct
from enum import IntEnum

lib_dll=CDLL(r"G:\универ\4 курс\Леонов\Lab2_Con2\ClientServer2_2\Debug\SerializeLib.dll")

class Messages(IntEnum):
	M_CREATE=0
	M_EXIST=1
	M_NOUSER=2
	M_INIT=3
	M_EXIT=4
	M_GETDATA=5
	M_NODATA=6
	M_TEXT=7
	M_CONFIRM=8
	M_INCORRECT=9
	M_ACTIVE=10
	M_INACTIVE=11
	M_ABSENT=12


class Header():
	def __init__(self, m_To="", m_From="", m_Type=0, m_Size=0):
		self.m_To=m_To
		self.m_From=m_From
		self.m_Type=m_Type
		self.m_Size=m_Size

	def HeaderInit(self, header):
		self.m_To=header[0]
		self.m_From=header[1]
		self.m_Type=header[2]
		self.m_Size=header[3]

class Message():
	def __init__(self, To='', From="", Type=0, m_Data=''):
		self.m_Header=Header();
		self.m_Header.m_To=To;
		self.m_Header.m_From=From;
		self.m_Header.m_Type=Type;
		self.m_Header.m_Size=int(len(m_Data))
		self.m_Data=m_Data
	def SendData(self, s, password):
		buffer=ctypes.create_string_buffer(1024)
		lib_dll.getSerializeString(byref(buffer),self.m_Header.m_From.encode('utf-8'), self.m_Header.m_To.encode('utf-8'), self.m_Header.m_Type, self.m_Header.m_Size)

		lenght=int(len(buffer.value))
		s.send(struct.pack('i',lenght))
		s.send(struct.pack(f'{lenght}s', buffer.value))

		if (self.m_Header.m_Type==Messages.M_TEXT):
			s.send(struct.pack(f'{self.m_Header.m_Size}s', self.m_Data.encode('utf-8')))
		if (self.m_Header.m_Type==Messages.M_INIT or  self.m_Header.m_Type==Messages.M_CREATE):
			s.send(struct.pack('i',int(len(password))))
			s.send(struct.pack(f'{int(len(password))}s', password.encode('utf-8')))
		del buffer
	def ReceiveData(self, s):
		self.m_Header = Header()
		lenght=struct.unpack('i', s.recv(4))
		buffer=struct.unpack(f'{lenght[0]}s', s.recv(lenght[0]))[0]

		frombuffer=ctypes.create_string_buffer(1024)
		tobuffer=ctypes.create_string_buffer(1024)
		typebuffer=c_int(0)
		sizebuffer=c_int(0)
		
		lib_dll.getM_HeaderFromString(buffer, byref(frombuffer), byref(tobuffer), byref(typebuffer), byref(sizebuffer))

		self.m_Header.m_From=frombuffer.value
		self.m_Header.m_To=tobuffer.value
		self.m_Header.m_Size=sizebuffer.value
		self.m_Header.m_Type=typebuffer.value

		if self.m_Header.m_Type==Messages.M_TEXT:
			self.m_Data=struct.unpack(f'{self.m_Header.m_Size}s', s.recv(self.m_Header.m_Size+1))[0]
		del frombuffer
		del tobuffer
		del typebuffer
		del sizebuffer
		return self.m_Header