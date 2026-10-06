<template><div ref="host" style="height:360px;width:100%" /></template>
<script setup>
import {ref,onMounted,onBeforeUnmount,watch} from 'vue'
import * as echarts from 'echarts'
const props=defineProps({option:Object}),host=ref();let chart,observer
onMounted(()=>{chart=echarts.init(host.value);chart.setOption(props.option||{});observer=new ResizeObserver(()=>chart.resize());observer.observe(host.value)})
watch(()=>props.option,v=>chart?.setOption(v||{},true),{deep:true})
onBeforeUnmount(()=>{observer?.disconnect();chart?.dispose()})
</script>
