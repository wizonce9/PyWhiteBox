<template>
  <div id="app">
    <div class="content">
      <router-view></router-view>
    </div>
  </div>
</template>

<script>
export default {
  name: 'App',
};
</script>

<style scoped>

/* 内容区域样式 */
.content {
  padding-top: -10px; /* 确保内容不会被导航栏遮挡 */
}

</style>
