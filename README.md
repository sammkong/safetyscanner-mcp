# SafetyScanner

> 거래·알바 글을 붙여 넣으면 사기 의심 신호를 찾아 위험도 점수와 근거를 돌려주는 읽기 전용 MCP 서버입니다.

SafetyScanner는 사용자가 중고거래 글이나 단기알바 공고를 보고 “이거 괜찮은가?”를 판단하기 전에, 에이전트가 먼저 호출할 수 있는 안전 필터입니다.  
현재 단계는 **실행 환경과 서버 뼈대만 준비한 상태**이며, 실제 점수 계산 로직은 다음 단계에서 구현합니다.

## 문제 정의

중고거래와 단기알바 사기는 글 안에 위험 신호가 드러나는 경우가 많습니다.

| 상황 | 자주 보이는 신호 |
| --- | --- |
| 중고거래 | 선입금 요구, 안전결제 회피, 외부 메신저 유도, 지나치게 낮은 가격 |
| 알바 공고 | 보증금·교육비 요구, 신분증·통장사본 요구, 고수익 보장, 업무 내용 모호 |

문제는 사용자가 급하거나 익숙하지 않을 때 이런 신호를 놓치기 쉽다는 점입니다.  
SafetyScanner는 글을 읽고 “왜 위험한지”를 근거와 함께 돌려주어, 에이전트가 더 일관되고 설명 가능한 경고를 할 수 있게 돕습니다.

## 어떻게 쓰이나요?

사용 흐름은 단순합니다.

| 단계 | 내용 |
| --- | --- |
| 1 | 사용자가 거래글이나 알바 공고를 에이전트에게 붙여 넣습니다. |
| 2 | 에이전트가 `score_listing_risk(text)` 도구를 호출합니다. |
| 3 | 서버가 위험도 점수와 탐지 근거를 반환합니다. |
| 4 | 에이전트가 사용자에게 주의할 지점을 설명합니다. |

예상 최종 응답 형태는 아래처럼 짧고 읽기 쉬운 텍스트입니다.

```text
risk_score: 75/100 (위험)
탐지 신호:
- 선입금 요구 [높음]
- 외부 메신저 유도 [중간]
근거: "예약금 먼저 보내주세요", "텔레그램으로 연락"
권장: 안전결제 이용, 외부 채널 거래 금지
```

<details>
<summary>현재 구현 상태</summary>

지금은 PlayMCP 등록 규격에 맞는 서버 실행과 도구 노출을 확인하기 위한 초기 뼈대입니다.

- `score_listing_risk(text)` 도구 1개 등록
- Streamable HTTP 전송
- 무세션 방식
- `/mcp` 엔드포인트
- 실제 점수 계산은 아직 미구현
- 현재 반환값: `risk_score: 0/100 (stub)`

</details>

## 기술 구조

| 항목 | 값 |
| --- | --- |
| 언어 | Python 3.11 이상 |
| MCP 프레임워크 | 공식 MCP Python SDK의 FastMCP |
| 설치 패키지 | `mcp[cli]` |
| 전송 방식 | Streamable HTTP |
| 세션 방식 | 무세션 |
| 실행 주소 | `0.0.0.0:8000` |
| 엔드포인트 | `/mcp` |

서버와 도구 이름에는 제한된 플랫폼명을 넣지 않습니다.

## 설치

### macOS/Linux

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 실행

```bash
python server.py
```

실행 후 MCP 엔드포인트:

```text
http://localhost:8000/mcp
```

## MCP Inspector로 확인

```bash
npx @modelcontextprotocol/inspector
```

Inspector에서 아래처럼 설정합니다.

| 항목 | 값 |
| --- | --- |
| Transport | `Streamable HTTP` |
| URL | `http://localhost:8000/mcp` |

확인할 것:

- 도구 목록에 `score_listing_risk`가 보이는지
- 샘플 `text`로 실행했을 때 stub 응답이 오는지

## PlayMCP 체크리스트

- [x] 공식 MCP Python SDK 사용
- [x] `FastMCP` 기반 서버
- [x] Streamable HTTP
- [x] 무세션 방식
- [x] `0.0.0.0:8000/mcp`
- [x] 도구 annotations 5개 값 지정
- [x] 읽기 전용 도구
- [ ] 실제 위험 신호 사전 구현
- [ ] 실제 점수 계산 구현
- [ ] 결과 텍스트 최소화 검수
- [ ] 평균 100ms, p99 3초 목표 검증
- [ ] 광고성 문구 없음 검수

## 배포 메모

개발 중에는 ngrok으로 로컬 서버를 임시 공개 URL로 노출해 Inspector와 PlayMCP 등록 흐름을 확인합니다.  
상시 운영 단계에서는 Render나 Cloudtype 같은 배포 환경을 사용합니다.

## 다음 단계

| 단계 | 범위 |
| --- | --- |
| v1 | 거래·알바 위험 신호 사전과 가중치 기반 스코어러 구현 |
| v2 | 신호 확장, `explain_signal`, `safe_trade_checklist` 추가 |
| v3 | LLM/SBERT 기반 보조 탐지를 사전 배치 방식으로 연결 |

이번 저장소는 v1 구현에 들어가기 전, 서버가 제대로 뜨고 MCP 도구가 연결되는지 확인하기 위한 출발점입니다.
