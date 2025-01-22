<script setup>
import { usePalEditorStore } from "@/stores/paleditor";
import PathPicker from "@/components/PathPicker.vue";
const palStore = usePalEditorStore();
</script>

<template>
  <div id="entryDiv">
    <PathPicker />
    <div class="main-content">
      <img
        alt="Logo"
        class="logo"
        src="@/assets/logo.ico"
        width="125"
        height="125" />

      <div class="instructions">
        <p>请选择或输入存档路径（包含 Level.sav 的文件夹）</p>
      </div>

      <div class="save-path">
        <input
          type="text"
          v-model="palStore.PAL_GAME_SAVE_PATH"
          placeholder="存档路径，例如：C:\Users\[Username]\AppData\Local\Pal\Saved\SaveGames\[SteamID]\[SaveID]"
          :disabled="palStore.LOADING_FLAG" />

        <div class="button-group">
          <button class="pathSelect" @click="palStore.show_file_picker">
            选择路径
          </button>
          <button @click="palStore.loadSave" :disabled="palStore.LOADING_FLAG">
            载入存档
          </button>
        </div>
      </div>
    </div>
    <div class="version-container">
      <p class="version-info">VERSION: {{ palStore.VERSION }}</p>
    </div>
  </div>
</template>

<style scoped>
div#entryDiv {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem;
}

.main-content {
  max-width: 800px;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.instructions {
  margin: 2rem 0;
  text-align: center;
}

.save-path {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.button-group {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

p {
  word-wrap: break-word;
  font-size: 1.2rem;
  margin: 0.5rem 0;
}

input {
  width: 100%;
  height: 3rem;
  background-color: #34353a;
  color: whitesmoke;
  border: none;
  outline: none;
  border-radius: 0.5rem;
  font-size: 1.2rem;
  padding: 0 0.7rem;
}

input:focus {
  background-color: #b4b7be;
  color: rgb(0, 0, 0);
}

button {
  min-width: 120px;
  height: 3rem;
  background-color: #3365da;
  color: whitesmoke;
  border: none;
  outline: none;
  border-radius: 0.5rem;
  font-size: 1.2rem;
  transition: all 0.3s ease-in-out;
}

button:hover {
  background-color: #1b49b4;
  cursor: pointer;
}

button.pathSelect {
  background-color: #3f3f3f;
}

button.pathSelect:hover {
  background-color: rgb(125, 125, 125);
}

button:disabled {
  background-color: #8a8a8a;
  cursor: not-allowed;
}

.version-container {
  position: fixed;
  bottom: 10px;
  right: 10px;
}

.version-info {
  font-size: 0.9rem;
  color: #868686;
  opacity: 0.7;
}
</style>
