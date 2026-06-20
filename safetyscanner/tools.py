"""MCP tool definitions for SafetyScanner."""

import re

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from safetyscanner.scorer import ScoreResult, score_text
from safetyscanner.signals import SIGNALS


def create_mcp(port: int = 8000) -> FastMCP:
    app = FastMCP(
        name="SafetyScanner",
        host="0.0.0.0",
        port=port,
        streamable_http_path="/mcp",
        stateless_http=True,
    )

    @app.tool(
        description=(
            "Use this when a user pastes a marketplace or part-time job listing and "
            "asks whether it might be a scam. Returns a fraud risk score (0-100), "
            "detected signals, and evidence from SafetyScanner(세이프티스캐너)."
        ),
        annotations=ToolAnnotations(
            title="Score Listing Risk",
            readOnlyHint=True,
            destructiveHint=False,
            openWorldHint=False,
            idempotentHint=True,
        ),
    )
    def score_listing_risk(text: str) -> str:
        """Score a listing text for fraud risk."""
        return format_score_result(score_text(text))

    @app.tool(
        description=(
            "Use this when a user asks WHY a specific phrase or signal in a "
            "job/marketplace listing is dangerous (e.g. 'why is asking for a "
            "deposit risky?'). Explains the scam type and how to respond, from "
            "SafetyScanner(세이프티스캐너)."
        ),
        annotations=ToolAnnotations(
            title="Explain Fraud Signal",
            readOnlyHint=True,
            destructiveHint=False,
            openWorldHint=False,
            idempotentHint=True,
        ),
    )
    def explain_signal(query: str) -> str:
        """Explain why a fraud signal is risky."""
        return format_signal_explanation(query)

    @app.tool(
        description=(
            "Use this when a user asks for a safety checklist before taking a "
            "part-time job or making a secondhand trade. Returns key red-flags "
            "to self-check, from SafetyScanner(세이프티스캐너)."
        ),
        annotations=ToolAnnotations(
            title="Safe Trade Checklist",
            readOnlyHint=True,
            destructiveHint=False,
            openWorldHint=False,
            idempotentHint=True,
        ),
    )
    def safe_trade_checklist(category: str = "all") -> str:
        """Return a safety checklist for trade or job listings."""
        return format_safe_checklist(category)

    return app


mcp = create_mcp()


def format_score_result(result: ScoreResult) -> str:
    if not result["matched"]:
        return (
            f"✅ 위험도 : {result['score']}/100 (안전)\n\n"
            "명백한 위험 신호는 발견되지 않았습니다.\n"
            "다만 안전을 보장하는 것은 아니므로 아래를 직접 확인하세요.\n"
            " - 선입금·보증금·교육비를 요구하지 않는지\n"
            " - 외부 메신저나 의심 링크로 이동을 요구하지 않는지\n"
            " - 신분증·계좌·로그인 정보를 먼저 요구하지 않는지"
        )

    lines = [f"🚨 위험도 : {result['score']}/100 ({result['band']})", "", "⚠️ 사기인 이유"]

    for signal in _unique_scam_explanations(result):
        lines.append(f" - {signal['scam_type']}")
        lines.append(f"   → {signal['why']}")

    lines.append("")
    lines.append("🔍 탐지된 신호")
    for signal in result["matched"]:
        lines.append(f" - {signal['label']} ({signal['weight_label']})")

    lines.append("")
    lines.append("📌 근거 문구")
    if result["evidence"]:
        quoted = ", ".join(f'"{item}"' for item in result["evidence"][:5])
        lines.append(f" {quoted}")
    else:
        lines.append(" 없음")

    lines.append("")
    lines.append("✅ 권장")
    lines.append(f" {_recommendation(result)}")
    return "\n".join(lines)


def format_signal_explanation(query: str) -> str:
    matched = _find_signals(query)[:3]
    if not matched:
        return (
            "🔍 신호 : 등록된 직접 매칭 없음\n\n"
            "해당 표현은 등록된 위험 신호와 직접 매칭되지 않습니다. 일반 안전수칙을 확인하세요.\n\n"
            "✅ 대응\n"
            " 선입금·보증금·교육비를 요구하면 진행하지 마세요.\n"
            " 신분증·계좌·로그인 정보, 외부 메신저 이동 요구는 다시 확인하세요."
        )

    lines: list[str] = []
    for index, signal in enumerate(matched):
        if index:
            lines.append("")
        lines.append(f"🔍 신호 : {signal['label']}")
        lines.append("")
        lines.append("⚠️ 왜 위험한가")
        lines.append(f" {signal['scam_type']} : {signal['why']}")
        lines.append("")
        lines.append("✅ 대응")
        lines.append(f" {_response_for_signal(signal)}")

    return "\n".join(lines)


def format_safe_checklist(category: str = "all") -> str:
    normalized = category if category in {"trade", "job", "all"} else "all"
    title = {
        "trade": "✅ 중고거래 안전 체크리스트",
        "job": "✅ 알바 안전 체크리스트",
        "all": "✅ 거래·알바 안전 체크리스트",
    }[normalized]

    signals = _checklist_signals(normalized)
    lines = [title, ""]
    for signal in signals:
        lines.append(f" - {_checklist_item(signal)}")
    return "\n".join(lines)


def _find_signals(query: str) -> list[dict[str, object]]:
    normalized_query = _normalize(query)
    found: list[dict[str, object]] = []
    for signal in SIGNALS:
        if _signal_matches_query(signal, query, normalized_query):
            found.append(signal)
    return found


