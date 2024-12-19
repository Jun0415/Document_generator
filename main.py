import os
import uuid
import aiofiles
from openai import OpenAI, AsyncOpenAI
from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from werkzeug.utils import secure_filename

from jinja2 import FileSystemLoader, select_autoescape, StrictUndefined, BaseLoader
from jinja2 import Environment, FileSystemLoader

from libs.prompt_generator import PromptGenerator
from libs.document_processor import DocumentProcessor

# 비동기 마크다운 파서 관련 (필요 시)
from mistune import create_markdown
markdown_parser = create_markdown(renderer="ast", plugins=['strikethrough'])

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')

UPLOAD_FOLDER = os.path.join(STATIC_DIR, 'uploads')
IMAGE_FOLDER = os.path.join(STATIC_DIR, 'images')
TEMPLATE_FOLDER = STATIC_DIR

# /static 경로로 정적파일 서빙
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# 템플릿 로더 설정 (jinja2 비동기 환경)
templates = Environment(
    loader=FileSystemLoader(os.path.join(BASE_DIR, 'templates')),
    autoescape=select_autoescape(['html', 'xml']),
    enable_async=True,
    undefined=StrictUndefined
)

client = AsyncOpenAI(api_key="OPENAI API키를 넣어주세요.")

# 클래스 초기화
prompt_generator = PromptGenerator(api_key="OPENAI API키를 넣어주세요.")
document_processor = DocumentProcessor(TEMPLATE_FOLDER, UPLOAD_FOLDER, STATIC_DIR, api_key="OPENAI API키를 넣어주세요.")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # first.html 템플릿 렌더링
    template = templates.get_template('first.html')
    content = await template.render_async()
    return HTMLResponse(content=content, status_code=200)

@app.post("/questions")
async def questions(
    request: Request
):
    form = await request.form()
    answers = {}
    for i in range(1, 6):
        answers[f'question_{i}'] = form.get(f'question_{i}', '')

    # 섹션 생성
    generated_sections = await prompt_generator.generate_sections_from_answers(answers)
    
    #TAM,SAM,SOM 데이터 생성
    # generated_sections_TAM1 = await prompt_generator.create_tam_result('TAM', answers)
    # generated_sections_TAM1 = '1. 정보 제공 (TAM/SAM/SOM 데이터 관련 자료)\n\n' + generated_sections_TAM1
    # generated_sections_TAM2 = await prompt_generator.create_tam_result('TAM2', answers)
    # generated_sections_TAM2 = '2. 정보 제공2 (데이터 관련 자료)\n\n' + generated_sections_TAM2
    # generated_sections_TAM = generated_sections_TAM1 + "\n\n" + generated_sections_TAM2
    generated_sections_TAM = await prompt_generator.create_tam_result('TAM', answers)
        
    temp_docx_path, final_texts = await document_processor.generate_docx(generated_sections, image_list=None, is_temp=True, index = 1)
    temp_pdf_path = await document_processor.convert_docx_to_pdf(temp_docx_path)
        
    pdf_filename = os.path.basename(temp_pdf_path)
        
    final_texts_dict = {key: {"text": value} for key, value in final_texts.items()}

    # 세 그룹으로 분리
    template_tags = ['SECTION2-A2','SECTION2-A3','SECTION4-A6','SECTION4-A7','SECTION5-A2','SECTION5-A3','SECTION8-A2','SECTION8-A3']
    # text_tags = [tag for tag in final_texts.keys() if not tag.startswith('T')]
    text_tags = list(final_texts.keys())
    image_tags = ['SECTION1-A2','SECTION1-A3','SECTION1-A6','SECTION1-A7','SECTION2-A6','SECTION2-A7','SECTION2-A10','SECTION2-A11','SECTION2-A14','SECTION2-A15','SECTION3-A2','SECTION3-A3','SECTION3-A6','SECTION3-A7','SECTION3-A10','SECTION3-A11','SECTION3-A13','SECTION3-A14','SECTION3-A16','SECTION3-A17','SECTION4-A2','SECTION4-A3','SECTION6-A2','SECTION6-A5','SECTION6-A8','SECTION10-A1','SECTION10-A3','SECTION10-A4']
        
    combined_tags = template_tags + text_tags + image_tags
    combined_tags.sort(key=prompt_generator.extract_section_number)

    template = templates.get_template('index.html')
    html_content = await template.render_async(
        combined_tags=combined_tags,
        template_tags=template_tags,
        text_tags=text_tags,
        image_tags=image_tags,
        generated_sections=final_texts_dict,
        pdf_file=pdf_filename,
        generated_sections_TAM = generated_sections_TAM
    )

    return HTMLResponse(content=html_content, status_code=200)

