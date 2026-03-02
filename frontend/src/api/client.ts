/**
 * Axios HTTP client configured for the Bridge API.
 *
 * Key features:
 * - All requests go to "/api/..." (proxied to FastAPI in development)
 * - Cookies are sent automatically by the browser (same origin via proxy)
 * - 401 responses trigger an automatic token refresh, then retry the
 *   original request. If the refresh also fails, the user is redirected
 *   to the login page.
 *
 * WHY an interceptor instead of checking 401 in every API call:
 * The interceptor runs automatically for ALL requests. Without it, every
 * single API call would need try/catch logic for expired tokens. The
 * interceptor handles it once, transparently.
 */
import axios from "axios";
import type { AxiosError, InternalAxiosRequestConfig } from "axios";

/** Extended request config with a _retry flag to prevent infinite loops. */
interface RetryableRequest extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

const api = axios.create({
  // Base URL for all requests. The Vite proxy (see vite.config.ts)
  // forwards "/api" to the FastAPI backend at localhost:8000.
  baseURL: "/api",
});

// Track whether we're currently refreshing the token, so we don't
// fire multiple refresh requests simultaneously.
let isRefreshing = false;

// Queue of requests that arrived while we were refreshing.
// Once the refresh completes, we retry all of them.
let failedQueue: Array<{
  resolve: (value: unknown) => void;
  reject: (reason: unknown) => void;
}> = [];

/**
 * Process the queue of failed requests after a token refresh.
 * If the refresh succeeded (error is null), retry them all.
 * If it failed, reject them all.
 */
function processQueue(error: unknown) {
  failedQueue.forEach((promise) => {
    if (error) {
      promise.reject(error);
    } else {
      promise.resolve(undefined);
    }
  });
  failedQueue = [];
}

// Response interceptor: intercept 401s and try to refresh the token.
api.interceptors.response.use(
  // Success: pass through unchanged.
  (response) => response,

  // Error: check if it's a 401 we can recover from.
  async (error: AxiosError) => {
    const originalRequest = error.config as RetryableRequest | undefined;

    // Only attempt refresh if:
    // 1. We got a 401 (Unauthorized)
    // 2. We have a request config to retry
    // 3. This isn't already a retry (prevents infinite loops)
    // 4. This isn't an auth endpoint (login/register/refresh return 401
    //    for wrong credentials or missing tokens -- not expired tokens)
    const isAuthEndpoint = originalRequest?.url?.startsWith("/auth/");
    if (
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retry &&
      !isAuthEndpoint
    ) {
      if (isRefreshing) {
        // Another request is already refreshing the token.
        // Queue this request to be retried after the refresh completes.
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then(() => api(originalRequest));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        // Call the refresh endpoint. If it succeeds, the backend sets
        // a new access_token cookie automatically.
        await api.post("/auth/refresh");
        processQueue(null);
        // Retry the original request with the fresh cookie.
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError);
        // Refresh failed -- the user's session has fully expired.
        // We don't redirect here; the protectedLoader in App.tsx
        // handles the redirect to /login on 401.
        // Using window.location.href would cause an infinite loop:
        // page reload → getMe() → 401 → refresh → 401 → redirect → repeat.
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  },
);

export default api;