def _signal_matches_query(
    signal: dict[str, object], query: str, normalized_query: str
) -> bool:
    searchable_fields = (
        str(signal["label"]),
        str(signal["scam_type"]),
    )
    if any(_normalize(field) in normalized_query or normalized_query in _normalize(field) for field in searchable_fields):
        return True

    for pattern in signal["patterns"]:
        pattern_text = str(pattern)
        if re.search(pattern_text, query, flags=re.IGNORECASE):
            return True
        literal_hint = _regex_to_search_hint(pattern_text)
        if literal_hint and literal_hint in normalized_query:
            return True
    return False


def _regex_to_search_hint(pattern: str) -> str:
    hint = re.sub(r"\\s\*|\\s\+|\.\{[^}]+\}|\([^)]*\)|\[.*?\]|\?", "", pattern)
    hint = re.sub(r"[^0-9A-Za-z가-힣]+", "", hint)
    return _normalize(hint)


def _normalize(value: str) -> str:
    return re.sub(r"\s+", "", value).lower()


def _response_for_signal(signal: dict[str, object]) -> str:
    category = str(signal["category"])
    label = str(signal["label"])
    if category == "scam_participation":
        return "범죄 가담 위험이 있으므로 즉시 중단하고 신고(112/경찰청)를 고려하세요."
    if "금전" in label or "선입금" in label or "예약금" in label:
        return "일하기 전 또는 거래 전 돈을 먼저 보내지 말고 안전한 결제·계약 절차를 확인하세요."
    if "개인정보" in label or "신분증" in label or "계좌" in label:
        return "신분증·계좌·통장사본·로그인 정보는 검증 전 제공하지 마세요."
    if "외부" in label:
        return "플랫폼 밖 메신저로 이동하기 전에 거래 기록과 신고 가능성을 확인하세요."
    return "요구 사항을 그대로 따르지 말고 상대 신원, 결제 방식, 계약 조건을 다시 확인하세요."


def _checklist_signals(category: str) -> list[dict[str, object]]:
    wanted_ids = {
        "trade": [
            "trade_advance_payment",
            "trade_safe_payment_avoidance",
            "trade_external_channel",
            "trade_suspicious_url",
            "trade_shipping_only",
        ],
        "job": [
            "job_money_request",
            "job_identity_account_request",
            "participation_money_mule",
            "participation_pickup_delivery",
            "participation_illegal_device",
            "participation_name_signature_rental",
            "participation_account_rental",
            "job_external_messenger",
        ],
    }
    ids = wanted_ids["trade"] + wanted_ids["job"] if category == "all" else wanted_ids[category]
    signal_by_id = {str(signal["id"]): signal for signal in SIGNALS}
    return [signal_by_id[signal_id] for signal_id in ids if signal_id in signal_by_id]


def _checklist_item(signal: dict[str, object]) -> str:
    items = {
        "trade_advance_payment": "물건 확인 전에 선입금·예약금·계약금을 요구하지 않는가",
        "trade_safe_payment_avoidance": "안전결제나 플랫폼 보호 절차를 피하려 하지 않는가",
        "trade_external_channel": "카톡·텔레그램 등 외부 메신저로 이동하자고 하지 않는가",
        "trade_suspicious_url": "출처가 불분명한 링크 접속을 요구하지 않는가",
        "trade_shipping_only": "직접 확인을 피하고 택배 거래만 강요하지 않는가",
        "job_money_request": "일하기 전에 보증금·교육비·선결제를 요구하지 않는가",
        "job_identity_account_request": "신분증·계좌·통장사본·카드 정보를 먼저 요구하지 않는가",
        "participation_money_mule": "내 계좌로 돈을 받아 이체·인출·전달하라고 하지 않는가",
        "participation_pickup_delivery": "현금·상품권·골드바·명품을 대신 결제·수거·전달하라고 하지 않는가",
        "participation_illegal_device": "집에 장비·공유기·모뎀을 설치하고 연결만 하라고 하지 않는가",
        "participation_name_signature_rental": "동행·서명·명의 제공·캐피탈 방문을 요구하지 않는가",
        "participation_account_rental": "SNS 계정 대여, 로그인 정보 제공, 대리 포스팅을 요구하지 않는가",
        "job_external_messenger": "텔레그램·오픈채팅 등 외부 메신저로 옮기려 하지 않는가",
    }
    return items.get(str(signal["id"]), f"{signal['label']} 관련 요구가 없는지 확인")


def _unique_scam_explanations(result: ScoreResult) -> list[dict[str, str]]:
    seen: set[str] = set()
    explanations: list[dict[str, str]] = []
    for signal in result["matched"]:
        scam_type = signal["scam_type"]
        if scam_type in seen:
            continue
        seen.add(scam_type)
        explanations.append({"scam_type": scam_type, "why": signal["why"]})
    return explanations


def _recommendation(result: ScoreResult) -> str:
    has_participation_signal = any(
        signal["category"] == "scam_participation" for signal in result["matched"]
    )
    if has_participation_signal:
        return "범죄 가담 위험, 즉시 중단 및 신고(112/경찰청) 고려"
    if result["band"] == "위험":
        return "거래·지원 중단, 선입금 금지, 외부 채널 이동 금지"
    if result["band"] == "주의":
        return "안전결제 이용, 신분증·계좌 정보 제공 금지, 조건 재확인"
    return "기본 안전수칙 확인 후 진행"
