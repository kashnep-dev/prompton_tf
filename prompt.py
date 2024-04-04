from langchain import hub
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.prompts.chat import ChatPromptTemplate
from langchain_core.prompts import PromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from langchain.prompts.few_shot import FewShotPromptTemplate
from langchain_core.callbacks.base import BaseCallbackHandler


def load_by_web(url_list):
    loader = WebBaseLoader(url_list)
    docs = loader.load()
    print(f"문서의 수: {len(docs)}")
    print(docs)

    return docs


def make_vectorstore(docs):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=50)
    splits = text_splitter.split_documents(docs)

    # 벡터스토어를 생성합니다.
    vectorstore = FAISS.from_documents(documents=splits, embedding=OpenAIEmbeddings())

    return vectorstore


def format_docs(docs):
    # 검색한 문서 결과를 하나의 문단으로 합쳐줍니다.
    return "\n\n".join(doc.page_content for doc in docs)


def make_llm_chain(stocks, vectorstore):
    # 벡터 스토어를 검색기로 사용하기 위해 retriever 변수에 할당.
    retriever = vectorstore.as_retriever()
    # template = """
    # Question: {question}
    # {context}
    # **추가 정보:**
    # - 뉴스 기사는 300단어 이내로 간결하게 작성합니다.
    # - 요약 내용에는 각 기사의 주요 내용과 핵심 정보가 포함되어야 합니다.
    # - 요약은 객관적이고 중립적인 시각으로 작성되어야 합니다.
    # - 불필요한 정보는 제거하고 핵심 내용만 추출하여 작성해야 합니다.
    #
    # **출력:**
    # - 요약 결과는 300 단어 이내로 작성되어야 합니다.
    # - 요약 결과는 bullet point 형식으로 작성되어야 합니다.
    # - 기사별 요약 결과의 출처와 기사 작성일, 출처 url도 함께 작성 되어야 합니다.
    # """
    template = """
    Answer the following questions as best you can. Please always answer the results in Korean.
    You have access to the following tools:
    Question: {question}
    Gronding data: {context}
    Results: 
    """
    prompt = PromptTemplate(
        input_variables=["subject"],
        template=template
    )
    llm = ChatOpenAI(
        model_name="gpt-3.5-turbo",
        temperature=0
    )

    # 프롬프트, 모델, 출력 파서를 연결하여 처리 체인을 구성
    rag_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
    )

    # print(rag_chain.invoke("삼성전자 최신 뉴스 3개를 각각 요약해주세요. 기사별 요약 결과의 출처와 기사 작성일, 출처 url도 포함되는 표 형태로 답변해주세요."))
    # print(rag_chain.invoke("삼성전자 최신 뉴스를 요약해주세요."))
    return rag_chain
