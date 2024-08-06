import time
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv
from langchain.schema import ChatMessage
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain_core.runnables import RunnablePassthrough
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI

import prompt as pt
import search
from config import ls_configure
from custom_prompt_template import CustomPromptTemplate
from function_calling import run_conversation
from predict import PatternFinder
from stt import button_click
from tts import tts

# 환경변수 로드
load_dotenv()

# Langsmith 환경설정
client, run_collector, cfg = ls_configure()

# 메시지 히스토리 초기화
msgs = StreamlitChatMessageHistory(key="langchain_messages")


def get_run_url(run_id):
    time.sleep(1)
    return client.read_run(run_id).url


def handle_search_type(search_type, company):
    if search_type == 'get_news':
        return search.search_by_naver_api(company)
    elif search_type == 'get_finance':
        return search.search_by_dart_api(company)
    elif search_type == 'get_stock':
        start_date = datetime.today().strftime("%Y-01-01")
        end_date = datetime.today().strftime("%Y-%m-%d")
        company_code = search.item_code_by_item_name(company)
        p = PatternFinder()
        p.set_stock(company_code)
        result = p.search(start_date, end_date)
        pred = p.stat_prediction(result)
        plot_pattern = p.plot_pattern(result.index[1])
        monthly_price = search.get_monthly_price(company_code)
        return CustomPromptTemplate.STOCK_INFO_CONTEXT.value.format(start_date, end_date, company, str(plot_pattern),
                                                                    monthly_price)
    return ''


def main_chat(user_input, stt_tts, search_type, model_name, temperature):
    if search_type == 'Colabot':
        search_type, company, content = run_conversation(user_input)
        search_result = handle_search_type(search_type, company)
    elif search_type == 'Trend News':
        search_result = search.search_by_item(user_input)
    else:
        search_result = user_input
    st.session_state.messages.append(ChatMessage(role="user", content=user_input))
    st.chat_message("user").write(user_input)

    with st.chat_message("assistant"):
        stream_handler = pt.StreamHandler(st.empty())
        # if search_type is None and uploaded_file:
        #     llm = ChatOpenAI(model=model_name, temperature=temperature, streaming=True, callbacks=[stream_handler])
        #     chain = {"context": retriever, "question": RunnablePassthrough()} | prompt | llm
        #     response = chain.invoke(user_input).content
        # else:
        chain = pt.chain_with_api(search_type, model_name, temperature)
        chain_with_history = RunnableWithMessageHistory(chain, lambda session_id: msgs, input_messages_key="question",
                                                        history_messages_key="history")
        response = chain_with_history.invoke({"question": user_input, "context": search_result}, cfg).content

        if stt_tts:
            tts(response)
        st.session_state.messages.append(ChatMessage(role="assistant", content=response))


def setup_sidebar():
    with st.sidebar:
        st.title(":books: :blue[ OO 증권]")
        st.markdown('## Models and Parameters')
        search_type = st.selectbox('choose a chat type', ['Colabot', 'Trend News', 'gpt-4o'])
        temperature = st.slider('temperature Range (0.0 ~ 1.0 )', 0.0, 1.0, 0.0)
        model_name = st.selectbox('choose a model name', ['gpt-4o-mini', 'gpt-4o', 'gpt-4'])
        uploaded_file = st.file_uploader("upload your pdf file", type=['pdf'])
        if uploaded_file:
            search_type = 'Colabot'
            retriever, prompt = pt.make_prompt_by_file('증권약관 분석', uploaded_file)
        expander = st.expander("## About ")
        expander.write(
            """ Introducing Stock Summary and Financial Information Summarization with Generative AI (LLM) And Users can easily find the information they need in various documents, including securities terms and conditions. """)
        reset_history = st.button("채팅 초기화")
        stt_button = st.button("음성")
    return search_type, temperature, model_name, uploaded_file, reset_history, stt_button


st.set_page_config(page_title="AI Securities Search", page_icon=":books:")
st.write("")
st.markdown("<h1 style='text-align: center;'>원하는 회사의 금융정보를</h1>", unsafe_allow_html=True)
st.markdown("<h1 style='text-align: center;'>일목요연하게</h1>", unsafe_allow_html=True)
st.markdown("<h1 style='text-align: center;'>알려드립니다.</h1>", unsafe_allow_html=True)
st.write("")
st.markdown("<p style='text-align: center; font-size: 20px;'>종목뉴스/재무정보/주식정보/증권약관 분석 </p>", unsafe_allow_html=True)
st.write("")

search_type, temperature, model_name, uploaded_file, reset_history, stt_button = setup_sidebar()

if len(msgs.messages) == 0 or reset_history:
    msgs.clear()
    msgs.add_ai_message("무엇을 도와드릴까요?")
    st.session_state["last_run"] = None

if "messages" not in st.session_state:
    st.session_state["messages"] = [ChatMessage(role="assistant", content="무엇을 도와드릴까요?")]

for msg in st.session_state.messages:
    st.chat_message(msg.role).write(msg.content)

if user_input := st.chat_input():
    main_chat(user_input, False, search_type, model_name, temperature)

if stt_button:
    stt_text = button_click()
    st.session_state.messages.append(ChatMessage(role="user", content=stt_text))
    main_chat(stt_text, True, search_type, model_name, temperature)

if st.session_state.get("last_run"):
    run_url = get_run_url(st.session_state.last_run)
    st.sidebar.markdown(f"[LangSmith 추적🛠️]({run_url})")
