import re
import time
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv
from langchain.schema import ChatMessage
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI

import prompt as pt
import search
from config import ls_configure
from function_calling import run_conversation
from predict import PatternFinder, get_company_code

# 환경변수 로드
load_dotenv()

# Langsmith 환경설정
client, run_collector, cfg = ls_configure()


# @st.cache_data(ttl="2h", show_spinner=False)
def get_run_url(run_id):
    time.sleep(1)
    return client.read_run(run_id).url


#
st.set_page_config(
    page_title="AI Securities Search",
    page_icon=":books:")

st.write("")
st.markdown("<h1 style='text-align: center;'>원하는 회사의 주식정보를</h1>", unsafe_allow_html=True)
st.markdown("<h1 style='text-align: center;'>일목요연하게</h1>", unsafe_allow_html=True)
st.markdown("<h1 style='text-align: center;'>알려드립니다.</h1>", unsafe_allow_html=True)
st.write("")
st.markdown("<p style='text-align: center; font-size: 20px;'>종목뉴스/재무정보/주식정보/증권약관 분석 </p>", unsafe_allow_html=True)
st.write("")

# If user inputs a new prompt, generate and draw a new response
msgs = StreamlitChatMessageHistory(key="langchain_messages")

temperature = 0.0
model_name = 'gpt-3.5-turbo'
uploaded_file = None
retriever, prompt = None, None

# sidebar 구성
with st.sidebar as sidebar:
    st.title(":books: :blue[  OO 증권]")
    st.markdown('## Models and Parameters')
    temperature = st.slider('temperature Range (0.0 ~ 1.0 )', 0.0, 1.0, 0.0)  # min, max, default
    model_name = st.selectbox('chose a model name', ['gpt-3.5-turbo', 'gpt-4'])
    # if st.session_state["select_event"] == '증권약관 분석':
    uploaded_file = st.sidebar.file_uploader("upload your pdf file", type=['pdf'])
    if uploaded_file:
        search_type = '증권약관 분석'
        retriever, prompt = pt.make_prompt_by_file('증권약관 분석', uploaded_file)
    expander = st.expander("## About ")
    expander.write(""" 
                Introducing Stock Summary and Financial Information Summarization with Generative AI (LLM)
                And Users can easily find the information they need in various documents, including securities terms and conditions.
                """)
    reset_history = st.button("채팅 초기화")

# main 구성

if len(msgs.messages) == 0 or reset_history:
    msgs.clear()
    msgs.add_ai_message("무엇을 도와드릴까요?")
    st.session_state["last_run"] = None

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        ChatMessage(role="assistant", content="무엇을 도와드릴까요?")
    ]

for msg in st.session_state.messages:
    st.chat_message(msg.role).write(msg.content)

if user_input := st.chat_input():
    # 의도분류 - function calling
    search_type, company, content = run_conversation(user_input)
    print(search_type, company, content)

    search_result = ''
    if search_type == 'get_news':
        search_result = search.search_by_naver_api(company)
    elif search_type == 'get_finance':
        search_result = search.search_by_dart_api(company)
    elif search_type == 'get_stock':
        start_date = datetime.today().strftime("%Y-%m-01")
        end_date = datetime.today().strftime("%Y-%m-%d")

        print(company)
        company_code_with_text = get_company_code(company)
        print("company_code_with_text : " + company_code_with_text)
        company_code = re.findall(r'\d+', company_code_with_text)
        print(company_code)
        print("company_code[0] : " + company_code[0])

        p = PatternFinder()
        p.set_stock(company_code[0])
        result = p.search(start_date, end_date)
        pred = p.stat_prediction(result)
        text = p.plot_pattern(result.index[1])

        search_result = """
                            우선
                            {5}
                            에서 Date→날짜, Open→시작가격, High→최고가격, Low→최저가격, Close→종가, Volume→거래량, Change→등락률 로 명칭을 수정해줘.
                            그리고 반드시 '표' 형태로 출력해줘.
                            위 표는 {1}부터 {2}까지 {3}의 대한민국 주식장이 열린 날의 주식 가격이야.
                            
                            {4}의 값이 양수일 경우 다음 문장을 그대로 출력해줘. '이번 달 주가를 유사도 95%이상인 과거 차트에 대입시 5일후 주가는 +{4} 상승할 예정입니다.'
                            {4}의 값이 음수일 경우 다음 문장을 그대로 출력해줘. '이번 달 주가를 유사도 95%이상인 과거 차트에 대입시 5일후 주가는 -{4} 하락할 예정입니다.'
                        """.format('', start_date, end_date, company, str(text),
                                   search.get_monthly_price(company_code))

    st.session_state.messages.append(ChatMessage(role="user", content=user_input))
    st.chat_message("user").write(user_input)
    with st.chat_message("assistant"):
        stream_handler = pt.StreamHandler(st.empty())
        if company is None and search_type is None:
            if uploaded_file is not None:
                llm = ChatOpenAI(
                    model=model_name,
                    temperature=temperature,
                    streaming=True,
                    callbacks=[stream_handler]
                )
                chain = (
                        {
                            "context": retriever,
                            "question": RunnablePassthrough(),
                        }
                        | prompt
                        | llm
                )
                response = chain.invoke(user_input, cfg).content
            else:
                # response = content
                prompt_general = ChatPromptTemplate.from_messages(
                    [
                        ("system", content),
                        MessagesPlaceholder(variable_name="history"),
                        ("human", "{question}"),
                    ]
                )
                llm = ChatOpenAI(
                    model=model_name,
                    temperature=temperature,
                    streaming=True,
                    callbacks=[stream_handler]
                )
                chain = prompt_general | llm
                chain_with_history = RunnableWithMessageHistory(
                    chain,
                    lambda session_id: msgs,
                    input_messages_key="question",
                    history_messages_key="history",
                )
                response = chain_with_history.invoke({"question": user_input}, cfg).content
        else:
            chain = pt.chain_with_api(search_type, model_name, temperature)
            chain_with_history = RunnableWithMessageHistory(
                chain,
                lambda session_id: msgs,
                input_messages_key="question",
                history_messages_key="history",
            )
            response = chain_with_history.invoke({"question": user_input, "context": search_result}, cfg).content
        st.session_state.last_run = run_collector.traced_runs[0].id
        st.session_state.messages.append(ChatMessage(role="assistant", content=response))

if st.session_state.get("last_run"):
    run_url = get_run_url(st.session_state.last_run)
    st.sidebar.markdown(f"[LangSmith 추적🛠️]({run_url})")
