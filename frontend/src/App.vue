<template>
  <div id="app" :class="theme">
    <header class="app-header">
      <div class="container">
        <h1 class="app-title">
          <i class="el-icon-timer"></i>
          {{ $t('app.title') }}
        </h1>
        <div class="app-controls">
          <el-select
            v-model="locale"
            size="small"
            style="width: 100px; margin-right: 10px;"
            @change="changeLocale"
          >
            <el-option label="English" value="en"></el-option>
            <el-option label="中文" value="zh"></el-option>
          </el-select>
          <el-switch
            v-model="isDark"
            :active-text="$t('app.darkMode')"
            @change="toggleTheme"
          ></el-switch>
        </div>
      </div>
    </header>

    <main class="app-main">
      <div class="container">
        <router-view />
      </div>
    </main>

    <footer class="app-footer">
      <div class="container">
        <p>{{ $t('app.footer') }}</p>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useTheme } from './composables/useTheme'
import { useI18n } from 'vue-i18n'

const { locale: i18nLocale } = useI18n()
const { isDark, theme, toggleTheme } = useTheme()

const locale = ref(i18nLocale.value)

const changeLocale = (value: string) => {
  i18nLocale.value = value
  localStorage.setItem('locale', value)
}
</script>

<style lang="scss">
#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  transition: background-color 0.3s, color 0.3s;

  &.light {
    background-color: #f5f7fa;
    color: #303133;
  }

  &.dark {
    background-color: #1a1a1a;
    color: #e4e7ed;
  }
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.app-header {
  padding: 20px 0;
  border-bottom: 1px solid var(--el-border-color);

  .container {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .app-title {
    margin: 0;
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .app-controls {
    display: flex;
    align-items: center;
    gap: 10px;
  }
}

.app-main {
  flex: 1;
  padding: 30px 0;
}

.app-footer {
  padding: 20px 0;
  border-top: 1px solid var(--el-border-color);
  text-align: center;
  font-size: 0.9em;
  color: var(--el-text-color-secondary);
}
</style>