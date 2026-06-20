import {
  loadIdentityDetailPageData as loadIdentityDetailPageDataFromLib,
  loadIdentityExplorerPageData as loadIdentityExplorerPageDataFromLib,
  searchIdentities as searchIdentitiesFromLib,
} from "@/lib/api";
import { requestJson } from "./client";
import type { Identity, IdentityListResponse } from "@/types";

export async function listIdentities(page = 1, pageSize = 20): Promise<IdentityListResponse> {
  return requestJson<IdentityListResponse>(`/identities?page=${page}&page_size=${pageSize}`);
}

export async function getIdentity(personId: string): Promise<Identity> {
  return requestJson<Identity>(`/identities/${personId}`);
}

export const loadIdentityExplorerPageData = loadIdentityExplorerPageDataFromLib;
export const loadIdentityDetailPageData = loadIdentityDetailPageDataFromLib;
export const searchIdentities = searchIdentitiesFromLib;
