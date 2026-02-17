<script lang="ts">
  import { onMount } from 'svelte';
  import { settings, type BusinessSettings } from '$lib/api';
  
  let data: BusinessSettings = {};
  let isLoading = true;
  let isSaving = false;
  let error = '';
  let success = '';
  
  onMount(async () => {
    try {
      data = await settings.get();
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to load settings';
    } finally {
      isLoading = false;
    }
  });
  
  async function save() {
    isSaving = true;
    error = '';
    success = '';
    
    try {
      data = await settings.update(data);
      success = 'Settings saved!';
      setTimeout(() => success = '', 3000);
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to save settings';
    } finally {
      isSaving = false;
    }
  }
</script>

<svelte:head>
  <title>Settings - Smart Invoice</title>
</svelte:head>

<div class="max-w-2xl mx-auto py-8 px-4">
  <h1 class="text-3xl font-bold text-gray-900 mb-2">Settings</h1>
  <p class="text-gray-600 mb-8">Configure your business information and tax settings.</p>
  
  {#if error}
    <div class="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
      <p class="text-red-700">❌ {error}</p>
    </div>
  {/if}
  
  {#if success}
    <div class="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
      <p class="text-green-700">✅ {success}</p>
    </div>
  {/if}
  
  {#if isLoading}
    <div class="text-center py-12 text-gray-500">Loading...</div>
  {:else}
    <div class="space-y-8">
      <!-- Business Info -->
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">Business Information</h2>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Business Name</label>
            <input 
              type="text" 
              bind:value={data.business_name}
              placeholder="My Business"
              class="w-full border border-gray-300 rounded-lg px-3 py-2"
            />
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Address</label>
            <textarea 
              bind:value={data.business_address}
              placeholder="123 Main St&#10;City, Province A1B 2C3"
              rows="2"
              class="w-full border border-gray-300 rounded-lg px-3 py-2"
            ></textarea>
          </div>
          
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Phone</label>
              <input 
                type="tel" 
                bind:value={data.business_phone}
                placeholder="(555) 123-4567"
                class="w-full border border-gray-300 rounded-lg px-3 py-2"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input 
                type="email" 
                bind:value={data.business_email}
                placeholder="billing@mybusiness.com"
                class="w-full border border-gray-300 rounded-lg px-3 py-2"
              />
            </div>
          </div>
        </div>
      </div>
      
      <!-- Tax Settings -->
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">Tax Settings</h2>
        <div class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Primary Tax Name</label>
              <input 
                type="text" 
                bind:value={data.tax_name}
                placeholder="GST"
                class="w-full border border-gray-300 rounded-lg px-3 py-2"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Rate (%)</label>
              <input 
                type="number" 
                bind:value={data.tax_rate}
                step="0.01"
                min="0"
                max="1"
                placeholder="0.05"
                class="w-full border border-gray-300 rounded-lg px-3 py-2"
              />
              <p class="text-xs text-gray-500 mt-1">Enter as decimal (e.g., 0.05 for 5%)</p>
            </div>
          </div>
          
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Secondary Tax Name (optional)</label>
              <input 
                type="text" 
                bind:value={data.secondary_tax_name}
                placeholder="PST"
                class="w-full border border-gray-300 rounded-lg px-3 py-2"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Rate (%)</label>
              <input 
                type="number" 
                bind:value={data.secondary_tax_rate}
                step="0.01"
                min="0"
                max="1"
                placeholder="0.07"
                class="w-full border border-gray-300 rounded-lg px-3 py-2"
              />
            </div>
          </div>
        </div>
      </div>
      
      <div class="flex justify-end">
        <button 
          onclick={save}
          disabled={isSaving}
          class="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition"
        >
          {isSaving ? 'Saving...' : 'Save Settings'}
        </button>
      </div>
    </div>
  {/if}
</div>
