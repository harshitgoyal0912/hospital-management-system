/**
 * Tool-call surface.
 *
 * A non-executed outcome must never reach a caller shaped like a result. It
 * throws, because callers already wrap tool calls in try/catch and an exception
 * cannot be rendered as "done".
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';

import apiClient, { Outcome } from '../apiClient';
import DirectHttpMCPClient, { ToolNotExecutedError } from '../directHttpMcpClient';

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

// The module exports the class, not a singleton.
let mcpClient;

beforeEach(() => {
  sessionStorage.clear();
  vi.restoreAllMocks();
  apiClient.setSession(makeToken(), { id: 'u-1', role: 'doctor' });
  mcpClient = new DirectHttpMCPClient();
});

describe('callTool', () => {
  it('returns the legacy shape for an executed action', async () => {
    vi.stubGlobal('fetch', () =>
      mockResponse(200, { success: true, executed: true, result: { beds: [] }, run_id: 'r1' })
    );
    const out = await mcpClient.callTool('list_beds', {});
    expect(out.executed).toBe(true);
    expect(JSON.parse(out.result.content[0].text)).toEqual({ beds: [] });
  });

  it('throws rather than returning when approval is required', async () => {
    vi.stubGlobal('fetch', () =>
      mockResponse(202, {
        executed: false,
        status: 'REQUIRE_HUMAN_APPROVAL',
        tool: 'delete_patient',
        reason: 'irreversible',
      })
    );
    await expect(mcpClient.callTool('delete_patient', { patient_id: 'P1' })).rejects.toThrow(
      ToolNotExecutedError
    );
  });

  it('marks approval-required as awaiting a human', async () => {
    vi.stubGlobal('fetch', () =>
      mockResponse(202, { executed: false, status: 'REQUIRE_HUMAN_APPROVAL', tool: 'delete_patient' })
    );
    try {
      await mcpClient.callTool('delete_patient', { patient_id: 'P1' });
      throw new Error('should have thrown');
    } catch (error) {
      expect(error).toBeInstanceOf(ToolNotExecutedError);
      expect(error.awaitingHuman).toBe(true);
      expect(error.executed).toBe(false);
      expect(error.userMessage).toMatch(/needs approval/i);
    }
  });

  it('throws on a policy denial with a permission message', async () => {
    vi.stubGlobal('fetch', () =>
      mockResponse(403, { executed: false, error: { code: 'POLICY_DENIED', message: 'not permitted' } })
    );
    try {
      await mcpClient.callTool('delete_patient', { patient_id: 'P1' });
      throw new Error('should have thrown');
    } catch (error) {
      expect(error.outcome).toBe(Outcome.DENIED);
      expect(error.awaitingHuman).toBe(false);
      expect(error.userMessage).toMatch(/permission/i);
    }
  });

  it('never returns a result object for any non-executed outcome', async () => {
    for (const [status, body] of [
      [202, { status: 'REQUIRE_HUMAN_APPROVAL' }],
      [403, { error: {} }],
      [400, { error: {} }],
      [404, { error: {} }],
      [502, { error: {} }],
    ]) {
      vi.stubGlobal('fetch', () => mockResponse(status, { executed: false, ...body }));
      await expect(
        mcpClient.callTool('delete_patient', { patient_id: 'P1' })
      ).rejects.toBeInstanceOf(ToolNotExecutedError);
    }
  });
});

describe('callToolDetailed', () => {
  it('returns the outcome without throwing, for UI that renders states', async () => {
    vi.stubGlobal('fetch', () =>
      mockResponse(202, { executed: false, status: 'REQUIRE_CONFIRMATION', tool: 'discharge_bed' })
    );
    const out = await mcpClient.callToolDetailed('discharge_bed', { bed_id: 'B1' });
    expect(out.outcome).toBe(Outcome.AWAITING_CONFIRMATION);
    expect(out.executed).toBe(false);
  });
});
