import time

import chat_with_news as cwn
import streamlit as st
from dotenv import load_dotenv
from langchain.schema import ChatMessage
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI
from streamlit_feedback import streamlit_feedback

from search import search_by_naver_api

load_dotenv()


@st.cache_data(ttl="2h", show_spinner=False)
def get_run_url(run_id):
    time.sleep(1)
    return client.read_run(run_id).url


st.sidebar.title(":books: :blue[  OO 증권]")
# expander = st.sidebar.markdown('## Requirements')

select_event = st.sidebar.selectbox('How do you want to find data?',
                                    ['종목뉴스 요약', '재무정보 요약', '증권약관 조회', '기업 분석', '기술적 분석'])
#  ['Stock New Summary','inancial Information Summary','Document Analysis','Company Analysis','Techical Analysis'])


expander = st.sidebar.markdown('## Models and Parameters')
temperature = st.sidebar.slider('temperature Range (0.0 ~ 2.0 )', 0.0, 2.0, 0.2)  # min, max, default
model_name = st.sidebar.selectbox('chose a model name', ['gpt-3.5-turbo', 'gpt-4.0'])

if select_event == '종목뉴스 요약':
    st.title('Stock New Summary')
    st.markdown("""
                * _Stock News Sentiment Analysis_  
                *  Bing Search, Never News API 등을 통한 사업자(종목)에 대한 뉴스 요약을 해드립니다. 
                """)
    ########################################################
    # If user inputs a new prompt, generate and draw a new response
    msgs = StreamlitChatMessageHistory(key="langchain_messages")

    reset_history = st.sidebar.button("채팅 초기화")
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
        client, run_collector, cfg = cwn.configure_run()
        search_result = search_by_naver_api(user_input)

        st.session_state.messages.append(ChatMessage(role="user", content=user_input))
        st.chat_message("user").write(user_input)
        with st.chat_message("assistant"):
            stream_handler = cwn.StreamHandler(st.empty())
            llm = ChatOpenAI(streaming=True, callbacks=[stream_handler])
            prompt = cwn.make_prompt()
            chain = prompt | llm
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
        feedback = streamlit_feedback(
            feedback_type="thumbs",
            optional_text_label=None,
            key=f"feedback_{st.session_state.last_run}",
        )
        if feedback:
            scores = {"👍": 1, "👎": 0}
            client.create_feedback(
                st.session_state.last_run,
                feedback["type"],
                score=scores[feedback["score"]],
                comment=feedback.get("text", None),
            )
            st.toast("피드백을 저장하였습니다.!", icon="📝")
    ########################################################
elif select_event == '재무정보 요약':
    st.title('Financial Information Summary')
    st.markdown("""
                """)
    context = st.text_input('사업자(종목)명을 입력해주세요')
    if st.button('재무정보 요약'):
        with st.spinner('[' + context + '] Searching ...'):
            st.text('준비중 입니다.')

elif select_event == '증권약관 조회':
    st.title('Document Analysis')
    st.markdown("""
                """)
    uploaded_files = st.file_uploader("upload your file", type=['pdf', 'docx', 'pptx'], accept_multiple_files=True)
    process = st.button("Process")

    context = st.text_input('궁금하신 내용을 입력해주세요')
    if st.button('약관내용 조회'):
        with st.spinner('[' + context + '] Searching ...'):
            st.text('준비중 입니다.')

elif select_event == '기업 분석':
    st.title('Company Analysis')
    st.markdown("""
                """)
    uploaded_files = st.file_uploader("upload your file", type=['pdf', 'docx', 'pptx'], accept_multiple_files=True)
    process = st.button("Process")

    context = st.text_input('사업자(종목)명을 입력해주세요')
    if st.button('기업분석'):
        with st.spinner('[' + context + '] Searching ...'):
            st.text('준비중 입니다.')
else:
    st.title('Techical Analysis')
    st.markdown("""
                """)
    context = st.text_input('사업자(종목)명을 입력해주세요')
    if st.button('종목분석'):
        with st.spinner('[' + context + '] Searching ...'):
            st.text('준비중 입니다.')

expander = st.sidebar.expander("## About ")
expander.write(""" 
                Introducing Stock Summary and Financial Information Summarization with Generative AI (LLM)

                And Users can easily find the information they need in various documents, including securities terms and conditions.

                """)
