import re
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
from predict import PatternFinder, get_company_name, get_company_code
from function_calling import run_conversation

# 환경변수 로드
load_dotenv()

# Langsmith 환경설정
ls_configure()

# 
st.set_page_config(
page_title="AI Securities Search",
page_icon = ":books:")

# If user inputs a new prompt, generate and draw a new response
msgs = StreamlitChatMessageHistory(key="langchain_messages")

# sidebar 구성
with st.sidebar as sidebar:
    st.title(":books: :blue[  OO 증권]")
    # st.session_state["select_event"] = st.selectbox('How do you want to find data?', ['종목뉴스 요약', '재무정보 요약', '주식정보 분석', '증권약관 분석'])
    st.markdown('## Models and Parameters')
    st.session_state["temperature"] = st.slider('temperature Range (0.0 ~ 1.0 )', 0.0, 1.0, 0.0)  # min, max, default
    st.session_state["model_name"] = st.selectbox('chose a model name', ['gpt-3.5-turbo', 'gpt-4'])
    # if st.session_state["select_event"] == '증권약관 분석':
    uploaded_file = st.sidebar.file_uploader("upload your pdf file", type=['pdf'])
    if uploaded_file:
        st.session_state['uploaded_file'] = uploaded_file
    if 'uploaded_file' in st.session_state and 'retriever' not in st.session_state:
        pt.make_prompt_by_file('증권약관 분석')
    expander = st.expander("## About ")
    expander.write(""" 
                Introducing Stock Summary and Financial Information Summarization with Generative AI (LLM)
                And Users can easily find the information they need in various documents, including securities terms and conditions.
                """)
    reset_history = st.button("채팅 초기화")

# main 구성
# select_event = st.session_state["select_event"]
# if select_event == '종목뉴스 요약':
#     st.title('Stock News Summary')
#     st.markdown("""* Never News API 등을 통한 사업자(종목)에 대한 뉴스 요약을 해드립니다.""")
# elif select_event == '재무정보 요약':
#     st.title('Financial Information Summary')
#     st.markdown("""* DART API를 통한 사업자(종목)에 대한 재무정보 요약을 해드립니다.""")
# elif select_event == '증권약관 분석':
#     st.title('Document Analysis')
#     st.markdown("""* 증권약관(pdf)을 분석하여 답변을 해드립니다.""")
# elif select_event == '주식정보 분석':
#     st.title('Stock Information Analysis')
#     st.markdown("""* FinanceDataReader를 활용하여 주식정보를 분석합니다.""")
# else:
#     st.title('Techical Analysis')
#     st.markdown("""* 사용하지 않음 """)
#     context = st.text_input('사업자(종목)명을 입력해주세요')
#     if st.button('주식정보 분석'):
#         with st.spinner('[' + context + '] Searching ...'):
#             st.text('준비중 입니다.')
page_bg_img = '''
<style>
body {
background-image: url("https://images.unsplash.com/photo-1542281286-9e0a16bb7366");
background-size: cover;
}
</style>
'''

st.markdown(page_bg_img, unsafe_allow_html=True)

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

    # 의도분류 - function calling
    run_conversation(user_input)
    search_type, company = '', ''
    print(search_type, company)
    if 'uploaded_file' in st.session_state and 'search_type' not in st.session_state and 'company' not in st.session_state:
        search_type = '증권약관 분석'
    else:
        search_type, company = st.session_state["search_type"], st.session_state["company"]

    search_result = ''
    if search_type == '종목뉴스 요약':
        search_result = search.search_by_naver_api(company)
    elif search_type == '재무정보 요약':
        search_result = search.search_by_dart_api(company)
    elif search_type == '주식정보 분석':
        start_date = datetime.today().strftime("%Y-%m-01")
        end_date = datetime.today().strftime("%Y-%m-%d")

        # company_name = get_company_name(user_input)
        company_code_with_text = get_company_code(company)
        print("company_code_with_text : " + company_code_with_text)
        company_code = re.findall(r'\d+', company_code_with_text)
        print("company_code[0] : " + company_code[0])

        p = PatternFinder()
        p.set_stock(company_code[0])
        result = p.search(start_date, end_date)
        pred = p.stat_prediction(result)
        text = p.plot_pattern(result.index[1])
        search_result = """
                            우선
                            {5}
                            의 칼럼명을 Date→날짜, Open→시작가격, High→최고가격, Low→최저가격, Close→종가, Volume→거래량, Change→등락률 로 수정하고, 표 형태로 출력해줘.
                            그리고 제목 행도 데이터 행들과 열의 너비가 똑같게 출력해줘.
                            위 표는 {1}부터 {2}까지 {3}의 대한민국 주식장이 열린 날의 주식 가격이야.

                            #최저가 : '종가' 열의 값들 중 가장 작은 값
                            #최고가 : '종가' 열의 값들 중 가장 큰 값
                            #평균가 : '종가' 열의 값들의 평균 값
                            #현재가 : '종가' 열의 값들 중 마지막 날짜의 값

                            앞으로 내가 묻는 질문에 넌 반드시 Close 열의 값들 중에서만 대답을 해야해.
                            위 표를 기준으로, {1}부터 {2}까지 {3}의 #최저가, #최고가, #평균가, #현재가 를 알려줘.
                            그리고 {4}의 값에 따라 제일 마지막 라인에 한줄 띄고 아래 문장을 줄바꿈 하여 그대로 출력해줘.
                            {4}의 값이 양수일 경우, '유사도 95%이상인 과거 차트에 대입시, 5일후 주가 전망은 {4} 상승할 예정입니다.'
                            {4}의 값이 음수일 경우, '유사도 95%이상인 과거 차트에 대입시, 5일후 주가 전망은 {4} 하락할 예정입니다.'
                        """.format(
            search.get_monthly_close_price(company_code), start_date, end_date, company, str(text),
            search.get_monthly_price(company_code))

    st.session_state.messages.append(ChatMessage(role="user", content=user_input))
    st.chat_message("user").write(user_input)
    with st.chat_message("assistant"):
        stream_handler = pt.StreamHandler(st.empty())
        if search_type == '증권약관 분석':
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
            chain = pt.chain_with_api(search_type)
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
