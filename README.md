# OCR OSS

Python `tkinter`로 만든 Desktop 앱입니다. 화면 영역을 선택하고 주기적으로 캡처하며, 이미지가 변경될 때마다 OCR을 수행합니다.

## 설치 및 실행

### 1. 설치

```bash
pip install -r requirements.txt
```

### 2. Gemini API 설정 

### 설정 방법

1. **Gemini API 키 발급**
   - https://aistudio.google.com/app/apikeys 에서 API 키 발급

2. **.env 파일 생성 or 터미널 환경 변수 사용 **
   - 프로젝트 루트에 `.env` 파일 생성 (`.env.example` 참고)
   - 다음 내용 입력:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

   or 

   - powershell에  $env:GEMINI_API_KEY=" 발급 받은 API키 입력" 
   - echo $env:GEMINI_API_KEY 로 API 연결되었는지 확인

3. **기존 설치된 패키지 업데이트**
   ```bash
   pip install -r requirements.txt
   ```

### 사용 방법

1. 데이터베이스에 OCR 결과 저장
2. "Open Test UI" 버튼 클릭
3. Gemini 2.5 Flash Lite API가 자동으로 저장된 OCR 내용으로부터 객관식 4지선다형 문제, 주관식 문제 생성하고 사용자가 선택
4. 생성된 문제에서 정답 선택지를 고르고 "정답 체크" 클릭
5. 결과 확인 후 "다음 문제" 클릭

### 주의사항

- Gemini API 키가 설정되지 않으면 기본 문제(더미 객관식)로 폴백
- 인터넷 연결 필수
- API 호출 시간이 소요될 수 있음

## 주요 기능

- 영역 선택과 OCR 실행 분리
- 캡처와 OCR 모듈 분리
- 이미지 변경 감지 후 OCR 실행 (불필요한 반복 방지)
- 수동 인식 (`Recognize Now`)
- 원본 언어 선택 → 번역 언어 선택 번역 기능
- SQLite 데이터베이스에 JSON 형식으로 저장

## 저장 형식

저장된 OCR 기록은 일반 텍스트와 JSON 페이로드를 함께 저장합니다.

```json
{
  "time": "2026-04-15T14:30:00",
  "content": "인식된 텍스트"
}
```

## 폴더 구조

```text
ocr_project/
|- main.py
|- CORE/
|  |- db.py
|  |- ocr_engine.py
|  |- ocr_service.py
|  \- translation_service.py
\- UI/
   |- capture_monitor.py
   |- selector.py
   |- study_list.py
   |- test_ui.py
   \- overlay.py
```

## 디자인 notes

- 화면 캡처는 상대적으로 빠름, OCR이 expensive한 작업
- 이전 프레임과 비교하여 이미지 변경时才 OCR 실행 → 이미지 변경될 때만
- 결과는 누적되지 않고, 사용자가 저장할 때마다 최신 결과만 메모리에 유지

## 현재 제한

- OCR 정확도는 영역 크기, 텍스트 크기, 대비, 선택한 언어 쌍에 따라 달라짐
- 너무 넓은 영역은 느리고 정확도도 낮음

## 개발 예정

### 단기

- OCR 전처리 (확대, 그레이스케일, 대비, threshold)
- 캡처 간격 및 OCR 옵션 UI 노출
- 저장 메타데이터 개선

### 중기

- 자막 모드와 문서 모드 분리
- OCR 엔진 비교
- 결과 필터링 및 학습 워크플로우 개선

### 장기

- OCR 결과 기반 번역 및 요약 워크플로우
- GPU 또는 batch OCR 평가