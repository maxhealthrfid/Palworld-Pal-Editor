<script setup>
import { usePalEditorStore } from "@/stores/paleditor";
import { ref, computed, reactive, onMounted, nextTick, watch } from "vue";
import PathPicker from "./PathPicker.vue";

const palStore = usePalEditorStore();

const palListContainer = ref(null);

const showTransfer = ref(false);
const sourceSavePath = ref("");
const palGuid = ref("");
const showSourcePalPicker = ref(false);
const sourcePals = ref([]);
const showImport = ref(false);
const importPalData = ref("");
const selectedPals = ref([]);

const isAllSelected = computed(() => {
  return (
    sourcePals.value.length > 0 &&
    selectedPals.value.length === sourcePals.value.length
  );
});

watch(
  async () => palStore.SELECTED_PLAYER_ID,
  async () => {
    await nextTick();
    try {
      const button = palListContainer.value.querySelector(
        "button:not(:disabled)"
      );
      if (button) {
        button.click();
      }
    } catch (error) {
      return;
    }
  }
);

// watch(async () => palStore.ADD_PAL_RESELECT_CTR, async () => {
//     await nextTick();
//     try {
//         const button = palListContainer.value.querySelector('button:not(:disabled)');
//         if (button) {
//             button.click();
//         }
//     } catch (error) {
//         return
//     }
// })

watch(
  async () => palStore.UPDATE_PAL_RESELECT_CTR,
  async () => {
    await nextTick();
    try {
      const button = palListContainer.value.querySelector(
        `button[value="${palStore.SELECTED_PAL_ID}"]`
      );
      if (button) {
        if (!palStore.isElementInViewport(button)) {
          button.scrollIntoView({ behavior: "smooth" });
        }
      }
    } catch (error) {
      return;
    }
  }
);

watch(
  async () => palStore.SELECTED_PAL_ID,
  async () => {
    await nextTick();
    try {
      const button = palListContainer.value.querySelector(
        `button[value="${palStore.SELECTED_PAL_ID}"]`
      );
      if (button) {
        if (
          palStore.SELECTED_PAL_ID != palStore.SELECTED_PAL_DATA?.InstanceId
        ) {
          palStore.selectPal(palStore.SELECTED_PAL_ID, true);
        }
        if (!palStore.isElementInViewport(button)) {
          button.scrollIntoView({ behavior: "smooth" });
        }
      }
    } catch (error) {
      return;
    }
  }
);

onMounted(async () => {
  await nextTick();
  // TODO Note: this is just a temp fix for pal selection when pal list is refreshed by updatePlayer
  await nextTick();
  await nextTick();
  const button = palListContainer.value.querySelector("button:not(:disabled)");
  if (button) {
    button.click();
  }
});

function get_filtered_pal_list() {
  // console.log("FILTER")
  return Array.from(palStore.PAL_MAP.values()).filter(
    (pal) => !palStore.isFilteredPal(pal)
  );
}

async function showTransferDialog() {
  showTransfer.value = true;
  sourcePals.value = [];
}

function closeTransferDialog() {
  showTransfer.value = false;
  sourceSavePath.value = "";
  palGuid.value = "";
  sourcePals.value = [];
  selectedPals.value = [];
}

async function loadSourcePals() {
  if (!sourceSavePath.value) return;

  try {
    const response = await palStore.loadSourcePals(sourceSavePath.value);
    if (response && response.status === 0) {
      sourcePals.value = response.data.filter((pal) => pal.in_owner_palbox);
    }
  } catch (error) {
    console.error("Failed to load source pals:", error);
  }
}

async function selectSourcePath() {
  showSourcePalPicker.value = true;
  await palStore.show_file_picker();
}

function onSourcePathSelected(path) {
  sourceSavePath.value = path;
  showSourcePalPicker.value = false;
  loadSourcePals();
}

function onSourcePathPickerClose() {
  showSourcePalPicker.value = false;
}

