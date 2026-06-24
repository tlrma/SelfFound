import base64
from django.core.mail import EmailMessage
from django.conf import settings


def send_match_email(user_email: str, user_name: str, item, reasoning: str = "", auth_code: str = ""):
    """
    매칭 성공 시 신고자에게 이메일 발송.

    Args:
        user_email : 신고자 이메일
        user_name  : 신고자 이름
        item       : 매칭된 Item 인스턴스
        reasoning  : LLM 판단 근거 문자열
    """
    if not settings.EMAIL_HOST_USER:
        print("[email] EMAIL_HOST_USER 미설정 — 이메일 발송 건너뜀")
        return

    subject = "[SelfFound] 분실물 매칭 알림"

    category_map = {
        'Card': '카드', 'Glasses': '안경', 'Keys': '열쇠',
        'Phone': '휴대폰', 'Sunglasses': '선글라스',
        'Wallet': '지갑', 'Watch': '시계', 'Etc': '기타',
    }
    category_kr = category_map.get(item.category, item.category)

    reasoning_line = f"\n매칭 근거: {reasoning}" if reasoning else ""
    auth_line = f"\n\n[수령 인증 코드]\n{auth_code}\n방문 시 이 코드를 제시해 주세요." if auth_code else ""

    body = f"""{user_name}님, 분실하신 물건이 접수됐습니다.

[매칭된 분실물 정보]
물품 종류 : {category_kr}
습득 장소 : {item.found_info or '미확인'}
습득 일시 : {item.created_at.strftime('%Y-%m-%d %H:%M')}
물품 묘사 : {item.description or '없음'}{reasoning_line}{auth_line}

분실물 센터로 방문하여 본인 확인 후 수령해 주세요.
문의: SelfFound 운영팀
"""

    try:
        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user_email],
        )
        if item.image_b64:
            image_bytes = base64.b64decode(item.image_b64)
            email.attach(f"item_{item.id}.jpg", image_bytes, "image/jpeg")
        email.send(fail_silently=False)
        print(f"[email] 발송 완료 → {user_email}")
    except Exception as e:
        print(f"[email] 발송 실패: {e}")
