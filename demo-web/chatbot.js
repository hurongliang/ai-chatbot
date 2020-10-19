import Vue from 'vue';

import axios from 'axios';
window.axios = axios;
axios.defaults.withCredentials=false;

import ElementUI from 'element-ui';
import 'element-ui/lib/theme-chalk/index.css';
Vue.use(ElementUI, {size: 'small'});

const data = require('./data.json');
window.data = data;

import {dev, prd} from './src/Urls';
window.urls = prd;

import chatbot from './chatbot.vue';
new Vue({
  el: '#app',
  render: h => h(chatbot)
});

