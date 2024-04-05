from tempfile import NamedTemporaryFile

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader, JSONLoader
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI, OpenAIEmbeddings


def load_by_json(json_strs):
    temp_json = NamedTemporaryFile(mode="w", dir=".", delete=True, suffix=".json")
    temp_json.write(json_strs)
    loader = JSONLoader(
        file_path=temp_json.name,
        jq_schema='.items[]',
        text_content=False
    )
    docs = loader.load()
    print(f"문서의 수: {len(docs)}")
    print(docs[0])
    return docs


def load_by_web(url_list):
    loader = WebBaseLoader(url_list)
    docs = loader.load()
    print(f"문서의 수: {len(docs)}")
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


def make_summarize_prompt():
    template = """

    """


def make_llm_chain(stocks, vectorstore):
    # 벡터 스토어를 검색기로 사용하기 위해 retriever 변수에 할당.
    retriever = vectorstore.as_retriever()
    template = """
    Answer the following questions as best you can. Please always answer the results in Korean.
    You have access to the following tools:
    #Additional information:
    - News articles should be written concisely, no longer than 300 words.
    - The summary should include the main content and key information of each article.
    - The summary must be written from an objective and neutral perspective.
    - Unnecessary information should be removed and only the core content should be extracted and written.

    #Print:
    - Summary results must be written in 300 words or less.
    - Please write the summary results in table form.
    - The source of the summary results for each article, the article creation date, and the source url must also be written.

    #Data Source:
    - summary : You must definitely refer to description.
    - source of the article : You must definitely refer to description.
    - the article cration date : You must definitely refer to pubdate.
    - source url : You must definitely refer to originallink.
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
            {"context": retriever, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
    )
    return rag_chain
