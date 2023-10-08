import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

# 文書ベクトル化関数
def vecs_array(documents):
 
    docs = np.array(documents)
    # vectorizer = TfidfVectorizer(analyzer=wakachi,binary=True,use_idf=False)
    vectorizer = TfidfVectorizer(binary=True,use_idf=False)    
    vecs = vectorizer.fit_transform(docs)
    return vecs.toarray()


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

def description_of(atom, atoms):

    print(atom)

    print(atoms[atom])

    # for atom in atoms:
    #     print(atom)


# ask
def ask_about_matching(may_match, kdb, target):

    # may_matchに含まれるatomのマッチング結果が正しいかどうか聞く
    lis = may_match['result']['result']

    kdb_formula_list = kdb['formula_list']
    target_formula_list = target['formula_list']
    kdb_atoms = atoms(kdb_formula_list)
    target_atoms = atoms(target_formula_list)

    answers = []

    for match in lis:

        atom_in_kdb = match['id_pair'][0]
        atom_in_target = match['id_pair'][1]

        if (atom_in_kdb in kdb_atoms) and (atom_in_target in target_atoms):
            # ok
            pass
        elif (atom_in_kdb in target_atoms) and (atom_in_target in kdb_atoms):
            # なぜかひっくり返っている...
            # swap
            temp = atom_in_kdb
            atom_in_kdb = atom_in_target
            atom_in_target = temp
        else:
            # ignore
            # 変な組み合わせになっている
            continue

        print('--->')        
        print('[Question]\n"{}" in KDB == "{}" in TARGET ?\n'.format(atom_in_kdb, atom_in_target))
        print('- "{}": {}'.format(atom_in_kdb, kdb_atoms[atom_in_kdb]['description']))
        print('- "{}": {}'.format(atom_in_target, target_atoms[atom_in_target]['description']))

        print('')
        print('[Anser]')
        is_same = True
        
        if is_same :
            print('{} == {}'.format(atom_in_kdb, atom_in_target))
            answer = {'atom_in_kdb': atom_in_kdb, 'atom_in_target': atom_in_target}
            answers.append(answer)
        else:
            print('{} != {}'.format(atom_in_kdb, atom_in_target))            
        
        print('<---\n')

    return answers

def recommend_bottomup(answers, kdb):

    answers_id = []
    for answer in answers:
        answers_id.append(answer['atom_in_kdb'])

    # print(answers_id)
    found_formula = []
    for formula in kdb['formula_list']:
        ids = []
        atoms = formula['atoms']
        for atom in atoms:
            ids.append(atom['id'])

        # answers_id >= idsなら、answers_idでこのformulaは解ける
        if( set(answers_id).issuperset(set(ids)) ):
            # print('found!')
            # print(formula)
            found_formula.append(formula)

        # answers_ids < ids であり、len(answers_id) >= 1かつlen(ids)-len(answers_ids)であるなら、その（len(ids)-len(answers_ids)）個分の質問をすることで、あたらしくformulaが解けるかもしれない
        # この辺の閾値の設定が必要
        if set(ids).issuperset(set(answers_id)) and len(answers_id) >= 1:
            questions = len(ids) - len(answers_id)
            if questions <= 3:
                #
                # !!! 未実装
                # 
                print('[NOT IMPLEMENTED]')


    # print('--- found --->')
    # print(found_formula)
    # print('<--- found ---')
    
    return found_formula


def compare_with_tfidf(formula_kdb, formula_target):


    formula_list = []
    formula_table = {}    

    id=0
    for formula in formula_kdb:
        formula_list.append(formula['prop'])
        formula_table[str(id)] = {'formula':formula, 'type':'kdb'}
        id+=1

    for formula in formula_target:
        formula_list.append(formula['prop'])
        formula_table[str(id)] = {'formula':formula, 'type':'target'}
        id+=1

