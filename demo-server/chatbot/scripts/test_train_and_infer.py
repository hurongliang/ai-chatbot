import json

from chatbot.models import MilvusModel

model = MilvusModel()

with open('chatbot/data/data.json', 'r') as f:
    arr = json.load(f)
    qlist = []
    alist = []
    for item in arr:
        qlist.append(item['q'])
        alist.append(item['a'])
    data = {
        'questions': qlist,
        'answers': alist
    }
    session_id = model.train(data)
    a = model.infer('什么药可以治疗冠状病毒', session_id)
    print('answer ', a)

