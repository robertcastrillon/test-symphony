export interface User {
  id: string;
  email: string;
  name: string;
  telegram_chat_id?: string;
}

export interface Client {
  id: string;
  user_id: string;
  name: string;
  email?: string;
  hourly_rate: number;
  currency: string;
  created_at: string;
}

export interface Project {
  id: string;
  user_id: string;
  client_id?: string;
  name: string;
  description?: string;
  color: string;
  is_active: boolean;
  created_at: string;
}

export interface Session {
  id: string;
  user_id: string;
  project_id: string;
  description?: string;
  started_at: string;
  ended_at?: string;
  duration_seconds?: number;
  created_at: string;
}

export interface Invoice {
  id: string;
  user_id: string;
  client_id: string;
  invoice_number: string;
  period_start: string;
  period_end: string;
  total_hours: number;
  total_amount: number;
  currency: string;
  status: string;
  pdf_path?: string;
  created_at: string;
}

export interface ProjectBreakdown {
  project_id: string;
  project_name: string;
  total_hours: number;
  billable_hours: number;
}

export interface ClientBreakdown {
  client_id: string;
  client_name: string;
  total_hours: number;
  billable_hours: number;
}

export interface DayBreakdown {
  date: string;
  total_hours: number;
  billable_hours: number;
}

export interface ReportSummary {
  total_hours: number;
  billable_hours: number;
  by_project: ProjectBreakdown[];
  by_client: ClientBreakdown[];
  by_day: DayBreakdown[];
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
