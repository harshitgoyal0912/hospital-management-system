/**
 * Auth service contract.
 *
 * The behaviour that matters: the role the app sees comes from the server's
 * token, and nothing the browser does can change it.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';

import apiClient from '../apiClient';
import authService from '../authService';

function makeToken(role = 'doctor') {
  const b64 = (o) => btoa(JSON.stringify(o)).replace(/=/g, '');
  return `${b64({ alg: 'HS256' })}.${b64({ sub: 'u-1', role, exp: Math.floor(Date.now() / 1000) + 3600 })}.sig`;
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
  vi.restoreAllMocks();
});

describe('signIn', () => {
  it('returns the role the server issued', async () => {
    vi.stubGlobal('fetch', () =>
      mockResponse(200, { token: makeToken('nurse'), user: { id: 'u-3', role: 'nurse' } })
    );
    const result = await authService.signIn('nurse@hospital.com', 'pw');
    expect(result.success).toBe(true);
    expect(result.user.role).toBe('nurse');
  });

  it('cannot be told which role to use', async () => {
    const fetchMock = vi.fn(() =>
      mockResponse(200, { token: makeToken('receptionist'), user: { id: 'u-4', role: 'receptionist' } })
    );
    vi.stubGlobal('fetch', fetchMock);

    const result = await authService.signIn('someone@hospital.com', 'pw');
    // the server said receptionist; nothing client-side can promote that
    expect(result.user.role).toBe('receptionist');
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).not.toHaveProperty('role');
  });

  it('reports failure without throwing', async () => {
    vi.stubGlobal('fetch', () =>
      mockResponse(401, { error: { code: 'INVALID_CREDENTIALS', message: 'invalid credentials' } })
    );
    const result = await authService.signIn('x@y.z', 'wrong');
    expect(result.success).toBe(false);
    expect(result.error).toBeTruthy();
    expect(result.token).toBeUndefined();
  });

  it('does not accept the old hardcoded demo passwords', async () => {
    vi.stubGlobal('fetch', () =>
      mockResponse(401, { error: { message: 'invalid credentials' } })
    );
    for (const [email, password] of [
      ['admin@hospital.com', 'admin123'],
      ['doctor@hospital.com', 'doctor123'],
      ['nurse@hospital.com', 'nurse123'],
    ]) {
      const result = await authService.signIn(email, password);
      expect(result.success, `${email} still authenticates locally`).toBe(false);
    }
  });
});

describe('signUp', () => {
  it('is refused, because it would let a caller choose their own role', async () => {
    const result = await authService.signUp({ email: 'a@b.c', password: 'x', role: 'admin' });
    expect(result.success).toBe(false);
    expect(result.error).toMatch(/administrator/i);
  });

  it('makes no network request at all', async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);
    await authService.signUp({ role: 'admin' });
    expect(fetchMock).not.toHaveBeenCalled();
  });
});

describe('session', () => {
  it('signOut clears the stored session', async () => {
    apiClient.setSession(makeToken(), { id: 'u-1', role: 'doctor' });
    await authService.signOut();
    expect(authService.isAuthenticated()).toBe(false);
  });

  it('getUserProfile reports not signed in when there is no session', async () => {
    const result = await authService.getUserProfile();
    expect(result.success).toBe(false);
  });

  it('department is display-only and never used for authorization', () => {
    // a role the policy engine does not know still yields a safe label
    expect(authService.getDepartmentByRole('not-a-role')).toBe('General');
  });
});
