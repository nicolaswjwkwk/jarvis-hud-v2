(function(global){
  'use strict';

  const BACKEND_BASE = (global.location && global.location.hostname === 'localhost')
    ? 'http://localhost:8080'
    : (global.JARVIS_BACKEND_URL || 'http://localhost:8080');

  const state = {
    sessionToken: localStorage.getItem('jarvis_session_token') || '',
    sessionUser: JSON.parse(localStorage.getItem('jarvis_session_user') || 'null'),
    lastChatId: null
  };

  function api(path, options = {}) {
    const headers = Object.assign({ 'Content-Type': 'application/json' }, options.headers || {});
    if (state.sessionToken) {
      headers['Authorization'] = 'Bearer ' + state.sessionToken;
    }
    return fetch(BACKEND_BASE + path, Object.assign({
      mode: 'cors',
      credentials: 'omit',
      headers
    }, options));
  }

  async function health() {
    try {
      const response = await fetch(BACKEND_BASE + '/health', { method: 'GET' });
      return await response.json();
    } catch (error) {
      return { ok: false, error: String(error) };
    }
  }

  async function googleStart() {
    const response = await api('/auth/google/start', { method: 'POST' });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Google auth unavailable');
    if (data.url) {
      global.location.href = data.url;
    }
    return data;
  }

  async function phoneRequest(phone) {
    const response = await api('/auth/phone/request', {
      method: 'POST',
      body: JSON.stringify({ phone })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'OTP request failed');
    return data;
  }

  async function phoneVerify(phone, code) {
    const response = await api('/auth/phone/verify', {
      method: 'POST',
      body: JSON.stringify({ phone, code })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'OTP validation failed');
    state.sessionToken = data.token || '';
    localStorage.setItem('jarvis_session_token', state.sessionToken);
    return data;
  }

  async function sessionInfo() {
    if (!state.sessionToken) return null;
    const response = await api('/api/session?token=' + encodeURIComponent(state.sessionToken), { method: 'GET' });
    if (!response.ok) return null;
    const data = await response.json();
    state.sessionUser = data.session || null;
    localStorage.setItem('jarvis_session_user', JSON.stringify(state.sessionUser));
    return data.session;
  }

  async function sendChat(messages, system) {
    const payload = {
      messages: messages.map((item) => ({ role: item.role, content: item.content })),
      system: system || 'Você é JARVIS, assistente pessoal e superagente.'
    };
    const response = await api('/api/chat', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error((data && data.detail) || 'Chat request failed');
    }
    return data;
  }

  async function sendWhatsApp(to, text) {
    const response = await api('/api/whatsapp/send', {
      method: 'POST',
      body: JSON.stringify({ to, text })
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error((data && data.detail) || 'WhatsApp send failed');
    }
    return data;
  }

  async function authStatus() {
    const response = await fetch(BACKEND_BASE + '/auth/status', { method: 'GET' });
    if (!response.ok) return { ok: false };
    return response.json();
  }

  global.JARVIS_Backend = {
    BACKEND_BASE,
    health,
    googleStart,
    phoneRequest,
    phoneVerify,
    sessionInfo,
    sendChat,
    sendWhatsApp,
    authStatus,
    getSessionToken: () => state.sessionToken,
    logout: () => {
      state.sessionToken = '';
      state.sessionUser = null;
      localStorage.removeItem('jarvis_session_token');
      localStorage.removeItem('jarvis_session_user');
    }
  };

  global.dispatchEvent(new CustomEvent('jarvis:backend-ready', { detail: { base: BACKEND_BASE } }));
})(window);
