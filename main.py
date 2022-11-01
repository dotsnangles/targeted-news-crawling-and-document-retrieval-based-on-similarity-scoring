import json
import argparse
import pandas as pd
from tqdm import tqdm
from module.crawler import get_news_list, crawl_news
from module.preprocess import preprocess
from module.utils import filter_time

### 사용 예시
### python main.py --query '인공지능' --org '문화체육관광부' --business '클라썸'

def main():
    ### Naver API 사용을 위한 ID와 Key
    client_id = 'hwEnzlSdGXZTyeubesmy'
    client_secret = 'WkpCvqbw6u'

    ### Crawling을 위한 Header 설정
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36',
        'cookie': 'nid_inf=1417715440; NID_AUT=jB6JKkl0bQJkzabA2sqcsZPcc58lN3Nk/oKjGyVYl1n8PedB7ujlxHdECKcm9kS7; NID_JKL=CdIfrElqYRkes7uT/S10prytLgVd7C1HBLS0nz55Sys=; VISIT_LOG_CLEAN=1; NFS=2; NID_SES=AAABkxQsSdlab5VkBVUMJHd12mikXaT/HRo/rtzzaxgjXmXJLfOFG25S5TiaZsFNk5bLeRF4Ej3UoZTevQC7Jd7fVFOAFJtSFoNgapi8qqUTVHDqzpWo4zUjmx/LD5cdsWbvaL/cByCai8XYLRLdB0o6W7sQutPmRMFUblZMKU/CdpBh8aziLA/i9wHRgkCr4zpYxc/YROLyZLZ7QmphI5qakKYHN4OxNKYy/Dp+PvlCsWk6azoXw7AxABwR/NdLMwDxNgZ6yN0iUJDkWFFPEN0yBGCm5VaOa1oF4tU0GkLMQsbyMb/+mOw6aBjxQNSgS5RDsn3Vs6H9l1qczNtasU4OpdonIK0EzoLYyQEgLkpXeLTnzkdaJnqR7EyjKjl8hH/EsaVdnRaAEs0afY3VK8f+pCn0z/5n9xpiCd0UVrpoI3nwF1No4x/mEk71EW2ghH90hyg/9F0KHAHLneYZ6lCvcdhE/ENHrmc1nP0R0sUnOltV0XIyf0fEua7rvSqv0P0iuE0xD2+WUqh//96WFUP+XyeQxvn16XPBT8PSfE/nU/FQ; nx_ssl=2; page_uid=h1WRNsp0YiRssKvZbrNssssssMh-389234; BMR='
    }

    ### 기관 정보 불러오기
    with open('government_organization_chart.json', encoding='utf-8') as f:
        gov_orgs = json.load(f)

    ### Argument Parsing
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", dest="query", action="store")
    parser.add_argument("--business", dest="business", action="store")
    parser.add_argument("--org", dest="org", action="store")
    args = parser.parse_args()

    query = args.query
    business_name = args.business
    org_name = args.org
    sub_orgs = gov_orgs[args.org]

    ### 입력으로 받은 상위기관의 하위기관-검색어 조합 생성
    crawling_trgs = []
    for sub_org in sub_orgs:
        crawling_trg = ' '.join([sub_org, query])
        crawling_trgs.append(crawling_trg)

    ### 사업체-검색어 조합을 크롤링 목록에 추가
    crawling_trgs.append(' '.join([business_name, query]))
    print(crawling_trgs)

    ### get_news_list와 crawl_news로 Crawling 진행
    crawled_news_dfs = []
    for crawling_trg in tqdm(crawling_trgs):
        news_list_df = get_news_list(crawling_trg, client_id, client_secret)
        if type(news_list_df) != type(None):
            ### 90일 전까지의 기사만 필터링합니다.
            news_list_df = filter_time(news_list_df)
            
            crawled_news_df = crawl_news(news_list_df, headers)
            crawled_news_dfs.append(crawled_news_df)
        
    result = pd.concat(crawled_news_dfs)

    ### 제외 if not (하위기관명 and 검색어) in 뉴스본문
    search_sub_org = result.content.str.contains('|'.join(sub_orgs+[business_name]), case=False, regex=True)
    search_query = result.content.str.contains(query, case=False, regex=True)
    result = result[search_sub_org & search_query].copy().reset_index(drop=True)
    
    ### 간단한 전처리를 진행합니다.
    result = preprocess(result)

    ### 저장하기
    save_name = f'{"_".join([query, org_name, business_name])}_crawled.csv'
    result.to_csv(save_name, index=False, encoding='utf-8-sig')
    
    # print(f'검색어 {query}, 상위기관명 {org_name}으로 총 {len(result)}건이 수집되었습니다.')
    print(save_name)
    
if __name__ == '__main__':
    main()