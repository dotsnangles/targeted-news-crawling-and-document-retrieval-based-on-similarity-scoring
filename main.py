import json
import argparse
import pandas as pd
from tqdm import tqdm
from module.crawler import get_news_list, crawl_news
from module.preprocess import preprocess
from module.utils import filter_time
from module.retrieve import retrieve_docs

### 사용 예시
### python main.py --keyword '인공지능' --org '문화체육관광부' --business '클라썸'

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
    parser.add_argument("--keyword", dest="keyword", action="store")
    parser.add_argument("--business", dest="business", action="store")
    parser.add_argument("--org", dest="org", action="store")
    args = parser.parse_args()

    keyword = args.keyword
    business_name = args.business
    org_name = args.org
    sub_orgs = gov_orgs[args.org]
    sub_orgs += [business_name]

    ### 하위기관명과 키워드 조합 / 비지니스명과 키워드 조합 크롤링 수행
    crawled_news_dfs = []
    for sub_org in tqdm(sub_orgs):
        news_list_df = get_news_list(sub_org, keyword, client_id, client_secret)
        if type(news_list_df) != type(None):
            ### 90일 전까지의 기사만 필터링합니다.
            news_list_df = filter_time(news_list_df)
            
            crawled_news_df = crawl_news(sub_org, keyword, news_list_df, headers)
            crawled_news_dfs.append(crawled_news_df)
        
    crawling_result = pd.concat(crawled_news_dfs)

    ### 간단한 전처리를 진행합니다.
    crawling_result = preprocess(crawling_result)

    ### 저장하기
    save_name = f'{"_".join([keyword, org_name, business_name])}_crawled.csv'
    crawling_result.to_csv(save_name, index=False, encoding='utf-8-sig')
    print(f'크롤링이 완료되었습니다. 다음 파일을 생성했습니다.')
    print(f'{save_name}')
    
    print('문서간 유사도 검사를 수행합니다.')
    top_of_business_news_contents, tops_of_org_news_contents_splits, result = retrieve_docs(business_name, crawling_result)

    top_of_business_news_contents.to_csv('top_scored_business_news.csv', index=False, encoding='utf-8-sig')
    tops_of_org_news_contents_splits.to_csv('list_of_top_scored_org_news.csv', index=False, encoding='utf-8-sig')
    result.to_csv('top_5_orgs_and_their_news.csv', index=False, encoding='utf-8-sig')
    
    print('문서간 유사도 검사가 완료되었습니다. 다음 파일을 생성했습니다.')
    print('top_scored_business_news_for_keyword.csv')
    print('list_of_top_scored_org_news_for_keyword_by_org.csv')
    print('top_5_orgs_and_their_news_for_top_scored_business_news.csv')
    
if __name__ == '__main__':
    main()