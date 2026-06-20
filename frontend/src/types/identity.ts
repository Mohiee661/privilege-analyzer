export interface IdentityAccount {
  status: string;
  role: string;
  last_login?: string | null;
}

export interface Identity {
  person_id: string;
  name: string;
  email: string;
  accounts: Record<string, IdentityAccount>;
  platforms: string[];
}

export interface IdentityListResponse {
  items: Identity[];
  page: number;
  page_size: number;
  total: number;
}