async function transferPal() {
  if (!sourceSavePath.value || !palGuid.value) return;

  // 检查是否已加载存档
  if (!palStore.SAVE_LOADED_FLAG) {
    alert("Please load a save file first before transferring pals.");
    return;
  }

  await palStore.transferPal(sourceSavePath.value, palGuid.value);
  closeTransferDialog();
}

async function showImportDialog() {
  showImport.value = true;
  importPalData.value = "";
}

function closeImportDialog() {
  showImport.value = false;
  importPalData.value = "";
}

async function importPal() {
  if (!importPalData.value) return;

  try {
    const palData = JSON.parse(importPalData.value);
    const response = await palStore.importPal(palData);
    if (response) {
      closeImportDialog();
    }
  } catch (error) {
    console.error("Failed to import pal:", error);
    alert("导入失败，请检查JSON格式是否正确");
  } finally {
    palStore.LOADING_FLAG.value = false;
  }
}

function toggleSelectAll() {
  if (isAllSelected.value) {
    selectedPals.value = [];
  } else {
    selectedPals.value = sourcePals.value.map((pal) => pal.InstanceId);
  }
}

function togglePalSelection(palId) {
  const index = selectedPals.value.indexOf(palId);
  if (index === -1) {
    selectedPals.value.push(palId);
  } else {
    selectedPals.value.splice(index, 1);
  }
}

async function confirmTransfer() {
  if (selectedPals.value.length === 0) return;

  try {
    await palStore.transferPal(sourceSavePath.value, selectedPals.value);
    closeTransferDialog();
  } catch (error) {
    console.error("Transfer failed:", error);
  }
}
</script>

