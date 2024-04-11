from function import PatternFinder


def getPrompt(company_code, start_date, end_date):
    '''
    올해 최저가/최고가/평균가를 구하는 프롬프트
    '''

    # 페르소나
    persona = "너의 페르소나는 주식 애널리스트야. 반드시 애널리스트처럼 생각하고 행동해야돼. "

    # 맥락
    context = "나는 주식투자를 해본 적 없고, 주식투자를 통해 자산을 늘려보려고 해. "

    #작업
    task = "'현재가격'은 내가 처음에 전달한 LiteralString 중 제일 '마지막' 글자이고, 내가 말한 기간 동안의 최저가격, 최고가격, 평균가격, '현재가격'을 알려줘."

    #예시
    example = ""

    #형식
    form = ""

    #어조
    tone = "확실하게 이해할 수 있도록 전문 애널리스트 톤으로 대답해줘. "

    #그냥 읽어줄 것
    p = PatternFinder()
    p.set_stock(company_code)
    result = p.search(start_date, end_date)
    pred = p.stat_prediction(result)
    text = p.plot_pattern(result.index[1])
    speak = "그리고 이 문장은 그대로 읽어줘. '유사도 98%이상인 과거 차트에 대입시, 5일후 주가 전망은 " + str(text) + "' 입니다."

    prompt = persona + context + task + example + form + tone + speak


    return prompt
