import prompt as pt
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
from config import ls_configure, get_run_url

# 환경변수 로드
load_dotenv()

# 환경설정
ls_configure()

# If user inputs a new prompt, generate and draw a new response
msgs = StreamlitChatMessageHistory(key="langchain_messages")

# sidebar 구성
with st.sidebar as sidebar:
    st.title(":books: :blue[  OO 증권]")
    st.session_state["select_event"] = st.selectbox('How do you want to find data?',
                                                    ['종목뉴스 요약', '재무정보 요약', '주식정보 분석', '증권약관 분석'])
    st.markdown('## Models and Parameters')
    st.session_state["temperature"] = st.slider('temperature Range (0.0 ~ 2.0 )', 0.0, 2.0, 0.0)  # min, max, default
    st.session_state["model_name"] = st.selectbox('chose a model name', ['gpt-3.5-turbo', 'gpt-4'])
    if st.session_state["select_event"] == '증권약관 분석':
        uploaded_file = st.sidebar.file_uploader("upload your pdf file", type=['pdf'])
        if uploaded_file:
            st.session_state['uploaded_file'] = uploaded_file
        if 'uploaded_file' in st.session_state and 'retriever' not in st.session_state:
            pt.make_prompt_by_file(st.session_state["select_event"])
    expander = st.expander("## About ")
    expander.write(""" 
                Introducing Stock Summary and Financial Information Summarization with Generative AI (LLM)
                And Users can easily find the information they need in various documents, including securities terms and conditions.
                """)
    reset_history = st.button("채팅 초기화")

# main 구성
select_event = st.session_state["select_event"]
if select_event == '종목뉴스 요약':
    st.title('Stock New Summary')
    st.markdown("""* Never News API 등을 통한 사업자(종목)에 대한 뉴스 요약을 해드립니다.""")
elif select_event == '재무정보 요약':
    st.title('Financial Information Summary')
    st.markdown("""* DART API를 통한 사업자(종목)에 대한 재무정보 요약을 해드립니다.""")
elif select_event == '증권약관 분석':
    st.title('Document Analysis')
    st.markdown("""* 증권약관(pdf)을 분석하여 답변을 해드립니다.""")
elif select_event == '주식정보 분석':
    st.title('Stock Information Analysis')
    st.markdown("""* FinanceDataReader를 활용하여 주식정보를 분석합니다.""")
else:
    st.title('Techical Analysis')
    st.markdown("""* 사용하지 않음 """)
    context = st.text_input('사업자(종목)명을 입력해주세요')
    if st.button('주식정보 분석'):
        with st.spinner('[' + context + '] Searching ...'):
            st.text('준비중 입니다.')

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
    client = st.session_state["client"]
    run_collector = st.session_state["run_collector"]
    cfg = st.session_state["cfg"]

    search_result = ''
    if select_event == '종목뉴스 요약':
        search_result = search.search_by_naver_api(user_input.split()[0])
    elif select_event == '재무정보 요약':
        search_result = search.search_by_dart_api(user_input.split()[0])
    elif select_event == '주식정보 분석':
        start_date = datetime(datetime.now().year, 1, 1)
        end_date = datetime.now()
        search_result = search.get_yearly_price(search.item_code_by_item_name(user_input.split()[0]))
        search_result = search_result + "는 {0}부터 {1}까지 {2}의 주식 가격이야.".format(start_date, end_date, user_input.split()[0])

    st.session_state.messages.append(ChatMessage(role="user", content=user_input))
    st.chat_message("user").write(user_input)
    with st.chat_message("assistant"):
        stream_handler = pt.StreamHandler(st.empty())
        if select_event == '증권약관 분석':
            prompt = st.session_state["prompt"]
            retriever = st.session_state["retriever"]

            llm = ChatOpenAI(
                model=st.session_state["model_name"],
                temperature=st.session_state["temperature"],
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
            response = chain.invoke(user_input, cfg)
        else:
            chain = pt.chain_with_api(select_event)
            chain_with_history = RunnableWithMessageHistory(
                chain,
                lambda session_id: msgs,
                input_messages_key="question",
                history_messages_key="history",
            )
            response = chain_with_history.invoke({"question": user_input, "context": search_result}, cfg)
        st.session_state.messages.append(
            ChatMessage(role="assistant", content=response.content)
        )
    st.session_state.last_run = run_collector.traced_runs[0].id

if st.session_state.get("last_run"):
    run_url = get_run_url(st.session_state.last_run)
    st.sidebar.markdown(f"[LangSmith 추적🛠️]({run_url})")
