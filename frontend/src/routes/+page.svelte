<script lang="ts">
  import { invoices, type ParseResponse, type Invoice } from '$lib/api';
  
  let workDescription = '';
  let isLoading = false;
  let error = '';
  let parsedInvoice: ParseResponse | null = null;
  let createdInvoice: Invoice | null = null;
  
  async function parseWork() {
    if (!workDescription.trim()) return;
    
    isLoading = true;
    error = '';
    parsedInvoice = null;
    
    try {
      parsedInvoice = await invoices.parse(workDescription);
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to parse work description';
    } finally {
      isLoading = false;
    }
  }
  
  async function createInvoice() {
    if (!workDescription.trim()) return;
    
    isLoading = true;
    error = '';
    
    try {
      createdInvoice = await invoices.create(workDescription);
      parsedInvoice = null;
      workDescription = '';
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to create invoice';
    } finally {
      isLoading = false;
    }
  }
  
  function reset() {
    parsedInvoice = null;
    createdInvoice = null;
    error = '';
  }
  
  function formatCurrency(amount: number): string {
    return new Intl.NumberFormat('en-CA', { style: 'currency', currency: 'CAD' }).format(amount);
  }
</script>

<svelte:head>
  <title>Smart Invoice - Create Invoice</title>
</svelte:head>

<div class="max-w-4xl mx-auto py-8 px-4">
  <h1 class="text-3xl font-bold text-gray-900 mb-2">Create Invoice</h1>
  <p class="text-gray-600 mb-8">Describe your work and we'll generate a professional invoice with your preset rates.</p>
  
  {#if createdInvoice}
    <!-- Success state -->
    <div class="bg-green-50 border border-green-200 rounded-lg p-6 mb-8">
      <div class="flex items-center mb-4">
        <span class="text-2xl mr-3">✅</span>
        <h2 class="text-xl font-semibold text-green-800">Invoice Created!</h2>
      </div>
      <p class="text-green-700 mb-4">
        Invoice #{createdInvoice.invoice_number} for {formatCurrency(createdInvoice.total)} has been created.
      </p>
      <div class="flex gap-3">
        <a 
          href={invoices.downloadPdf(createdInvoice.id)}
          target="_blank"
          class="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition"
        >
          📄 Download PDF
        </a>
        <button 
          onclick={reset}
          class="bg-white text-green-700 border border-green-300 px-4 py-2 rounded-lg hover:bg-green-50 transition"
        >
          Create Another
        </button>
      </div>
    </div>
  {:else}
    <!-- Input form -->
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
      <label for="work" class="block text-sm font-medium text-gray-700 mb-2">
        Describe your work
      </label>
      <textarea
        id="work"
        bind:value={workDescription}
        placeholder="e.g., Bill Johnson Electric for 3 hours troubleshooting, replaced a 30-amp breaker, and 45 minutes travel"
        rows="4"
        class="w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        disabled={isLoading}
      ></textarea>
      
      <div class="mt-4 flex gap-3">
        <button
          onclick={parseWork}
          disabled={isLoading || !workDescription.trim()}
          class="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
        >
          {#if isLoading}
            Parsing...
          {:else}
            🔍 Preview Invoice
          {/if}
        </button>
      </div>
    </div>
    
    {#if error}
      <div class="bg-red-50 border border-red-200 rounded-lg p-4 mb-8">
        <p class="text-red-700">❌ {error}</p>
        <p class="text-red-600 text-sm mt-2">
          Make sure you have set up your <a href="/rate-card" class="underline">rate card</a> first.
        </p>
      </div>
    {/if}
    
    {#if parsedInvoice}
      <!-- Preview -->
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div class="bg-gray-50 px-6 py-4 border-b border-gray-200">
          <h2 class="text-lg font-semibold text-gray-900">Invoice Preview</h2>
          <p class="text-sm text-gray-500">Review and confirm before creating</p>
        </div>
        
        {#if parsedInvoice.unmatched_items.length > 0}
          <div class="bg-yellow-50 px-6 py-3 border-b border-yellow-200">
            <p class="text-yellow-800 text-sm">
              ⚠️ Some items couldn't be matched to your rate card: 
              <span class="font-medium">{parsedInvoice.unmatched_items.join(', ')}</span>
            </p>
          </div>
        {/if}
        
        <div class="p-6">
          {#if parsedInvoice.client_name}
            <p class="text-sm text-gray-600 mb-4">
              <span class="font-medium">Client:</span> {parsedInvoice.client_name}
            </p>
          {/if}
          
          <table class="w-full mb-6">
            <thead>
              <tr class="border-b border-gray-200">
                <th class="text-left py-3 text-sm font-medium text-gray-600">Description</th>
                <th class="text-right py-3 text-sm font-medium text-gray-600">Qty</th>
                <th class="text-left py-3 text-sm font-medium text-gray-600 pl-4">Unit</th>
                <th class="text-right py-3 text-sm font-medium text-gray-600">Rate</th>
                <th class="text-right py-3 text-sm font-medium text-gray-600">Amount</th>
              </tr>
            </thead>
            <tbody>
              {#each parsedInvoice.line_items as item}
                <tr class="border-b border-gray-100">
                  <td class="py-3">{item.description}</td>
                  <td class="py-3 text-right">{item.quantity}</td>
                  <td class="py-3 pl-4">{item.unit}</td>
                  <td class="py-3 text-right">{formatCurrency(item.unit_price)}</td>
                  <td class="py-3 text-right font-medium">{formatCurrency(item.line_total)}</td>
                </tr>
              {/each}
            </tbody>
          </table>
          
          <div class="border-t border-gray-200 pt-4">
            <div class="flex justify-end">
              <div class="w-64 space-y-2">
                <div class="flex justify-between text-sm">
                  <span class="text-gray-600">Subtotal</span>
                  <span>{formatCurrency(parsedInvoice.subtotal)}</span>
                </div>
                {#if parsedInvoice.tax_amount > 0}
                  <div class="flex justify-between text-sm">
                    <span class="text-gray-600">{parsedInvoice.tax_name}</span>
                    <span>{formatCurrency(parsedInvoice.tax_amount)}</span>
                  </div>
                {/if}
                {#if parsedInvoice.secondary_tax_amount && parsedInvoice.secondary_tax_amount > 0}
                  <div class="flex justify-between text-sm">
                    <span class="text-gray-600">{parsedInvoice.secondary_tax_name}</span>
                    <span>{formatCurrency(parsedInvoice.secondary_tax_amount)}</span>
                  </div>
                {/if}
                <div class="flex justify-between text-lg font-bold pt-2 border-t border-gray-200">
                  <span>Total</span>
                  <span class="text-blue-600">{formatCurrency(parsedInvoice.total)}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="bg-gray-50 px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
          <button
            onclick={reset}
            class="px-4 py-2 text-gray-700 hover:text-gray-900 transition"
          >
            Cancel
          </button>
          <button
            onclick={createInvoice}
            disabled={isLoading || parsedInvoice.line_items.length === 0}
            class="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            ✅ Create Invoice
          </button>
        </div>
      </div>
    {/if}
  {/if}
</div>
