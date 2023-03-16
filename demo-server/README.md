# 准备

下载USE模型，链接：https://storage.googleapis.com/tfhub-modules/google/universal-sentence-encoder-multilingual-large/3.tar.gz 

将其解压到 `chatbot/models/large-3`，目录结构如下：

```bash
-- large-3
    |-- assets
    |-- saved_model.pb
    `-- variables
        |-- variables.data-00000-of-00001
        `-- variables.index
```

部署Milvus模型，建议使用docker部署。

```bash

# 下载镜像
docker pull milvusdb/milvus:0.8.0-cpu-d041520-464400

# 下载配置文件，假设登录用户为root，配置文件选择放在`/root/milvus/conf`目录
mkdir -p /root/milvus/conf
cd /root/milvus/conf
wget https://raw.githubusercontent.com/milvus-io/milvus/v0.8.0/core/conf/demo/server_config.yaml
wget https://raw.githubusercontent.com/milvus-io/milvus/v0.8.0/core/conf/demo/log_config.conf

# 启动容器
docker run -d --name milvus_cpu \
-p 19530:19530 \
-p 19121:19121 \
-p 9091:9091 \
-v ~/docker/milvus/db:/var/lib/milvus/db \
-v ~/docker/milvus/conf:/var/lib/milvus/conf \
-v ~/docker/milvus/logs:/var/lib/milvus/logs \
-v ~/docker/milvus/wal:/var/lib/milvus/wal \
milvusdb/milvus

```

根据实际部署情况调整配置文件`chatbot/models.py/MilvusModel`

# 环境初始化

创建pythons环境，并安装依赖，建议使用conda

```bash
conda create -n chatbot python=3.6
conda activate chatbot
pip install -r requirments.txt
```

# 启动服务

run `./deploy.py`
