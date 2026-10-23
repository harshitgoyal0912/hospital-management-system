/**
 * Response-envelope handling.
 *
 * The rule these tests exist to protect: the frontend must never infer that an
 * action happened from an HTTP status. A 202 is a successful request for an
 * action that deliberately did NOT happen, and rendering it as "done" would
 * defeat the approval gate entirely.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import apiClient, { AuthRequiredError, Outcome } from '../apiClient';

// a token that expires far in the future
function makeToken(role = 'doctor', expOffsetSeconds = 3600) {
  const b64 = (o) => btoa(JSON.stringify(o)).replace(/=/g, '');
  const claims = { sub: 'u-1', role, exp: Math.floor(Date.now() / 1000) + expOffsetSeconds };
  return `${b64({ alg: 'HS256', typ: 'JWT' })}.${b64(claims)}.sig`;
}

function mockResponse(status, body) {
  return Promise.resolve({
    status,
    ok: status >= 200 && status < 300,
    json: () => Promise.resolve(body),
  });
}

beforeEach(() => {
  sessionStorage.clear();
  apiClient.onAuthRequired = null;
  vi.restoreAllMocks();
});

afterEach(() => {
  sessionStorage.clear();
});

describe('session handling', () => {
  it('stores and reports an authenticated session', () => {
    apiClient.setSession(makeToken(), { id: 'u-1', role: 'doctor' });
    expect(apiClient.isAuthenticated()).toBe(true);
    expect(apiClient.getUser().role).toBe('doctor');
  });

  it('treats an expired token as no session', () => {
    apiClient.setSession(makeToken('doctor', -10), { id: 'u-1', role: 'doctor' });
    expect(apiClient.isAuthenticated()).toBe(false);
    expect(apiClient.getToken()).toBeNull();
  });

  it('clears the session on logout', () => {
    apiClient.setSession(makeToken(), { id: 'u-1', role: 'doctor' });
    apiClient.logout();
    expect(apiClient.isAuthenticated()).toBe(false);
    expect(apiClient.getUser()).toBeNull();
  });

  it('sends the bearer token on tool calls', async () => {
    apiClient.setSession(makeToken(), { id: 'u-1', role: 'doctor' });
    const fetchMock = vi.fn(() =>
      mockResponse(200, { success: true, executed: true, result: {}, run_id: 'r1' })
    );
    vi.stubGlobal('fetch', fetchMock);

    await apiClient.callTool('list_beds', {});

    const [, options] = fetchMock.mock.calls[0];
    expect(options.headers.Authorization).toMatch(/^Bearer /);
  });

  it('calls the guarded endpoint, not the legacy one', async () => {
    apiClient.setSession(makeToken(), { id: 'u-1', role: 'doctor' });
    const fetchMock = vi.fn(() =>
      mockResponse(200, { success: true, executed: true, result: {} })
    );
    vi.stubGlobal('fetch', fetchMock);

    await apiClient.callTool('list_beds', {});
    expect(fetchMock.mock.calls[0][0]).toContain('/v2/tools/call');
  });
});

describe('response envelope', () => {
  beforeEach(() => {
    apiClient.setSession(makeToken(), { id: 'u-1', role: 'doctor' });
  });

  it('200 with success marks the action executed', async () => {
    vi.stubGlobal('fetch', () =>
      mockResponse(200, { success: true, executed: true, result: { beds: [] }, run_id: 'r1' })
    );
    const out = await apiClient.callTool('list_beds', {});
    expect(out.outcome).toBe(Outcome.EXECUTED);
    expect(out.executed).toBe(true);
    expect(out.result).toEqual({ beds: [] });
  });

  it('202 approval is NOT executed', async () => {
    vi.stubGlobal('fetch', () =>
      mockResponse(202, {
        success: false,
        executed: false,
        status: 'REQUIRE_HUMAN_APPROVAL',
        tool: 'delete_patient',
        reason: 'irreversible',
      })
    );
    const out = await apiClient.callTool('delete_patient', { patient_id: 'P1' });
    expect(out.outcome).toBe(Outcome.AWAITING_APPROVAL);
    expect(out.executed).toBe(false);
  });

  it('202 confirmation is NOT executed', async () => {
    vi.stubGlobal('fetch', () =>
      mockResponse(202, {
        success: false,
        executed: false,
        status: 'REQUIRE_CONFIRMATION',
        tool: 'discharge_bed',
      })
    );
    const out = await apiClient.callTool('discharge_bed', { bed_id: 'B1' });
    expect(out.outcome).toBe(Outcome.AWAITING_CONFIRMATION);
    expect(out.executed).toBe(false);
  });

  it('403 is a policy denial and not executed', async () => {
    vi.stubGlobal('fetch', () =>
      mockResponse(403, {
        success: false,
        executed: false,
        error: { code: 'POLICY_DENIED', message: 'not permitted', rule: 'role_not_permitted' },
      })
    );
    const out = await apiClient.callTool('delete_patient', { patient_id: 'P1' });
    expect(out.outcome).toBe(Outcome.DENIED);
    expect(out.executed).toBe(false);
    expect(out.rule).toBe('role_not_permitted');
  });

  it('400 surfaces the schema violations', async () => {
    vi.stubGlobal('fetch', () =>
      mockResponse(400, {
        success: false,
        executed: false,
        error: { code: 'INVALID_ARGUMENTS', message: 'rejected', violations: [{ loc: ['patient_id'] }] },
      })
    );
    const out = await apiClient.callTool('assign_bed_to_patient', { bed_id: 'B1' });
    expect(out.outcome).toBe(Outcome.INVALID);
    expect(out.executed).toBe(false);
    expect(out.violations).toHaveLength(1);
  });

  it('404 is an unknown tool', async () => {
    vi.stubGlobal('fetch', () =>
      mockResponse(404, { success: false, executed: false, error: { code: 'UNKNOWN_TOOL' } })
    );
    const out = await apiClient.callTool('made_up', {});
    expect(out.outcome).toBe(Outcome.UNKNOWN_TOOL);
    expect(out.executed).toBe(false);
  });

  it('502 is a failure, never a success', async () => {
    vi.stubGlobal('fetch', () =>
      mockResponse(502, {
        success: false,
        executed: false,
        error: { code: 'TOOL_EXECUTION_FAILED', message: 'did not complete' },
      })
    );
    const out = await apiClient.callTool('list_beds', {});
    expect(out.outcome).toBe(Outcome.FAILED);
    expect(out.executed).toBe(false);
  });

  it('a network failure is never a completed action', async () => {
    vi.stubGlobal('fetch', () => Promise.reject(new Error('offline')));
    const out = await apiClient.callTool('assign_bed_to_patient', { bed_id: 'B1', patient_id: 'P1' });
    expect(out.executed).toBe(false);
    expect(out.outcome).toBe(Outcome.FAILED);
  });

  it('no non-executed outcome ever reports executed', async () => {
    const cases = [
      [202, { status: 'REQUIRE_HUMAN_APPROVAL', executed: false }],
      [403, { executed: false, error: {} }],
      [400, { executed: false, error: {} }],
      [404, { executed: false, error: {} }],
      [502, { executed: false, error: {} }],
    ];
    for (const [status, body] of cases) {
      vi.stubGlobal('fetch', () => mockResponse(status, { success: false, ...body }));
      const out = await apiClient.callTool('delete_patient', { patient_id: 'P1' });
      expect(out.executed, `status ${status} reported executed`).toBe(false);
    }
  });
});

describe('authentication failures', () => {
  it('401 throws and clears the session', async () => {
    apiClient.setSession(makeToken(), { id: 'u-1', role: 'doctor' });
    vi.stubGlobal('fetch', () =>
      mockResponse(401, { success: false, executed: false, error: { code: 'INVALID_TOKEN' } })
    );

    await expect(apiClient.callTool('list_beds', {})).rejects.toThrow(AuthRequiredError);
    expect(apiClient.isAuthenticated()).toBe(false);
  });

  it('401 notifies the app so it can require login again', async () => {
    apiClient.setSession(makeToken(), { id: 'u-1', role: 'doctor' });
    const onAuthRequired = vi.fn();
    apiClient.onAuthRequired = onAuthRequired;
    vi.stubGlobal('fetch', () => mockResponse(401, { error: {} }));

    await expect(apiClient.callTool('list_beds', {})).rejects.toThrow();
    expect(onAuthRequired).toHaveBeenCalled();
  });

  it('calling a tool with no session throws without any request', async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);

    await expect(apiClient.callTool('list_beds', {})).rejects.toThrow(AuthRequiredError);
    expect(fetchMock).not.toHaveBeenCalled();
  });
});

describe('login', () => {
  it('stores the session returned by the server', async () => {
    vi.stubGlobal('fetch', () =>
      mockResponse(200, { success: true, token: makeToken('nurse'), user: { id: 'u-7', role: 'nurse' } })
    );
    await apiClient.login('nurse@hospital.com', 'pw');
    expect(apiClient.isAuthenticated()).toBe(true);
    expect(apiClient.getUser().role).toBe('nurse');
  });

  it('rejects bad credentials without storing anything', async () => {
    vi.stubGlobal('fetch', () =>
      mockResponse(401, { success: false, error: { code: 'INVALID_CREDENTIALS', message: 'invalid credentials' } })
    );
    await expect(apiClient.login('x', 'y')).rejects.toThrow(AuthRequiredError);
    expect(apiClient.isAuthenticated()).toBe(false);
  });

  it('never sends a role to the server', async () => {
    const fetchMock = vi.fn(() =>
      mockResponse(200, { token: makeToken(), user: { id: 'u-1', role: 'doctor' } })
    );
    vi.stubGlobal('fetch', fetchMock);
    await apiClient.login('a@b.c', 'pw');
    const sent = JSON.parse(fetchMock.mock.calls[0][1].body);
    expect(sent).not.toHaveProperty('role');
    expect(Object.keys(sent).sort()).toEqual(['password', 'username']);
  });
});
