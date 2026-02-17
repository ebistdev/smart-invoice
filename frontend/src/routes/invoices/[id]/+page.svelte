<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { invoices, type Invoice } from '$lib/api';
  
  let invoice: Invoice | null = null;
  let isLoading = true;
  let error = '';
  
  // Payment form
  let showPaymentForm = false;
  let paymentAmount = 0;
  let paymentMethod = 'cash';
  let paymentReference = '';
  let isRecordingPayment = false;
  
  // Email form
  let showEmailForm = false;
  let emailTo = '';
  let emailMessage = '';
  let isSendingEmail = false;
  let emailSuccess = '';
  
  $: invoiceId = $page.params.id;
  
  onMount(async () => {
    try {
      invoice = await invoices.get(invoiceId);
      if (invoice?.client_name) {
        emailTo = ''; // Would get from client
      }
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to load invoice';
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
      month: 'long',
      day: 'numeric'
    });
  }
  
  function getStatusColor(status: string): string {
    switch (status) {
      case 'paid': return 'bg-green-100 text-green-800';
      case 'sent': return 'bg-blue-100 text-blue-800';
      case 'overdue': return 'bg-red-100 text-red-800';
      case 'partial': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  }
  
  async function recordPayment() {
    if (!invoice || paymentAmount <= 0) return;
    
    isRecordingPayment = true;
    try {
      const response = await fetch(`/api/invoices/${invoiceId}/payment`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          amount: paymentAmount,
          method: paymentMethod,
          reference: paymentReference || undefined
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        invoice = await invoices.get(invoiceId);
        showPaymentForm = false;
        paymentAmount = 0;
        paymentReference = '';
      } else {
        throw new Error('Failed to record payment');
      }
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to record payment';
    } finally {
      isRecordingPayment = false;
    }
  }
  
  async function sendEmail() {
    if (!invoice) return;
    
    isSendingEmail = true;
    emailSuccess = '';
    try {
      const params = new URLSearchParams();
      if (emailTo) params.append('to_email', emailTo);
      if (emailMessage) params.append('message', emailMessage);
      
      const response = await fetch(`/api/invoices/${invoiceId}/send?${params}`, {
        method: 'POST'
      });
      
      if (response.ok) {
        const result = await response.json();
        emailSuccess = `Sent to ${result.sent_to}`;
        invoice = await invoices.get(invoiceId);
        setTimeout(() => {
          showEmailForm = false;
          emailSuccess = '';
        }, 2000);
      } else {
        const err = await response.json();
        throw new Error(err.detail || 'Failed to send email');
      }
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to send email';
    } finally {
      isSendingEmail = false;
    }
  }
</script>

<svelte:head>
  <title>{invoice ? `Invoice #${invoice.invoice_number}` : 'Invoice'} - Smart Invoice</title>
</svelte:head>

<div class="max-w-4xl mx-auto py-8 px-4">
  {#if isLoading}
    <div class="text-center py-12 text-gray-500">Loading...</div>
  {:else if error}
    <div class="bg-red-50 border border-red-200 rounded-lg p-4">
      <p class="text-red-700">❌ {error}</p>
    </div>
  {:else if invoice}
    <!-- Header -->
    <div class="flex items-center justify-between mb-8">
      <div>
        <a href="/invoices" class="text-gray-500 hover:text-gray-700 text-sm mb-2 inline-block">
          ← Back to Invoices
        </a>
        <h1 class="text-3xl font-bold text-gray-900">Invoice #{invoice.invoice_number}</h1>
        <p class="text-gray-600">
          {invoice.client_name || 'No client'} • {formatDate(invoice.invoice_date)}
        </p>
      </div>
      <div class="flex items-center gap-3">
        <span class="px-3 py-1 rounded-full text-sm font-medium {getStatusColor(invoice.status)}">
          {invoice.status}
        </span>
      </div>
    </div>
    
    <!-- Actions -->
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6 flex gap-3">
      <a 
        href={invoices.downloadPdf(invoice.id)}
        target="_blank"
        class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition"
      >
        📄 Download PDF
      </a>
      <button
        onclick={() => showEmailForm = !showEmailForm}
        class="bg-white text-gray-700 border border-gray-300 px-4 py-2 rounded-lg hover:bg-gray-50 transition"
      >
        ✉️ Send Email
      </button>
      {#if invoice.status !== 'paid'}
        <button
          onclick={() => { showPaymentForm = !showPaymentForm; paymentAmount = invoice.total - (invoice.amount_paid || 0); }}
          class="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition"
        >
          💰 Record Payment
        </button>
      {/if}
    </div>
    
    <!-- Email Form -->
    {#if showEmailForm}
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <h3 class="text-lg font-semibold mb-4">Send Invoice via Email</h3>
        {#if emailSuccess}
          <div class="bg-green-50 text-green-700 p-3 rounded-lg mb-4">✅ {emailSuccess}</div>
        {/if}
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Recipient Email</label>
            <input 
              type="email"
              bind:value={emailTo}
              placeholder="client@example.com (or leave blank to use client's email)"
              class="w-full border border-gray-300 rounded-lg px-3 py-2"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Custom Message (optional)</label>
            <textarea 
              bind:value={emailMessage}
              placeholder="Add a personal note..."
              rows="2"
              class="w-full border border-gray-300 rounded-lg px-3 py-2"
            ></textarea>
          </div>
          <div class="flex gap-3">
            <button
              onclick={sendEmail}
              disabled={isSendingEmail}
              class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {isSendingEmail ? 'Sending...' : 'Send Invoice'}
            </button>
            <button
              onclick={() => showEmailForm = false}
              class="text-gray-600 hover:text-gray-900"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    {/if}
    
    <!-- Payment Form -->
    {#if showPaymentForm}
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <h3 class="text-lg font-semibold mb-4">Record Payment</h3>
        <div class="grid grid-cols-3 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Amount</label>
            <input 
              type="number"
              bind:value={paymentAmount}
              step="0.01"
              min="0"
              class="w-full border border-gray-300 rounded-lg px-3 py-2"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Method</label>
            <select bind:value={paymentMethod} class="w-full border border-gray-300 rounded-lg px-3 py-2">
              <option value="cash">Cash</option>
              <option value="check">Check</option>
              <option value="etransfer">E-Transfer</option>
              <option value="credit_card">Credit Card</option>
              <option value="bank_transfer">Bank Transfer</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Reference (optional)</label>
            <input 
              type="text"
              bind:value={paymentReference}
              placeholder="Check #, Transaction ID"
              class="w-full border border-gray-300 rounded-lg px-3 py-2"
            />
          </div>
        </div>
        <div class="mt-4 flex gap-3">
          <button
            onclick={recordPayment}
            disabled={isRecordingPayment || paymentAmount <= 0}
            class="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50"
          >
            {isRecordingPayment ? 'Recording...' : 'Record Payment'}
          </button>
          <button
            onclick={() => showPaymentForm = false}
            class="text-gray-600 hover:text-gray-900"
          >
            Cancel
          </button>
        </div>
      </div>
    {/if}
    
    <!-- Invoice Details -->
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      <div class="p-6">
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
            {#each invoice.line_items as item}
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
                <span>{formatCurrency(invoice.subtotal)}</span>
              </div>
              {#if invoice.tax_amount > 0}
                <div class="flex justify-between text-sm">
                  <span class="text-gray-600">Tax</span>
                  <span>{formatCurrency(invoice.tax_amount)}</span>
                </div>
              {/if}
              <div class="flex justify-between text-lg font-bold pt-2 border-t border-gray-200">
                <span>Total</span>
                <span class="text-blue-600">{formatCurrency(invoice.total)}</span>
              </div>
              {#if invoice.amount_paid && invoice.amount_paid > 0}
                <div class="flex justify-between text-sm text-green-600">
                  <span>Paid</span>
                  <span>{formatCurrency(invoice.amount_paid)}</span>
                </div>
                <div class="flex justify-between text-sm font-medium">
                  <span>Balance Due</span>
                  <span>{formatCurrency(invoice.total - invoice.amount_paid)}</span>
                </div>
              {/if}
            </div>
          </div>
        </div>
        
        {#if invoice.notes}
          <div class="mt-6 p-4 bg-gray-50 rounded-lg">
            <h4 class="text-sm font-medium text-gray-700 mb-2">Notes</h4>
            <p class="text-gray-600">{invoice.notes}</p>
          </div>
        {/if}
      </div>
    </div>
  {/if}
</div>
