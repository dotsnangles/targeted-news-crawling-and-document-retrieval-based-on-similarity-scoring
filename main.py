import json
import os
import argparse
import pandas as pd
from tqdm import tqdm
from module.crawler import get_news_list, crawl_news
from module.preprocess import preprocess
from module.utils import filter_time
from module.retrieve import retrieve_docs
from module.visualize import save_pie_chart, save_wordclouds

### 사용 예시
### python main.py --keyword '인공지능' --org '문화체육관광부' --business '클라썸'
### python main.py --keyword '영화' --org '문화체육관광부' --business '명필름'

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

    ### 크롤링 타겟 설정
    targets = gov_orgs[args.org]
    targets += [args.business]

    ### 하위기관명과 키워드 조합 / 비지니스명과 키워드 조합 크롤링 수행
    crawled_news_dfs = []
    for target in tqdm(targets):
        news_list_df = get_news_list(target, args.keyword, client_id, client_secret)
        if type(news_list_df) == type(None):
            continue
        ### 90일 전까지의 기사만 필터링합니다.
        news_list_df = filter_time(news_list_df)
        
        crawled_news_df = crawl_news(target, args.keyword, news_list_df, headers)
        crawled_news_dfs.append(crawled_news_df)
    if len(crawled_news_dfs) == 0:
        print('크롤링 결과가 존재하지 않습니다. 오류 로그를 확인하세요.')
        return
    crawling_result = pd.concat(crawled_news_dfs)

    ### 간단한 전처리를 진행합니다.
    crawling_result = preprocess(crawling_result)

    ### 크롤링 데이터 저장하기
    SAVE_ROOT = os.path.join('results', '_'.join([args.keyword, args.org, args.business]))
    os.makedirs(SAVE_ROOT, exist_ok=True)
    
    save_name = f'{"_".join([args.keyword, args.org, args.business])}_crawled.csv'
    crawling_result.to_csv(os.path.join(SAVE_ROOT, save_name), index=False, encoding='utf-8-sig')
    print(f'크롤링이 완료되었습니다. 다음 파일을 생성했습니다.')
    print(f'{os.path.join(SAVE_ROOT, save_name)}')
    
    ### 유사도 점수 기반 리트리벌 시작
    print('문서간 유사도 검사를 수행합니다.')
    top_of_business_news_contents, tops_of_org_news_contents_splits, result = retrieve_docs(args.business, crawling_result)
    if type(top_of_business_news_contents) == type(None):
        return

    ### 유사도 점수 기반 리트리벌 결과 저장하기
    top_of_business_news_contents.to_csv(os.path.join(SAVE_ROOT, 'top_scored_business_news.csv'), index=False, encoding='utf-8-sig')
    tops_of_org_news_contents_splits.to_csv(os.path.join(SAVE_ROOT, 'list_of_top_scored_org_news.csv'), index=False, encoding='utf-8-sig')
    result.to_csv(os.path.join(SAVE_ROOT, 'top_orgs_and_their_news.csv'), index=False, encoding='utf-8-sig')

    print('문서간 유사도 검사가 완료되었습니다. 다음 폴더에 결과물을 저장합니다.')
    print(f'저장 폴더: {SAVE_ROOT}')

    save_pie_chart(result, SAVE_ROOT)
    save_wordclouds(result, SAVE_ROOT)
    
if __name__ == '__main__':
    main()