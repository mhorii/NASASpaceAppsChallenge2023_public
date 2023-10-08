import os
import json

with open("handbook_870922_baseline_with_change_7.knowledge", "r") as f:
    content = json.loads(f.read())

print(content)    

with open("hoge.txt", "w", encoding="utf-8")  as f:
    f.write(json.dumps(content, ensure_ascii=False))

    
