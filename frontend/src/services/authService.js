/**
 * Authentication against the server.
 *
 * Replaces the previous mock, which seeded demo accounts into localStorage,
 * minted `mock_token_${id}_${Date.now()}`, and recovered the role by splitting
 * that string. A role the browser writes is not an authorization signal, so the
 * backend policy engine could not be built on it.
 *
 * Identity now comes from POST /auth/login and the role is whatever the server
 * put in the signed token. Nothing here can change it.
 *
 * The public method names are unchanged so existing callers keep working.
 */

import apiClient, { AuthRequiredError } from './apiClient';

class AuthService {
  /**
   * Sign in. Returns { success, user, token } or { success: false, error }.
   *
   * `email` is passed through as the username: the backend accepts either,
   * because the seeded rows use both.
   */
  async signIn(email, password) {
    try {
      const body = await apiClient.login(email, password);
      return {
        success: true,
        user: {
          id: body.user?.id,
          email,
          role: body.user?.role,
          department: this.getDepartmentByRole(body.user?.role),
        },
        token: body.token,
      };
    } catch (error) {
      // The server deliberately returns one message for every failure mode, so
      // a wrong password and an unknown account are indistinguishable here too.
      return {
        success: false,
        error: error instanceof AuthRequiredError ? error.message : 'Unable to sign in',
      };
    }
  }

  /**
   * Self-service registration is not available.
   *
   * The previous implementation let the caller choose their own `role`, which
   * under server-side authorization would be a privilege-escalation path: pick
   * "admin" at signup and the policy engine would honour it. Accounts are
   * created administratively, and the role is set on the user record.
   *
   * See backend-python/scripts/reset_dev_users.py for development accounts.
   */
  async signUp() {
    return {
      success: false,
      error:
        'Account creation is handled by an administrator. Please contact your system administrator for access.',
    };
  }

  /** The signed-in user, from the stored session. */
  async getUserProfile() {
    const user = apiClient.getUser();
    if (!user || !apiClient.isAuthenticated()) {
      return { success: false, error: 'Not signed in' };
    }
    return {
      success: true,
      user: {
        id: user.id,
        role: user.role,
        department: this.getDepartmentByRole(user.role),
      },
    };
  }

  async signOut() {
    apiClient.logout();
    return { success: true };
  }

  isAuthenticated() {
    return apiClient.isAuthenticated();
  }

  getCurrentUser() {
    return apiClient.getUser();
  }

  getCurrentRole() {
    return apiClient.getUser()?.role || null;
  }

  /** Display-only helper. Never used for authorization. */
  getDepartmentByRole(role) {
    const departments = {
      admin: 'Administration',
      doctor: 'Medical',
      nurse: 'Nursing',
      manager: 'Operations',
      receptionist: 'Front Desk',
    };
    return departments[role] || 'General';
  }

  async checkBackendHealth() {
    try {
      const response = await fetch(`${apiClient.baseURL}/health`);
      return { success: response.ok, status: response.status };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }
}

export default new AuthService();
