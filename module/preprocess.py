### remove charactor entities and html tags then shrink whitespaces
def preprocess(df):
    pat = r'(&[a-z]{1,9};)|(</?[a-z]{1,9}>)'
    
    title = df.title.str.replace(pat, '', regex=True)
    title = title.replace(r'\xa0', ' ', regex=True)
    title = title.str.replace(r' +', ' ', regex=True)
    df['title'] = title.apply(lambda x: x.strip())
    
    description = df.description.str.replace(pat, '', regex=True)
    description = description.replace(r'\xa0', ' ', regex=True)
    description = description.str.replace(r' +', ' ', regex=True)
    df['description'] = description.apply(lambda x: x.strip())

    content = df.content.str.replace(pat, '', regex=True)
    content = content.str.replace(r'\xa0', ' ', regex=True)
    content = content.str.replace(r' +', ' ', regex=True)
    df['content'] = content.apply(lambda x: x.strip())
    
    return df