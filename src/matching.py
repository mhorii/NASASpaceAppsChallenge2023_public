import openai
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import json

openai.api_key = '<YOUR OWN API KEY>'

# 文書ベクトル化関数
def vecs_array(documents):
 
    docs = np.array(documents)
    # vectorizer = TfidfVectorizer(analyzer=wakachi,binary=True,use_idf=False)
    vectorizer = TfidfVectorizer(binary=True,use_idf=False)    
    vecs = vectorizer.fit_transform(docs)
    return vecs.toarray()

def split_list(input_list, chunk_size):
    it = iter(input_list)
    return [list(chunk) for chunk in zip(*[it] * chunk_size)]

def atoms(formula_list):

    all_atoms = {}
    for formula in formula_list:
        atoms = formula['atoms']

        for atom in atoms:
            # そのatomが含まれているformulaを入れとく
            atom['formula'] = formula
            all_atoms[atom['id']] = atom

    # atomのidがキーになり、そのatomが含まれているformulaがvalueになる

    return all_atoms
    

def review_with_tfidf(kdb, target):
    
    kdb_atoms = atoms(kdb)
    target_atoms = atoms(target)

    # それぞれの配列の番地が対応している
    kdb_symbol_table = []
    kdb_description_table = []
    for atom in kdb_atoms:
        # atom(symbol)がキーになる
        desc = kdb_atoms[atom]['description']
        kdb_symbol_table.append(atom)
        kdb_description_table.append(desc)

    target_symbol_table = []
    target_description_table = []
    for atom in target_atoms:
        # atom(symbol)がキーになる        
        desc = target_atoms[atom]['description']
        target_symbol_table.append(atom)
        target_description_table.append(desc)

    print(len(kdb_description_table))
    print(len(target_description_table))

    docs = kdb_description_table + target_description_table
    symbols = kdb_symbol_table + target_symbol_table

    # 類似度行列作成
    cs_array = np.round(cosine_similarity(vecs_array(docs), vecs_array(docs)),3)

    result_list = []
    row_count = 0
    col_count = 0
    for row in cs_array:
        col_count = 0
        for col in row:
            val = col
            result = {'atom_in_kdb': symbols[row_count], 'atom_in_target': symbols[col_count], 'value': val}
            result_list.append(result)
            col_count = col_count + 1

        row_count = row_count + 1

    reduced_result = []
    for result in result_list:
        # 1.0は自分自身であり、いらないので消す
        # 0もいらない
        if result['value'] == 1.0 or result['value'] == 0:
            continue

        sym1 = result['atom_in_kdb']
        sym2 = result['atom_in_target']

        # 同じドキュメント間で比較してもしょうがない
        # atom_in_kdbとatom_in_targetが別々のドキュメントであれば、残す
        # kdb_atoms、target_atomsのキーが存在するかどうかで判定する。
        if sym1 in kdb_atoms:
            # sym1はkdb側のatom
            sym1_is_in = "kdb"
            desc_sym1 = kdb_atoms[sym1]['description']
        else:
            # sym1はtarget側のatom            
            sym1_is_in = "target"
            desc_sym1 = target_atoms[sym1]['description']            

        if sym2 in kdb_atoms:
            # sym2はkdb側のatom
            sym2_is_in = "kdb"
            desc_sym2 = kdb_atoms[sym2]['description']            
        else:
            # sym2はtarget側のatom            
            sym2_is_in = "target"
            desc_sym2 = target_atoms[sym2]['description']                        

        # 両方kdb、あるいは両方targetどおしで比較しても意味がない
        if sym1_is_in == sym2_is_in:
            continue

        result['description_kdb'] = desc_sym1
        result['description_target'] = desc_sym2
        
        reduced_result.append(result)

    # sorted_result = sorted(reduced_result, key=lambda item: item['value'], reverse=True)
    sorted_result = sorted(reduced_result, key=lambda item: item['value'], reverse=False)

    filtered = []
    for result in sorted_result:
        if result['value'] >= 0.6:
            print(result)
            filtered.append(result)

    normalized = []
    for result in filtered:
        id_pair = [result['atom_in_kdb'], result['atom_in_target']]
        reason = "Result of TFIDF (value = {})".format(result['value'])

        obj = {'id_pair':id_pair, 'reason':reason, 'tfidf': True}
        print(obj)
        normalized.append(obj)

    return {'result':normalized}

