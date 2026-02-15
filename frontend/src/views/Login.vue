
<template>
  <div class="login-container">
    <a-card class="login-card" title="钱呢 (MoneyWhere)" :bordered="false">
      <a-segmented
        v-model:value="loginMode"
        class="mode-switch"
        block
        :options="[
          { label: '账号密码', value: 'password' },
          { label: '微信扫码', value: 'wechat' }
        ]"
        @change="handleModeChange"
      />

      <div v-if="loginMode === 'password'" class="password-mode">
        <a-form
          :model="formState"
          name="basic"
          :label-col="{ span: 8 }"
          :wrapper-col="{ span: 16 }"
          autocomplete="off"
          @finish="onFinish"
          @finishFailed="onFinishFailed"
        >
          <a-form-item
            label="Username"
            name="username"
            :rules="[{ required: true, message: 'Please input your username!' }]"
          >
            <a-input v-model:value="formState.username" />
          </a-form-item>

          <a-form-item
            label="Password"
            name="password"
            :rules="[{ required: true, message: 'Please input your password!' }]"
          >
            <a-input-password v-model:value="formState.password" />
          </a-form-item>

          <a-form-item name="remember" :wrapper-col="{ offset: 8, span: 16 }">
            <a-checkbox v-model:checked="formState.remember">Remember me</a-checkbox>
          </a-form-item>

          <a-form-item :wrapper-col="{ offset: 8, span: 16 }">
            <a-button type="primary" html-type="submit" :loading="loading">Submit</a-button>
          </a-form-item>
        </a-form>
      </div>

      <div v-else class="wechat-mode">
        <div class="wechat-toolbar">
          <a-button type="primary" size="small" :loading="wechatLoading" @click="startWechatLogin">
            刷新二维码
          </a-button>
          <span v-if="wechatExpiresIn > 0" class="countdown">剩余 {{ wechatExpiresIn }} 秒</span>
        </div>

        <div id="wx-login-container" class="wx-container" />

        <a-alert
          v-if="wechatHint"
          :message="wechatHint"
          type="info"
          show-icon
          class="wechat-alert"
        />
        <a-alert
          v-if="wechatError"
          :message="wechatError"
          type="error"
          show-icon
          class="wechat-alert"
        />

        <div v-if="wechatSession?.qr_url" class="fallback-link">
          <a :href="wechatSession.qr_url" target="_blank" rel="noopener noreferrer">
            如果二维码未显示，请点此在新窗口打开
          </a>
        </div>
      </div>

      <div v-if="errorMessage" class="error-message">{{ errorMessage }}</div>
    </a-card>
  </div>
</template>

