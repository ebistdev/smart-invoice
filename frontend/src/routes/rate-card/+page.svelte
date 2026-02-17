<script lang="ts">
  import { onMount } from 'svelte';
  import { rateItems, type RateItem, type RateItemCreate } from '$lib/api';
  
  let items: RateItem[] = [];
  let isLoading = true;
  let error = '';
  let showForm = false;
  
  // Form state
  let category = 'labor';
  let name = '';
  let description = '';
  let rate = 0;
  let unit = 'hour';
  let aliases = '';
  let editingId: string | null = null;
  
  const categories = ['labor', 'materials', 'other'];
  const units = ['hour', 'each', 'sqft', 'linear ft', 'day', 'job'];
  
  onMount(loadItems);
  
  async function loadItems() {
    isLoading = true;
    try {
      items = await rateItems.list();
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to load rate items';
    } finally {
      isLoading = false;
    }
  }
  
  function resetForm() {
    category = 'labor';
    name = '';
    description = '';
    rate = 0;
    unit = 'hour';
    aliases = '';
    editingId = null;
    showForm = false;
  }
  
  function editItem(item: RateItem) {
    category = item.category;
    name = item.name;
    description = item.description || '';
    rate = item.rate;
    unit = item.unit;
    aliases = item.aliases.join(', ');
    editingId = item.id;
    showForm = true;
  }
  
  async function saveItem() {
    const data: RateItemCreate = {
      category,
      name,
      description: description || undefined,
      rate,
      unit,
      aliases: aliases ? aliases.split(',').map(a => a.trim()) : []
    };
    
    try {
      if (editingId) {
        await rateItems.update(editingId, data);
      } else {
        await rateItems.create(data);
      }
      resetForm();
      await loadItems();
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to save';
    }
  }
  
  async function deleteItem(id: string) {
    if (!confirm('Delete this rate item?')) return;
    try {
      await rateItems.delete(id);
      await loadItems();
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to delete';
    }
  }
  
  function formatCurrency(amount: number): string {
    return new Intl.NumberFormat('en-CA', { style: 'currency', currency: 'CAD' }).format(amount);
  }
  
  $: groupedItems = items.reduce((acc, item) => {
    if (!acc[item.category]) acc[item.category] = [];
    acc[item.category].push(item);
    return acc;
  }, {} as Record<string, RateItem[]>);
</script>

<svelte:head>
  <title>Rate Card - Smart Invoice</title>
</svelte:head>

<div class="max-w-4xl mx-auto py-8 px-4">
  <div class="flex justify-between items-center mb-8">
    <div>
      <h1 class="text-3xl font-bold text-gray-900">Rate Card</h1>
      <p class="text-gray-600">Set your prices for services and materials. These are used for all invoices.</p>
    </div>
    <button
      onclick={() => showForm = true}
      class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition"
    >
      + Add Item
    </button>
  </div>
  
  {#if error}
    <div class="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
      <p class="text-red-700">❌ {error}</p>
    </div>
  {/if}
  
  {#if showForm}
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
      <h2 class="text-lg font-semibold mb-4">{editingId ? 'Edit' : 'Add'} Rate Item</h2>
      
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Category</label>
          <select 
            bind:value={category}
            class="w-full border border-gray-300 rounded-lg px-3 py-2"
          >
            {#each categories as cat}
              <option value={cat}>{cat.charAt(0).toUpperCase() + cat.slice(1)}</option>
            {/each}
          </select>
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Name</label>
          <input 
            type="text" 
            bind:value={name}
            placeholder="e.g., Troubleshooting"
            class="w-full border border-gray-300 rounded-lg px-3 py-2"
          />
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Rate</label>
          <input 
            type="number" 
            bind:value={rate}
            step="0.01"
            min="0"
            class="w-full border border-gray-300 rounded-lg px-3 py-2"
          />
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Unit</label>
          <select 
            bind:value={unit}
            class="w-full border border-gray-300 rounded-lg px-3 py-2"
          >
            {#each units as u}
              <option value={u}>{u}</option>
            {/each}
          </select>
        </div>
        
        <div class="col-span-2">
          <label class="block text-sm font-medium text-gray-700 mb-1">Description (optional)</label>
          <input 
            type="text" 
            bind:value={description}
            placeholder="Brief description"
            class="w-full border border-gray-300 rounded-lg px-3 py-2"
          />
        </div>
        
        <div class="col-span-2">
          <label class="block text-sm font-medium text-gray-700 mb-1">Aliases (comma-separated, for AI matching)</label>
          <input 
            type="text" 
            bind:value={aliases}
            placeholder="e.g., debug, diagnose, fix"
            class="w-full border border-gray-300 rounded-lg px-3 py-2"
          />
        </div>
      </div>
      
      <div class="mt-4 flex justify-end gap-3">
        <button 
          onclick={resetForm}
          class="px-4 py-2 text-gray-600 hover:text-gray-900"
        >
          Cancel
        </button>
        <button 
          onclick={saveItem}
          disabled={!name || rate <= 0}
          class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {editingId ? 'Update' : 'Add'} Item
        </button>
      </div>
    </div>
  {/if}
  
  {#if isLoading}
    <div class="text-center py-12 text-gray-500">Loading...</div>
  {:else if items.length === 0}
    <div class="bg-gray-50 rounded-lg p-12 text-center">
      <span class="text-4xl mb-4 block">📋</span>
      <h3 class="text-lg font-semibold text-gray-900 mb-2">No rate items yet</h3>
      <p class="text-gray-600 mb-4">Add your first service or material to get started.</p>
      <button
        onclick={() => showForm = true}
        class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
      >
        Add Your First Item
      </button>
    </div>
  {:else}
    {#each Object.entries(groupedItems) as [cat, catItems]}
      <div class="mb-8">
        <h2 class="text-lg font-semibold text-gray-900 mb-3 capitalize">{cat}</h2>
        <div class="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <table class="w-full">
            <thead class="bg-gray-50">
              <tr>
                <th class="text-left px-4 py-3 text-sm font-medium text-gray-600">Name</th>
                <th class="text-right px-4 py-3 text-sm font-medium text-gray-600">Rate</th>
                <th class="text-left px-4 py-3 text-sm font-medium text-gray-600">Unit</th>
                <th class="text-right px-4 py-3 text-sm font-medium text-gray-600">Actions</th>
              </tr>
            </thead>
            <tbody>
              {#each catItems as item}
                <tr class="border-t border-gray-100">
                  <td class="px-4 py-3">
                    <div class="font-medium">{item.name}</div>
                    {#if item.description}
                      <div class="text-sm text-gray-500">{item.description}</div>
                    {/if}
                  </td>
                  <td class="px-4 py-3 text-right font-medium">{formatCurrency(item.rate)}</td>
                  <td class="px-4 py-3 text-gray-600">{item.unit}</td>
                  <td class="px-4 py-3 text-right">
                    <button 
                      onclick={() => editItem(item)}
                      class="text-blue-600 hover:text-blue-800 mr-3"
                    >
                      Edit
                    </button>
                    <button 
                      onclick={() => deleteItem(item.id)}
                      class="text-red-600 hover:text-red-800"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      </div>
    {/each}
  {/if}
</div>
