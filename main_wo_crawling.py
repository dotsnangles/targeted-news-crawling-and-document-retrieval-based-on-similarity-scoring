import os
import argparse
import pandas as pd
from module.retrieve import retrieve_docs
from module.visualize import save_pie_chart, save_wordclouds

### 사용 예시
### python main_wo_crawling.py --file 'results/인공지능_문화체육관광부_클라썸/인공지능_문화체육관광부_클라썸_crawled.csv' --path '인공지능_문화체육관광부_클라썸_test_wo_crawling_v2'

def main():
    ### Argument Parsing
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", dest="file", action="store")
    parser.add_argument("--path", dest="path", action="store")
    args = parser.parse_args()

    crawling_result = pd.read_csv(args.file)
    business_name = crawling_result.target.iloc[-1]

    SAVE_ROOT = os.path.join('results', args.path)
    os.makedirs(SAVE_ROOT, exist_ok=True)
    
    print('문서간 유사도 검사를 수행합니다.')
    top_of_business_news_contents, tops_of_org_news_contents_splits, result = retrieve_docs(business_name, crawling_result)
    if type(top_of_business_news_contents) == type(None):
        return

    top_of_business_news_contents.to_csv(os.path.join(SAVE_ROOT, 'top_scored_business_news.csv'), index=False, encoding='utf-8-sig')
    tops_of_org_news_contents_splits.to_csv(os.path.join(SAVE_ROOT, 'list_of_top_scored_org_news.csv'), index=False, encoding='utf-8-sig')
    result.to_csv(os.path.join(SAVE_ROOT, 'top_5_orgs_and_their_news.csv'), index=False, encoding='utf-8-sig')
    
    print('문서간 유사도 검사가 완료되었습니다. 다음 폴더에 결과물을 저장합니다.')
    print(f'저장 폴더: {SAVE_ROOT}')

    save_pie_chart(result, SAVE_ROOT)
    save_wordclouds(result, SAVE_ROOT)
    
if __name__ == '__main__':
    main()