<script lang="ts" setup>
import { reactive, ref, onUnmounted } from 'vue';
import { useAuthStore } from '../stores/auth';
import { useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import api from '@/services/api';

// ---------------------------------------------------------------------------
// WeChat QR Login Frontend Contract (maintenance notes)
// ---------------------------------------------------------------------------
// 1) Login page provides two parallel modes:
//    - password: original username/password login
//    - wechat: QR-based login
//    Password mode is not replaced; it remains fully available.
//
// 2) WeChat mode flow:
//    - create session: POST /auth/wechat/qr-session
//    - render QR widget via WxLogin SDK
//    - poll status: GET /auth/wechat/qr-session/{id}
//    - exchange ticket: POST /auth/wechat/exchange-ticket
//    - finalize by authStore.loginWithToken(token)
//
// 3) Why polling:
//    - callback lands in mobile browser context.
//    - desktop browser learns confirmation via polling shared session status.
//
// 4) Timer handling:
//    - poll timer and countdown timer must be cleaned on:
//      * mode switch back to password
//      * QR refresh
//      * component unmount
//    - this prevents duplicate requests and memory leaks.
//
// 5) SDK handling:
//    - WxLogin SDK is lazy-loaded only when needed.
//    - scriptLoadPromise is memoized to avoid duplicate <script> tags.
//    - on load failure, fallback direct QR URL is shown.
//
// 6) Session status behavior:
//    - PENDING: show waiting hint.
//    - CONFIRMED: exchange ticket for JWT.
//    - EXPIRED/FAILED: stop polling and show actionable message.
//    - CONSUMED: likely completed in another tab/browser.
//
// 7) Security behavior:
//    - frontend never handles app_secret.
//    - frontend only receives temporary ticket, not callback token.
//    - JWT storage remains aligned with existing auth store behavior.
//
// 8) Error strategy:
//    - endpoint 404 on WeChat APIs means feature disabled in current env.
//    - all other errors are normalized into user-friendly prompts.
//
// 9) UX strategy:
//    - support manual "refresh QR" action.
//    - show countdown for current session validity.
//    - keep fallback link for environments where embedded widget fails.
//
// 10) Compatibility:
//    - no router guard changes required.
//    - business pages remain unaware of login method used.
// ---------------------------------------------------------------------------

declare global {
  interface Window {
    WxLogin?: any;
  }
}

interface WechatSessionResponse {
  session_id: string;
  qr_url: string;
  expires_in: number;
  poll_interval_ms: number;
  wechat_app_id: string;
  wechat_redirect_uri: string;
  wechat_scope: string;
  state: string;
}

interface WechatSessionStatusResponse {
  status: 'PENDING' | 'CONFIRMED' | 'EXPIRED' | 'FAILED' | 'CONSUMED';
  expires_in: number;
  ticket?: string | null;
  error_code?: string | null;
  error_message?: string | null;
}

const authStore = useAuthStore();
const router = useRouter();

// Keep original password-login form untouched; WeChat is an additive mode.
const formState = reactive({
  username: '',
  password: '',
  remember: true,
});

// Login mode switch state.
const loginMode = ref<'password' | 'wechat'>('password');
const loading = ref(false);
const errorMessage = ref('');

// WeChat login runtime state.
const wechatLoading = ref(false);
const wechatError = ref('');
const wechatHint = ref('');
const wechatSession = ref<WechatSessionResponse | null>(null);
const wechatExpiresIn = ref(0);
const exchangingTicket = ref(false);

let pollTimer: number | null = null;
let countdownTimer: number | null = null;
let scriptLoadPromise: Promise<void> | null = null;

const onFinish = async (values: any) => {
  // Existing username/password login flow.
  loading.value = true;
  errorMessage.value = '';
  try {
    await authStore.login(values.username, values.password);
    message.success('Login successful');
    router.push('/');
  } catch (error: any) {
    if (error.response && error.response.status === 401) {
      errorMessage.value = 'Invalid username or password';
    } else {
      errorMessage.value = 'An error occurred. Please try again later.';
    }
  } finally {
    loading.value = false;
  }
};

const onFinishFailed = (errorInfo: any) => {
  console.log('Failed:', errorInfo);
};

const clearWechatTimers = () => {
  // Avoid duplicate polling loops when user switches modes or refreshes QR.
  if (pollTimer !== null) {
    window.clearInterval(pollTimer);
    pollTimer = null;
  }
  if (countdownTimer !== null) {
    window.clearInterval(countdownTimer);
    countdownTimer = null;
  }
};

const loadWxLoginScript = async () => {
  // Lazy-load WeChat JS SDK only when user enters WeChat mode.
  if (window.WxLogin) return;
  if (!scriptLoadPromise) {
    scriptLoadPromise = new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = 'https://res.wx.qq.com/connect/zh_CN/htmledition/js/wxLogin.js';
      script.async = true;
      script.onload = () => resolve();
      script.onerror = () => {
        scriptLoadPromise = null;
        reject(new Error('Failed to load wxLogin.js'));
      };
      document.head.appendChild(script);
    });
  }
  return scriptLoadPromise;
};

const renderWechatQrcode = async (session: WechatSessionResponse) => {
  // Render official WeChat QR widget into fixed container.
  const container = document.getElementById('wx-login-container');
  if (!container) return;
  container.innerHTML = '';

  await loadWxLoginScript();
  if (!window.WxLogin) {
    throw new Error('WxLogin is not available');
  }

  new window.WxLogin({
    self_redirect: false,
    id: 'wx-login-container',
    appid: session.wechat_app_id,
    scope: session.wechat_scope,
    redirect_uri: encodeURIComponent(session.wechat_redirect_uri),
    state: session.state,
    style: 'black',
  });
};

