# Document Generator

AI 기반 사업계획서 자동 생성 시스템

## 소개

정부지원사업 창업패키지 사업계획서를 자동으로 생성하는 시스템입니다. 사용자의 입력을 기반으로 AI가 사업계획서의 각 섹션을 자동으로 작성하고, 템플릿에 맞춰 문서를 생성합니다.

## 개발 환경

- Python 버전: 3.10.11
- IDE: Visual Studio Code

## 주요 기능

- AI 기반 사업계획서 자동 생성
- 템플릿 기반 문서 포맷팅
- 섹션별 사용자 정의 가능한 내용
- TAM/SAM/SOM 시장 분석 데이터 제공
- 이미지 및 템플릿 선택 기능
- 실시간 문서 미리보기

## 기술 스택

- Backend: Python, FastAPI
- Frontend: HTML, CSS, JavaScript
- AI: OpenAI API
- Document Processing: python-docx
- 기타: PDF.js, Sortable.js

## 설치 방법

```bash
# 저장소 클론
git clone [repository URL]

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# OpenAI API 키 등 필요한 환경 변수 설정

## 1. main.py (메인 애플리케이션)

### 초기화 및 설정
```python
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')
UPLOAD_FOLDER = os.path.join(STATIC_DIR, 'uploads')
IMAGE_FOLDER = os.path.join(STATIC_DIR, 'images')
TEMPLATE_FOLDER = STATIC_DIR
```

### API 엔드포인트

#### 1. GET / (home)
- **기능**: 초기 페이지 렌더링
- **응답**: HTMLResponse (first.html)
- **사용 템플릿**: first.html
- **처리 과정**: Jinja2 템플릿 렌더링

#### 2. POST /questions
- **기능**: 사용자 답변 처리 및 문서 생성
- **입력 파라미터**: 
  - questions_1 ~ questions_5 (사용자 답변)
- **처리 과정**:
  - 답변 데이터 수집 및 정리
  - AI를 통한 섹션 생성
  - TAM/SAM/SOM 데이터 생성
  - 임시 문서 및 PDF 생성
- **응답**: HTMLResponse (index.html)
- **생성 데이터**:
  - generated_sections (섹션별 텍스트)
  - generated_sections_TAM (시장 분석 데이터)
  - pdf_filename (생성된 PDF 파일명)

#### 3. GET /get_template_images
- **기능**: 템플릿 이미지 목록 제공
- **입력 파라미터**: folder (이미지 폴더 경로)
- **응답**: JSONResponse (이미지 파일 목록)
- **처리 과정**: 지정된 폴더의 이미지 파일 검색 및 URL 생성

#### 4. POST /
- **기능**: 최종 문서 생성
- **입력 파라미터**:
  - file: UploadFile (선택적 파일 업로드)
  - section_order: str (섹션 순서)
  - selected_layout: str (선택된 레이아웃)
- **처리 과정**:
  - 이미지 업로드 처리
  - 섹션별 텍스트 및 이미지 결합
  - DOCX 및 PDF 문서 생성
- **응답**: HTMLResponse (result.html)

#### 5. GET /result
- **기능**: 결과 페이지 표시
- **입력 파라미터**:
  - filename: str (DOCX 파일명)
  - pdf_filename: str (PDF 파일명)
- **응답**: HTMLResponse (result.html)

## 2. prompt_generator.py (AI 텍스트 생성)

### 클래스: PromptGenerator

#### 초기화
```python
def __init__(self, api_key):
    self.api_key = api_key
    self.client = AsyncOpenAI(api_key=api_key)
```

#### 주요 메서드

1. `generate_sections_from_answers(answers)`
- **기능**: 사용자 답변 기반 섹션 생성
- **입력**: answers (dict) - 질문별 답변
- **처리 과정**:
  - 섹션-질문 매핑 확인
  - 병렬 처리로 섹션별 내용 생성
  - AI 응답 처리 및 구조화
- **반환**: generated_sections (dict)

2. `process_section(tag, answers, generated_sections, section_to_keys)`
- **기능**: 개별 섹션 처리
- **입력**:
  - tag: str (섹션 태그)
  - answers: dict (답변 데이터)
  - generated_sections: dict (생성된 섹션)
  - section_to_keys: dict (섹션-키 매핑)
- **처리 과정**:
  - 프롬프트 생성
  - AI 응답 요청
  - 응답 파싱 및 저장

3. `create_tam_result(index, answers)`
- **기능**: 시장 분석 데이터 생성
- **입력**:
  - index: str (분석 유형)
  - answers: dict (답변 데이터)
- **처리 과정**:
  - 맞춤형 프롬프트 생성
  - AI를 통한 시장 데이터 분석
  - 결과 포맷팅

4. `extract_section_number(tag)`
- **기능**: 섹션 태그에서 숫자 추출
- **입력**: tag (str) - 섹션 태그
- **반환**: int (섹션 번호)

#### 테이블 처리

1. `create_dictionary_from_table(table, max_columns, index)`
- **기능**: 테이블 데이터 변환
- **입력**:
  - table: str (테이블 텍스트)
  - max_columns: int (최대 열 수)
  - index: str (인덱스 접두사)
- **반환**: dict (구조화된 테이블 데이터)

2. `preprocess_table(text, column_config)`
- **기능**: 테이블 텍스트 전처리
- **입력**:
  - text: str (원본 텍스트)
  - column_config: dict (열 설정)
- **반환**: str (전처리된 테이블 텍스트)

## 3. document_processor.py (문서 처리)

### 클래스: DocumentProcessor

#### 초기화
```python
def __init__(self, template_folder, upload_folder, static_dir, api_key):
    self.template_folder = template_folder
    self.upload_folder = upload_folder
    self.static_dir = static_dir
    self.api_key = api_key