def split_string(text, size):    
    chunk_size = size
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

    return chunks

def review_with_openai(kdb, target):
    kdb_atoms = atoms(kdb)
    target_atoms = atoms(target)

    kdb_table =[]
    for atom in kdb_atoms:
        item = {'id':atom, 'description': kdb_atoms[atom]['description'], 'from': 'kdb'}
        kdb_table.append(item)

    target_table =[]
    for atom in target_atoms:
        item = {'id':atom, 'description': target_atoms[atom]['description'], 'from': 'target'}
        target_table.append(item)


    pair_list = []
    for atom_in_kdb in kdb_atoms:
        for atom_in_target in target_table:
            desc_in_kdb = kdb_atoms[atom_in_kdb]['description']
            desc_in_target = target_atoms[atom_in_target['id']]['description']
            pair = ({'id':atom_in_kdb, 'desc':desc_in_kdb},{'id': atom_in_target['id'], 'desc': desc_in_target})
        
            pair_list.append(pair)
    
    chunks = split_list(pair_list, 150)

    result = []

    import time

    i = 0
    max = len(chunks)
    
    for chunk in chunks:

        print('--- [ {}/{} ] --->'.format(i, max))

        input = str({'cont':chunk})

        task = '''

上記のテキストを読んで、以下の質問に答えてください。

contには、idとdescのオブジェクトのペアのリストが入っています。
それぞれのdescとidが対応しています。
ペアの一つ目のdescと、ペアの二つ目のdescの意味が似ているペアを探してください。
以下のjsonフォーマットだけ教えてください。
無駄な文字列を決して出力せず、jsonフォーマットの結果のみを出力してください。

{
 "result":[{"id_pair": id_pair, "reason":"")}]
}

id_pairは、descが似ている二つのdescのidが入ります。
例えば、idがid1のdesc2と、idがid2のdesc2の意味が似ているとき、id_pairは[id1,id2]としてください。

reasonには似ていると判断した理由を英語で100文字以内で説明してください。

もし似ている文字列が一つも見つからなければ、resultを空の配列にして回答してください。

無駄な文字列を決して出力せず、jsonフォーマットの結果のみを出力してください。
'''

        prompt = input + task
        
        # messagesを作る
        messages = []
    
        # header
        messages.append({"role": "user", "content": prompt})

        try:
            completion = openai.ChatCompletion.create(model="gpt-4", messages=messages)    
            content = completion.choices[0]['message']['content']
            print(content)
            content_json = json.loads(content)
            res = content_json['result']
            
            print(res)
            
        except Exception as e:
            print('[error] {}'.format(e))
            res = []

        print(res)

        result.extend(res)

        print('<--- [ {}/{} ] ---'.format(i, max))
        i += 1

        time.sleep(10)

        # if i > 3:
        #     break


    print(result)

    return {"result":result}


