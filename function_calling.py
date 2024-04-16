import inspect
import json
import os

from dotenv import load_dotenv
from openai import OpenAI

# 환경변수 로드
load_dotenv()


# client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


def get_finance(company, unit="test"):
    # print("재무정보 요약 : " + company)
    search_type = '재무정보 요약'
    return search_type, company


def get_news(company, unit="test"):
    # print("종목뉴스 요약 : " + company)
    search_type = '종목뉴스 요약'
    return search_type, company


def get_stock(company, unit="test"):
    # print("주식정보 분석 : " + company)
    search_type = '주식정보 분석'
    return search_type, company


available_functions = {
    "get_finance": get_finance,
    "get_news": get_news,
    "get_stock": get_stock
}


# 함수에 제공되는 매개변수가 맞는지 검수하는 함수
def check_args(function, args):
    sig = inspect.signature(function)
    params = sig.parameters
    for name in args:
        if name not in params:
            return False
    for name, param in params.items():
        if param.default is param.empty and name not in args:
            return False
    return True


def run_conversation(user_input):
    # Step 1: send the conversation and available functions to GPT
    messages = []
    messages.append({"role": "user", "content": user_input})
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_finance",
                "description": "Be sure to analyze the company's financial information, excluding stock information.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "company": {
                            "type": "string",
                            "description": "Company's name, e.g. 삼성전자, LG전자, LG유플러스",
                        }
                    },
                    "required": ["company"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_news",
                "description": "Search and summarize stock news of a specific company.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "company": {
                            "type": "string",
                            "description": "Company's name, e.g. 삼성전자, LG전자, LG유플러스",
                        }
                    },
                    "required": ["company"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_stock",
                "description": "Analyzing the stock price and status of a specific company",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "company": {
                            "type": "string",
                            "description": "Company's name, e.g. 삼성전자, LG전자, LG유플러스",
                        }
                    },
                    "required": ["company"]
                }
            }
        }
    ]
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )
    # print(response)

    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls
    if tool_calls:
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            # verify function exists
            if function_name not in available_functions:
                return "Function " + function_name + " does not exist"
            fuction_to_call = available_functions[function_name]
        function_args = json.loads(tool_call.function.arguments)
        if check_args(fuction_to_call, function_args) is False:
            return "Invalid number of arguments for function: " + function_name
        function_response = fuction_to_call(**function_args)
        company = json.loads(response_message.tool_calls[0].function.arguments)['company']
        function_name = response_message.tool_calls[0].function.name
        content = None
    else:
        function_name = None
        company = None
        content = response.choices[0].message.content

    return function_name, company, content


msg = '안녕하세요'
print(run_conversation(msg))
