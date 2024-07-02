import tempfile

import streamlit as st
from langchain.callbacks.base import BaseCallbackHandler
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, FewShotChatMessagePromptTemplate
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter

import embeddings
from custom_prompt_template import CustomPromptTemplate


class StreamHandler(BaseCallbackHandler):
    def __init__(self, container, initial_text=""):
        self.container = container
        self.text = initial_text

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self.text += token
        self.container.markdown(self.text)


def get_prompt(template_type):
    prompt_template = ''
    prompt_instruction = ''

    if template_type == 'get_news':
        prompt_template = CustomPromptTemplate.NEWS_TEMPLATE_FEW_SHOT.value
        prompt_instruction = CustomPromptTemplate.NEWS_TEMPLATE_INSTRUCTION.value
    elif template_type == 'get_finance':
        prompt_template = CustomPromptTemplate.FINANCE_TEMPLATE_FEW_SHOT.value
        prompt_instruction = CustomPromptTemplate.FINANCE_TEMPLATE_INSTRUCTION.value
    elif template_type == 'get_stock':
        prompt_template = CustomPromptTemplate.STOCK_INFO_TEMPLATE_FEW_SHOT.value
        prompt_instruction = CustomPromptTemplate.STOCK_INFO_TEMPLATE_INSTRUCTION.value
    elif template_type == '증권약관 분석':
        prompt_template = CustomPromptTemplate.DOCUMENT_TEMPLATE_FEW_SHOT.value
        prompt_instruction = CustomPromptTemplate.DOCUMENT_TEMPLATE_INSTRUCTION.value
    elif template_type == 'Trend News':
        prompt_template = CustomPromptTemplate.TREND_NEWS_TEMPLATE_FEW_SHOT.value
        prompt_instruction = CustomPromptTemplate.TREND_NEWS_TEMPLATE_INSTRUCTION.value

    example_prompt = ChatPromptTemplate.from_messages(
        [
            ("human", "{question}:\n{context}"),
            ("ai", "{answer}")
        ]
    )

    few_shot_prompt = FewShotChatMessagePromptTemplate(
        examples=prompt_template,
        example_prompt=example_prompt,
    )
    if template_type == '증권약관 분석':
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", prompt_instruction),
                few_shot_prompt,
                ("human", "{question}\n{context}"),
            ]
        )
    else:
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", prompt_instruction),
                few_shot_prompt,
                MessagesPlaceholder(variable_name="history"),
                ("human", "{question}\n{context}"),
            ]
        )
    return prompt


def chain_with_api(template_type, model_name, temperature):
    prompt = get_prompt(template_type)
    stream_handler = StreamHandler(st.empty())
    llm = ChatOpenAI(
        model=model_name,
        temperature=temperature,
        streaming=True,
        callbacks=[stream_handler]
    )
    chain = prompt | llm
    return chain


def load_pdf(uploaded_file):
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(uploaded_file.read())
        f.flush()
        loader = PyPDFLoader(f.name)
        docs = loader.load()
    return docs


def make_prompt_by_file(search_type, uploaded_file):
    prompt = get_prompt(search_type)
    docs = load_pdf(uploaded_file)

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=5000, chunk_overlap=500)
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

        st.write("완료 ✅")
        status.update(label="완료 ✅", state="complete", expanded=False)
        st.markdown(f'💬 `{uploaded_file.name}`')
        st.markdown("🔔참고\n\n**새로운 파일** 로 대화를 시작하려면, `새로고침` 후 진행해 주세요")
        return faiss_retriever, prompt
