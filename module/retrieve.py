import torch
from sentence_transformers import SentenceTransformer, util
from gensim.corpora import Dictionary
import pandas as pd
import numpy as np

### 모델과 토크나이저를 SentenceTransformer 클래스로 불러옵니다.
pretrained_model_path = "sbert/training_klue_sts_klue-roberta-base-2022-08-17_23-27-13"
model = SentenceTransformer(pretrained_model_path)

def make_bow(query, articles):
    name = articles.crawling_trg.unique()[0].split('[SEP]')[0].strip()
    print(name)
    articles['content'] = articles.content.str.replace(name, ''.join(name.split()))
    name = ''.join(name.split())
    print(name)
    articles = articles.content.apply(lambda x: x.split()).to_list().copy()
    articles = [[word if not (query in word) else query for word in article] for article in articles]
    articles = [[word if not (name in word) else name for word in article] for article in articles]

    dct = Dictionary(articles)  # fit dictionary
    bow_articles = [dct.doc2bow(article) for article in articles]  # convert corpus to BoW format
    bow_articles = [{k:v for k, v in bow_article} for bow_article in bow_articles]
    
    return name, dct, bow_articles

def id_by_tf_retrieve(query, name, dct, bow_articles, query_th=0, name_th=0):
    query_id = dct.token2id[query]
    query_tfs = []
    for bow_article in bow_articles:
        query_tfs.append(bow_article[query_id])
    query_tfs = np.array(query_tfs)

    name_id = dct.token2id[name]
    name_tfs = []
    for bow_article in bow_articles:
        try:
            name_tfs.append(bow_article[name_id])
        except Exception as e:
            print(e)
    name_tfs = np.array(name_tfs)
    
    tf_pairs = [(q, n) for q, n in zip(query_tfs, name_tfs)]
    ids = {}
    for id, tf_pair in enumerate(tf_pairs):
        query_tf, name_tf = tf_pair[0], tf_pair[1]
        if query_tf >= query_th and name_tf >= name_th:
            ids[id] = query_tfs[id] + name_tfs[id]
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

def retrieve_docs(query, business_name, crawling_result):
    ### crawling_trg에 business_name 이름이 있는 것과 없는 것을 구분하여 데이터를 나눕니다.
    crawling_result['checker'] = crawling_result.crawling_trg.str.find(business_name)

    bussiness_news = crawling_result[crawling_result.checker > -1].copy().reset_index(drop=True)
    bussiness_news['idx_original'] = range(len(bussiness_news))

    org_news = crawling_result[crawling_result.checker == -1].copy().reset_index(drop=True)
    org_news['idx_original'] = range(len(org_news))

    business_news_contents = bussiness_news[['idx_original', 'crawling_trg', 'pubDate', 'title', 'content', 'link']]
    org_news_contents = org_news[['idx_original', 'crawling_trg', 'pubDate', 'title', 'content', 'link']]
    
    
    ### 비지니스명과 쿼리의 term frequency threshold를 충족한 기사 중 term frequency의 합계가 가장 높은 기사를 가지고 옵니다.(중복시 첫 번째)
    name, dct, bow_articles = make_bow(query, business_news_contents)
    doc_id, tf_score = id_by_tf_retrieve(query, name, dct, bow_articles, query_th=1, name_th=3)
    if doc_id == None:
        print(f'{name}: 주목할 만한 기사 없음.')
        print('프로그램을 종료합니다.')
        return None
    else:
        top_of_business_news_contents = business_news_contents.iloc[doc_id].to_list() + list([tf_score])
        top_of_business_news_contents = pd.DataFrame([top_of_business_news_contents], columns=['idx_original', 'crawling_trg', 'pubDate', 'title', 'content', 'link', 'score'])

    ### 기관별로 데이터를 나눕니다.
    org_news_contents_splits = []
    for org in org_news_contents.crawling_trg.unique():
        org_news_contents_split = org_news_contents[org_news_contents.crawling_trg == org].reset_index(drop=True).copy()
        org_news_contents_splits.append(org_news_contents_split)

    ### 각 기관별 수행. 기관명과 쿼리의 term frequency threshold를 충족한 기사 중 term frequency의 합계가 가장 높은 기사를 가지고 옵니다.(중복시 첫 번째)
    tops_of_org_news_contents_splits = []
    for org_news_contents_split in org_news_contents_splits:
        name, dct, bow_articles = make_bow(query, org_news_contents_split)
        doc_id, tf_score = id_by_tf_retrieve(query, name, dct, bow_articles, query_th=2, name_th=3)
        if doc_id == None:
            print(f'{name}: 주목할 만한 기사 없음.')
            print()
            continue
        top_of_org_news_contents_split = org_news_contents_split.iloc[doc_id].to_list() + list([tf_score])
        tops_of_org_news_contents_splits.append(top_of_org_news_contents_split)

    if len(tops_of_org_news_contents_splits) == 0:
        print('검색한 상위 기관에 대하여 주목할 만한 기사 없음.')
        print('프로그램을 종료합니다.')
        return None
    
    tops_of_org_news_contents_splits = pd.DataFrame(tops_of_org_news_contents_splits, columns=['idx_original', 'crawling_trg', 'pubDate', 'title', 'content', 'link', 'score'])
    tops_of_org_news_contents_splits = tops_of_org_news_contents_splits.sort_values('score', ascending=False).reset_index(drop=True).copy()

    ### 가장 높은 점수의 business_name 문서를 쿼리로 하여 
    ### 가장 높은 점수의 기관별 문서 뭉치와 유사도 점수를 계산하고 유사도 점수 상위 5개 문서를 찾아옵니다.
    indices, scores = get_indices_and_scores(top_of_business_news_contents.content.iloc[0], tops_of_org_news_contents_splits, 5)
    result = tops_of_org_news_contents_splits.iloc[list(indices)].copy()
    result['score'] = scores

    return top_of_business_news_contents, tops_of_org_news_contents_splits, result