#!/bin/bash
/home/ssafy/finalPJT/SelfFound/backend/.venv/bin/python -c "
from pymodbus.client.sync import ModbusTcpClient
c = ModbusTcpClient('localhost', port=5020)
c.connect()
c.write_register(1, 1)
c.close()
print('reg[1]=1 → RealSense 트리거')
"
