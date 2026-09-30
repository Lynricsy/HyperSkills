<!-- src/packageB/report/index.vue — uni-app (Vue 3 + Vite), built with `npm run build:mp-weixin` -->
<template>
  <view class="report">
    <chart-card :series="series" />
    <text>{{ total }}</text>
    <button @tap="refresh">Refresh</button>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
// packageA/utils/chart.ts is only shipped in subpackage packageA
import { buildSeries, sum } from '../../packageA/utils/chart'

const series = ref<number[]>([])
const total = ref(0)

function refresh() {
  series.value = buildSeries(30)
  total.value = sum(series.value)
}
</script>
