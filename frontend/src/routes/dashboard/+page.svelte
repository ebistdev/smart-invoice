<script lang="ts">
  import { onMount } from 'svelte';
  
  interface DashboardData {
    revenue_period: number;
    revenue_period_days: number;
    outstanding: number;
    total_revenue: number;
    total_invoices: number;
    status_breakdown: Record<string, number>;
    overdue_count: number;
    revenue_chart: { month: string; revenue: number; invoices: number }[];
    top_clients: { id: string; name: string; total_billed: number; total_paid: number; invoice_count: number }[];
    overdue_invoices: { id: string; invoice_number: string; total: number; outstanding: number; days_overdue: number }[];
  }
  
  let data: DashboardData | null = null;
  let isLoading = true;
  let error = '';
  
  onMount(async () => {
    try {
      const response = await fetch('/api/dashboard?days=30');
      if (response.ok) {
        data = await response.json();
      } else {
        throw new Error('Failed to load dashboard');
      }
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to load';
    } finally {
      isLoading = false;
    }
  });
  
  function formatCurrency(amount: number): string {
    return new Intl.NumberFormat('en-CA', { style: 'currency', currency: 'CAD' }).format(amount);
  }
</script>

<svelte:head>
  <title>Dashboard - Smart Invoice</title>
</svelte:head>

<div class="max-w-7xl mx-auto py-8 px-4">
  <h1 class="text-3xl font-bold text-gray-900 mb-8">Dashboard</h1>
  
  {#if isLoading}
    <div class="text-center py-12 text-gray-500">Loading...</div>
  {:else if error}
    <div class="bg-red-50 border border-red-200 rounded-lg p-4">
      <p class="text-red-700">❌ {error}</p>
    </div>
  {:else if data}
    <!-- Stats Cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <p class="text-sm text-gray-500 mb-1">Revenue (30 days)</p>
        <p class="text-3xl font-bold text-green-600">{formatCurrency(data.revenue_period)}</p>
      </div>
      
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <p class="text-sm text-gray-500 mb-1">Outstanding</p>
        <p class="text-3xl font-bold text-orange-600">{formatCurrency(data.outstanding)}</p>
      </div>
      
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <p class="text-sm text-gray-500 mb-1">Total Revenue</p>
        <p class="text-3xl font-bold text-blue-600">{formatCurrency(data.total_revenue)}</p>
      </div>
      
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <p class="text-sm text-gray-500 mb-1">Total Invoices</p>
        <p class="text-3xl font-bold text-gray-900">{data.total_invoices}</p>
        {#if data.overdue_count > 0}
          <p class="text-sm text-red-600 mt-1">{data.overdue_count} overdue</p>
        {/if}
      </div>
    </div>
    
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <!-- Revenue Chart -->
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">Revenue (6 Months)</h2>
        <div class="space-y-3">
          {#each data.revenue_chart as month}
            <div class="flex items-center gap-4">
              <span class="w-20 text-sm text-gray-600">{month.month}</span>
              <div class="flex-1 bg-gray-100 rounded-full h-6 overflow-hidden">
                <div 
                  class="bg-blue-500 h-full rounded-full transition-all"
                  style="width: {Math.min(100, (month.revenue / Math.max(...data.revenue_chart.map(m => m.revenue || 1))) * 100)}%"
                ></div>
              </div>
              <span class="w-24 text-right text-sm font-medium">{formatCurrency(month.revenue)}</span>
            </div>
          {/each}
        </div>
      </div>
      
      <!-- Top Clients -->
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">Top Clients</h2>
        {#if data.top_clients.length === 0}
          <p class="text-gray-500 text-center py-8">No clients yet</p>
        {:else}
          <div class="space-y-4">
            {#each data.top_clients as client}
              <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p class="font-medium text-gray-900">{client.name}</p>
                  <p class="text-sm text-gray-500">{client.invoice_count} invoices</p>
                </div>
                <div class="text-right">
                  <p class="font-medium text-gray-900">{formatCurrency(client.total_billed)}</p>
                  <p class="text-sm text-green-600">{formatCurrency(client.total_paid)} paid</p>
                </div>
              </div>
            {/each}
          </div>
        {/if}
      </div>
    </div>
    
    <!-- Overdue Invoices -->
    {#if data.overdue_invoices.length > 0}
      <div class="mt-8 bg-red-50 rounded-lg border border-red-200 p-6">
        <h2 class="text-lg font-semibold text-red-800 mb-4">⚠️ Overdue Invoices</h2>
        <div class="space-y-3">
          {#each data.overdue_invoices as inv}
            <div class="flex items-center justify-between bg-white p-4 rounded-lg border border-red-200">
              <div>
                <a href="/invoices/{inv.id}" class="font-medium text-red-800 hover:underline">
                  #{inv.invoice_number}
                </a>
                <p class="text-sm text-red-600">{inv.days_overdue} days overdue</p>
              </div>
              <div class="text-right">
                <p class="font-medium text-red-800">{formatCurrency(inv.outstanding)} outstanding</p>
              </div>
            </div>
          {/each}
        </div>
      </div>
    {/if}
    
    <!-- Status Breakdown -->
    <div class="mt-8 bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h2 class="text-lg font-semibold text-gray-900 mb-4">Invoice Status</h2>
      <div class="flex flex-wrap gap-4">
        {#each Object.entries(data.status_breakdown) as [status, count]}
          <div class="px-4 py-2 rounded-full text-sm font-medium
            {status === 'paid' ? 'bg-green-100 text-green-800' : ''}
            {status === 'sent' ? 'bg-blue-100 text-blue-800' : ''}
            {status === 'draft' ? 'bg-gray-100 text-gray-800' : ''}
            {status === 'overdue' ? 'bg-red-100 text-red-800' : ''}
            {status === 'partial' ? 'bg-yellow-100 text-yellow-800' : ''}
          ">
            {status}: {count}
          </div>
        {/each}
      </div>
    </div>
  {/if}
</div>
