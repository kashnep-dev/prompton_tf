import json
import os
import urllib.request
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup


# bing 검색결과를 가져오는 함수
def search_by_bing(param):
    search_url = "https://www.bing.com/news/search?q={0}&qft=interval%3d%228%22&form=PTFTNR".format(param)
    html_doc = requests.get(search_url)
    soup = BeautifulSoup(html_doc.text, "html.parser")

    news_list = soup.select("div[id='algocore']>div")

    url_list = []
    if len(news_list) > 0:
        for news_card in news_list:
            if "hankyung" not in news_card and "yna" not in news_card:
                # print(news_card.attrs['data-url'])
                url_list.append(news_card.attrs['data-url'])
                if len(url_list) > 19: break
    else:
        print("No Results")
    return url_list


# bing 검색결과를 가져오는 함수
def search_by_bing_api(param):
    subscription_key = os.getenv("BING_SEARCH_KEY")
    api_endpoint = os.getenv("BING_SEARCH_ENDPOINT")

    # Construct a request
    mkt = 'ko-KR'
    params = {'q': param, 'mkt': mkt, 'count': 5, 'setLang': mkt, 'freshness': 'Week'}
    headers = {'Ocp-Apim-Subscription-Key': subscription_key}

    # Call the API
    response = requests.get(api_endpoint, headers=headers, params=params)
    doc_list = []
    for article in response.json()['value']:
        doc_list.append(article['url'])
    return doc_list


def search_by_yna(param):
    today = datetime.now().strftime("%Y%m%d")
    one_week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")

    yna_endpoint = os.getenv("YNA_ENDPOINT")
    yna_endpoint = 'https://yna.co.kr/search/index?query={0}&sort=weight'.format(param)
    print('yna_endpoint ', yna_endpoint)
    html_doc = requests.get(yna_endpoint)
    soup = BeautifulSoup(html_doc.text, "html.parser")
    print(soup)
    news_list = soup.select("div[class='cts_atclst']")
    print(news_list)
    url_list = []
    if len(news_list) > 0:
        for news_card in news_list:
            url_list.append(news_card.attrs['href'])
            if len(url_list) > 19: break
    else:
        print("No Results")
    return url_list


# 네이버 뉴스 검색 API 
def search_by_naver_api(param):
    client_id = "zn8zLchSGS3_WhIMHNpY"
    client_secret = "mhrP9vRyIk"

    encText = urllib.parse.quote(param)
    display_num = urllib.parse.quote("100")  # 한 번에 표시할 검색 결과 개수(기본값: 10, 최댓값: 100) 
    start = urllib.parse.quote("1")  # 검색 시작 위치(기본값: 1, 최댓값: 1000)
    sort = urllib.parse.quote("date")  # 검색 결과 정렬 방법 - sim: 정확도순으로 내림차순 정렬 / - date: 날짜순으로 내림차순 정렬

    url = "https://openapi.naver.com/v1/search/news.json?query=" + encText + "&display=" + display_num + "&start=" + start + "&sort=" + sort  # JSON 결과

    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", client_id)
    request.add_header("X-Naver-Client-Secret", client_secret)
    response = urllib.request.urlopen(request)
    rescode = response.getcode()

    if (rescode == 200):
        response_body = response.read()
        result = json.loads(response_body)
        print(result)
        return json.dumps(result, ensure_ascii=False)
    else:
        print("Error Code:" + rescode)
