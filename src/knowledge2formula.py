import openai
import json
import os

openai.api_key = '<YOUR OWN API KEY>'

def dump_formula_list(formula_list, error, knowledge_file_path):

    formula_base_path = "./formula"
    os.makedirs(formula_base_path, exist_ok=True)

    with open(knowledge_file_path, 'r') as f:
        knowledge = json.loads(f.read())

    unique_id = os.path.splitext(os.path.basename(knowledge_file_path))[0]

    formula_file_path = "{}/{}.formula".format(formula_base_path, unique_id)

    with open(formula_file_path,'w', encoding="utf-8") as f:
        content = {
            'id': knowledge['id'],
            'input': knowledge['input'],
            'error': error,
            'knowledge': knowledge['knowledge'],
            'formula_list': formula_list 
        }
        
        try:
            f.write(json.dumps(content, ensure_ascii=False))
        except Exception as e:
            print(e)

def split_list(input_list, chunk_size):
    it = iter(input_list)
    return [list(chunk) for chunk in zip(*[it] * chunk_size)]

def construct_formula(knowledge_file_path):

    with open(knowledge_file_path, 'r') as f:
        content = json.loads(f.read())

    knowledge = content['knowledge']

    chunk_list = split_list(knowledge, 20)

    print(len(chunk_list))

    all_formula_list = []

    error_flag = False
    error_message = ""

    i = 1
    length = len(chunk_list)
    for chunk in chunk_list:

        # i = i+1
        # if i >= 3:
        #     break

        print('---- [ {}/{} ] ---->'.format(i, length))
        
        data = json.dumps({"props":chunk}, ensure_ascii=False)

        header = '以下が入力です。jsonフォーマットによる入力です。\n\n{}\n'.format(data)

        task = '''
入力したjsonフォーマットのpropsには、システムが満たすべき性質がリスト形式で記述されています。
以下の手順に従って、順番に処理していき、各性質を命題論理式に変換してください。

手順１：それぞれの性質を命題論理式で表現する前に、まずは性質を原子項に分解してみましょう。
手順２：分解した原子項を用いて、各性質を命題論理式で表現してください。

以下のjsonフォーマットのみを回答してください。それ以外の文字列は決して、絶対に出力しないでください。
{
 "formula_list":[
  {
    "prop": "",
    "atoms: [ {"id": Atom, "description": ""}],
    "formula":"",
  }
]}

propには、性質を説明した文字列がそのまま入ります。命題論理式に変換するまえの文字列をそのまま入れてください。ただし、文字列が日本語で記述されている場合は英語に翻訳してください。
atomsには、propに記述された性質に含まれる原子項が入ります。原子項も日本語ではなくアルファベットで示して下さい。idには原子項を入れてください。descriptionには、その原子項の説明を主語と述語がある完全な文章にして50文字以内で説明した文字列を入れてください。
formulaには、atomsで示された原子項を用いた命題論理式が入ります。なお、formulaは、命題論理式をS式で表現した文字列を入れてください。例えば、
* Aである: A
* AかつB: (and A B)
* AまたはB: (or A B)
* Aではない: (not A)
* AならばB: (imply A B)
'''

        prompt = header + task

        messages = []
        messages.append({"role": "user", "content": prompt})

        try:
            # completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)        
            completion = openai.ChatCompletion.create(model="gpt-4", messages=messages)
            content = completion.choices[0]['message']['content']

        except Exception as e:
            # 何らかの原因で失敗した場合は、その旨を出力し、ブレークする。
            print('[ERROR] {}'.format(e))
            error_flag = True
            error_message = e
            break
        

        try:
            ret = json.loads(content)
            formula_list = ret['formula_list']
            print(formula_list)            
        except Exception as e:
            formula_list = []
            print(formula_list)

        all_formula_list.extend(formula_list)
        print('<---- [ {}/{} ] ----'.format(i, length))
        i = i+1

    if error_flag == True:
        return all_formula_list, error_message
    else:
        return all_formula_list, None

knowledge_file_path = "./knowledge/handbook_870922_baseline_with_change_7.knowledge"

formula_list, error = construct_formula(knowledge_file_path)

dump_formula_list(formula_list, error, knowledge_file_path)







