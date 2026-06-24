"""
Modbus TCP 서버 — 분실물 센터 중앙 레지스터 허브.

독립 프로세스로 실행합니다 (ROS2 불필요).

실행:
  python server.py              # 기본 포트 5020
  sudo python server.py -p 502  # 표준 Modbus 포트

레지스터 (Holding Register, address 0~1):
  reg[0]  컨베이어   0=대기  1=활성
  reg[1]  RealSense  0=대기  1=활성
"""

import argparse
import logging
import threading
import time

from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusServerContext,
    ModbusSlaveContext,
)
from pymodbus.server.sync import StartTcpServer

REG_NAMES = {0: "컨베이어", 1: "RealSense"}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [Modbus] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def _monitor(context: ModbusServerContext, interval: float = 0.5):
    """레지스터 변화 감지 시 로그 출력."""
    prev = [None] * 2
    while True:
        cur = context[0].getValues(3, 0, count=2)
        for i, (p, c) in enumerate(zip(prev, cur)):
            if p != c:
                log.info(f"reg[{i}] {REG_NAMES.get(i, '?')}  {p} → {c}")
        prev = list(cur)
        time.sleep(interval)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", type=int, default=5020,
                        help="Modbus TCP 포트 (기본: 5020, 표준: 502)")
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()

    store = ModbusSlaveContext(
        hr=ModbusSequentialDataBlock(0, [0] * 10)
    )
    context = ModbusServerContext(slaves=store, single=True)

    threading.Thread(target=_monitor, args=(context,), daemon=True).start()

    log.info(f"Modbus 서버 시작  {args.host}:{args.port}")
    log.info("reg[0]=컨베이어  reg[1]=RealSense")
    StartTcpServer(context, address=(args.host, args.port))


if __name__ == "__main__":
    main()
