import datetime
import json
import os
import urllib.request
from collections import OrderedDict
from datetime import datetime, timedelta

import FinanceDataReader as fdr
import pandas as pd
import requests
from bs4 import BeautifulSoup


def is_json_key_present(json, key):
    try:
        buf = json[key]
    except KeyError:
        return False

    return True


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


# bing 검색 API 결과를 가져오는 함수
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
    client_id = os.getenv("NAVER_CLIENT_ID")
    client_secret = os.getenv("NAVER_CLIENT_SECRET")

    encText = urllib.parse.quote(param)
    display_num = urllib.parse.quote("10")  # 한 번에 표시할 검색 결과 개수(기본값: 10, 최댓값: 100)
    start = urllib.parse.quote("1")  # 검색 시작 위치(기본값: 1, 최댓값: 1000)
    sort = urllib.parse.quote("date")  # 검색 결과 정렬 방법 - sim: 정확도순으로 내림차순 정렬 / - date: 날짜순으로 내림차순 정렬

    url = os.getenv("NAVER_API_ENDPOINT").format(encText, display_num, start, sort)  # JSON 결과

    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", client_id)
    request.add_header("X-Naver-Client-Secret", client_secret)
    response = urllib.request.urlopen(request)
    rescode = response.getcode()

    if (rescode == 200):
        response_body = response.read()
        json_str = json.loads(response_body)
        result = OrderedDict()
        article_list = []
        for article in json_str['items']:
            article_dict = OrderedDict()
            article_dict['originallink'] = article['link']
            article_dict['description'] = article['description']
            article_dict['pubDate'] = article['pubDate']
            article_list.append(article_dict)
        result['items'] = article_list
        return json.dumps(result, ensure_ascii=False, indent='\t')
    else:
        print("Error Code:" + rescode)


def search_by_item(user_input: str) -> str:
    """Naver에서 검색어로 뉴스를 검색하고 첫 번째 기사 내용을 반환합니다.

        Args:
            user_input (str): 검색어

        Returns:
            str: 첫 번째 뉴스 기사 내용 (없으면 빈 문자열)
        """
    encoded_text = urllib.parse.quote(user_input)
    url = os.getenv("NAVER_SEARCH_ENDPOINT").format(encoded_text)

    with requests.get(url) as response:  # with 문 사용
        soup = BeautifulSoup(response.content, "html.parser")  # content 사용

    first_news = soup.select_one("ul._infinite_list > li")
    if first_news is None:
        return "조회 결과가 없습니다"

    link = first_news.select_one("a.news_tit")["href"]

    with requests.get(link) as response_item:  # with 문 사용
        soup_item = BeautifulSoup(response_item.content, "html.parser")  # content 사용

    paragraphs = soup_item.select("article.story-news p")
    article = "\n".join(p.get_text() for p in paragraphs[:-1])  # Generator 표현식 사용
    return article


# dart 재무정보 검색 API
def search_by_dart_api(param):
    dart_api_key = os.getenv("DART_API_KEY")
    with open('data/CORPCODE.json', encoding='utf-8') as f:
        darts = json.load(f)
    corp_code = ''
    for corp in darts['items']:
        if param == corp['corp_name']:
            corp_code = corp['corp_code']
            break

    url = os.getenv("DART_API_ENDPOINT").format(dart_api_key, corp_code)  # JSON 결과

    request = urllib.request.Request(url)
    response = urllib.request.urlopen(request)
    result_code = response.getcode()

    if (result_code == 200):
        response_body = response.read()
        json_str = json.loads(response_body)
        info_list = []
        result = OrderedDict()
        if is_json_key_present(json_str, 'list'):
            for el in json_str['list']:
                if el['account_id'] == 'ifrs-full_Revenue' or el['account_id'] == 'ifrs-full_ProfitLoss' or el[
                    'account_id'] == 'dart_OperatingIncomeLoss':
                    info_dict = OrderedDict()
                    if is_json_key_present(el, 'sj_nm'):
                        info_dict['bsns_year'] = el['bsns_year']
                        info_dict['sj_div'] = el['sj_div']
                        info_dict['account_id'] = el['account_id']
                        info_dict['account_nm'] = el['account_nm']
                        info_dict['account_detail'] = el['account_detail']
                        info_dict['thstrm_nm'] = el['thstrm_nm']
                        info_dict['thstrm_amount'] = el['thstrm_amount']
                        info_dict['frmtrm_nm'] = el['frmtrm_nm']
                        info_dict['frmtrm_amount'] = el['frmtrm_amount']
                        info_dict['bfefrmtrm_nm'] = el['bfefrmtrm_nm']
                        info_dict['bfefrmtrm_amount'] = el['bfefrmtrm_amount']
                        info_dict['currency'] = el['currency']

                        info_list.append(info_dict)
                        result['items'] = info_list
            return json.dumps(result, ensure_ascii=False, indent='\t')
        else:
            return "No Results"
    else:
        print("Error Code:" + result_code)


# 종목명을 받아 종목코드를 찾아 반환하는 함수
def item_code_by_item_name(item_name):
    df_krx = pd.read_csv("data/krx.csv")
    item_code_list = df_krx.loc[df_krx["Name"] == item_name, "Symbol"].tolist()
    if len(item_code_list) > 0:
        item_code = item_code_list[0]
        return item_code
    else:
        return False


# 이번달 '종가'를 가져온다
def get_monthly_close_price(company_code):
    # close_list = fdr.DataReader(company_code, "2024-04-01")['Close'].values
    close_list = fdr.DataReader(company_code, datetime.today().strftime("%Y-%m-01"))['Close'].values
    close_list = close_list.astype('str')
    # close_str = ', '.join(close_list)
    # return close_str
    return close_list


def get_monthly_price(company_code):
    return fdr.DataReader(company_code, datetime.today().strftime("%Y-01-01"))


# 올해 전체 가격
def get_yearly_price(company_code):
    return (fdr.DataReader(company_code, "2024-01-01")).to_json(orient='columns')


# 현재 가격
def get_today_price(company_code):
    today = datetime.now().strftime("%Y-%m-%d")
    return fdr.DataReader(company_code, today, today)


# 올해 최저가
def get_yearly_low(company_code):
    return fdr.DataReader(company_code, "2024-01-01")['Close'].min()


# 올해 최고가
def get_yearly_high(company_code):
    return fdr.DataReader(company_code, "2024-01-01")['Close'].max()


# 올해 평균 종가
def get_avg_close(company_code):
    return fdr.DataReader(company_code, "2024-01-01")['Close'].mean()
