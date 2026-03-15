import { useCallback, useEffect, useState } from 'react';

function Settings({ apiUrl, authToken, user }) {
  const [apiKeys, setApiKeys] = useState([]);
  const [newKeyName, setNewKeyName] = useState('');
  const [createdKey, setCreatedKey] = useState(null);
  const [notifPrefs, setNotifPrefs] = useState({
    email_on_critical: true,
    email_on_run_complete: false,
    in_app_notifications: true,
  });
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState('');

  const headers = authToken
    ? { Authorization: `Bearer ${authToken}`, 'Content-Type': 'application/json' }
    : { 'Content-Type': 'application/json' };

  const loadApiKeys = useCallback(() => {
    if (!authToken) return;
    fetch(`${apiUrl}/api/v1/auth/api-keys`, { headers })
      .then(res => res.ok ? res.json() : null)
      .then(data => { if (data) setApiKeys(data.api_keys || []); })
      .catch(() => {});
  }, [apiUrl, authToken]);

  useEffect(() => { loadApiKeys(); }, [loadApiKeys]);

  const createApiKey = async (e) => {
    e.preventDefault();
    if (!newKeyName.trim()) return;
    try {
      const res = await fetch(`${apiUrl}/api/v1/auth/api-keys`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ name: newKeyName }),
      });
      const data = await res.json();
      if (res.ok) {
        setCreatedKey(data.key);
        setNewKeyName('');
        loadApiKeys();
      }
    } catch {
      // ignore
    }
  };

  const saveProfile = async () => {
    if (!authToken) return;
    setSaving(true);
    setSaveMsg('');
    try {
      const res = await fetch(`${apiUrl}/api/v1/auth/me`, {
        method: 'PUT',
        headers,
        body: JSON.stringify({ notification_preferences: notifPrefs }),
      });
      if (res.ok) setSaveMsg('Settings saved');
      else setSaveMsg('Failed to save');
    } catch {
      setSaveMsg('Failed to save');
    } finally {
      setSaving(false);
      setTimeout(() => setSaveMsg(''), 3000);
    }
  };

  if (!user) {
    return (
      <div className='settings'>
        <div className='settings-section'>
          <h2>Settings</h2>
          <p className='settings-hint'>Sign in to manage your account settings, API keys, and notification preferences.</p>
        </div>
      </div>
    );
  }

  return (
    <div className='settings'>
      <h2>Settings</h2>

      {/* Account Info */}
      <div className='settings-section'>
        <h3>Account</h3>
        <div className='settings-card'>
          <div className='settings-row'>
            <span className='settings-label'>Email</span>
            <span className='settings-value'>{user.email}</span>
          </div>
          <div className='settings-row'>
            <span className='settings-label'>Role</span>
            <span className='settings-value'>{user.role || 'member'}</span>
          </div>
          <div className='settings-row'>
            <span className='settings-label'>Plan</span>
            <span className='settings-value badge-info' style={{ display: 'inline-block' }}>{(user.plan || 'free').toUpperCase()}</span>
          </div>
        </div>
      </div>

      {/* Notification Preferences */}
      <div className='settings-section'>
        <h3>Notification Preferences</h3>
        <div className='settings-card'>
          <label className='toggle-label'>
            <input type='checkbox' checked={notifPrefs.in_app_notifications}
              onChange={e => setNotifPrefs(p => ({ ...p, in_app_notifications: e.target.checked }))} />
            In-app notifications
          </label>
          <label className='toggle-label'>
            <input type='checkbox' checked={notifPrefs.email_on_critical}
              onChange={e => setNotifPrefs(p => ({ ...p, email_on_critical: e.target.checked }))} />
            Email on critical issues
          </label>
          <label className='toggle-label'>
            <input type='checkbox' checked={notifPrefs.email_on_run_complete}
              onChange={e => setNotifPrefs(p => ({ ...p, email_on_run_complete: e.target.checked }))} />
            Email when browser runs complete
          </label>
          <div style={{ marginTop: '1rem', display: 'flex', gap: '1rem', alignItems: 'center' }}>
            <button type='button' className='btn btn-primary' onClick={saveProfile} disabled={saving}>
              {saving ? 'Saving...' : 'Save Preferences'}
            </button>
            {saveMsg && <span className='save-message'>{saveMsg}</span>}
          </div>
        </div>
      </div>

      {/* API Keys */}
      <div className='settings-section'>
        <h3>API Keys</h3>
        <p className='settings-hint'>Use API keys to authenticate with the OmniAudit API programmatically.</p>

        {createdKey && (
          <div className='api-key-created'>
            <strong>New API key created. Copy it now — it won't be shown again:</strong>
            <code className='api-key-value'>{createdKey}</code>
            <button type='button' className='btn btn-small' onClick={() => {
              navigator.clipboard.writeText(createdKey).catch(() => {});
              setCreatedKey(null);
            }}>Copy &amp; Dismiss</button>
          </div>
        )}

        <form className='api-key-form' onSubmit={createApiKey}>
          <input type='text' placeholder='Key name (e.g., CI/CD)' value={newKeyName}
            onChange={e => setNewKeyName(e.target.value)} required />
          <button type='submit' className='btn btn-primary btn-small'>Create Key</button>
        </form>

        {apiKeys.length > 0 ? (
          <div className='api-keys-list'>
            {apiKeys.map(k => (
              <div key={k.id} className='api-key-item'>
                <span className='api-key-name'>{k.name}</span>
                <span className='api-key-prefix'>{k.key_prefix}...</span>
                <span className='api-key-date'>{k.created_at ? new Date(k.created_at).toLocaleDateString() : ''}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className='empty-text'>No API keys yet</p>
        )}
      </div>
    </div>
  );
}

export default Settings;
