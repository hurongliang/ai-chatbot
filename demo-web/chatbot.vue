<template>
    <el-card>
        <div slot="header">
            <span>{{model.title}}</span>
        </div>
        <div>
            <div class="box-column">
                <el-form :inline="true" class="inline-form">
                    <el-form-item><el-input v-model="infer.q"></el-input></el-form-item>
                    <el-form-item><el-button @click="submitInfer" :disabled="infer.buttonDisable">提问</el-button> </el-form-item>
                    <el-form-item><el-link :href="indexUrl" type="info">创建一个新的问答机器人</el-link> </el-form-item>
                </el-form>
                <el-input style="width:800px" type="textarea" autosize v-model="infer.a"></el-input>
            </div>
        </div>
    </el-card>
</template>

<style>
    .box {
        display: flex;
        display: -webkit-flex;
        justify-content: center;
        align-items: center;
        margin: 20px 0;
    }
    .box-column {
        display: flex;
        flex-direction: column;
        display: -webkit-flex;
        justify-content: center;
        align-items: center;
        margin: 20px 0;
    }
</style>
<script>
    import dayjs from 'dayjs';

    export default {
      data() {
        return {
          indexUrl: urls.index,
          model: {
            trainStatus: 'ready',
            trainMessages: [],
            botid: null,
            title: null
          },
          infer: {
            q:null,
            a:null,
            buttonDisable: false
          }
        }
      },
      computed: {
        trainReady: function() {
          return this.model.trainStatus === 'ready';
        },
        trainRunning: function() {
          return this.model.trainStatus === 'training';
        },
        trainDone: function () {
          return this.model.trainStatus === 'trained' && this.model.botid;
        }
      },
      mounted() {
        const botid = this.getBotIdParam();
        if (botid == null) {
          this.infer.a = '没有找到模型';
        } else {
          this.loadData(botid);
        }
      },
      methods: {
        getBotIdParam() {
          let botid = null;
          let params = window.location.href.split('?');
          if (params.length === 2) {
            const paramItems = params[1].split('&');
            paramItems.forEach(item => {
              let splits = item.split('=');
              if (splits.length === 2 && splits[0]==='botid' && splits[1].length > 0) {
                botid = splits[1];
              }
            });
          }
          return botid;
        },
        modelIsAvailable() {
          return this.model.trainStatus==='trained' && this.model.botid;
        },
        submitInfer() {
          if (this.modelIsAvailable()) {
            this.infer.a = '检索中，请稍等';
            this.infer.buttonDisable = true;
            axios.post(urls.infer, {
              'q': this.infer.q,
              'botid': this.model.botid
            }).then(resp => {
              this.infer.a = resp.data;
              this.infer.buttonDisable = false;
            }).catch(error => {
              if (error.response && error.response.data) {
                this.infer.a = error.response.data;
              } else {
                this.infer.a = error.message;
              }
              this.infer.buttonDisable = false;
            });
          } else {
            this.infer.a = '模型未就绪，请先训练模型。';
          }
        },
        loadData(botid) {
          const url = urls.load + '?botid=' + botid;
          console.log('post url ' + url);
          axios.get(url)
            .then(resp => {
                if (resp.status === 200) {
                  this.model.title = resp.data;
                  this.model.botid = botid;
                  this.model.trainStatus = 'trained';
                  console.log('模型加载成功');
                }else{
                  this.infer.a = resp.data;
                }
            }).catch(error => {
              if (error.response) {
                this.infer.a = error.response.data;
              } else {
                this.infer.a = error.message;
              }
          });
        }
      }
    }
</script>