```

#### 문서 생성

1. `generate_docx(generated_sections, image_list, is_temp, index)`
- **기능**: DOCX 문서 생성
- **입력**:
  - generated_sections: dict (섹션 내용)
  - image_list: list (이미지 정보)
  - is_temp: bool (임시 문서 여부)
  - index: int (템플릿 인덱스)
- **처리 과정**:
  - 템플릿 로드
  - 섹션 내용 삽입
  - 이미지 처리
  - 스타일 적용
- **반환**: str (생성된 파일 경로)

2. `convert_docx_to_pdf(docx_file_path)`
- **기능**: DOCX를 PDF로 변환
- **입력**: docx_file_path (str)
- **반환**: str (PDF 파일 경로)

#### 문서 내용 처리

1. `process_element(element, parent, style_mapping)`
- **기능**: 마크다운 요소 처리
- **입력**:
  - element: dict (마크다운 요소)
  - parent: Document (상위 문서 객체)
  - style_mapping: dict (스타일 매핑)
- **처리 과정**:
  - 요소 타입 확인
  - 스타일 적용
  - 하위 요소 재귀 처리

2. `parse_markdown_and_insert(markdown_text, parent, style_mapping)`
- **기능**: 마크다운 파싱 및 삽입
- **입력**:
  - markdown_text: str (마크다운 텍스트)
  - parent: Document (문서 객체)
  - style_mapping: dict (스타일 매핑)
- **처리 과정**:
  - 마크다운 파싱
  - 요소별 처리
  - 문서 삽입

#### 유틸리티 기능

1. `init_document_styles(document)`
- **기능**: 문서 스타일 초기화
- **입력**: document (Document)
- **처리**: 기본 스타일, 폰트, 여백 설정

2. `clean_empty_rows(document, start_page)`
- **기능**: 빈 행 제거
- **입력**:
  - document: Document
  - start_page: int
- **처리**: 지정 페이지 이후 빈 행 제거

3. `validate_image_path(image_path)`
- **기능**: 이미지 경로 검증
- **입력**: image_path (str)
- **반환**: bool (유효성 여부)

4. `cleanup_temporary_files(file_paths)`
- **기능**: 임시 파일 정리
- **입력**: file_paths (list)
- **처리**: 임시 파일 삭제

# 사업계획서 생성 시스템 수정 가이드

## 1. 레이아웃 선택 관련 수정하기

레이아웃 선택 화면에서 보이는 옵션의 개수를 수정하고 싶을 때:

1. index.html 파일을 열어주세요.
2. Ctrl+F를 눌러서 'loadLayoutOptions'를 검색해주세요.
3. 아래 코드를 찾아서 숫자를 원하는 만큼 추가/삭제해주세요:

```javascript
var layouts = [1, 2, 3];  // 여기서 [1, 2, 3, 4, 5] 처럼 숫자를 추가하면 됩니다
```

4. static/layout 폴더에 가서 추가한 숫자에 맞는 PDF 파일을 넣어주세요
   - 예: 4를 추가했다면 4.pdf 파일이 필요합니다
   - 파일 이름은 반드시 순서대로 된 숫자여야 합니다 (1.pdf, 2.pdf, 3.pdf ...)

5. /libs/document_processor.py 파일을 열어서 아래 부분을 찾아주세요:

```python
if index == 1:
    template_path = os.path.join(self.TEMPLATE_FOLDER, 'documents_tag_meating_resection.docx')
elif index == 2:
    template_path = os.path.join(self.TEMPLATE_FOLDER, 'documents_tag_meating_resection.docx')
elif index == 3:
    template_path = os.path.join(self.TEMPLATE_FOLDER, 'documents_tag_meating_resection.docx')
else:
    template_path = os.path.join(self.TEMPLATE_FOLDER, 'documents_tag_meating_resection.docx')