def review_with_openai_failed(kdb, target):

    kdb_atoms = atoms(kdb)
    target_atoms = atoms(target)

    kdb_table =[]
    for atom in kdb_atoms:
        item = {'id':atom, 'description': kdb_atoms[atom]['description'], 'from': 'kdb'}
        kdb_table.append(item)

    target_table =[]
    for atom in target_atoms:
        item = {'id':atom, 'description': target_atoms[atom]['description'], 'from': 'target'}
        target_table.append(item)

    table = kdb_table + target_table

    data = json.dumps({'table': table})

    chunks = split_string(data, 5000)

    # messagesを作る
    messages = []
    
    # header
    header = '''
今からテキストを入力します。すべて入力し終わったら、私があなたに「テキストが入力し終わりました。」と伝えます。そのあとに、私が、あなたに質問します。その後に、入力したテキストに関してその質問に答えてください。私が「テキストが入力し終わりました」とあなたに伝えるまで、あなたは作業を始めず、代わりに「次の入力を待っています」とだけ回答してください。
'''
    messages.append({"role": "user", "content": header})

    # chunks
    # print(len(chunks))
    for chunk in chunks:
        messages.append({"role": "assistant", "content": "次の入力を待っています。"})
        messages.append({"role": "user", "content": chunk})
        
    # task
    task = '''
入力したテキストのtableには、id、description、fromが入っています。意味が似ているdescriptionか、または意味が矛盾するdescriptionがないか確認してください。余計な文字を出力せず、以下のjsonフォーマットで答えてください。jsonフォーマット以外の文字列は絶対に一切出力しないでください。

{
 'result':[(id1, id2, type, reason)]
}

id1とid2にはそれぞれのdescriptionのidが入ります。
typeには、それらのdescriptionの意味が似ていれば、"same", 矛盾していれば"conf"が入ります。
reasonには、そう判断した理由を入れます。reasonは英語で入力してください。
'''
    messages.append({"role": "assistant", "content": "次の入力を待っています。"})    
    messages.append({"role": "user", "content": task})



    completion = openai.ChatCompletion.create(model="gpt-4", messages=messages)    
    content = completion.choices[0]['message']['content']

    # except Exception as e:
    #     # 何らかの原因で失敗した場合は、その旨を出力し、ブレークする。
    #     print('[ERROR] {}'.format(e))

    print(content)

    ret = json.loads(content)



    

def main():    
    # 背景となるformula(knowledgeDB: KDB)を読み込む
    kdb_input = './formula/NASA-STD-871924B-Annex-Change-1_0.formula'
    with open(kdb_input) as f:
        kdb = json.loads(f.read())['formula_list']

    # レビューしてほしい対象のformula（target）を読み込む
    target_input = './formula/handbook_870922_baseline_with_change_7.formula'
    with open(target_input) as f:
        target = json.loads(f.read())['formula_list']

    # KDBに含まれるformulaに基づいて、targetのformulaを評価し、レビューする。
    result = review_with_tfidf(kdb = kdb, target = target)
    dump_tfidf(result, kdb_input, target_input)

    # OpenAIでatomsのマッチングをする際の設定
    # 適宜コメントアウトしろ
    # result = review_with_openai(kdb = kdb, target = target)
    # dump_ai(result, kdb_input, target_input)

def dump_tfidf(result, kdb_input, target_input):
    
    import os
    
    result_base_path = "./atom_matching"
    os.makedirs(result_base_path, exist_ok=True)

    unique_id = os.path.splitext(os.path.basename(target_input))[0]

    result_file_path = "{}/{}.matching_with_tfidf".format(result_base_path, unique_id)

    with open(result_file_path,'w', encoding="utf-8") as f:
        content = {
            'kdb': kdb_input,
            'target': target_input,
            'result': result
        }
        
        try:
            f.write(json.dumps(content, ensure_ascii=False))
        except Exception as e:
            print(e)

def dump_ai(result, kdb_input, target_input):
    
    import os
    
    result_base_path = "./atom_matching"
    os.makedirs(result_base_path, exist_ok=True)

    unique_id = os.path.splitext(os.path.basename(target_input))[0]

    result_file_path = "{}/{}.matching_with_ai".format(result_base_path, unique_id)

    with open(result_file_path,'w', encoding="utf-8") as f:
        content = {
            'kdb': kdb_input,
            'target': target_input,
            'result': result
        }
        
        try:
            f.write(json.dumps(content, ensure_ascii=False))
        except Exception as e:
            print(e)

main()
