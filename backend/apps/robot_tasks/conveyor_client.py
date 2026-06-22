from pymodbus.client.sync import ModbusTcpClient

MODBUS_HOST = "localhost"
MODBUS_PORT = 5020

# reg[0]: 컨베이어 (0=대기, 1=활성)


def trigger_conveyor_belt() -> bool:
    """키오스크 확인 버튼 → Modbus reg[0]=1 쓰기."""
    try:
        client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)
        client.connect()
        client.write_register(0, 1)
        client.close()
        print("[Modbus] reg[0] = 1 (컨베이어 시작)")
        return True
    except Exception as e:
        print(f"[Modbus] 연결 실패: {e}")
        return False
