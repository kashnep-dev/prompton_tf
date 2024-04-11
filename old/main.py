#API Key 저장을 위한 os 라이브러리 호출
import os

import function
import datetime
import prompt
import re

from langchain_openai import ChatOpenAI


#OpenAI API키 저장
os.environ["OPENAI_API_KEY"] = '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'


# 기본정보(사용자 수정 항목)
start_date = "2024-04-01"
end_date = "2024-04-11"
today = datetime.datetime.now().date()
llm = ChatOpenAI(
    model_name="gpt-3.5-turbo"
)


# 질문 시작
ques = "현재 LGU+의 주식상황을 알려줘"
company_name = function.get_company_name(ques)
print("company_name : " + company_name)
#company_code = function.get_company_code(company_name)
company_code_with_text = function.get_company_code(company_name)
print("company_code_with_text : " + company_code_with_text)
company_code = re.findall(r'\d+', company_code_with_text)
print("company_code : " + company_code[0])
question = (function.get_yearly_close_price(company_code)
            + f"는 {start_date}부터 {end_date}까지 {company_name}의 주식가격이야. "
            + prompt.getPrompt(company_code, start_date, end_date))
answer = llm.predict(question)

print(answer)

