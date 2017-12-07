#!/usr/bin/env python
# -*- coding: utf_8 -*-
import time

import rocmod
from rocmod import roc_tcp
from rocmod import crc




if __name__ == "__main__":
	
	#DATA TYPES FROM THE PYTHON STRUCT LIBRARY
	#https://docs.python.org/2/library/struct.html
	
	oMaster = rocmod.roc_tcp.TcpMaster(server="10.0.0.1", port=4000, host_address=3, host_group=1)
	oMaster.set_timeout(5.0)
	
	#READ MULTIPLE TLP'S
	print oMaster.opcode180(address=1, group=2, TLP=[[10,0,0],[10,0,1],[10,0,2],[10,0,3],[10,0,5],[10,0,7],[17,0,0],[17,0,1]], data_format=['f','f','f','f','f','f','c10','h'])
	
	#READ ROC HISTORY
	print oMaster.opcode128(address=1, group=2, point=0, day=5, month=12)
	print oMaster.opcode128(address=1, group=2, point=6, day=5, month=12)
	print oMaster.opcode128(address=1, group=2, point=1, day=5, month=12)
	print oMaster.opcode128(address=1, group=2, point=2, day=5, month=12)
	print oMaster.opcode128(address=1, group=2, point=3, day=5, month=12)
	
	
	#WRITE SINGLE TLP
	
	#WRITE A STRING
	#VALUE CAN BE EITHER AA SINGLE STRING OR ARRACY OF CHAR
	#print oMaster.opcode181(address=1, group=2, TLP=[[17,5,0]], data_format=['c10'], values='Soft Pt 6 ')
	
	
	#WRITE AN INTEGER
	#print oMaster.opcode181(address=1, group=2, TLP=[[17,5,1]], data_format=['h'], values=[2])
	
	#WRITE A FLOAT
	#print oMaster.opcode181(address=1, group=2, TLP=[[17,5,2]], data_format=['f'], values=[2.0])
