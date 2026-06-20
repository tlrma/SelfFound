"""
LLM 기반 분실물 묘사 생성.

GMS_KEY 환경변수가 설정돼 있어야 합니다.
"""

import base64
import os
import requests

GMS_KEY     = os.environ.get("GMS_KEY")
GEMINI_BASE = "https://gms.ssafy.io/gmsapi/generativelanguage.googleapis.com/v1beta/models"

_CATEGORY_EXTRA_PROMPT = {
    "Card": (
        "카드 표면에 보이는 로고나 텍스트를 바탕으로 카드사"
        "(예: 신한, 국민, 하나, 우리, 농협, 삼성, 현대, 롯데, BC 등)를 "
        "추론할 수 있으면 반드시 포함하세요. 확실하지 않으면 '카드사 불분명'이라고 쓰세요. "
    ),
    "Wallet": (
        "로고, 패턴, 마감 등을 바탕으로 브랜드"
        "(예: 루이비통, 구찌, 프라다, 코치, 몽블랑 등)를 "
        "추론할 수 있으면 반드시 포함하세요. 확실하지 않으면 '브랜드 불분명'이라고 쓰세요. "
    ),
}


def generate_description(image: "np.ndarray", category: str = "") -> str:
    """
    이미지(numpy array) → 한국어 자연어 묘사 (gemini-3.5-flash).

    Args:
        image   : cv2로 읽은 BGR 이미지
        category: YOLO 분류 결과 — Card/Wallet 등 카테고리별 추가 추론에 사용

    Returns:
        생성된 묘사 문자열. API 키 미설정 또는 오류 시 빈 문자열 반환.
    """
    if not GMS_KEY:
        return ""

    import cv2
    import numpy as np

    # 이미지를 512px 이하로 축소 (GMS 요청 크기 제한 대응)
    h, w = image.shape[:2]
    max_side = 512
    if max(h, w) > max_side:
        scale = max_side / max(h, w)
        image = cv2.resize(image, (int(w * scale), int(h * scale)))
    _, buf = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 70])
    image_b64 = base64.b64encode(buf.tobytes()).decode("utf-8")

    extra = _CATEGORY_EXTRA_PROMPT.get(category, "")
    text_prompt = (
        "이 분실물을 한국어로 간결하게 설명해주세요. "
        "색상, 재질, 크기, 특징적인 부분을 포함해 2~3문장으로만 답하세요. "
        f"{extra}"
        "설명 외 다른 말은 하지 마세요."
    )

    url = f"{GEMINI_BASE}/gemini-3.5-flash:generateContent?key={GMS_KEY}"
    response = requests.post(
        url,
        headers={"Content-Type": "application/json"},
        json={"contents": [{"parts": [
            {"inline_data": {"mime_type": "image/jpeg", "data": image_b64}},
            {"text": text_prompt},
        ]}]},
        timeout=15,
    )
    if not response.ok:
        print(f"[llm] GMS 오류 {response.status_code}: {response.text}")
        return ""
    return response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