<template>
  <div class="flex">
    <div class="title">
      <p>
        {{ palStore.getTranslatedText("PalList_Text") }}
      </p>
      <input
        class="palFilter"
        type="text"
        v-model="palStore.PAL_LIST_SEARCH_KEYWORD"
        placeholder="Search Pal"
        :disabled="palStore.LOADING_FLAG" />
      <button
        class="add_pal"
        v-if="!palStore.BASE_PAL_BTN_CLK_FLAG"
        :title="`Add Pal for Player ${
          palStore.PLAYER_MAP.get(palStore.SELECTED_PLAYER_ID).name
        }`"
        :disabled="palStore.LOADING_FLAG"
        @click="palStore.addPal"
        name="add_pal">
        +
      </button>
      <button
        class="transfer_pal"
        v-if="!palStore.BASE_PAL_BTN_CLK_FLAG"
        :title="'Transfer Pal from another save'"
        :disabled="palStore.LOADING_FLAG"
        @click="showTransferDialog"
        name="transfer_pal">
        ↓
      </button>
      <button
        class="import_pal"
        v-if="!palStore.BASE_PAL_BTN_CLK_FLAG"
        :title="'Import Pal from JSON'"
        :disabled="palStore.LOADING_FLAG"
        @click="showImportDialog"
        name="import_pal">
        📄
      </button>
    </div>

    <!-- Transfer Dialog -->
    <div v-if="showTransfer" class="transfer-dialog">
      <div class="transfer-content">
        <h3>从其他存档转移帕鲁</h3>
        <div class="input-group">
          <label>源存档路径：</label>
          <div class="path-input">
            <input
              type="text"
              v-model="sourceSavePath"
              placeholder="选择源存档路径"
              readonly />
            <button @click="selectSourcePath">浏览</button>
          </div>
        </div>

        <div v-if="sourcePals.length > 0" class="pal-list">
          <h4>选择要转移的帕鲁：</h4>
          <div class="pal-selection-header">
            <label>
              <input
                type="checkbox"
                :checked="isAllSelected"
                @change="toggleSelectAll" />
              全选
            </label>
            <span>已选择 {{ selectedPals.length }} 个帕鲁</span>
          </div>
          <div class="pal-grid">
            <div
              v-for="pal in sourcePals"
              :key="pal.InstanceId"
              class="pal-item"
              :class="{ selected: selectedPals.includes(pal.InstanceId) }"
              @click="togglePalSelection(pal.InstanceId)">
              <div class="pal-info">
                <span class="pal-name">{{ pal.DisplayName }}</span>
                <span class="pal-level">等级 {{ pal.Level }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="dialog-buttons">
          <button @click="closeTransfer">取消</button>
          <button
            @click="confirmTransfer"
            :disabled="selectedPals.length === 0">
            转移 ({{ selectedPals.length }})
          </button>
        </div>
      </div>
    </div>

    <!-- Import Dialog -->
    <div v-if="showImport" class="import-dialog">
      <div class="import-content">
        <h3>从JSON导入帕鲁</h3>
        <div class="input-group">
          <label>帕鲁JSON数据:</label>
          <textarea
            v-model="importPalData"
            placeholder="请粘贴帕鲁的JSON数据"
            rows="10"></textarea>
        </div>

        <div class="button-group">
          <button @click="importPal" :disabled="!importPalData">导入</button>
          <button @click="closeImportDialog">取消</button>
        </div>
      </div>
    </div>

    <div v-if="showSourcePalPicker" class="path-picker-overlay">
      <PathPicker
        @selected="onSourcePathSelected"
        @close="onSourcePathPickerClose" />
    </div>

    <div class="overflow-list" ref="palListContainer">
      <div class="overflow-container" v-for="pal in get_filtered_pal_list()">
        <button
          :class="[
            'pal',
            {
              male: pal.displayGender() == '♂️',
              female: pal.displayGender() == '♀️',
              unref: pal.Is_Unref_Pal,
              out_of_container: !pal.in_owner_palbox,
            },
          ]"
          :value="pal.InstanceId"
          @click="palStore.selectPal(pal.InstanceId)"
          :disabled="
            palStore.SELECTED_PAL_ID == pal.InstanceId || palStore.LOADING_FLAG
          "
          :selected="palStore.SELECTED_PAL_ID == pal.InstanceId">
          <img :class="['palIcon']" :src="`/image/pals/${pal.IconAccessKey}`" />
          {{ pal.DisplayName }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
div.flex {
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  width: 15rem;
  height: var(--sub-height);
  padding-right: 0.3rem;
  /* scrollbar */
}

div.title {
  display: flex;
  flex-direction: row;
  flex-wrap: nowrap;
  align-items: center;
  gap: 0.5rem;
  /* justify-content: space-between; */
}

div.overflow-list {
  display: flex;
  flex-direction: column;
  overflow-y: scroll;
  gap: 0.2rem 0rem;
}

.overflow-container {
  display: flex;
  overflow-x: auto;
  white-space: nowrap;
  max-height: 3.5rem;
  flex-shrink: 0;
  padding-bottom: 0.1rem;
  /* scrollbar */
  width: 100%;
}

input.palFilter {
  display: flex;
  align-items: center;
  background-color: #34353a;
  width: 7rem;
  height: 1rem;
  margin: 0.2rem;
  padding: 0.2rem 0.6rem;
  border-radius: 1rem;
  color: rgb(208, 212, 226);
  box-shadow: 2px 2px 10px rgb(38, 38, 38);
  border: none;
  outline: none;
}

input.palFilter:focus {
  background-color: #b4b7be;
  color: rgb(0, 0, 0);
}

img.palIcon {
  width: 2rem;
  border-radius: 50%;
}

button {
  cursor: pointer;
}

button.pal {
  display: flex;
  align-items: center;
  justify-content: left;
  white-space: nowrap;
  min-width: 100%;
  max-height: 3rem;
  padding: 0rem;
  padding-left: 0.3rem;
  min-height: 3rem;
  background-color: #323232;
  color: whitesmoke;
  border: none;
  outline: none;
  border-radius: 0.5rem;
  font-size: 1rem;
  text-align: left;
  transition: all 0.15s ease-in-out;
}

button.pal:hover {
  background-color: #686868;
  transition: all 0.15s ease-in-out;
}

button.pal:disabled {
  background-color: #8a8a8a;
  box-shadow: 0 0 0;
  filter: grayscale(100%);
  cursor: not-allowed;
}

button.pal:disabled:hover {
  background-color: #8a8a8a;
  box-shadow: 0 0 0;
  filter: grayscale(100%);
  cursor: not-allowed;
}

button.pal.male {
  /* background-color: #095594; */
  border-color: #095594;
  border-style: solid;
  border-width: 0.15rem;
}

button.pal.male:hover {
  background-color: #023b69;
}

button.pal.male:disabled {
  background-color: #023b69;
  box-shadow: 0 0 0;
  filter: grayscale(100%);
  cursor: not-allowed;
}

button.pal.male:disabled[selected="true"] {
  background-color: #023b69;
  box-shadow: 0 0 0;
  filter: none;
  cursor: not-allowed;
}

button.pal.female {
  border-color: #a13268;
  border-style: solid;
  border-width: 0.15rem;
}

button.pal.female:hover {
  background-color: #5d0b32;
}

button.pal.female:disabled {
  background-color: #5d0b32;
  box-shadow: 0 0 0;
  filter: grayscale(100%);
  cursor: not-allowed;
}

button.pal.female:disabled[selected="true"] {
  background-color: #5d0b32;
  box-shadow: 0 0 0;
  filter: none;
  cursor: not-allowed;
}

button.unref {
  filter: grayscale(100%);
}

button.unref:hover {
  background-color: #5e5e5e !important;
}

button.unref:disabled {
  background-color: #5e5e5e !important;
  box-shadow: 0 0 0;
  filter: grayscale(100%);
  cursor: not-allowed;
}

button.out_of_container {
  color: #3db15e;
}

button.add_pal {
  background-color: #3db15e;
  /* padding: 0; */
  color: whitesmoke;
  border: none;
  outline: none;
  border-radius: 0.2rem;
  font-size: 1rem;
}

button.add_pal:hover {
  background-color: #4b8d5e;
  box-shadow: 2px 2px 10px rgb(38, 38, 38);
  cursor: pointer;
}

button.add_pal:disabled {
  background-color: #8a8a8a;
  box-shadow: 0 0 0;
  filter: grayscale(100%);
  cursor: not-allowed;
}

.transfer-dialog {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.transfer-content {
  background: #2a2a2a;
  padding: 2rem;
  border-radius: 8px;
  width: 80%;
  max-width: 800px;
  max-height: 80vh;
  overflow-y: auto;
}

.input-group {
  margin-bottom: 1rem;
}

.path-input {
  display: flex;
  gap: 1rem;
}

.path-input input {
  flex: 1;
  padding: 0.5rem;
}

.pal-selection-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding: 0.5rem;
  background: #333;
  border-radius: 4px;
}

.pal-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}

.pal-item {
  background: #333;
  padding: 1rem;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.pal-item:hover {
  background: #444;
}

.pal-item.selected {
  background: #1b49b4;
}

.pal-info {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.pal-name {
  font-weight: bold;
}

.pal-level {
  font-size: 0.9rem;
  color: #aaa;
}

.dialog-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 2rem;
}

.dialog-buttons button {
  padding: 0.5rem 1.5rem;
}

.dialog-buttons button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.path-picker-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1100;
}

.transfer_pal {
  background: none;
  border: none;
  color: var(--text-color);
  cursor: pointer;
  font-size: 1.2em;
  padding: 0 5px;
}

.transfer_pal:hover {
  color: var(--hover-color);
}

.transfer_pal:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.import_pal {
  background: none;
  border: none;
  color: var(--text-color);
  cursor: pointer;
  font-size: 1.2em;
  padding: 0 5px;
}

.import_pal:hover {
  color: var(--hover-color);
}

.import_pal:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.import-dialog {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.import-content {
  background: rgba(45, 45, 45, 0.95);
  padding: 30px;
  border-radius: 12px;
  min-width: 600px;
  max-width: 800px;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  color: #ffffff;
}

.import-content textarea {
  width: 100%;
  min-height: 200px;
  background: rgba(60, 60, 60, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  color: #ffffff;
  padding: 10px;
  font-family: monospace;
  resize: vertical;
}
</style>
