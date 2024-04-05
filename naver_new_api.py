# 네이버 뉴스 검색 API 
import os
import sys
import urllib.request
from bs4 import BeautifulSoup


client_id = "zn8zLchSGS3_WhIMHNpY"
client_secret = "mhrP9vRyIk"

encText = urllib.parse.quote("삼성전자")
display_num = urllib.parse.quote("100")    #한 번에 표시할 검색 결과 개수(기본값: 10, 최댓값: 100) 
start = urllib.parse.quote("1")           # 검색 시작 위치(기본값: 1, 최댓값: 1000)
sort =  urllib.parse.quote("date")        # 검색 결과 정렬 방법 - sim: 정확도순으로 내림차순 정렬 / - date: 날짜순으로 내림차순 정렬

url = "https://openapi.naver.com/v1/search/news.xml?query=" + encText + "&display=" + display_num + "&start=" + start + "&sort=" + sort# JSON 결과

# url = "https://openapi.naver.com/v1/search/news.xml?query=" + encText # XML 결과

request = urllib.request.Request(url)
request.add_header("X-Naver-Client-Id",client_id)
request.add_header("X-Naver-Client-Secret",client_secret)
response = urllib.request.urlopen(request)
rescode = response.getcode()

if(rescode==200):
    response_body = response.read()
    # BeautifulSoup으로 XML 파싱
    soup = BeautifulSoup(response_body, "lxml")
        
    # 뉴스 기사 목록 추출
    news_items = soup.find_all("item")
    i = 0 
      # 각 기사 정보 출력
    for item in news_items:
        i = i + 1
        print(item)
        print(f"<{i}>")
        print(f"제목: {item.title.text}")
        print(f"링크: {item.link.text}")
        print(f"언론사: {item.originallink.text}")
        print(f"날짜: {item.pubdate.text}")
        print(f"요약: {item.description.text}")
        print("-----------------")
        
    print(response_body.decode('utf-8'))
else:
    print("Error Code:" + rescode)