# i=0
    # for formula in formula_list:
    #     print(formula)
    #     print(formula_table[str(i)]['formula']['prop'])
    #     i+=1

    # 類似度行列作成
    cs_array = np.round(cosine_similarity(vecs_array(formula_list), vecs_array(formula_list)),3)

    result_list = []
    row_count = 0
    col_count = 0
    for row in cs_array:
        col_count = 0
        for col in row:
            val = col
            result = {'prop1': row_count, 'prop2': col_count, 'value': val}
            result_list.append(result)
            col_count = col_count + 1

        row_count = row_count + 1

    reduced_result = []
    for result in result_list:
        # 1.0は自分自身であり、いらないので消す
        # 0もいらない
        if result['value'] == 1.0 or result['value'] == 0:
            continue

        prop1 = result['prop1']
        prop2 = result['prop2']

        prop1_is_in = ""
        prop2_is_in = ""

        if formula_table[str(prop1)]['type'] == 'kdb':
            prop1_is_in = 'kdb'
        else:
            prop1_is_in = 'target'

        if formula_table[str(prop2)]['type'] == 'kdb':
            prop2_is_in = 'kdb'
        else:
            prop2_is_in = 'target'
            
        # 両方kdb、あるいは両方targetどおしで比較しても意味がない
        if prop1_is_in == prop2_is_in:
            continue

        if prop1_is_in == 'kdb':
            result['kdb'] = formula_table[str(prop1)]
            result['target'] = formula_table[str(prop2)]
        else:
            result['kdb'] = formula_table[str(prop2)]
            result['target'] = formula_table[str(prop1)]
        
        reduced_result.append(result)

    # sorted_result = sorted(reduced_result, key=lambda item: item['value'], reverse=True)
    sorted_result = sorted(reduced_result, key=lambda item: item['value'], reverse=False)

    filtered = []
    for result in sorted_result:
        if result['value'] >= 0.3:
            filtered.append(result)

    normalized = []
    for result in filtered:
        reason = "Result of TFIDF (value = {})".format(result['value'])
        result['reason'] = reason
        normalized.append(result)

    return {'result':normalized}


def ask_about_properties(kdb, target):

    formula_kdb = kdb['formula_list']
    formula_target = target['formula_list']

    # TFIDFを使って比較
    similar_props = compare_with_tfidf(formula_kdb, formula_target)

    new_props = []
    for props in similar_props['result']:


        print('--->')        
        print('[Question]\nAre these properties same ?\n')

        props_kdb = props['kdb']['formula']['prop']
        props_target = props['target']['formula']['prop']        

        print('(Property in KDB)')
        print(props_kdb)

        print('')
        print('(Property in TARGET)')        
        print(props_target)
        

        print('')
        print('[Answer]')
        print('=> Yes')
        
        same = True

        print('<---')
        

    return []
    

def main():

    # atom_matchingの結果を読み込む
    with open('./atom_matching/handbook_870922_baseline_with_change_7.matching_with_ai', 'r') as f:
        matching_with_ai = json.loads(f.read())

    with open('./atom_matching/handbook_870922_baseline_with_change_7.matching_with_tfidf', 'r') as f:
        matching_with_tfidf = json.loads(f.read())

    result = {'result':matching_with_ai['result']['result'] + matching_with_tfidf['result']['result']}

    matching = matching_with_tfidf
    matching['result'] = result

    # 背景となるformula(knowledgeDB: KDB)を読み込む
    kdb_input = './formula/NASA-STD-871924B-Annex-Change-1_0.formula'
    with open(kdb_input) as f:
        kdb = json.loads(f.read())

    # レビューしてほしい対象のformula（target）を読み込む
    target_input = './formula/handbook_870922_baseline_with_change_7.formula'
    with open(target_input) as f:
        target = json.loads(f.read())


    # 同じであることがわかったatomのリストが返ってくる
    # [{'atoms_in_kdb':'A', 'atoms_in_target':'B'}]
    # answers = ask_about_matching(matching, kdb, target)

    # atoms_targetに加えて、answersに入っているatoms_in_kdbの集合(も真であることがわかった
    # atoms_in_kdbにより、kdbに入っているprops（formula）全体で真になるものがあるか？
    # あるのであれば、それがレコメンドされるべき命題である
    # recommendations = recommend_bottomup(answers, kdb)


    answers = ask_about_properties(kdb, target)

    # print(recommendations)


    
        
main()
