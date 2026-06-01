const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export type AuthUser = {
  id: string;
  telegram_id: number;
  username?: string | null;
  first_name?: string | null;
  last_name?: string | null;
  language_code?: string | null;
  is_admin: boolean;
};

export type AuthResponse = {
  access_token: string;
  token_type: "bearer";
  user: AuthUser;
};

export function getTelegramInitData() {
  return window.Telegram?.WebApp?.initData || "";
}

export function isTelegramWebApp() {
  return Boolean(getTelegramInitData());
}

export async function authenticateWithTelegram(initData: string): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE_URL}/auth/telegram`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ init_data: initData }),
  });
  if (!response.ok) {
    throw new Error("Не вдалося увійти через Telegram.");
  }
  return response.json();
}
