import torch
from sentence_transformers import SentenceTransformer, util
import pandas as pd
import numpy as np

### 모델과 토크나이저를 SentenceTransformer 클래스로 불러옵니다.
pretrained_model_path = "sbert/training_klue_sts_klue-roberta-base-2022-08-17_23-27-13"
model = SentenceTransformer(pretrained_model_path)

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

def retrieve_docs(query, business_name, crawling_result):
    ### crawling_trg에 business_name 이름이 있는 것과 없는 것을 구분하여 데이터를 나눕니다.
    crawling_result['checker'] = crawling_result.crawling_trg.str.find(business_name)

    bussiness_news = crawling_result[crawling_result.checker > -1].copy().reset_index(drop=True)
    bussiness_news['idx_original'] = range(len(bussiness_news))

    org_news = crawling_result[crawling_result.checker == -1].copy().reset_index(drop=True)
    org_news['idx_original'] = range(len(org_news))

    business_news_contents = bussiness_news[['idx_original', 'crawling_trg', 'pubDate', 'title', 'content', 'link']]
    org_news_contents = org_news[['idx_original', 'crawling_trg', 'pubDate', 'title', 'content', 'link']]

    ### 쿼리와 business_name 문서 뭉치 간의 유사도 점수를 계산하여 가장 높은 점수의 business_name 문서를 찾아옵니다.
    indices, scores = get_indices_and_scores(query, business_news_contents, 1)
    top_of_business_news_contents = business_news_contents.iloc[int(indices)].to_list() + list([float(scores)])
    top_of_business_news_contents = pd.DataFrame([top_of_business_news_contents], columns=['idx_original', 'crawling_trg', 'pubDate', 'title', 'content', 'link', 'score'])

    ### 기관별로 데이터를 나눕니다.
    org_news_contents_splits = []
    for org in org_news_contents.crawling_trg.unique():
        org_news_contents_split = org_news_contents[org_news_contents.crawling_trg == org].reset_index(drop=True).copy()
        org_news_contents_splits.append(org_news_contents_split)

    ### 쿼리와 각 기관별 문서 뭉치간의 유사도 점수를 계산하여 기관별 가장 높은 점수의 문서를 찾아옵니다.
    tops_of_org_news_contents_splits = []
    for org_news_contents_split in org_news_contents_splits:
        indices, scores  = get_indices_and_scores(query, org_news_contents_split, 1)
        top_of_org_news_contents_split = org_news_contents_split.iloc[int(indices)].to_list() + list([float(scores)])
        tops_of_org_news_contents_splits.append(top_of_org_news_contents_split)
        
    tops_of_org_news_contents_splits = pd.DataFrame(tops_of_org_news_contents_splits, columns=['idx_original', 'crawling_trg', 'pubDate', 'title', 'content', 'link', 'score'])
    tops_of_org_news_contents_splits = tops_of_org_news_contents_splits.sort_values('score', ascending=False).reset_index(drop=True).copy()

    ### 가장 높은 점수의 business_name 문서를 쿼리로 하여 
    ### 가장 높은 점수의 기관별 문서 뭉치와 유사도 점수를 계산하고 유사도 점수 상위 5개 문서를 찾아옵니다.
    indices, scores = get_indices_and_scores(top_of_business_news_contents.content.iloc[0], tops_of_org_news_contents_splits, 5)
    result = tops_of_org_news_contents_splits.iloc[list(indices)].copy()
    result['score'] = scores

    return top_of_business_news_contents, tops_of_org_news_contents_splits, result
