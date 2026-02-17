const API_BASE = '/api';

async function fetchApi<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    },
    ...options
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// Rate Items
export interface RateItem {
  id: string;
  category: string;
  name: string;
  description?: string;
  rate: number;
  unit: string;
  aliases: string[];
  is_active: boolean;
  created_at: string;
}

export interface RateItemCreate {
  category: string;
  name: string;
  description?: string;
  rate: number;
  unit: string;
  aliases?: string[];
}

export const rateItems = {
  list: () => fetchApi<RateItem[]>('/rate-items'),
  create: (data: RateItemCreate) => fetchApi<RateItem>('/rate-items', {
    method: 'POST',
    body: JSON.stringify(data)
  }),
  update: (id: string, data: RateItemCreate) => fetchApi<RateItem>(`/rate-items/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data)
  }),
  delete: (id: string) => fetchApi(`/rate-items/${id}`, { method: 'DELETE' })
};

// Invoice Parsing
export interface ParsedLineItem {
  item_key: string;
  description: string;
  quantity: number;
  unit: string;
  unit_price: number;
  line_total: number;
  rate_item_id?: string;
  notes?: string;
  matched: boolean;
}

export interface ParseResponse {
  line_items: ParsedLineItem[];
  subtotal: number;
  tax_amount: number;
  tax_name: string;
  secondary_tax_amount?: number;
  secondary_tax_name?: string;
  total: number;
  client_name?: string;
  work_date?: string;
  notes?: string;
  unmatched_items: string[];
}

export interface InvoiceLineItem {
  id: string;
  description: string;
  quantity: number;
  unit: string;
  unit_price: number;
  line_total: number;
}

export interface Invoice {
  id: string;
  invoice_number: string;
  status: string;
  client_name?: string;
  work_date?: string;
  invoice_date: string;
  due_date?: string;
  subtotal: number;
  tax_amount: number;
  secondary_tax_amount?: number;
  total: number;
  notes?: string;
  line_items: InvoiceLineItem[];
  created_at: string;
}

export const invoices = {
  parse: (work_description: string, client_id?: string) => 
    fetchApi<ParseResponse>('/invoices/parse', {
      method: 'POST',
      body: JSON.stringify({ work_description, client_id })
    }),
  create: (work_description: string, client_id?: string, notes?: string) =>
    fetchApi<Invoice>('/invoices', {
      method: 'POST',
      body: JSON.stringify({ work_description, client_id, notes })
    }),
  list: (status?: string, limit?: number) => {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (limit) params.append('limit', limit.toString());
    return fetchApi<Invoice[]>(`/invoices?${params}`);
  },
  get: (id: string) => fetchApi<Invoice>(`/invoices/${id}`),
  downloadPdf: (id: string) => `${API_BASE}/invoices/${id}/pdf`
};

// Business Settings
export interface BusinessSettings {
  business_name?: string;
  business_address?: string;
  business_phone?: string;
  business_email?: string;
  tax_rate?: number;
  tax_name?: string;
  secondary_tax_rate?: number;
  secondary_tax_name?: string;
}

export const settings = {
  get: () => fetchApi<BusinessSettings>('/settings'),
  update: (data: Partial<BusinessSettings>) => fetchApi<BusinessSettings>('/settings', {
    method: 'PUT',
    body: JSON.stringify(data)
  })
};

// Clients
export interface Client {
  id: string;
  name: string;
  email?: string;
  phone?: string;
  address?: string;
  notes?: string;
  created_at: string;
}

export interface ClientCreate {
  name: string;
  email?: string;
  phone?: string;
  address?: string;
  notes?: string;
}

export const clients = {
  list: () => fetchApi<Client[]>('/clients'),
  create: (data: ClientCreate) => fetchApi<Client>('/clients', {
    method: 'POST',
    body: JSON.stringify(data)
  })
};