```

여기에 새로운 레이아웃을 추가하려면 elif 문을 새로 넣으면 됩니다:
```python
elif index == 4:
    template_path = os.path.join(self.TEMPLATE_FOLDER, '원하는문서이름.docx')
```

## 2. TAM/SAM/SOM 및 다른 템플릿 수정하기

1. 새로운 template_tag를 추가하고 싶을 때:
   - main.py 파일을 열어서 template_tags = [] 부분을 찾습니다
   - 리스트 안에 새로운 태그를 추가합니다
   예시: 'SECTION11-A3' 같은 새로운 태그 추가

2. 템플릿 파일 준비:
   - /static/image_templates/ 폴더에 새로운 태그 이름으로 폴더를 만듭니다
   - 또는 기존 태그 폴더에 새로운 템플릿을 추가합니다
   - 중요: 한 템플릿당 .jpg와 .docx 파일이 반드시 쌍으로 있어야 하고, 두 파일의 이름이 같아야 합니다

## 3. 프롬프트 태그 시스템 수정하기

libs/prompt_generator.py 파일에서:

```python
pattern = r'(<S1a\(\d+\)>)’ 
# pattern = r'(<P\d+>)’  # 이 부분을 수정하면 태그 형식을 바꿀 수 있습니다

if re.match(r'<S1a\(\d+\)>', part):
# if re.match(r'<P\d+>', part):  # P 태그인 경우 
```

참고: 같은 섹션 안에서 <P1>,<P2>,<P3>,<P1>,<P2>,<P3> 같은 형식으로 반복되어도 시스템이 잘 작동합니다.

## 4. 프롬프트 수정하기

1. TAM/SAM/SOM 관련 프롬프트 수정:
   - create_tam_result 함수에서 수정
   - 'TAM', 'TAM2' 등의 index에 따라 다른 프롬프트 설정 가능

2. 섹션 관련 프롬프트 수정:
   - create_prompt_for_section 함수에서 수정
   - tag 별로 다른 프롬프트 설정 가능

3. 표 관련 설정:
   - 여러 개의 표: 'TABLE1' 형식 사용
   - 한 개의 표: 'TABLE2' 형식 사용
   - 각 표의 열 개수는 max_columns 값으로 조정

4. 큰 섹션 태그가 바뀔 때:
   - generate_sections_from_answers 함수의 section_tags 리스트 수정 필요

5. 섹션 분리가 달라질 때:
   - section_to_keys의 매칭 수정
   예시:
   ```python
   'SECTION1-A1': ['SECTION1-A1', 'SECTION1-A4', 'SECTION1-A5', 'SECTION1-A8']
   ```
   이렇게 하면 SECTION1-A1의 내용이 4개 부분으로 나뉘어 저장됩니다.

## 5. 양식 수정하기

1. 텍스트 양식 수정:
   - prompt_generator.py의 section_to_keys 매핑 수정

2. 템플릿 태그 수정:
   - questions 함수의 template_tags 리스트 수정
   - image_templates 폴더 구조도 같이 수정

3. 이미지 태그 수정:
   - questions 함수의 image_tags 리스트 수정

4. 전체 양식 파일 수정:
   - 새 양식 파일을 /static 폴더에 넣기
   - document_processor.py의 generate_docx 함수에서 파일명 수정
   - if/elif는 레이아웃 선택용, else는 기본 선택용입니다

## 6. 웹페이지 로고 수정 관련 설명

1. /templates/index.html 상에 다음 코드 부분을 수정해야합니다.
```python
<h1 class="logo"><a href="/"><img src="/static/images/layout/logo-c.png" alt="data linker"></a></h1>
```
여기 코드의 src 경로를 바꿔주시고 해당 폴더에 새로운 로고 png 파일을 삽입해주세요. (alt=’‘) 내용도 같이 수정해주셔야 합니다!

2. 파비콘(브라우저 탭에 표시되는 작은 아이콘)도 변경 시에도 다음 코드 부분을 수정해야 합니다. 
```python
<link rel="shortcut icon" type="image/x-icon" 
href="/static/images/favicon.ico" />
```

# 주의 사항

#### 1. 같은 템플릿 넣으면 파일 손상됨 - 템플릿 선택 시 무조건 다른 docx 파일 템플릿이 들어가야함.

#### 2. 코드 수정 시 무조건 백업본 생성하기 - 조금 수정하시더라도 아예 같은 파일을 통째로 복사본을 만드시거나 드래그 후 'ctrl+/' 로 주석 처리 후 수정 코드 같이 입력해서 유지 보수에 적절하게 작업하시는게 좋습니다.

#### 3. http://127.0.0.1:5000/ 로 접속 가능합니다! 파이썬의 경우 터미널 창에 python main.py 실행 후 http://0.0.0.0:5000 로 웹페이지 실행 후 링크 수정 혹은 바로 링크 웹페이지에 입력 후 접속