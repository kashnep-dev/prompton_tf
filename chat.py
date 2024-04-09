import streamlit as st
from dotenv import load_dotenv
from langchain.schema import ChatMessage

import old.old_prompt as pt
from search import search_by_naver_api

# 1. 환경변수를 읽어온다.
load_dotenv()

# 2. naver 뉴스 api 검색을 한다.
# param = "LG유플러스"
# param = st.text_input("OpenAI API Key", type="text")


with st.sidebar:
    openai_api_key = st.text_input("OpenAI API Key", type="password")

if "messages" not in st.session_state:
    st.session_state["messages"] = [ChatMessage(role="assistant", content="무엇을 도와드릴까요?")]

for msg in st.session_state.messages:
    st.chat_message(msg.role).write(msg.content)

if prompt := st.chat_input():
    st.session_state.messages.append(ChatMessage(role="user", content=prompt))
    st.chat_message("user").write(prompt)

    with st.chat_message("assistant"):
        # stream_handler = StreamHandler(st.empty())
        # 6. llm chain을 생성한다.
        # 3. naver 뉴스 api 결과를 가져온다.
        json_str = search_by_naver_api(prompt)

        # 4. api 결과를 JSONLoader로 읽어온다.
        docs = pt.load_by_json(json_str)

        # 5. 벡터스토어를 생성한다.
        vectorstore = pt.make_vectorstore(docs)
        rag_chain = pt.make_llm_chain(prompt, vectorstore)
        response = rag_chain.invoke(st.session_state.messages)
        st.session_state.messages.append(ChatMessage(role="assistant", content=response.content))

# print(
#     rag_chain.invoke(
#         "LG유플러스 관련 뉴스를 요약해주세요."
#     )  # 문서에 대한 질의를 입력하고, 답변을 출력합니다.
# )