const pollWechatStatus = async () => {
  // Prevent overlapping requests while ticket exchange is in flight.
  if (!wechatSession.value || exchangingTicket.value) return;
  try {
    const response = await api.get<WechatSessionStatusResponse>(`/auth/wechat/qr-session/${wechatSession.value.session_id}`);
    const data = response.data;
    wechatExpiresIn.value = data.expires_in;

    if (data.status === 'PENDING') {
      // Keep UI informative while waiting for mobile confirmation.
      wechatHint.value = '请使用微信扫码并在手机上确认登录。';
      return;
    }
    if (data.status === 'FAILED') {
      clearWechatTimers();
      wechatError.value = data.error_message || '微信登录失败，请刷新二维码重试。';
      wechatHint.value = '';
      return;
    }
    if (data.status === 'EXPIRED') {
      clearWechatTimers();
      wechatError.value = '二维码已过期，请点击“刷新二维码”。';
      wechatHint.value = '';
      return;
    }
    if (data.status === 'CONFIRMED' && data.ticket) {
      // Convert one-time ticket to JWT, then reuse existing token login path.
      exchangingTicket.value = true;
      const tokenResponse = await api.post('/auth/wechat/exchange-ticket', {
        session_id: wechatSession.value.session_id,
        ticket: data.ticket,
      });
      await authStore.loginWithToken(tokenResponse.data.access_token);
      clearWechatTimers();
      message.success('微信登录成功');
      router.push('/');
      return;
    }
    if (data.status === 'CONSUMED') {
      // Another browser tab may have consumed the ticket already.
      clearWechatTimers();
      wechatHint.value = '登录已完成，请刷新页面继续。';
      return;
    }
  } catch (error: any) {
    if (error.response?.status === 404) {
      clearWechatTimers();
      wechatError.value = '扫码会话不存在，请刷新二维码。';
      wechatHint.value = '';
      return;
    }
    wechatError.value = '轮询登录状态失败，请稍后重试。';
  } finally {
    exchangingTicket.value = false;
  }
};

const startWechatLogin = async () => {
  // (Re)initialize a fresh QR session from backend.
  clearWechatTimers();
  wechatLoading.value = true;
  wechatError.value = '';
  wechatHint.value = '';
  wechatSession.value = null;
  wechatExpiresIn.value = 0;

  try {
    const response = await api.post<WechatSessionResponse>('/auth/wechat/qr-session');
    const data = response.data;
    wechatSession.value = data;
    wechatExpiresIn.value = data.expires_in;
    wechatHint.value = '请使用微信扫码并在手机上确认登录。';

    try {
      await renderWechatQrcode(data);
    } catch (error) {
      // Keep fallback URL available if SDK or iframe rendering fails.
      wechatError.value = '二维码组件加载失败，请使用下方备用链接。';
    }

    // Trigger one immediate status pull, then continue periodic polling.
    await pollWechatStatus();
    pollTimer = window.setInterval(pollWechatStatus, data.poll_interval_ms || 2000);
    countdownTimer = window.setInterval(() => {
      if (wechatExpiresIn.value > 0) {
        wechatExpiresIn.value -= 1;
      }
    }, 1000);
  } catch (error: any) {
    if (error.response?.status === 404) {
      wechatError.value = '当前环境未开启微信扫码登录。';
    } else {
      wechatError.value = '初始化微信扫码登录失败，请稍后再试。';
    }
  } finally {
    wechatLoading.value = false;
  }
};

const handleModeChange = async (value: 'password' | 'wechat') => {
  // Switch to WeChat mode lazily; keep password mode clean and synchronous.
  if (value === 'wechat' && !wechatSession.value) {
    await startWechatLogin();
  } else if (value === 'password') {
    clearWechatTimers();
  }
};

onUnmounted(() => {
  // Prevent timer leaks after route change.
  clearWechatTimers();
});
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f0f2f5;
  padding: 24px;
}

.login-card {
  width: 440px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.mode-switch {
  margin-bottom: 20px;
}

.wechat-mode {
  min-height: 360px;
}

.wechat-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.countdown {
  color: #595959;
  font-size: 12px;
}

.wx-container {
  display: flex;
  justify-content: center;
  min-height: 260px;
  border: 1px dashed #d9d9d9;
  border-radius: 8px;
  padding: 12px 0;
  background: #fafafa;
}

.wechat-alert {
  margin-top: 12px;
}

.fallback-link {
  margin-top: 12px;
  text-align: center;
}

.error-message {
  color: #cf1322;
  margin-top: 10px;
  text-align: center;
}
</style>
