<template>
    <el-card>
        <div slot="header">
            <span>智能问答机器人</span>
        </div>
        <div>
            <el-steps :active="activeStep" finish-status="success">
                <el-step title="准备环节" description="添加相关领域的知识的问题和答案"></el-step>
                <el-step title="训练环节" description="使用模型对问答进行编码"></el-step>
                <el-step title="预测环节" description="提问并获得回答"></el-step>
<!--                <el-step title="发布环节" description="创建永久链接，可以分享给他人体验。"></el-step>-->
            </el-steps>

            <div style="margin-bottom:20px; text-align: center">
                <el-button style="margin-top: 12px;" @click="prev" :disabled="activeStep === 0">上一步</el-button>
                <el-button style="margin-top: 12px;" @click="next" :disabled="activeStep === 2">下一步</el-button>
            </div>

            <div v-if="activeStep===0">
                <el-row>
                    <el-col :span="14">
                        <el-table :data="qa.data" border  @selection-change="handleSelectionChange">
                            <el-table-column type="selection" width="55"></el-table-column>
                            <el-table-column label="提问" prop="q" width="180"></el-table-column>
                            <el-table-column label="回答" prop="a"></el-table-column>
                        </el-table>
                        <el-button @click="deleteSelectedQa"
                                   type="danger"
                                   style="margin-top:20px"
                                   :disabled="!qaSelected || !trainReady">删除选中({{this.qa.multipleSelection.length}}/{{this.qa.data.length}})</el-button>
                        <el-button @click="resetQa"
                                   type="primary"
                                   style="margin-top:20px"
                                   :disabled="!trainReady">重置</el-button>
                    </el-col>
                    <el-col :offset="2" :span="8">
                        <el-card style="width:400px">
                            <div slot="header">添加一个问答</div>
                            <el-form  :disabled="!trainReady">
                                <el-form-item label="提问" required>
                                    <el-input v-model="qa.addParam.q"></el-input>
                                </el-form-item>
                                <el-form-item label="回答" required>
                                    <el-input v-model="qa.addParam.a" type="textarea" autosize></el-input>
                                </el-form-item>
                                <el-form-item>
                                    <el-button @click="addQa" type="primary">添加</el-button>
                                </el-form-item>
                            </el-form>
                        </el-card>
                    </el-col>
                </el-row>

            </div>

            <div v-if="activeStep===1">
                <div class="box">
                    <el-button :disabled="!trainReady" type="primary" @click="train">训练模型</el-button>
                    <el-button :disabled="!trainDone" type="primary" @click="rollbackTrain">重置模型</el-button>
                </div>
                <div class="box">
                    <el-timeline>
                        <el-timeline-item v-for="(activity, index) in model.trainMessages" :key="index" :timestamp="activity.timestamp">
                            {{activity.content}}
                        </el-timeline-item>
                    </el-timeline>
                </div>
            </div>

            <div v-if="activeStep===2" class="box-column">

                <el-form :inline="true" class="inline-form">
                    <el-form-item><el-input v-model="infer.q"></el-input></el-form-item>
                    <el-form-item><el-button @click="submitInfer" :disabled="infer.buttonDisable">提问</el-button> </el-form-item>
                </el-form>
                <el-input style="width:800px" type="textarea" autosize v-model="infer.a"></el-input>
            </div>

            <div v-if="activeStep===3" class="box-column">

                <el-form :inline="true" class="inline-form">
                    <el-form-item label="取个吸引人的名字"><el-input v-model="publish.title"></el-input></el-form-item>
                    <el-form-item><el-button @click="createShareLink" :disabled="infer.buttonDisable">发布机器人</el-button> </el-form-item>
                </el-form>
                <el-link :href="publish.link" target="_blank">{{publish.link}}</el-link>
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
          activeStep: 0,
          qa: {
            addParam: {
              q:null,
              a: null
            },
            data: [],
            multipleSelection: []
          },
          model: {
            trainStatus: 'ready',
            trainMessages: [],
            botid: null,
          },
          infer: {
            q:null,
            a:null,
            buttonDisable: false
          },
          publish: {
            title: null,
            link: null
          }
        }
      },
      computed: {
        qaSelected: function() {
          return this.qa.multipleSelection.length > 0;
        },
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
        this.qa.data = data.concat();
      },
      methods: {
        prev() {
          if (this.activeStep > 0) {
            this.activeStep--;
          }
        },
        next() {
          if (this.activeStep < 2) {
            this.activeStep++;
          }
        },
        addQa() {
            this.qa.data.push({q: this.qa.addParam.q, a: this.qa.addParam.a});
            this.qa.addParam = {q: null, a: null};
        },
        deleteSelectedQa() {
          this.qa.multipleSelection.forEach(item => {
            this.qa.data.splice(this.qa.data.indexOf(item),1);
          })
        },
        resetQa () {
          this.qa.data = window.data.concat();
        },
        handleSelectionChange(val) {
          this.qa.multipleSelection = val
        },
        train() {
          if (this.qa.data.length === 0) {
            this.log('请先添加问答');
          } else {
            this.log('收集到' + this.qa.data.length + '个问答');
            this.log('开始训练');
            this.model.trainStatus = 'training';
            const bodyData = {
              'questions': this.qa.data.map(a=>a.q),
              'answers': this.qa.data.map(a=>a.a),
              'botid': this.model.botid
            };
            axios.post(urls.train, bodyData).then(resp => {
              if (resp.status===200) {
                this.trainSuccessCallback(resp.data);
              } else {
                this.trainFailureCallback(resp.data);
              }
            }).catch(e=>{
              this.trainFailureCallback(e);
            });
          }
        },
        rollbackTrain() {
            axios.post(urls.clean,{
              'botid': this.model.botid
            }).then(data => {
              this.trainRollbackCallback();
            }).catch(e => {
              this.log(e);
            });
        },
        trainSuccessCallback(botid) {
          console.log('botid ' + botid);
          this.model.trainStatus = 'trained';
          this.model.botid = botid;
          this.log('模型训练完成。请点击下一步按钮进入预测环节。')
        },
        trainFailureCallback(msg) {
          this.log(msg);
          this.model.trainStatus = 'ready';
        },
        trainRollbackCallback() {
          this.model.trainStatus='ready';
          this.model.botid = null;
          this.log('模型已重置。');
        },
        log(msg) {
          this.model.trainMessages.splice(0, 0, {
            timestamp: dayjs().format('HH:mm:ss'),
            content: msg
          });
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
              this.infer.a = error.message;
              this.infer.buttonDisable = false;
            });
          } else {
            this.infer.a = '模型未就绪，请先训练模型。';
          }
        },
        createShareLink() {
          if (this.modelIsAvailable()) {
            axios.post(urls.save, {
              'botid': this.model.botid,
              'title': this.publish.title
            }).then(resp => {
              if (resp.status===200) {
                this.publish.link = urls.chatbot + '?botid=' + this.model.botid;
              } else {
                this.publish.link=resp.data;
              }
            }).catch (error => {
              this.publish.link=error.message;
            });
          } else {
            this.publish.link='模型未就绪，请先训练模型。';
          }
        }
      }
    }
</script>
