/**
 * Authenticated API client.
 *
 * Single place where the frontend holds identity and interprets the guarded
 * backend's response envelope. Everything that calls a tool goes through here,
 * so the rules below cannot be forgotten at an individual call site.
 *
 * The envelope changed with the guarded path, and the differences matter:
 *
 *   legacy                          guarded
 *   ------                          -------
 *   always HTTP 200                 200 / 202 / 4xx / 502
 *   failures nested in `result`     success:false, executed:false
 *   -                               202 = accepted, NOT executed
 *
 * The single most important rule: **never infer execution from an HTTP status.**
 * A 202 is a successful request for an action that deliberately did not happen.
 * Read `executed`.
 */

/** Where the token lives.
 *
 * sessionStorage rather than localStorage: clinical workstations are shared, so
 * a token that dies with the tab is the safer default. Neither survives XSS —
 * an httpOnly, SameSite cookie issued by the server is stronger, and is the
 * right upgrade if the deployment ever puts the API on the same origin.
 */
const TOKEN_KEY = 'hms_auth_token';
const USER_KEY = 'hms_auth_user';

export class AuthRequiredError extends Error {
  constructor(message = 'Authentication required') {
    super(message);
    this.name = 'AuthRequiredError';
    this.code = 'UNAUTHENTICATED';
  }
}

export class PolicyDeniedError extends Error {
  constructor(message, rule) {
    super(message);
    this.name = 'PolicyDeniedError';
    this.code = 'POLICY_DENIED';
    this.rule = rule;
  }
}

/** Outcomes a caller can branch on without knowing about HTTP. */
export const Outcome = {
  EXECUTED: 'EXECUTED',
  AWAITING_APPROVAL: 'AWAITING_APPROVAL',
  AWAITING_CONFIRMATION: 'AWAITING_CONFIRMATION',
  DENIED: 'DENIED',
  INVALID: 'INVALID',
  UNKNOWN_TOOL: 'UNKNOWN_TOOL',
  FAILED: 'FAILED',
};

function safeStorage() {
  try {
    if (typeof sessionStorage !== 'undefined') return sessionStorage;
  } catch {
    /* private browsing or blocked storage */
  }
  return null;
}

/** Read `exp` without verifying. Verification is the server's job; this only
 *  avoids sending a token we already know is stale. */
function tokenExpiry(token) {
  try {
    const [, payload] = token.split('.');
    const claims = JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/')));
    return typeof claims.exp === 'number' ? claims.exp * 1000 : null;
  } catch {
    return null;
  }
}

class ApiClient {
  constructor() {
    this.baseURL = `http://${window.location.hostname}:8000`;
    this.onAuthRequired = null; // set by the app to trigger re-login
  }

  // -- token ------------------------------------------------------------

  setSession(token, user) {
    const store = safeStorage();
    if (!store) return;
    store.setItem(TOKEN_KEY, token);
    if (user) store.setItem(USER_KEY, JSON.stringify(user));
  }

  getToken() {
    const store = safeStorage();
    if (!store) return null;
    const token = store.getItem(TOKEN_KEY);
    if (!token) return null;

    const expiresAt = tokenExpiry(token);
    if (expiresAt !== null && expiresAt <= Date.now()) {
      this.clearSession();
      return null;
    }
    return token;
  }

  getUser() {
    const store = safeStorage();
    if (!store) return null;
    try {
      return JSON.parse(store.getItem(USER_KEY) || 'null');
    } catch {
      return null;
    }
  }

  isAuthenticated() {
    return this.getToken() !== null;
  }

  clearSession() {
    const store = safeStorage();
    if (!store) return;
    store.removeItem(TOKEN_KEY);
    store.removeItem(USER_KEY);
  }

  // -- requests ---------------------------------------------------------

  authHeaders() {
    const token = this.getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  async login(username, password) {
    const response = await fetch(`${this.baseURL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });

    const body = await response.json().catch(() => ({}));

    if (!response.ok) {
      // The server returns one message for every failure mode on purpose.
      throw new AuthRequiredError(body?.error?.message || 'Invalid credentials');
    }

    this.setSession(body.token, body.user);
    return body;
  }

  logout() {
    this.clearSession();
  }

  /**
   * Call a tool through the guarded endpoint.
   *
   * Always resolves to a normalised result; it throws only for authentication,
   * because that is the one case the whole app must react to identically.
   */
  async callTool(name, args = {}) {
    if (!this.isAuthenticated()) {
      this.#requireAuth();
      throw new AuthRequiredError();
    }

    let response;
    try {
      response = await fetch(`${this.baseURL}/v2/tools/call`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
          ...this.authHeaders(),
        },
        body: JSON.stringify({ params: { name, arguments: args } }),
      });
    } catch (networkError) {
      // A network failure is never a completed action.
      return {
        outcome: Outcome.FAILED,
        executed: false,
        tool: name,
        error: { code: 'NETWORK_ERROR', message: networkError.message },
      };
    }

    const body = await response.json().catch(() => ({}));
    return this.#interpret(name, response.status, body);
  }

  #requireAuth() {
    this.clearSession();
    if (typeof this.onAuthRequired === 'function') this.onAuthRequired();
  }

  #interpret(name, status, body) {
    const base = {
      tool: body?.tool || name,
      runId: body?.run_id || null,
      executed: body?.executed === true,
    };

    if (status === 401) {
      this.#requireAuth();
      throw new AuthRequiredError(body?.error?.message);
    }

    if (status === 200 && body?.success === true) {
      return { ...base, outcome: Outcome.EXECUTED, executed: true, result: body.result };
    }

    // Accepted, deliberately not executed. Must never read as completion.
    if (status === 202) {
      const awaiting =
        body?.status === 'REQUIRE_HUMAN_APPROVAL'
          ? Outcome.AWAITING_APPROVAL
          : Outcome.AWAITING_CONFIRMATION;
      return { ...base, outcome: awaiting, executed: false, reason: body?.reason || '' };
    }

    if (status === 403) {
      return {
        ...base,
        outcome: Outcome.DENIED,
        executed: false,
        error: { code: 'POLICY_DENIED', message: body?.error?.message || 'Not permitted' },
        rule: body?.error?.rule,
      };
    }

    if (status === 404) {
      return {
        ...base,
        outcome: Outcome.UNKNOWN_TOOL,
        executed: false,
        error: { code: 'UNKNOWN_TOOL', message: body?.error?.message || 'No such tool' },
      };
    }

    if (status === 400) {
      return {
        ...base,
        outcome: Outcome.INVALID,
        executed: false,
        error: { code: body?.error?.code || 'INVALID_ARGUMENTS', message: body?.error?.message || 'Invalid arguments' },
        violations: body?.error?.violations || [],
      };
    }

    return {
      ...base,
      outcome: Outcome.FAILED,
      executed: false,
      error: {
        code: body?.error?.code || 'TOOL_EXECUTION_FAILED',
        message: body?.error?.message || `Request failed (HTTP ${status})`,
      },
    };
  }
}

export const apiClient = new ApiClient();
export default apiClient;
