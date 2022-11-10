import torch
from sentence_transformers import SentenceTransformer, util
from gensim.corpora import Dictionary
import pandas as pd
import numpy as np

### 모델과 토크나이저를 SentenceTransformer 클래스로 불러옵니다.
pretrained_model_path = "sbert/training_klue_sts_klue-roberta-base-2022-08-17_23-27-13"
model = SentenceTransformer(pretrained_model_path)

def id_by_tf_retrieve(df, keyword_th=0, name_th=0):
    keyword = df.keyword.unique()[0]
    name = df.target.unique()[0]

    keyword_tfs = df.content.str.count(keyword).tolist()
    name_tfs = df.content.str.count(name).tolist()

    tf_pairs = [(q, n) for q, n in zip(keyword_tfs, name_tfs)]
    ids = {}
    for id, tf_pair in enumerate(tf_pairs):
        keyword_tf, name_tf = tf_pair[0], tf_pair[1]
        if keyword_tf >= keyword_th and name_tf >= name_th:
            ids[id] = keyword_tfs[id] + name_tfs[id]
    if bool(ids) == False:
        return None, None
    
    doc_id = max(ids, key=ids.get)
    tf_score = max(ids.values())

    return doc_id, tf_score

### 유사도를 계산하여 인덱스와 스코어를 반환하는 함수입니다.
def get_indices_and_scores(query, news_contents, top_k):
    with torch.no_grad():
        query_embedding = model.encode(query)
        query_embedding = np.expand_dims(query_embedding, axis=0)
        news_embeddings = model.encode(news_contents.content)
        cos_scores = util.pytorch_cos_sim(query_embedding, news_embeddings).squeeze()

        top_k = min(top_k, len(news_contents.content))
        top_k_results = torch.topk(cos_scores, k=top_k)

        scores = top_k_results.values.squeeze()
        indices = top_k_results.indices.squeeze()

    return indices, scores

### 유사도 점수에 기반하여 문서를 찾아옵니다.

def retrieve_docs(business_name, crawling_result):
    ### target 칼럼에 business_name 이름이 있는 것과 없는 것을 구분하여 데이터를 나눕니다.
    crawling_result['checker'] = crawling_result.target.str.find(business_name)

    bussiness_news = crawling_result[crawling_result.checker > -1].copy().reset_index(drop=True)
    bussiness_news['idx_original'] = range(len(bussiness_news))

    org_news = crawling_result[crawling_result.checker == -1].copy().reset_index(drop=True)
    org_news['idx_original'] = range(len(org_news))

    business_news_contents = bussiness_news[['idx_original', 'target', 'keyword', 'pubDate', 'title', 'content', 'link']]
    org_news_contents = org_news[['idx_original', 'target', 'keyword', 'pubDate', 'title', 'content', 'link']]
    
    ### 비지니스명과 쿼리의 term frequency threshold를 충족한 기사 중 term frequency의 합계가 가장 높은 기사를 가지고 옵니다.(중복시 첫 번째)
    doc_id, tf_score = id_by_tf_retrieve(business_news_contents, keyword_th=1, name_th=2)
    if doc_id == None:
        print(f'{business_name}: 주목할 만한 기사 없음.')
        print('프로그램을 종료합니다.')
        return None
    else:
        top_of_business_news_contents = business_news_contents.iloc[doc_id].to_list() + list([tf_score])
        top_of_business_news_contents = pd.DataFrame([top_of_business_news_contents], columns=['idx_original', 'target', 'keyword', 'pubDate', 'title', 'content', 'link', 'score'])

    ### 기관별로 데이터를 나눕니다.
    org_news_contents_splits = []
    for org in org_news_contents.target.unique():
        org_news_contents_split = org_news_contents[org_news_contents.target == org].reset_index(drop=True).copy()
        org_news_contents_splits.append(org_news_contents_split)

    ### 각 기관별 수행. 기관명과 쿼리의 term frequency threshold를 충족한 기사 중 term frequency의 합계가 가장 높은 기사를 가지고 옵니다.(중복시 첫 번째)
    tops_of_org_news_contents_splits = []
    for org_news_contents_split in org_news_contents_splits:
        target_name = org_news_contents_split.target.unique()[0]
        doc_id, tf_score = id_by_tf_retrieve(org_news_contents_split, keyword_th=2, name_th=3)
        if doc_id == None:
            print(f'{target_name}: 주목할 만한 기사 없음.')
            print()
            continue
        top_of_org_news_contents_split = org_news_contents_split.iloc[doc_id].to_list() + list([tf_score])
        tops_of_org_news_contents_splits.append(top_of_org_news_contents_split)

    if len(tops_of_org_news_contents_splits) == 0:
        print('검색한 상위 기관에 대하여 주목할 만한 기사 없음.')
        print('프로그램을 종료합니다.')
        return None
    
    tops_of_org_news_contents_splits = pd.DataFrame(tops_of_org_news_contents_splits, columns=['idx_original', 'target', 'keyword', 'pubDate', 'title', 'content', 'link', 'score'])
    tops_of_org_news_contents_splits = tops_of_org_news_contents_splits.sort_values('score', ascending=False).reset_index(drop=True).copy()

    ### 가장 높은 점수의 비지니스 뉴스를 쿼리로 하여 
    ### 가장 높은 점수를 받은 기관별 뉴스 뭉치와 유사도 점수를 계산하고 유사도 점수 상위 5개 문서를 찾아옵니다.
    indices, scores = get_indices_and_scores(top_of_business_news_contents.content.iloc[0], tops_of_org_news_contents_splits, 5)
    result = tops_of_org_news_contents_splits.iloc[list(indices)].copy()
    result['score'] = scores

    return top_of_business_news_contents, tops_of_org_news_contents_splits, result