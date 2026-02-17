<script>
  import '../app.css';
</script>

<div class="min-h-screen flex flex-col">
  <nav class="bg-white border-b border-gray-200">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between h-16">
        <div class="flex items-center">
          <a href="/" class="flex items-center">
            <span class="text-2xl mr-2">🧾</span>
            <span class="font-bold text-xl text-blue-600">Smart Invoice</span>
          </a>
          <div class="ml-10 flex space-x-4">
            <a href="/dashboard" class="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">
              📊 Dashboard
            </a>
            <a href="/" class="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">
              New Invoice
            </a>
            <a href="/invoices" class="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">
              Invoices
            </a>
            <a href="/rate-card" class="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">
              Rate Card
            </a>
            <a href="/settings" class="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">
              Settings
            </a>
          </div>
        </div>
      </div>
    </div>
  </nav>
  
  <main class="flex-1">
    <slot />
  </main>
  
  <footer class="bg-white border-t border-gray-200 py-4">
    <div class="max-w-7xl mx-auto px-4 text-center text-sm text-gray-500">
      Smart Invoice &copy; 2026 - AI-powered invoicing with guaranteed pricing
    </div>
  </footer>
</div>
