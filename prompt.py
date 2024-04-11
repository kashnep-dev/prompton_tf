import tempfile

import streamlit as st
from custom_prompt_template import CustomPromptTemplate
from langchain.callbacks.base import BaseCallbackHandler
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter

import embeddings


class StreamHandler(BaseCallbackHandler):
    def __init__(self, container, initial_text=""):
        self.container = container
        self.text = initial_text

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self.text += token
        self.container.markdown(self.text)


def get_prompt(type):
    if type == '종목뉴스 요약':
        return CustomPromptTemplate.NEWS_TEMPLATE.value
    elif type == '재무정보 요약':
        return CustomPromptTemplate.FINANCE_TEMPLATE.value
    elif type == '주식정보 분석':
        return CustomPromptTemplate.STOCK_INFO_TEMPLATE.value
    elif type == '증권약관 분석':
        return CustomPromptTemplate.DOCUMENT_TEMPLATE.value


def chain_with_api(type):
    template = get_prompt(type)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", template),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}"),
        ]
    )
    stream_handler = StreamHandler(st.empty())
    llm = ChatOpenAI(
        model=st.session_state["model"],
        temperature=st.session_state["temperature"],
        streaming=True,
        callbacks=[stream_handler]
    )
    chain = prompt | llm
    return chain


def load_pdf():
    with tempfile.NamedTemporaryFile(delete=True) as f:
        f.write(st.session_state["uploaded_file"].read())
        f.flush()
        loader = PDFPlumberLoader(f.name)
        docs = loader.load()
    return docs


def make_prompt_by_file(type):
    template = get_prompt(type)
    docs = load_pdf()

    prompt = ChatPromptTemplate.from_template(template)

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=50)
    splits = text_splitter.split_documents(docs)

    with st.status("파일을 처리 중입니다..", expanded=True) as status:
        st.write("① 임베딩 생성")
        status.update(label="① 임베딩을 생성 중..🔥", state="running")
        embedding = embeddings.embedding_factory()

        st.write("② DB 인덱싱")
        status.update(label="② DB 인덱싱 생성 중..🔥", state="running")
        faiss = FAISS.from_documents(splits, embedding["faiss"])

        st.write("③ Retriever 생성")
        status.update(label="③ Retriever 생성 중..🔥", state="running")
        faiss_retriever = faiss.as_retriever()

        st.session_state["retriever"] = faiss_retriever
        st.session_state["prompt"] = prompt

        st.write("완료 ✅")
        status.update(label="완료 ✅", state="complete", expanded=False)
        st.markdown(f'💬 `{st.session_state["uploaded_file"].name}`')
        st.markdown("🔔참고\n\n**새로운 파일** 로 대화를 시작하려면, `새로고침` 후 진행해 주세요")
