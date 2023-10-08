import openai
import json
import os
from pdfminer.high_level import extract_text

openai.api_key = '<YOUR OWN API KEY>'

def askAI(query):

    completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[
        {"role": "system", "content": "ドキュメントの内容を精査して、検査する人"},        
        {"role": "user", "content": "Hello world"},
    ])
    print(completion.choices[0].message.content)

def split_string(text, size):    
    chunk_size = size
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

    return chunks


#
# Header
#

#
# Input
#
# {'val': 0.578, 'col': 'handbook_870922_baseline_with_change_7.txt', 'row': 'NASA-STD-871924B-Annex-Change-1_0.txt'}
# {'val': 0.545, 'col': 'nasa-hdbk-873923a.txt', 'row': 'NASA-HDBK-4008w-Chg-1.txt'}

# file_path = "./NASA_Standards/audio_and_video_standards_for_internet_resources_nasa_std_2821v20.txt"
# file_path = "./NASA_Standards/2020-01-28_nasa-std-10001-bim_final_1-3-2020docx.txt"

def extract_knowledge(file_path):

    # file_pathはpdfである必要がある。
    try:
        text = extract_text(file_path)
    except Exception as e:
        # pdfでなかったり、ファイルが存在しない場合は、エラーを出力して終わる
        print(e)
        return [], e

    chunks = split_string(text, 10000)

    header = '''
今からテキストを入力します。すべて入力し終わったら、私があなたに「テキストが入力し終わりました。」と伝えます。そのあとに、私が、あなたに質問します。その後に、入力したテキストに関してその質問に答えてください。私が「テキストが入力し終わりました」とあなたに伝えるまで、あなたは作業を始めず、代わりに「次の入力を待っています」とだけ回答してください。
'''

#     question = '''
# テキストが入力し終わりました。

# 今、私はテキストに記載されている推奨事項を知りたいです。推奨事項とは、満たされなければならない要件、性質、条件、あるいは満たしてはいけない要件、性質、条件のことです。見つかったそれぞれの推奨事項に関して、一つの推奨事項当たり500文字以内で可能な限り具体的に日本語で説明してください。推奨事項は、例えば「XXXべきである」、「でない」、「かつ」、「または」、「XXXならば」「その時点から始まるすべての場合において」、「その時点から始まるある場合において」、「次の時点で」、「すべての時点で」、「ある時点で」、「ある時点でXXXべきである/べきでない、その直前まではYYYべきある/べきでない」、「ある時点でXXXである/べきでない、その直前まではYYYべきである/べきでない、またはすべての状態でYYYべきである」という形でテキストに含まれることがあります。また、以下のjsonフォーマットで答えてください。余計な文字を出力せず、jsonフォーマット以外の文字列は決して出力しないでください。propsは、日本語の文字列で示された項目の配列です。もし、見つけた数の項目が多すぎて一度に出力できない場合はendにfalseを入れて、すべての項目を配列に入れることができた場合は、trueを入れてください。推奨事項が見つからない場合は、{"props":[], "end":true}とjsonフォーマットで返してください。

# {
#  "props": [""],
#  "end": ,
# }
# '''


    question = '''
テキストが入力し終わりました。

今、私はテキストに記載されている推奨事項、基準、標準などを知りたいです。推奨事項、基準、標準とは、満たされなければならない要件、性質、条件、あるいは満たしてはいけない要件、性質、条件のことです。見つかったそれぞれの推奨事項に関して、一つの推奨事項当たり500文字以内で可能な限り具体的に日本語で説明してください。説明する際、何がどういう場合/条件/文脈にどうするべきか、あるいは何がどういう場合/条件/文脈にどうするべきではないかを完全な文章で説明してください。

以下のjsonフォーマットで答えてください。余計な文字を出力せず、jsonフォーマット以外の文字列は決して出力しないでください。propsは、日本語の文字列で示された項目の配列です。推奨事項が見つからない場合は、{"props":[]}とjsonフォーマットで返してください。それ以外は何も出力する必要はありません。

{
 "props": [""]
}
'''

    i = 1
    all_props = []
    error_flag = False
    error_message = ""
    for chunk in chunks:

        print('---[ {}/{} ] --->'.format(i,len(chunks)))
        
        messages = []
        messages.append({"role": "system", "content": "ドキュメントの内容を精査して、検査する人"})
        messages.append({"role": "user", "content": header})
        messages.append({"role": "assistant", "content": "次の入力を待っています。"})
        messages.append({"role": "user", "content": chunk})
        messages.append({"role": "assistant", "content": "次の入力を待っています。"})
        messages.append({"role": "user", "content": question})

        try:
            # completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)        
            completion = openai.ChatCompletion.create(model="gpt-4", messages=messages)
            content = completion.choices[0]['message']['content']

        except Exception as e:
            # 何らかの原因で失敗した場合は、その旨を出力し、ブレークする。
            print('[ERROR] {}'.format(e))
            error_flag = True
            error_message = e
            print('<---[ {}/{} ] ---'.format(i,len(chunks)))            
            break

        print('props:')
        try:
            ret = json.loads(content)
            props = ret['props']
            print(props)            
        except Exception as e:
            props = []
            print(props)
            
        all_props.extend(props)

        i = i+1

        print('<---[ {}/{} ] ---'.format(i,len(chunks)))

    if error_flag == True:
        return all_props, error_message
    else:
        return all_props, None

def dump_knowledge(knowledge, error, input_file_path):

    knowledge_base_path = "./knowledge"
    os.makedirs(knowledge_base_path, exist_ok=True)

    unique_id = os.path.splitext(os.path.basename(input_file_path))[0]

    knowledge_file_path = "{}/{}.knowledge".format(knowledge_base_path, unique_id)

    with open(knowledge_file_path,'w', encoding="utf-8") as f:
        content = {
            'id': unique_id,
            'input': input_file_path,
            'error': error,
            'knowledge': knowledge
        }
        try:
            f.write(json.dumps(content, ensure_ascii=False))
        except Exception as e:
            print(e)

input_file_path = "./NASA_Standards/NASA-STD-871924B-Annex-Change-1_0.pdf"

knowledge, error = extract_knowledge(input_file_path)

dump_knowledge(knowledge, error, input_file_path)






