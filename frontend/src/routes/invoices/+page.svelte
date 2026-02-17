<script lang="ts">
  import { onMount } from 'svelte';
  import { invoices, type Invoice } from '$lib/api';
  
  let invoiceList: Invoice[] = [];
  let isLoading = true;
  let error = '';
  
  onMount(async () => {
    try {
      invoiceList = await invoices.list();
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to load invoices';
    } finally {
      isLoading = false;
    }
  });
  
  function formatCurrency(amount: number): string {
    return new Intl.NumberFormat('en-CA', { style: 'currency', currency: 'CAD' }).format(amount);
  }
  
  function formatDate(dateStr: string): string {
    return new Date(dateStr).toLocaleDateString('en-CA', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  }
  
  function getStatusColor(status: string): string {
    switch (status) {
      case 'paid': return 'bg-green-100 text-green-800';
      case 'sent': return 'bg-blue-100 text-blue-800';
      case 'overdue': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  }
</script>

<svelte:head>
  <title>Invoices - Smart Invoice</title>
</svelte:head>

<div class="max-w-6xl mx-auto py-8 px-4">
  <div class="flex justify-between items-center mb-8">
    <div>
      <h1 class="text-3xl font-bold text-gray-900">Invoices</h1>
      <p class="text-gray-600">View and manage your invoices</p>
    </div>
    <a 
      href="/"
      class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition"
    >
      + New Invoice
    </a>
  </div>
  
  {#if error}
    <div class="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
      <p class="text-red-700">❌ {error}</p>
    </div>
  {/if}
  
  {#if isLoading}
    <div class="text-center py-12 text-gray-500">Loading...</div>
  {:else if invoiceList.length === 0}
    <div class="bg-gray-50 rounded-lg p-12 text-center">
      <span class="text-4xl mb-4 block">📄</span>
      <h3 class="text-lg font-semibold text-gray-900 mb-2">No invoices yet</h3>
      <p class="text-gray-600 mb-4">Create your first invoice to get started.</p>
      <a 
        href="/"
        class="inline-block bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
      >
        Create Invoice
      </a>
    </div>
  {:else}
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      <table class="w-full">
        <thead class="bg-gray-50">
          <tr>
            <th class="text-left px-6 py-4 text-sm font-medium text-gray-600">Invoice #</th>
            <th class="text-left px-6 py-4 text-sm font-medium text-gray-600">Client</th>
            <th class="text-left px-6 py-4 text-sm font-medium text-gray-600">Date</th>
            <th class="text-right px-6 py-4 text-sm font-medium text-gray-600">Total</th>
            <th class="text-center px-6 py-4 text-sm font-medium text-gray-600">Status</th>
            <th class="text-right px-6 py-4 text-sm font-medium text-gray-600">Actions</th>
          </tr>
        </thead>
        <tbody>
          {#each invoiceList as inv}
            <tr class="border-t border-gray-100 hover:bg-gray-50">
              <td class="px-6 py-4 font-medium">{inv.invoice_number}</td>
              <td class="px-6 py-4 text-gray-600">{inv.client_name || 'No client'}</td>
              <td class="px-6 py-4 text-gray-600">{formatDate(inv.invoice_date)}</td>
              <td class="px-6 py-4 text-right font-medium">{formatCurrency(inv.total)}</td>
              <td class="px-6 py-4 text-center">
                <span class="px-2 py-1 rounded-full text-xs font-medium {getStatusColor(inv.status)}">
                  {inv.status}
                </span>
              </td>
              <td class="px-6 py-4 text-right">
                <a 
                  href={invoices.downloadPdf(inv.id)}
                  target="_blank"
                  class="text-blue-600 hover:text-blue-800 mr-3"
                >
                  📄 PDF
                </a>
                <a 
                  href="/invoices/{inv.id}"
                  class="text-gray-600 hover:text-gray-900"
                >
                  View
                </a>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>
