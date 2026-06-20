"""MCP tool definitions for SafetyScanner."""

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from safetyscanner.scorer import ScoreResult, score_text


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

    return app


mcp = create_mcp()


def format_score_result(result: ScoreResult) -> str:
    if not result["matched"]:
        return (
            f"위험도: {result['score']}/100 ({result['band']})\n\n"
            "명백한 위험 신호는 발견되지 않았습니다. 다만 안전을 보장하는 것은 아니므로 아래를 직접 확인하세요.\n"
            "- 선입금·보증금·교육비를 요구하지 않는지 확인\n"
            "- 외부 메신저나 의심 링크로 이동을 요구하지 않는지 확인\n"
            "- 신분증·계좌·로그인 정보를 먼저 요구하지 않는지 확인"
        )

    lines = [f"위험도: {result['score']}/100 ({result['band']})", "", "⚠️ 사기인 이유"]

    for signal in _unique_scam_explanations(result):
        lines.append(f"- {signal['scam_type']}: {signal['why']}")

    signal_text = ", ".join(
        f"{signal['label']} [{signal['weight_label']}]" for signal in result["matched"]
    )
    lines.append("")
    lines.append(f"🔍 탐지 신호: {signal_text}")
    if result["evidence"]:
        quoted = ", ".join(f'"{item}"' for item in result["evidence"][:5])
        lines.append(f"📌 근거: {quoted}")
    else:
        lines.append("📌 근거: 없음")

    lines.append(f"✅ 권장: {_recommendation(result)}")
    return "\n".join(lines)


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
