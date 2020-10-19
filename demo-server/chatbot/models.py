import tensorflow_hub as hub
import tensorflow_text
import os
import time
from milvus import Milvus, IndexType, MetricType
from services import LogService
import random
import uuid
import lmdb
import shutil
import json

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"


class ModelConfig:
    def __init__(self, client, embed, botid, title, questions, answers, question_encodings, vector_ids, timestamp):
        self.client = client
        self.embed = embed
        self.botid = botid
        self.title = title
        self.questions = questions
        self.answers = answers
        self.question_encodings = question_encodings
        self.vector_ids = vector_ids
        self.timestamp = timestamp

    @classmethod
    def encoding(cls, embed, text_list):
        return embed(text_list).numpy().tolist()

    @classmethod
    def create(cls, client, embed, botid, questions, answers):
        question_encodings = cls.encoding(embed, questions)
        vector_ids = client.save_vectors(question_encodings, botid)
        return ModelConfig(client, embed, botid, '简易问答', questions, answers, question_encodings, vector_ids, time.time())

    def find_answer(self, question):
        self.timestamp = time.time()

        question_encodings = self.encoding(self.embed, [question])
        vid = self.client.search_vectors(question_encodings, self.botid)
        if vid is not None and vid in self.vector_ids:
            idx = self.vector_ids.index(vid)
            return self.answers[idx]
        return None

    @classmethod
    def to_dict(cls, config):
        config_dict = {
            'botid': config.botid,
            'title': config.title,
            'questions': config.questions,
            'answers': config.answers,
            'question_encodings': config.question_encodings,
            'vector_ids': config.vector_ids,
            'timestamp': config.timestamp
        }
        return config_dict

    @classmethod
    def from_dict(cls, client, embed, config_dict):
        return ModelConfig(client, embed,
                           config_dict['botid'],
                           config_dict['title'],
                           config_dict['questions'],
                           config_dict['answers'],
                           config_dict['question_encodings'],
                           config_dict['vector_ids'],
                           config_dict['timestamp'])

    def dump(self):
        return json.dumps(self.to_dict(self), ensure_ascii=False)

    def destroy(self):
        self.client.empty_vectors(self.botid)

    def invalid(self):
        return time.time() - self.timestamp > 1800 # 30 minutes


class MilvusModel:
    def __init__(self):
        collection_name = 'chatbot'
        self.client = MilvusClient('122.51.212.91', '19530', collection_name, 512)
        self.lmdb_client = LmdbClient(os.path.abspath('chatbot/data/lmdb/'))
        self.embed = hub.load('chatbot/models/large-3/')
        self.model_configs = {}

    def fit(self):
        changed = False
        new_model_configs = {}
        for (botid, model_config) in self.model_configs.items():
            if model_config.invalid():
                model_config.destroy()
                changed = True
                LogService.info('removed invalid bot %s', botid)
            else:
                new_model_configs[botid] = model_config
        if changed:
            self.model_configs = new_model_configs

    def train(self, questions, answers):
        if len(questions) == 0:
            raise Exception('请先指定问答')
        if len(questions) != len(answers):
            raise Exception('问答需一一对应')

        botid = '%sv1' % uuid.uuid1().hex
        self.model_configs[botid] = ModelConfig.create(self.client, self.embed, botid, questions, answers)
        LogService.info('model trained with session %s', botid)
        return botid

    def clean_all(self):
        self.client.drop_all_collections()
        LogService.info('all bots removed')

    def clean(self, botid):
        if botid is None or len(botid) == 0:
            return

        if botid in self.model_configs:
            model_config = self.model_configs[botid]
            model_config.destroy()
            del self.model_configs[botid]
        LogService.info('model deleted with session %s', botid)

    def infer(self, question, botid):
        if question is None or len(question) == 0 or botid is None or len(botid) == 0:
            return ''

        if botid in self.model_configs:
            model_config = self.model_configs[botid]
            answer = model_config.find_answer(question)
            return answer if answer is not None else '抱歉，无法回答这个问题，能说的更明白些吗？'
        else:
            raise Exception('模型已过期，请重新训练模型。')

    def save(self, botid, title):
        if botid is None or len(botid) == 0:
            raise Exception('模型不存在')

        if botid in self.model_configs:
            model_config = self.model_configs[botid]
            model_config.title = title if title is not None and len(title) > 0 else '简易问答'
            model_config_str = model_config.dump()
            self.lmdb_client.put(botid, model_config_str)
            return 'success'
        else:
            raise Exception('模型已过期，请重新训练模型。')

    def get(self, botid):
        if botid is None or len(botid) == 0:
            raise Exception('模型不存在')

        model_config_str = self.lmdb_client.get(botid)
        if model_config_str is None:
            raise Exception('模型已过期，请重新训练模型。')
        model_config = json.loads(model_config_str)
        self.model_configs[botid] = ModelConfig.from_dict(self.client, self.embed, model_config)
        return model_config.title


