from safetyscanner.scorer import score_text
from safetyscanner.tools import format_score_result


def test_normal_listing_scores_safe() -> None:
    result = score_text("역 앞에서 직거래 가능합니다. 상태 좋고 안전결제도 가능합니다.")

    assert result["band"] == "안전"
    assert result["score"] <= 30


def test_normal_part_time_job_scores_safe() -> None:
    result = score_text("카페 주말 알바 모집합니다. 초보환영, 단순 업무 위주이며 면접 후 근무합니다.")

    assert result["band"] == "안전"
    assert result["score"] <= 30
    output = format_score_result(result)
    assert "안전합니다" not in output
    assert "명백한 위험 신호는 발견되지 않았습니다" in output


def test_normal_office_assistant_job_scores_safe() -> None:
    result = score_text("사무보조 평일 알바 모집합니다. 엑셀 정리와 전화 응대 업무이며 면접 후 계약합니다.")

    assert result["band"] == "안전"
    assert result["score"] <= 30
    assert "안전합니다" not in format_score_result(result)


def test_clear_job_scam_scores_danger() -> None:
    result = score_text("교육비 먼저 입금하고 텔레그램으로 연락 주세요. 신분증도 보내주세요.")

    assert result["band"] == "위험"
    assert result["score"] >= 61


def test_evidence_is_not_empty_for_matched_signal() -> None:
    result = score_text("예약금 먼저 보내주시면 링크 확인 후 택배만 가능합니다.")

    assert result["evidence"]
    assert result["matched"]


def test_money_mule_case_scores_danger() -> None:
    result = score_text(
        "외화 송금 환전 거래처 관리 업무입니다. 송금된 금액 확인 후 "
        "다른 계좌로 이체하거나 현금으로 인출해 전달합니다. "
        "이체 건당 1~3% 수수료 당일 지급합니다."
    )

    assert result["band"] == "위험"
    assert result["score"] >= 61


def test_illegal_device_install_case_scores_danger() -> None:
    result = score_text(
        "에어비앤비 객실 비대면 관리 업무입니다. 회사가 보내는 소형 전산 장비를 "
        "집에 설치하고 전원 인터넷만 연결하면 됩니다. 주급 40만원과 전기세 지원합니다."
    )

    assert result["band"] == "위험"
    assert result["score"] >= 61


def test_paid_signup_referral_case_scores_danger() -> None:
    result = score_text(
        "AI 데이터 라벨링 작업자 등록 및 본인 인증 절차 필요합니다. "
        "하는 만큼 벌어가는 구조이며 간단한 작업입니다."
    )

    assert result["band"] == "위험"
    assert result["score"] >= 61


def test_pickup_delivery_case_scores_danger() -> None:
    result = score_text(
        "백화점 명품 골드바 구매 대행 업무입니다. 회사 체크카드나 현금을 전달받아 "
        "대신 결제 후 픽업해 지정 장소로 전달하거나 퀵으로 전달합니다. "
        "일당 15만원 현금 당일 지급합니다."
    )

    assert result["band"] == "위험"
    assert result["score"] >= 61


def test_body_photo_model_case_scores_danger() -> None:
    result = score_text(
        "피팅 협찬 모델 모집입니다. 신체 부위 촬영과 속옷 라인 착용 컷이 필요하지만 "
        "얼굴 안 나와도 됩니다. 협찬 보증금 20~30만 먼저 입금하면 환불됩니다."
    )

    assert result["band"] == "위험"
    assert result["score"] >= 61


def test_paid_work_program_case_scores_danger() -> None:
    result = score_text(
        "번역 교정 재택 알바입니다. 회사 전용 정산 프로그램 설치가 필요하며 "
        "작업 프로그램 라이선스 비용 결제 후 첫 급여에 환불됩니다."
    )

    assert result["band"] == "위험"
    assert result["score"] >= 61


def test_signature_rental_case_scores_danger() -> None:
    result = score_text(
        "결혼식 하객과 신차 검수 동행 알바입니다. 서명만 같이 해주면 수수료를 지급하고 "
        "머릿수 채우면 인센티브가 있습니다. 캐피탈 방문 동행도 포함됩니다."
    )

    assert result["band"] == "위험"
    assert result["score"] >= 61
    assert "명의 도용 대출 사기" in format_score_result(result)


def test_signature_rental_companion_loan_case_explains_scam_type() -> None:
    result = score_text(
        "결혼식 하객 및 신차 출고 검수 동행 알바입니다. 계약 시 동행해서 "
        "서명만 해주면 되고 머릿수 채우면 수수료를 지급합니다."
    )

    output = format_score_result(result)

    assert result["band"] == "위험"
    assert result["score"] >= 61
    assert "명의 도용 대출 사기" in output


def test_account_rental_case_scores_danger() -> None:
    result = score_text(
        "SNS 대리 포스팅 알바입니다. 타 계정에 좋아요 댓글 작업을 하고 "
        "아이디 비밀번호 제공하면 알아서 올리고 돈만 주겠습니다."
    )

    assert result["band"] == "위험"
    assert result["score"] >= 61


def test_account_rental_without_password_case_explains_scam_type() -> None:
    result = score_text(
        "SNS 대리 포스팅 알바입니다. 타인 계정에 좋아요 작업과 댓글 작업을 하고 "
        "원고 회사 제공 복붙만 하면 됩니다. 건별 지급합니다."
    )

    output = format_score_result(result)

    assert result["band"] == "위험"
    assert result["score"] >= 61
    assert "불법 홍보" in output
