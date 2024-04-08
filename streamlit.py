import os
import json
import requests
from openai import AzureOpenAI
# from dotenv import load_dotenv
# load_dotenv()

# Stramlit 라이브러리 호출
import streamlit as st


st.sidebar.title(":books: :blue[  OO 증권]" )
# expander = st.sidebar.markdown('## Requirements')

select_event =  st.sidebar.selectbox('How do you want to find data?',
                                    ['종목뉴스 요약','재무정보 요약','증권약관 조회','기업 분석','기술적 분석'])
                                    #  ['Stock New Summary','inancial Information Summary','Document Analysis','Company Analysis','Techical Analysis'])


expander = st.sidebar.markdown('## Models and Parameters')
temperature = st.sidebar.slider('temperature Range (0.0 ~ 2.0 )', 0.0, 2.0, 0.2)  # min, max, default
model_name = st.sidebar.selectbox('chose a model name',['gpt-3.5-turbo', 'gpt-4.0'])

if select_event == '종목뉴스 요약' : 
    st.title('Stock New Summary')
    st.markdown("""
                * _Stock News Sentiment Analysis_  
                *  Bing Search, Never New API 등을 통한 사업자(종목)에 대한 뉴스 요약을 해드립니다. 
                """)
    context = st.text_input('사업자(종목)명을 입력해주세요') 
    
    if st.button('종목분석'):
        with st.spinner('[' + context +'] Searching ...'):       
            get_input_query(context)  
            
elif select_event == '재무정보 요약' :
    st.title('Financial Information Summary')
    st.markdown("""
                """)
    context = st.text_input('사업자(종목)명을 입력해주세요') 
    if st.button('재무정보 요약'):
        with st.spinner('[' + context +'] Searching ...'):       
            st.text('준비중 입니다.')  
              
elif select_event == '증권약관 조회' :
    st.title('Document Analysis')
    st.markdown("""
                """)
    uploaded_files = st.file_uploader("upload your file", type=['pdf', 'docx','pptx'] , accept_multiple_files =True)
    process = st.button("Process")

    context = st.text_input('궁금하신 내용을 입력해주세요') 
    if st.button('약관내용 조회'):
        with st.spinner('[' + context +'] Searching ...'):       
            st.text('준비중 입니다.')  
            
elif select_event == '기업 분석' :
    st.title('Company Analysis')
    st.markdown("""
                """)
    uploaded_files = st.file_uploader("upload your file", type=['pdf', 'docx','pptx'] , accept_multiple_files =True)
    process = st.button("Process")

    context = st.text_input('사업자(종목)명을 입력해주세요') 
    if st.button('기업분석'):
        with st.spinner('[' + context +'] Searching ...'):       
            st.text('준비중 입니다.')              
else :
    st.title('Techical Analysis')
    st.markdown("""
                """)
    context = st.text_input('사업자(종목)명을 입력해주세요') 
    if st.button('종목분석'):
        with st.spinner('[' + context +'] Searching ...'):       
            st.text('준비중 입니다.')  



expander = st.sidebar.expander("## About ")
expander.write(""" 
                Introducing Stock Summary and Financial Information Summarization with Generative AI (LLM)
                          
                And Users can easily find the information they need in various documents, including securities terms and conditions.
                
                """)
        