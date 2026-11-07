/**
 * Synchronisation hors-ligne Mi-bika.
 * Appeler syncOffline(token) au démarrage de l'app web/mobile.
 */
async function syncOffline(apiBase, token) {
  const res = await fetch(`${apiBase}/api/sync/offline/`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error('Sync offline échouée');
  const data = await res.json();
  localStorage.setItem('mibika_offline', JSON.stringify(data));
  return data;
}

function getOfflineCache() {
  const raw = localStorage.getItem('mibika_offline');
  return raw ? JSON.parse(raw) : null;
}

if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/static/sw.js').catch(() => {});
}
