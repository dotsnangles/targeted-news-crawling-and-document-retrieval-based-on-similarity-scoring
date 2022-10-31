import json
import argparse
import pandas as pd
from module.crawler import get_news_list, crawl_news

### python main.py --query '키워드' --org '기관명'

def main():
    client_id = 'hwEnzlSdGXZTyeubesmy'
    client_secret = 'WkpCvqbw6u'

    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36',
        'cookie': 'nid_inf=1417715440; NID_AUT=jB6JKkl0bQJkzabA2sqcsZPcc58lN3Nk/oKjGyVYl1n8PedB7ujlxHdECKcm9kS7; NID_JKL=CdIfrElqYRkes7uT/S10prytLgVd7C1HBLS0nz55Sys=; VISIT_LOG_CLEAN=1; NFS=2; NID_SES=AAABkxQsSdlab5VkBVUMJHd12mikXaT/HRo/rtzzaxgjXmXJLfOFG25S5TiaZsFNk5bLeRF4Ej3UoZTevQC7Jd7fVFOAFJtSFoNgapi8qqUTVHDqzpWo4zUjmx/LD5cdsWbvaL/cByCai8XYLRLdB0o6W7sQutPmRMFUblZMKU/CdpBh8aziLA/i9wHRgkCr4zpYxc/YROLyZLZ7QmphI5qakKYHN4OxNKYy/Dp+PvlCsWk6azoXw7AxABwR/NdLMwDxNgZ6yN0iUJDkWFFPEN0yBGCm5VaOa1oF4tU0GkLMQsbyMb/+mOw6aBjxQNSgS5RDsn3Vs6H9l1qczNtasU4OpdonIK0EzoLYyQEgLkpXeLTnzkdaJnqR7EyjKjl8hH/EsaVdnRaAEs0afY3VK8f+pCn0z/5n9xpiCd0UVrpoI3nwF1No4x/mEk71EW2ghH90hyg/9F0KHAHLneYZ6lCvcdhE/ENHrmc1nP0R0sUnOltV0XIyf0fEua7rvSqv0P0iuE0xD2+WUqh//96WFUP+XyeQxvn16XPBT8PSfE/nU/FQ; nx_ssl=2; page_uid=h1WRNsp0YiRssKvZbrNssssssMh-389234; BMR='
    }

    with open('government_organization_chart.json', encoding='utf-8') as f:
        gov_orgs = json.load(f)

    parser = argparse.ArgumentParser()
    parser.add_argument("--query", dest="query", action="store")
    parser.add_argument("--org", dest="org", action="store")
    args = parser.parse_args()

    query = args.query
    org_name = args.org
    sub_orgs = gov_orgs[args.org]

    crawling_trgs = []
    for sub_org in sub_orgs:
        crawling_trg = ' '.join([org_name, sub_org, query])
        crawling_trgs.append(crawling_trg)

    crawled_news_dfs = []
    for crawling_trg in crawling_trgs:
        news_list_df = get_news_list(crawling_trg, client_id, client_secret)
        crawled_news_df = crawl_news(news_list_df, headers)
        crawled_news_dfs.append(crawled_news_df)
        
    result = pd.concat(crawled_news_dfs)

    search_sub_org = result.body.str.contains('|'.join(sub_orgs), case=False, regex=True)
    search_query = result.body.str.contains(query, case=False, regex=True)
    result = result[search_sub_org & search_query]

    result.to_csv(f'{"_".join([query, org_name])}_crawled.csv', index=False)

if __name__ == '__main__':
    main()