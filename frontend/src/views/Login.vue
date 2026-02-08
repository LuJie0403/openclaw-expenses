
<template>
  <div class="login-container">
    <a-card class="login-card" title="OpenClaw Expenses" :bordered="false">
      <template #extra>
        <a href="#">Help</a>
      </template>
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
      <div v-if="errorMessage" class="error-message">
        {{ errorMessage }}
      </div>
    </a-card>
  </div>
</template>

<script lang="ts" setup>
import { reactive, ref } from 'vue';
import { useAuthStore } from '../stores/auth';
import { useRouter } from 'vue-router';
import { message } from 'ant-design-vue';

const authStore = useAuthStore();
const router = useRouter();

const formState = reactive({
  username: '',
  password: '',
  remember: true,
});

const loading = ref(false);
const errorMessage = ref('');

const onFinish = async (values: any) => {
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
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f0f2f5;
}

.login-card {
  width: 400px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.error-message {
  color: red;
  margin-top: 10px;
  text-align: center;
}
</style>
