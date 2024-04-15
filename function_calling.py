import openai
import json


# Example dummy function hard coded to return the same weather
# In production, this could be your backend API or an external API
def get_finance(company, unit="test"):
    
    print("재무재표 : " + company)
    
    return company

def get_news(company, unit="test"):

    print("뉴스요약 : " + company)
    
    return company

def get_stock(company, unit="test"):

    print("주식현황 : " + company)
    
    return company

def run_conversation():
    # Step 1: send the conversation and available functions to GPT
    messages = [{"role": "user", "content": "삼성전자 이번주 주식 변동폭 좀 알려줘"}]
    functions = [
        {
            "name": "get_finance",
            "description": "Analyze other financial statements of a specific company.",
            "parameters": {
                "type": "object",
                "properties": {
                    "company": {
                        "type": "string",
                        "description": "Company's name, e.g. 삼성전자, LG전자, LG유플러스",
                    },
                    "unit": {"type": "string", "enum": ["company"]},
                },
                "required": ["company"],
            },
        },
        {
            "name": "get_news",
            "description": "Search and summarize stock news of a specific company.",
            "parameters": {
                "type": "object",
                "properties": {
                    "company": {
                        "type": "string",
                        "description": "Company's name, e.g. 삼성전자, LG전자, LG유플러스",
                    },
                    "unit": {"type": "string", "enum": ["company"]},
                },
                "required": ["company"],
            },
        },
        {
            "name": "get_stock",
            "description": "Analyzing the stock price and status of a specific company",
            "parameters": {
                "type": "object",
                "properties": {
                    "company": {
                        "type": "string",
                        "description": "Company's name, e.g. 삼성전자, LG전자, LG유플러스",
                    },
                    "unit": {"type": "string", "enum": ["company"]},
                },
                "required": ["company"],
            },
        }
    ]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-1106",
        messages=messages,
        functions=functions,
        function_call="auto",  # auto is default, but we'll be explicit
    )
    response_message = response["choices"][0]["message"]

    # Step 2: check if GPT wanted to call a function
    if response_message.get("function_call"):
        # Step 3: call the function
        # Note: the JSON response may not always be valid; be sure to handle errors
        available_functions = {
            "get_finance": get_finance,
            "get_news": get_news,
            "get_stock": get_stock
        }  # only one function in this example, but you can have multiple
        function_name = response_message["function_call"]["name"]
        fuction_to_call = available_functions[function_name]
        function_args = json.loads(response_message["function_call"]["arguments"])
        function_response = fuction_to_call(
            company=function_args.get("company"),
            unit=function_args.get("unit"),
        )
        print(f"function_name = {function_name}")
        print(f"fuction_to_call = {fuction_to_call}")
        print(f"function_args = {function_args}")
        print(f"function_response = {function_response}")
        # Step 4: send the info on the function call and function response to GPT
        messages.append(response_message)  # extend conversation with assistant's reply
        messages.append(
            {
                "role": "function",
                "name": function_name,
                "content": function_response,
            }
        )  # extend conversation with function response
#         second_response = openai.ChatCompletion.create(
#             model="gpt-3.5-turbo-0613",
#             messages=messages,
#         )  # get a new response from GPT where it can see the function response
        return ""


print(run_conversation())