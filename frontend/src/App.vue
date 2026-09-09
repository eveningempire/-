<template>
  <!-- Root renders the current route; auth removed, all pages public -->
  <router-view />
</template>

<script setup>
// The App component does not require any logic at the root level. All
// routing and layout logic is handled in the router and the Layout
// component. Using the <script setup> syntax keeps this file concise.
</script>

<style>
/* You can place global styles here. Consider using CSS variables or
   a preprocessor if the styling becomes complex. */
</style>