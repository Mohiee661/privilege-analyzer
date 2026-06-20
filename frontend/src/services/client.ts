const env = import.meta.env as Record<string, string | undefined>;

export const API_BASE_URL = (env.NEXT_PUBLIC_API_URL ?? env.VITE_API_BASE_URL ?? "/api/v1").replace(
  /\/$/,
  "",
);

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
