from openai import AsyncOpenAI
import asyncio
import json
import re

class PromptGenerator:
    def __init__(self, api_key):
        self.client = AsyncOpenAI(api_key=api_key)
        # 초기화 코드

    async def generate_sections_from_answers(self, answers):
        generated_sections = {}
        
        section_tags = ['SECTION1-A1', 'SECTION2-A1', 'SECTION3-A1', 'SECTION4-A1', 'SECTION5-A1', 'SECTION6-A1', 'SECTION10-A1', 'SECTION11-A1','TABLE1','TABLE2']
        
        section_to_keys = {
            'SECTION1-A1': ['SECTION1-A1', 'SECTION1-A4', 'SECTION1-A5', 'SECTION1-A8'],
            'SECTION2-A1': ['SECTION2-A1', 'SECTION2-A4', 'SECTION2-A5', 'SECTION2-A8'],
            'SECTION3-A1': ['SECTION3-A1', 'SECTION3-A4', 'SECTION3-A5', 'SECTION3-A8'],
            'SECTION4-A1': ['SECTION4-A1', 'SECTION4-A4', 'SECTION4-A5', 'SECTION4-A8'],
            'SECTION5-A1': ['SECTION5-A1', 'SECTION5-A4'],
            'SECTION6-A1': ['SECTION6-A1', 'SECTION6-A3', 'SECTION6-A4', 'SECTION6-A6', 'SECTION6-A7', 'SECTION6-A9'],
            'SECTION8-A1': ['SECTION8-A1', 'SECTION8-A4', 'SECTION8-A5', 'SECTION8-A8'],
            'SECTION10-A1': ['SECTION10-A2', 'SECTION10-A4'],
            'SECTION11-A1': ['SECTION11-A1', 'SECTION11-A2', 'SECTION11-A3', 'SECTION11-A4', 'SECTION11-A5', 'SECTION11-A6'],
        }

        # 병렬 처리를 위해 각 섹션에 대한 작업을 생성
        tasks = [asyncio.create_task(self.process_section(tag, answers, generated_sections, section_to_keys)) for tag in section_tags]
        
        # 모든 작업 완료 대기
        await asyncio.gather(*tasks)
        
        print('here generted_sections result')
        print(generated_sections)

        return generated_sections
    
    def save_content(self, temp_content, current_key, generated_sections):
            if current_key in generated_sections:
                generated_sections[current_key]['text'] += f" {temp_content.strip()}"
            else:
                generated_sections[current_key] = {'text': temp_content.strip(), 'image': None}

    async def process_section(self, tag, answers, generated_sections, section_to_keys ):
        prompt = await self.create_prompt_for_section(tag, answers)
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}]
            )
            if response:
                generated_text = response.choices[0].message.content.strip()
                
            print(f'here {tag} response')
            print(generated_text) 

            if tag in section_to_keys:
                pattern = r'(<P\d+>)'
                # pattern = r'(<P\d+>)'
                parts = re.split(pattern, generated_text)
                if parts:
                    parts = [part.strip() for part in parts if part.strip()]

                keys = section_to_keys[tag]
                temp_content = ""
                key_index = 0

                for part in parts:
                    if re.match(r'(<P\d+>)', part):
                    # if re.match(r'<P\d+>', part):  # P 태그인 경우
                        if temp_content:
                            self.save_content(temp_content, keys[min(key_index, len(keys) - 1)], generated_sections)
                            key_index += 1
                        temp_content = part
                    else:
                        temp_content += f" {part}"

                if temp_content:
                    self.save_content(temp_content, keys[min(key_index, len(keys) - 1)], generated_sections)
                        
            elif tag == 'TABLE1':
                input_text = generated_text
                tables_raw = self.preprocess_table(input_text, column_config=None)
                    
                valid_tables = {name: data for name, data in tables_raw.items() if data}

                if valid_tables:
                    tables_list = list(valid_tables.values())
                    
                    first_table = tables_list[0] if len(tables_list) > 0 else []
                    first_dictionary = self.create_dictionary_from_table(first_table, max_columns=4, index=1)
                    
                    second_table = tables_list[1] if len(tables_list) > 1 else []
                    second_dictionary = self.create_dictionary_from_table(second_table, max_columns=4, index=2)
                    
                    third_table = tables_list[2] if len(tables_list) > 2 else []
                    third_dictionary = self.create_dictionary_from_table(third_table, max_columns=3, index=3)
                    
                    for dictionary in [first_dictionary, second_dictionary, third_dictionary]:
                        for key, value in dictionary.items():
                            if key not in generated_sections:
                                generated_sections[key] = {'text': value, 'image': None}
                else:
                    print("No valid table data found")
            
            elif tag == 'TABLE2':
                input_text = generated_text
                tables_raw = self.preprocess_table(input_text, column_config=None)

                valid_tables = {name: data for name, data in tables_raw.items() if data}

                if valid_tables:
                    tables_list = list(valid_tables.values())
                    
                    first_table = tables_list[0] if len(tables_list) > 0 else []
                    
                    if first_table:
                        first_dictionary = self.create_dictionary_from_table(first_table, max_columns=4, index=4)
                        for dictionary in [first_dictionary]:
                            for key, value in dictionary.items():
                                if key not in generated_sections:
                                    generated_sections[key] = {'text': value, 'image': None}
                    else:
                        print("No first table data found")
                else:
                    print("No valid table data found")
                                
            else:
                generated_sections[tag] = {'text': generated_text, 'image': None}
        except Exception as e:
            print(f"섹션 {tag}의 내용 생성 중 오류 발생: {e}")
            generated_sections[tag] = {'text': '', 'image': None}

    async def create_tam_result(self, index ,answers):
        generated_tam = {}
        if index == 'TAM':
            prompt = (
                    f"1. 역할\n"
                    f"1-1. 너는 정부지원사업 \"창업패키지\" 서류를 전문적으로 작성하는 10년차 컨설턴트야.\n"
                    f"1-2. 내가 입력하는 질문에 따라 사업계획서를 작성해야 해. 잘 작성하면 돈을 줄거야.\n\n"
                    f"2. 작성 방법\n"
                    f"TAM (Total Addressable Market)\n"
                    f"definition: \"전체 접근 가능한 시장 규모를 정의하고 계산합니다. 이는 제품이나 서비스가 이론적으로 도달할 수 있는 모든 잠재 고객을 포함합니다.\"\n"
                    f"calculation:\n"
                    f"  market_scope: \"제품 또는 서비스가 관련이 있는 모든 지역, 연령대, 사용자 유형을 포함합니다.\"\n"
                    f"  estimated_size: \"총 금액 또는 총 인구 수\"\n\n"
                    f"SAM (Serviceable Available Market)\n"
                    f"definition: \"실제로 서비스할 수 있는 시장의 규모를estimated_size 정의하고 계산합니다. 이는 제품이나 서비스가 접근 가능하고 경제적으로 타당한 특정 지리적 위치나 대상 그룹을 포함합니다.\"\n"
                    f"calculation:\n"
                    f"  market_scope: \"실제로 서비스 가능한 지역, 특정 연령대, 사용자 유형을 포함합니다.\"\n"
                    f"  estimated_size: \"TAM에서 제외된 제한적인 범위의 금액 또는 인구 수\"\n\n"
                    f"SOM (Serviceable Obtainable Market)\n"
                    f"definition: \"단기적으로 회사가 실제로 얻을 수 있는 시장의 규모를 정의하고 계산합니다. 이는 회사의 마케팅 능력, 경쟁 상황, 현재 자원 등을 고려한 시장의 부분집합입니다.\"\n"
                    f"calculation:\n"
                    f"  market_scope: \"단기적으로 타겟팅 가능하고 서비스할 수 있는 특정 지역, 연령대, 사용자 유형을 포함합니다.\"\n"
                    f"  estimated_size: \"SAM에서 더욱 제한된 범위의 금액 또는 인구 수\"\n\n"
                    f"3. 작성 조건\n"
                    f"3-1. 질문한 항목에 대해서만 작성할 것\n"
                    f"3-2. 작성 방법에 있는 항목을 시장조사 데이터를 참조해 수치를 반드시 기입할 것\n"
                    f"3-4. 주장과 근거에 대해 참조하는 경우, 정량적 데이터에 대한 내용을 넣을 것\n"
                    f"3-5. 데이터를 참조할 때 실제로 있는 데이터를 참고할 것(거짓말 치지 말 것)\n\n"
                    f"4. 참고 항목"
                    f"4-1. {answers['question_5']} # 질문5\n\n"
                )
        elif index == 'TAM2':
            prompt = (
                    f"1. 역할\n"
                    f"1-1. 너는 정부지원사업 \"창업패키지\" 서류를 전문적으로 작성하는 10년차 컨설턴트야.\n"
                    f"1-2. 내가 입력하는 질문에 따라 사업계획서를 작성해야 해. 잘 작성하면 돈을 줄거야.\n\n"
                    f"2. 작성 방법\n"
                    f"TAM (Total Addressable Market)\n"
                    f"definition: \"전체 접근 가능한 시장 규모를 정의하고 계산합니다. 이는 제품이나 서비스가 이론적으로 도달할 수 있는 모든 잠재 고객을 포함합니다.\"\n"
                    f"calculation:\n"
                    f"  market_scope: \"제품 또는 서비스가 관련이 있는 모든 지역, 연령대, 사용자 유형을 포함합니다.\"\n"
                    f"  estimated_size: \"총 금액 또는 총 인구 수\"\n\n"
                    f"SAM (Serviceable Available Market)\n"
                    f"definition: \"실제로 서비스할 수 있는 시장의 규모를estimated_size 정의하고 계산합니다. 이는 제품이나 서비스가 접근 가능하고 경제적으로 타당한 특정 지리적 위치나 대상 그룹을 포함합니다.\"\n"
                    f"calculation:\n"
                    f"  market_scope: \"실제로 서비스 가능한 지역, 특정 연령대, 사용자 유형을 포함합니다.\"\n"
                    f"  estimated_size: \"TAM에서 제외된 제한적인 범위의 금액 또는 인구 수\"\n\n"
                    f"SOM (Serviceable Obtainable Market)\n"
                    f"definition: \"단기적으로 회사가 실제로 얻을 수 있는 시장의 규모를 정의하고 계산합니다. 이는 회사의 마케팅 능력, 경쟁 상황, 현재 자원 등을 고려한 시장의 부분집합입니다.\"\n"
                    f"calculation:\n"
                    f"  market_scope: \"단기적으로 타겟팅 가능하고 서비스할 수 있는 특정 지역, 연령대, 사용자 유형을 포함합니다.\"\n"
                    f"  estimated_size: \"SAM에서 더욱 제한된 범위의 금액 또는 인구 수\"\n\n"
                    f"3. 작성 조건\n"
                    f"3-1. 질문한 항목에 대해서만 작성할 것\n"
                    f"3-2. 작성 방법에 있는 항목을 시장조사 데이터를 참조해 수치를 반드시 기입할 것\n"
                    f"3-4. 주장과 근거에 대해 참조하는 경우, 정량적 데이터에 대한 내용을 넣을 것\n"
                    f"3-5. 데이터를 참조할 때 실제로 있는 데이터를 참고할 것(거짓말 치지 말 것)\n\n"
                    f"4. 참고 항목"
                    f"4-1. {answers['question_5']} # 질문5\n\n"
                )
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}]
            )
            if response:
                generated_text = response.choices[0].message.content.strip()
                
                # print(f'here response : {generated_text}') 수정 전
                print(f'here {index} response')
                print(generated_text)
                
                # 해당 코드 나중에 index 여러 개일 경우 주석 처리(#) 혹은 삭제 하셔야 합니다.
                generated_text = '1. 정보 제공 (TAM/SAM/SOM 데이터 관련 자료)\n\n' + generated_text
            
                generated_tam[index] = {'text': generated_text, 'image': None}
                
        except Exception as e:
            print(f"내용 생성 중 오류 발생: {e}")
            generated_tam[index] = {'text': ''}

        return generated_tam

    async def create_prompt_for_section(self, tag, answers):
        # if tag == 'SECTION1-A1':
        if tag == 'SECTION1-A1':
            prompt = (
                f"1. 역할\n"
                f"1-1. 너는 정부지원사업 \"창업패키지\" 서류를 전문적으로 작성하는 10년차 컨설턴트야.\n"
                f"1-2. 내가 입력하는 질문에 따라 사업계획서를 작성해야 해. 잘 작성하면 돈을 줄거야.\n\n"
                f"2. 작성 방법\n"
                f"2-1. 질문에 대한 답변은 아래의 문장 구조에 맞게 작성돼.\n"
                f"  - <P1> 제목 1\n"
                f"  - <P2> 내용 1\n"
                f"  - <P3> 제목 2\n"
                f"  - <P4> 내용 2\n"        
                f"2-2. 제목은 25자 이하로 작성, 내용은 100-140자로 작성해\n"
                f"3. 작성 조건\n"
                f"3-1. 질문한 항목에 대해서만 작성할 것\n"
                f"3-2. 답변은 두괄식으로 작성할 것\n"
                f"3-3. 제목은 내용을 요약한 슬로건으로 작성할 것\n"
                f"3-4. 주장과 근거에 대한 사회적 근거(뉴스기사, 통계 등)나 과학적 근거(논문 등)를 참조하는 경우 주석으로 자료의 출처(제목, 발간처, 연도, 링크)를 첨부할 것\n"
                f"3-5. 주장과 근거에 대해 참조하는 경우, 정량적 데이터에 대한 내용을 넣을 것\n"
                f"3-6. 데이터를 참조할 때 실제로 있는 데이터를 참고할 것\n\n"
                f"4. 참고 항목\n"
                f"4-1. {answers['question_1']} #질문 1\n"
                f"4-2. {answers['question_2']} #질문 2\n\n"
                f"위 내용을 참조해서 \"제품 서비스의 배경 및 필요성\"를 작성해줘.\n"
                f"\"제품 서비스의 배경 및 필요성\"에 대한 설명은 아래와 같아. 해당 설명을 각각의 항목으로 구분하지 말고, 참고만 진행해.\n"
                f"- 아이디어를 제품·서비스로 개발 또는 구체화하게 된 내부적·외부적 동기, 목적 등\n"
                f"- 아이디어를 제품·서비스로 개발 또는 구체화 필요성, 주요 문제점 및 해결방안 등\n"
                f"- 내·외부적 동기, 필요성 등에 따라 도출된 제품·서비스의 혁신성, 유망성 등"
            )
            
        elif tag == 'SECTION2-A1':
            prompt = (
                f"1. 역할\n"
                f"1-1. 너는 정부지원사업 \"창업패키지\" 서류를 전문적으로 작성하는 10년차 컨설턴트야.\n"
                f"1-2. 내가 입력하는 질문에 따라 사업계획서를 작성해야 해. 잘 작성하면 돈을 줄거야.\n\n"
                f"2. 작성 방법\n"
                f"2-1. 질문에 대한 답변은 아래의 문장 구조에 맞게 작성돼.\n"
                f"  - <P1> 제목 1\n"
                f"  - <P2> 내용 1\n"
                f"  - <P3> 제목 2\n"
                f"  - <P4> 내용 2\n"        
                f"2-2. 제목은 25자 이하로 작성, 내용은 100-140자로 작성해\n"
                f"3. 작성 조건\n"
                f"3-1. 질문한 항목에 대해서만 작성할 것\n"
                f"3-2. 작성 방법에 있는 항목을 시장조사 데이터를 참조해 수치를 반드시 기입할 것\n"
                f"3-4. 주장과 근거에 대해 참조하는 경우, 정량적 데이터에 대한 내용을 넣을 것\n"
                f"3-5. 데이터를 참조할 때 실제로 있는 데이터를 참고할 것(거짓말 치지 말 것)\n\n"
                f"4. 참고 항목"
                f"4-1. {answers['question_5']} # 질문5\n\n"
                f"위 내용을 참조해서 \"창업아이템 목표시장(고객) 현황 분석\"를 작성해줘. "
                f"\"창업아이템 목표시장(고객) 현황 분석\"에 대한 설명은 아래와 같아. 해당 설명을 각각의 항목으로 구분하지 말고, 참고만 진행해.\n"
                f" - 제품·서비스로 개발/구체화 배경 및 필요성에 따라 정의된 목표시장(고객) 설정\n"
                f" - 정의된 목표시장(고객) 규모, 경쟁 강도, 기타 특성 등 주요 현황"
            )

        elif tag == 'SECTION3-A1':
            prompt = (
                f"1. 역할\n"
                f"1-1. 너는 정부지원사업 \"창업패키지\" 서류를 전문적으로 작성하는 10년차 컨설턴트야.\n"
                f"1-2. 내가 입력하는 질문에 따라 사업계획서를 작성해야 해. 잘 작성하면 돈을 줄거야.\n\n"
                f"2. 작성 방법\n"
                f"2-1. 질문에 대한 답변은 아래의 문장 구조에 맞게 작성돼.\n"
                f"  - <P1> 제목 1\n"
                f"  - <P2> 내용 1\n"
                f"  - <P3> 제목 2\n"
                f"  - <P4> 내용 2\n"        
                f"2-2. 제목은 25자 이하로 작성, 내용은 100-140자로 작성해\n"
                f"3. 작성 조건\n"
                f"3-1. 질문한 항목에 대해서만 작성할 것\n"
                f"3-2. 작성 방법에 있는 항목을 시장조사 데이터를 참조해 수치를 반드시 기입할 것\n"
                f"3-4. 주장과 근거에 대해 참조하는 경우, 정량적 데이터에 대한 내용을 넣을 것\n"
                f"3-5. 데이터를 참조할 때 실제로 있는 데이터를 참고할 것(거짓말 치지 말 것)\n\n"
                f"4. 참고 항목"
                f"4-1. {answers['question_5']} # 질문5\n\n"
                f"위 내용을 참조해서 \"창업아이템의 현황(준비정도)\"를 작성해줘. "
                f"\"창업아이템의 현황(준비정도)\"에 대한 설명은 아래와 같아. 해당 설명을 각각의 항목으로 구분하지 말고, 참고만 진행해.\n"
                f" - 사업 신청 시점의 제품·서비스의 개발 단계 및 구체화 현황\n"
                f" - 사업 신청 시점의 제품·서비스의 사용/이용 방법\n"
                f" - 정부지원금 활용을 통한 제품 개발 목표"
            )

        elif tag == 'SECTION4-A1':
            prompt = (
                f"1. 역할\n"
                f"1-1. 너는 정부지원사업 \"창업패키지\" 서류를 전문적으로 작성하는 10년차 컨설턴트야.\n"
                f"1-2. 내가 입력하는 질문에 따라 사업계획서를 작성해야 해. 잘 작성하면 돈을 줄거야.\n\n"
                f"2. 작성 방법\n"
                f"2-1. 질문에 대한 답변은 아래의 문장 구조에 맞게 작성돼.\n"
                f"  - <P1> 제목 1\n"
                f"  - <P2> 내용 1\n"
                f"  - <P3> 제목 2\n"
                f"  - <P4> 내용 2\n"        
                f"2-2. 제목은 25자 이하로 작성, 내용은 100-140자로 작성해\n"
                f"3. 작성 조건\n"
                f"3-1. 질문한 항목에 대해서만 작성할 것\n"
                f"3-2. 답변은 두괄식으로 작성할 것\n"
                f"3-3. 제목은 내용을 요약한 슬로건으로 작성할 것\n"
                f"3-4. 주장과 근거에 대한 사회적 근거(뉴스기사, 통계 등)나 과학적 근거(논문 등)를 참조하는 경우 주석으로 자료의 출처(제목, 발간처, 연도, 링크)를 첨부할 것\n"
                f"3-5. 주장과 근거에 대해 참조하는 경우, 정량적 데이터에 대한 내용을 넣을 것\n"
                f"3-6. 데이터를 참조할 때 실제로 있는 데이터를 참고할 것(거짓말 치지 말 것)\n\n"
                f"4. 참고 항목"
                f"4-1. {answers['question_5']} # 질문5\n\n"
                f"위 내용을 참조해서 \"창업아이템의 실현 및 구체화 방안\"를 작성해줘.\n"
                f"창업아이템의 실현 및 구체화 방안에 대한 설명은 아래와 같아. 해당 설명을 각각의 항목으로 구분하지 말고, 참고만 진행해.\n"
                f"- 제품·서비스에 대한 개발 또는 구체화 방안 등\n"
                f"- 보유 역량 기반, 경쟁사 대비 제품·서비스 차별성 등\n"
                )
            
        elif tag == 'SECTION5-A1':
            prompt = (
                f"1. 역할\n"
                f"1-1. 너는 정부지원사업 \"창업패키지\" 서류를 전문적으로 작성하는 10년차 컨설턴트야.\n"
                f"1-2. 내가 입력하는 질문에 따라 사업계획서를 작성해야 해. 잘 작성하면 돈을 줄거야.\n\n"
                 f"2-1. 질문에 대한 답변은 아래의 문장 구조에 맞게 작성돼.\n"
                f"  - <P1> 제목 1\n"
                f"  - <P2> 내용 1\n"
                f"  - <P3> 제목 2\n"
                f"  - <P4> 내용 2\n"        
                f"2-2. 제목은 25자 이하로 작성, 내용은 100-140자로 작성해\n"
                f"3. 작성 조건\n"
                f"3-1. 질문한 항목에 대해서만 작성할 것\n"
                f"3-2. 답변은 두괄식으로 작성할 것\n"
                f"3-3. 제목은 내용을 요약한 슬로건으로 작성할 것\n"
                f"3-4. 주장과 근거에 대한 사회적 근거(뉴스기사, 통계 등)나 과학적 근거(논문 등)를 참조하는 경우 주석으로 자료의 출처(제목, 발간처, 연도, 링크)를 첨부할 것\n"
                f"3-5. 주장과 근거에 대해 참조하는 경우, 정량적 데이터에 대한 내용을 넣을 것\n"
                f"3-6. 데이터를 참조할 때 실제로 있는 데이터를 참고할 것(거짓말 치지 말 것)\n\n"
                f"4. 참고 항목"
                f"4-1. {answers['question_5']} # 질문5\n\n"
                f"위 내용을 참조해서 \"창업아이템 비즈니스 모델 및 사업화 추진 성과\"를 작성해줘."
                f"창업아이템 비즈니스 모델 및 사업화 추진 성과에 대한 설명은 아래와 같아. 해당 설명을 각각의 항목으로 구분하지 말고, 참고만 진행해.\n"
                f"- 제품·서비스의 수익화를 위한 수익모델(비즈니스 모델) 등  \n"
                )
    
        elif tag == 'SECTION6-A1':
            prompt = (
                f"1. 역할\n"
                f"1-1. 너는 정부지원사업 \"창업패키지\" 서류를 전문적으로 작성하는 10년차 컨설턴트야.\n"
                f"1-2. 내가 입력하는 질문에 따라 사업계획서를 작성해야 해. 잘 작성하면 돈을 줄거야.\n\n"
                f"2. 작성 방법\n"
                f"2-1. 질문에 대한 답변은 아래의 문장 구조에 맞춰 답변해해.\n"
                f"  - <P1> 제목 1\n"
                f"  - <P2> 내용 1\n"
                f"  - <P3> 제목 2\n"
                f"  - <P4> 내용 2\n"        
                f"  - <P5> 제목 3\n"
                f"  - <P6> 내용 3\n"     
                f"2-2. 제목은 25자 이하로 작성, 내용은 100-140자로 작성해\n"
                f"2-3. 밑줄은 빼줘\n\n"
                f"3. 작성 조건\n"
                f"3-1. 질문한 항목에 대해서만 작성할 것\n"
                f"3-2. 작성 방법에 있는 항목을 시장조사 데이터를 참조해 수치를 반드시 기입할 것\n"
                f"3-4. 주장과 근거에 대해 참조하는 경우, 정량적 데이터에 대한 내용을 넣을 것\n"
                f"3-5. 데이터를 참조할 때 실제로 있는 데이터를 참고할 것(거짓말 치지 말 것)\n"
                f"4. 참고 항목"
                f"4-1. {answers['question_5']} # 질문5\n\n"
                f"위 내용을 참조해서 창업아이템 사업화 추진 전략을 작성해줘."
                f"창업아이템 사업화 추진 전략에 대한 설명은 아래와 같아.  해당 설명을 각각의 항목으로 구분하지 말고, 참고만 진행해.\n"
                f" - 정의된 목표시장(고객) 확보 전략 및 수익화(사업화) 전략\n"
                f" - 협약기간 내 사업화 성과 창출 목표(매출, 투자, 고용 등)\n"
                f" - 목표시장(고객)에 진출하기 위한 구체적인 생산·출시 방안 등\n"
                f" - 협약기간 종료 후 사업 지속을 위한 전략(생존율 제고 전략) 등"
            )
            
        elif tag == 'TABLE1':
            prompt = (
                f"1. 역할\n"
                f"1-1. 너는 정부지원사업 \"창업패키지\" 서류를 전문적으로 작성하는 10년차 컨설턴트야.\n"
                f"1-2. 내가 입력하는 질문에 따라 사업계획서를 작성해야 해. 잘 작성하면 돈을 줄거야.\n\n"
                f"2. 작성 방법\n"
                f"하나의 문단은 아래와 같이 구성돼.\n"
                f"2-1. 사업추진 일정(전체 사업단계) 표, 구성: 순번, 추진내용, 추진 기간, 세부 내용으로 구성돼. 24년부터 최장 27년까지 상/하반기로 구분해서 작성해줘.\n"
                f"2-2. 사업추진일정(협약기간 내) 표, 구성: 순번, 추진내용, 추진 기간, 세부 내용으로 구성되며, 24년 4월부터 24년 12월까지 월별로 구분해서 작성해줘.\n"
                f"2-3. 정부지원사업비 집행계획 표, 구성: 비목, 산출근거, 정부지원사업비(원)으로 구성되며, 최대 1억원 한도로 작성해줘.\n"
                f"위 조건에 맞춰 총 세 가지 표를 8줄 씩 작성해.\n\n"
                f"3. 작성 조건\n"
                f"3-1. 질문한 항목에 대해서만 작성할 것\n"
                f"3-2. 데이터를 참조할 때 실제로 있는 데이터를 참고할 것(거짓말 치지 말 것)\n\n"
                f"4. 참고 항목\n"
                f"4-1. {answers['question_1']}  # 질문1\n"
                f"4-2. {answers['question_3']}  # 질문3\n\n"
                f"위 내용을 참조해서 \"사업추진 일정 및 자금 운용 계획\"를 작성해줘."
                f"사업추진 일정 및 자금 운용 계획에 대한 설명은 아래와 같아. 해당 설명을 각각의 항목으로 구분하지 말고, 참고만 진행해.\n"
                f"- 전체 사업단계 및 협약기간 내 목표와 이를 달성하기 위한 상세 추진 일정 등\n"
                f"- 사업추진에 필요한 정부지원사업비 집행계획 등\n"
                f"- 정부지원사업비 외 투자유치 등 구체적인 계획 및 전략\n"
                )
            
        elif tag == 'TABLE2':
            prompt = (
                f"1. 역할\n"
                f"1-1. 너는 정부지원사업 \"창업패키지\" 서류를 전문적으로 작성하는 10년차 컨설턴트야.\n"
                f"1-2. 내가 입력하는 질문에 따라 사업계획서를 작성해야 해. 잘 작성하면 돈을 줄거야.\n\n"
                f"2. 작성 방법\n"
                f"하나의 문단은 아래와 같이 구성돼.\n"
                f"2-1. 사업추진 일정(전체 사업단계) 표, 구성: 순번, 추진내용, 추진 기간, 세부 내용으로 구성돼. 25년부터 최장 29년까지 상/하반기로 구분해서 작성해줘.\n"
                f"위 조건에 맞춰 표를 8줄 작성해.\n\n"
                f"3. 작성 조건\n"
                f"3-1. 질문한 항목에 대해서만 작성할 것\n"
                f"3-2. 답변은 두괄식으로 작성할 것\n"
                f"3-3. 제목은 내용을 요약한 슬로건으로 작성할 것\n"
                f"3-4. 주장과 근거에 대한 사회적 근거(뉴스기사, 통계 등)나 과학적 근거(논문 등)를 참조하는 경우 주석으로 자료의 출처(제목, 발간처, 연도, 링크)를 첨부할 것\n"
                f"3-5. 주장과 근거에 대해 참조하는 경우, 정량적 데이터에 대한 내용을 넣을 것\n"
                f"3-6. 데이터를 참조할 때 실제로 있는 데이터를 참고할 것(거짓말 치지 말 것)\n\n"
                f"4. 참고 항목\n"
                f"4-1. {answers['question_1']}  # 질문1\n"
                f"4-2. {answers['question_3']}  # 질문3\n\n"
                f"위 내용을 참조해서 \"자금조달 계획\"을 작성해줘."
                )
            
        elif tag == 'SECTION10-A1':
            prompt = (
                f"1. 역할\n"
                f"1-1. 너는 정부지원사업 \"창업패키지\" 서류를 전문적으로 작성하는 10년차 컨설턴트야.\n"
                f"1-2. 내가 입력하는 질문에 따라 사업계획서를 작성해야 해. 잘 작성하면 돈을 줄거야.\n\n"
                f"2. 작성 방법\n"
                f"2-1. 질문에 대한 답변은 아래의 문장 구조에 맞게 작성돼.\n"
                f"  - <P1> 제목 1\n"
                f"  - <P2> 내용 1\n"
                f"  - <P3> 제목 2\n"
                f"  - <P4> 내용 2\n"          
                f"2-2. 제목은 25자 이하로 작성, 내용은 100-140자로 작성해\n"
                f"3. 작성 조건\n"
                f"3-1. 질문한 항목에 대해서만 작성할 것\n"
                f"3-2. 답변은 두괄식으로 작성할 것\n"
                f"3-3. 제목은 내용을 요약한 슬로건으로 작성할 것\n"
                f"4. 참고 항목"
                f"4-1. {answers['question_1']}  # 질문1\n"
                f"4-2. {answers['question_2']}  # 질문2\n"
                f"4-3. {answers['question_3']}  # 질문3\n"
                f"4-4. {answers['question_4']}  # 질문4\n"
                f"4-5. {answers['question_5']}  # 질문5\n\n"
                f"위 내용을 참조해서 \"기업구성 및 보유 역량\"을 작성해줘."
                )
        elif tag == 'SECTION11-A1':
            prompt = (
                f"1. 역할\n"
                f"1-1. 너는 정부지원사업 \"창업패키지\" 서류를 전문적으로 작성하는 10년차 컨설턴트야.\n"
                f"1-2. 내가 입력하는 질문에 따라 사업계획서를 작성해야 해. 잘 작성하면 돈을 줄거야.\n\n"
                f"2. 작성 방법\n"
                f"2-1. 질문에 대한 답변은 아래의 문장 구조에 맞게 작성돼.\n"
                f"  - <P1> 제목 1\n"
                f"  - <P2> 내용 1\n"
                f"  - <P3> 제목 2\n"
                f"  - <P4> 내용 2\n"        
                f"  - <P5> 제목 3\n"
                f"  - <P6> 내용 3\n"     
                f"2-2. 제목은 25자 이하로 작성, 내용은 100-140자로 작성해\n"
                f"각 문장 별 주제는 아래와 같아\n"
                f"1. 환경보호\n"
                f"2. 사회적가치\n"
                f"3. 투명한 지배구조\n\n"
                f"3. 작성 조건\n"
                f"3-1. 질문한 항목에 대해서만 작성할 것\n"
                f"3-2. 답변은 두괄식으로 작성할 것\n"
                f"3-3. 제목은 내용을 요약한 슬로건으로 작성할 것\n"
                f"3-4. 주장과 근거에 대한 사회적 근거(뉴스기사, 통계 등)나 과학적 근거(논문 등)를 참조하는 경우 주석으로 자료의 출처(제목, 발간처, 연도, 링크)를 첨부할 것\n"
                f"3-5. 주장과 근거에 대해 참조하는 경우, 정량적 데이터에 대한 내용을 넣을 것\n"
                f"3-6. 데이터를 참조할 때 실제로 있는 데이터를 참고할 것(거짓말 치지 말 것)\n\n"
                f"4. 참고 항목"
                f"4-1. {answers['question_1']}  # 질문1\n"
                f"4-2. {answers['question_2']}  # 질문2\n"
                f"4-3. {answers['question_3']}  # 질문3\n"
                f"4-4. {answers['question_4']}  # 질문4\n"
                f"4-5. {answers['question_5']}  # 질문5\n\n"
                f"위 내용을 참조해서 \"ESG 경영 실천 계획\"을 작성해줘."
                )
        else:
            pass
        return prompt

    def extract_section_number(self, tag):
        try:
            # 기존 로직
            section_part = tag.replace('SECTION', '')
            number_part = section_part.split('-')[0]
            import re
            numbers = re.findall(r'\d+', number_part)
            return int(numbers[0]) if numbers else 0
        except Exception as e:
            print(f"Warning: Could not extract number from tag '{tag}': {e}")
            return 0
        
    # 주어진 데이터를 처리하는 함수
    def create_dictionary_from_table(self, table, max_columns, index):
        result = {}
        key_prefix = "T"  # Key prefix
        if index == 1:
            key_counter = 1  # Start key counter from 1
        elif index == 2:
            key_counter = 101  # Start key counter from 100
        elif index == 3:
            key_counter = 201  # Start key counter from 200
        elif index == 4:
            key_counter = 301  # Start key counter from 200

        # 첫 번째 행에서 유효한 열 개수를 확인
        headers = table[0]
        valid_columns = headers[:max_columns]  # '세부 내용'까지의 열만 사용

        # 데이터 행에서 유효한 데이터만 추출
        for row in table[1:]:
            valid_row = row[:max_columns]  # 유효 열 개수만큼 데이터 추출
            for i, value in enumerate(valid_row):
                key = f"{key_prefix}{key_counter}"
                if value:
                    result[key] = value.strip()  # Key-Value 저장
                key_counter += 1

        return result
    
    def preprocess_table(self, text, column_config=None):
        """
        불규칙한 텍스트 데이터를 테이블 형식으로 전처리하며, 테이블별로 다른 열 개수를 허용합니다.
        - text: 입력 텍스트
        - column_config: 테이블별 열 개수를 지정하는 딕셔너리 (예: {'table1': 4, 'table2': 3})
        """
        if column_config is None:
            column_config = {}
        
        tables = {}
        current_table = None
        table_data = []

        for line in text.split("\n"):
            if line:
                line = line.strip()

            # 테이블 제목을 기준으로 섹션 구분
            if line.startswith("###") or line.startswith("**") or line.startswith("##"):
                # 새 테이블 시작 시 기존 테이블 저장
                if current_table:
                    tables[current_table] = table_data

                # 새로운 테이블 시작
                current_table = line.replace("###", "").replace("**", "").replace("##", "").strip()
                table_data = []  # 데이터 초기화

            # 테이블 데이터 처리
            elif "|" in line:
                # 행을 | 기준으로 나누고 양쪽 여백 제거
                row = [cell.strip() for cell in line.split("|")[1:-1]]

                # 구분선 제거
                if row and all(cell.startswith("-") for cell in row):
                    continue

                # 현재 테이블에 대한 열 개수 확인
                expected_columns = column_config.get(current_table, len(row))
                
                # 열 개수에 맞게 데이터 추가
                if row:
                    table_data.append(row[:expected_columns])

        # 마지막 테이블 저장
        if current_table:
            tables[current_table] = table_data

        return tables
        