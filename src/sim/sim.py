# -*- coding: utf-8 -*-
import numpy as np
 
#わかち書き関数
def wakachi(text):
    from janome.tokenizer import Tokenizer
    t = Tokenizer()
    tokens = t.tokenize(text)
    docs=[]
    for token in tokens:
        docs.append(token.surface)
    return docs
 
#文書ベクトル化関数
def vecs_array(documents):
    from sklearn.feature_extraction.text import TfidfVectorizer
 
    docs = np.array(documents)
    vectorizer = TfidfVectorizer(analyzer=wakachi,binary=True,use_idf=False)
    vecs = vectorizer.fit_transform(docs)
    return vecs.toarray()


def read_docs():

    import os
    import json

    dir_path = "./NASA_Standards"


    files_file = [
        f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))
    ]

    lis = []
    for name in files_file:
        if name.endswith(".txt"):
            lis.append(name)



    docs_info = { "info": lis }
    with open('docs_info.json', 'w') as f:
        f.write(json.dumps(docs_info))


    docs = []
    for name in lis:

        with open("{}/{}".format(dir_path,name), 'r') as f:
            cont = f.read()
            docs.append(cont)

    return docs

def cal_sim():
    from sklearn.metrics.pairwise import cosine_similarity
    import json

    # テスト用との切り替え
    
    docs = read_docs()

    # docs = [
    # "私は犬が好きです。",
    # "私は犬が嫌いです。",
    # "私は犬のことがとても好きです。"]
 
    #類似度行列作成
    cs_array = np.round(cosine_similarity(vecs_array(docs), vecs_array(docs)),3)

    # 書き出し
    array = []
    for _line in cs_array:
        line = []
        for _item in _line:
            line.append(_item)
        array.append(line)

    cont = {'array': array}
    with open('array.json', 'w') as f:
        f.write(json.dumps(cont))

def show_info():
    import json    

    # 類似度行列の読み込み
    with open('array.json', 'r') as f:
        cont = json.loads(f.read())

    array = cont['array']

    # ドキュメント情報の読み込み
    with open('docs_info.json', 'r') as f:
        cont = json.loads(f.read())

    docs_info = cont['info']

    row_num = 0
    lis = []
    for row in array:
        col_num = 0        
        for col in row:
            item = { 'val': col,
                     'col': col_num,
                     'row': row_num
                    }
            lis.append(item)
            col_num += 1

        row_num += 1


    sorted_data = sorted(lis, key=lambda item: item['val'], reverse=True)

    lis = []
    for data in sorted_data:
        if data['val'] == 1 or data['val'] == 0.0:
            continue

        data['col'] = docs_info[data['col']]
        data['row'] = docs_info[data['row']]
        
        lis.append(data)

    for data in lis:
        print(data)



 
if __name__ == '__main__':
    
    show_info()
