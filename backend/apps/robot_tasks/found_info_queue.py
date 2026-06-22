"""키오스크 STT 결과를 임시 보관하는 인메모리 큐."""
from collections import deque

_queue: deque[str] = deque()


def push_found_info(text: str):
    _queue.append(text)


def pop_found_info() -> str:
    return _queue.popleft() if _queue else ''
