#API Key 저장을 위한 os 라이브러리 호출
import os

import stock_info_crawling_function
import stock_info_prompt

from langchain_openai import ChatOpenAI



#OpenAI API키 저장
os.environ["OPENAI_API_KEY"] = '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'


llm = ChatOpenAI(
    model_name="gpt-3.5-turbo"
)
question = function.get_yearly_close_price() + f"는 {function.start_date}부터 {function.end_date}까지 삼성전자의 주식가격이야." + prompt.getPrompt()
#question = function.get_yearly_close_price() + f"는 {function.start_date}부터 {function.end_date}까지 삼성전자의 주식가격이야." + prompt.getPredictPrompt()
answer = llm.predict(question)

print(answer)