@app.get("/get_template_images")
async def get_template_images(request: Request, folder: str):
    folder_path = os.path.join(STATIC_DIR, folder)
    image_files = []
    if os.path.exists(folder_path):
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                image_files.append(f"/static/{folder}/{filename}")
    return JSONResponse({'images': image_files})

@app.post("/")
async def index(
    request: Request,
    file: UploadFile = File(None),
    section_order: str = Form(None),
    selected_layout: str = Form(None)
):
    form = await request.form()
    
    section_order = form.get('section_order', '')
    
    if section_order:
        section_list = section_order.split(',')
        
    selected_layout = form.get('selected_layout', None)
    if selected_layout:
        print("선택된 레이아웃 번호:", selected_layout)

    image_list = []
    # 모든 폼 데이터를 순회하며 이미지 선택 항목 찾기
    for key in form.keys():
        if key.endswith('_selected_image'):
            image_path = form.get(key)
            if image_path:
                image_list.append({
                    'tag': key.replace('_selected_image', ''),
                    'path': image_path
                })
                
    if image_list:
        print("선택된 이미지들:", image_list)

    sections = {}
    for section_id in section_list:
        text = form.get(section_id, '')
        upload_key = f"{section_id}_image"
        upload_image = form.get(upload_key, None)
        image_path = None

        if upload_image and hasattr(upload_image, 'filename') and upload_image.filename != '':
            filename = secure_filename(f"{uuid.uuid4()}_{upload_image.filename}")
            save_path = os.path.join(UPLOAD_FOLDER, filename)
            async with aiofiles.open(save_path, 'wb') as out_file:
                content = await upload_image.read()
                await out_file.write(content)
            image_path = save_path

        sections[section_id] = {'text': text, 'image': image_path}
    
    print(f'generate before section : {sections}')

    output_file, _ = await document_processor.generate_docx(sections, image_list=image_list, index = selected_layout)
    if output_file:
        pdf_file = await document_processor.convert_docx_to_pdf(output_file)
        if pdf_file:
            file_url = f"/static/uploads/{os.path.basename(output_file)}"
            pdf_file_url = f"/static/uploads/{os.path.basename(pdf_file)}"
            template = templates.get_template('result.html')
            html_content = await template.render_async(file_url=file_url, pdf_file_url=pdf_file_url)
            return HTMLResponse(content=html_content, status_code=200)
        else:
            return JSONResponse({"error": "DOCX to PDF 변환 실패"}, status_code=500)
    else:
        return JSONResponse({"error": "DOCX 생성 실패"}, status_code=500)
    
@app.get("/result")
async def result(request: Request, filename: str, pdf_filename: str):
    if not filename or not pdf_filename:
        raise HTTPException(status_code=400, detail="잘못된 접근입니다.")

    file_url = f"/static/uploads/{filename}"
    pdf_file_url = f"/static/uploads/{pdf_filename}"
    template = templates.get_template('result.html')
    html_content = await template.render_async(file_url=file_url, pdf_file_url=pdf_file_url)
    return HTMLResponse(content=html_content, status_code=200)

if __name__ == '__main__':
    import uvicorn
    # uvicorn.run은 자체적으로 비동기로 동작하는 ASGI 서버를 실행
    uvicorn.run(app, host='0.0.0.0', port=5000)
    
    # http://127.0.0.1:5000/ 이 url로 접속 가능