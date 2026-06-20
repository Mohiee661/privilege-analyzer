const env = import.meta.env as Record<string, string | undefined>;

function resolveApiBaseUrl(): string {
  const raw = env.NEXT_PUBLIC_API_URL ?? env.VITE_API_BASE_URL;
  if (raw) {
    const normalized = raw.replace(/\/$/, "");
    return normalized.endsWith("/api/v1") ? normalized : `${normalized}/api/v1`;
  }

  if (typeof window === "undefined") {
    return "http://127.0.0.1:8000/api/v1";
  }

  return "/api/v1";
}

export const API_BASE_URL = resolveApiBaseUrl();

export async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      Accept: "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    const detail = await response.text().catch(() => "");
    throw new Error(
      detail
        ? `Request failed: ${response.status} ${response.statusText} - ${detail}`
        : `Request failed: ${response.status} ${response.statusText}`,
    );
  }

  return (await response.json()) as T;
}
