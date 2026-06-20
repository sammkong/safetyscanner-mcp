<p align="center">
  <img src="docs/safetyscanner-logo.png" alt="SafetyScanner 로고" width="180" />
</p>

# **SafetyScanner 안심 알바 스캐너**

> 거래·알바 글을 붙여 넣으면 **사기 의심 신호**를 찾아  
> **위험도 점수와 근거**를 돌려주는 읽기 전용 MCP 서버입니다.

SafetyScanner는 사용자가 중고거래 글이나 단기알바 공고를 보고  
**“이거 괜찮은가?”** 를 판단하기 전에 호출할 수 있는 **안전 필터**입니다.

에이전트가 글을 대신 검토할 때  
막연한 감이 아니라 **명확한 위험 신호와 근거**를 바탕으로  
사용자에게 주의가 필요한 지점을 설명하도록 돕습니다.

## 문제 정의

중고거래와 단기알바 사기는  
글 안에 위험 신호가 드러나는 경우가 많습니다.

| 상황 | 자주 보이는 신호 |
| --- | --- |
| 중고거래 | 선입금 요구, 안전결제 회피, 외부 메신저 유도, 지나치게 낮은 가격 |
| 알바 공고 | 보증금·교육비 요구, 신분증·통장사본 요구, 고수익 보장, 업무 내용 모호 |

문제는 사용자가 급하거나 익숙하지 않을 때  
이런 신호를 놓치기 쉽다는 점입니다.

SafetyScanner는 글을 읽고 **왜 위험한지**를 근거와 함께 돌려주어  
에이전트가 더 **일관되고 설명 가능한 경고**를 할 수 있게 돕습니다.

## 어떻게 쓰이나요?

사용 흐름은 단순합니다.

| 단계 | 내용 |
| --- | --- |
| 1 | 사용자가 거래글이나 알바 공고를 에이전트에게 붙여 넣습니다. |
| 2 | 에이전트가 `score_listing_risk(text)` 도구를 호출합니다. |
| 3 | 서버가 위험도 점수와 탐지 근거를 반환합니다. |
| 4 | 에이전트가 사용자에게 주의할 지점을 설명합니다. |

응답은 점수만 던지는 방식이 아니라  
**탐지된 신호, 근거 문구, 권장 행동**을 함께 보여주는 형태를 목표로 합니다.

```text
risk_score: 75/100 (위험)
탐지 신호:
- 선입금 요구 [높음]
- 외부 메신저 유도 [중간]
근거: "예약금 먼저 보내주세요", "텔레그램으로 연락"
권장: 안전결제 이용, 외부 채널 거래 금지
```

## 제공 Tools

| Tool | 언제 쓰나요? | 결과 |
| --- | --- | --- |
| `score_listing_risk` | 거래글·알바 공고가 사기인지 확인하고 싶을 때 | 위험도 점수, 사기 유형, 탐지 신호, 근거 문구, 권장 행동 |
| `explain_signal` | “선입금”, “장비 설치”, “계좌 이체” 같은 표현이 왜 위험한지 물을 때 | 해당 신호의 사기 유형, 위험한 이유, 대응 방법 |
| `safe_trade_checklist` | 거래나 알바를 시작하기 전 스스로 점검하고 싶을 때 | 중고거래·알바 안전 체크리스트 |

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

서버는 **Remote MCP 서버**로 동작하며,  
도구는 사용자 데이터를 변경하지 않는 **읽기 전용 방식**으로 설계합니다.

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

실행 후 MCP 엔드포인트는 아래 주소입니다.

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

## Render 배포

SafetyScanner는 Render의 **Web Service**로 배포할 수 있습니다.  
저장소 루트의 `render.yaml`을 Render가 인식하면  
빌드와 실행 명령이 자동으로 설정됩니다.

| 항목 | 값 |
| --- | --- |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `python server.py` |
| Python Version | `3.12.13` |

배포 흐름:

1. GitHub에 이 프로젝트를 올립니다.
2. Render에서 **New Web Service**를 선택합니다.
3. GitHub 레포를 연결하고 SafetyScanner 레포를 선택합니다.
4. Render가 루트의 `render.yaml`을 인식하는지 확인합니다.
5. 배포가 끝나면 Render가 제공한 HTTPS URL 뒤에 `/mcp`를 붙여 사용합니다.

예시:

```text
https://safetyscanner.onrender.com/mcp
```

로컬에서는 `PORT` 환경변수가 없어도 기본값인 `8000`으로 실행됩니다.

```bash
python server.py
```

Render에서는 `PORT` 환경변수가 자동으로 주입되며,  
서버는 그 값을 읽어 해당 포트로 실행됩니다.

무료 티어를 사용할 경우, 일정 시간 요청이 없으면 서버가 sleep 상태가 될 수 있습니다.  
이때 첫 요청은 서버가 다시 깨어나는 **cold start 지연**이 발생할 수 있습니다.

## 기술 스택

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![MCP](https://img.shields.io/badge/MCP-FastMCP-111111?style=for-the-badge)
![Transport](https://img.shields.io/badge/Transport-Streamable_HTTP-2563EB?style=for-the-badge)
![Render](https://img.shields.io/badge/Deploy-Render-46E3B7?style=for-the-badge&logo=render&logoColor=111111)