class LmdbClient:
    def __init__(self, db_dir):
        self.db_dir = db_dir
        FileHelper.create_folder(self.db_dir)

    def put(self, key, value):
        env = lmdb.open(self.db_dir, map_size=100 * 1000 * 1000 * 1000)
        with env.begin(write=True) as tx:
            if type(key) == str:
                key = key.encode()
            if type(value) == str:
                value = value.encode()
            tx.put(key, value)
        env.close()

    def get(self, key):
        env = lmdb.open(self.db_dir, readonly=True, lock=False)
        with env.begin(write=False) as tx:
            if type(key) == str:
                key = key.encode()
            value = tx.get(key)
        env.close()
        return value


class MilvusClient:
    def __init__(self, host, port, collection_name, vector_dim):
        self.client = Milvus(host, port)
        self.collection_name_prefix = collection_name
        self.vector_dim = vector_dim

    def save_vectors(self, vectors, botid):
        collection_name = self.decide_collection_name(botid)
        self.create_collection_if_need(collection_name)
        status, ids = self.client.insert(collection_name=collection_name, records=vectors)
        self.check_status(status)
        LogService.info('%d vectors saved into collection %s', len(vectors), collection_name)
        return ids

    def search_vectors(self, vectors, botid):
        search_param = {'nprobe': 16}
        collection_name = self.decide_collection_name(botid)
        LogService.info('search vector in collection %s', collection_name)
        status, results = self.client.search(collection_name=collection_name,
                                             query_records=vectors,
                                             top_k=1,
                                             params=search_param)
        self.check_status(status)
        if len(results) > 0:
            vid = results[0][0].id
            LogService.info('vector found with id %d in collection %s', vid, collection_name)
            return vid
        else:
            LogService.info('vector not found in collection %s', collection_name)
            return None

    def empty_vectors(self, botid):
        collection_name = self.decide_collection_name(botid)
        status = self.client.drop_collection(collection_name)
        self.check_status(status)
        LogService.info('collection %s dropped', collection_name)

    def create_collection_if_need(self, collection_name):
        LogService.info('prepare collection %s', collection_name)
        status, exists = self.client.has_collection(collection_name)
        self.check_status(status)
        if not exists:
            LogService.info('collection %s not exists, create it.', collection_name)
            create_param = {
                'collection_name': collection_name,
                'dimension': self.vector_dim,
                'index_file_size': 1024,
                'metric_type': MetricType.L2
            }
            status = self.client.create_collection(create_param)
            self.check_status(status)
            LogService.info('collection %s created', collection_name)

            status = self.client.create_index(collection_name, IndexType.IVF_FLAT, {'nlist': 16384})
            self.check_status(status)
            LogService.info('index for collection %s created', collection_name)
        else:
            LogService.info('collection %s already exists', collection_name)

    def drop_all_collections(self):
        LogService.info('drop all collections')
        status, collection_names = self.client.show_collections()
        self.check_status(status)
        if len(collection_names) > 0:
            for collection_name in collection_names:
                status = self.client.drop_collection(collection_name)
                self.check_status(status)
                LogService.info('%s dropped', collection_name)

    @classmethod
    def check_status(cls, status):
        if status.code != 0:
            raise Exception(status.message)

    def decide_collection_name(self, botid):
        return '%s%s' % (self.collection_name_prefix, botid)


class FileHelper:
    @staticmethod
    def init_folder(folder_path):
        if os.path.isdir(folder_path):
            shutil.rmtree(folder_path)
        os.makedirs(folder_path)

    @staticmethod
    def create_folder(folder_path, empty_if_exists=False):
        if os.path.isdir(folder_path):
            if empty_if_exists:
                shutil.rmtree(folder_path)
                os.makedirs(folder_path)
        else:
            os.makedirs(folder_path)

    @classmethod
    def delete_file(cls, filepath):
        if os.path.isfile(filepath):
            os.remove(filepath)

    @classmethod
    def rand_filename(cls, suffix=None):
        if suffix is None:
            return os.path.join('/tmp', str(uuid.uuid4()))
        else:
            return os.path.join('/tmp', str(uuid.uuid4()) + '.' + suffix)
