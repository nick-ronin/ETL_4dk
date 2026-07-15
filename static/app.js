async function fetchStatus() {
    try {
        // 1. Деплой-инфо
        const depRes = await fetch('/deployment');
        const dep = await depRes.json();
        if (!dep.error) {
            document.getElementById('branch').textContent = dep.branch || '—';
            document.getElementById('commit').textContent = dep.commit || '—';
            document.getElementById('message').textContent = dep.message || '—';
            document.getElementById('author').textContent = dep.author || '—';
            document.getElementById('deployed').textContent = dep.deployed_at || '—';
        }

        // 2. Версия из OpenAPI (опционально, можно просто зашить)
        try {
            const openapiRes = await fetch('/openapi.json');
            const openapi = await openapiRes.json();
            document.getElementById('version').textContent = openapi.info?.version || '—';
        } catch {
            document.getElementById('version').textContent = '1.0.0';
        }

        // 3. Health
        const healthRes = await fetch('/health');
        const health = await healthRes.json();
        const healthEl = document.getElementById('health-status');
        if (health.status === 'ok') {
            healthEl.textContent = 'OK';
            healthEl.className = 'badge ok';
        } else {
            healthEl.textContent = 'FAIL';
            healthEl.className = 'badge error';
        }

        // 4. Ready
        const readyRes = await fetch('/ready');
        const ready = await readyRes.json();
        const readyEl = document.getElementById('ready-status');
        if (ready.status === 'ready') {
            readyEl.textContent = 'READY';
            readyEl.className = 'badge ok';
        } else {
            readyEl.textContent = 'NOT READY';
            readyEl.className = 'badge error';
        }

        // Общий статус
        const statusEl = document.getElementById('status-text');
        if (health.status === 'ok' && ready.status === 'ready') {
            statusEl.textContent = 'Online';
            document.getElementById('status').className = 'status';
        } else {
            statusEl.textContent = 'Degraded';
            document.getElementById('status').className = 'status offline';
        }

        document.getElementById('check-time').textContent = new Date().toLocaleTimeString();

    } catch (err) {
        document.getElementById('status-text').textContent = 'Offline';
        document.getElementById('status').className = 'status offline';
        console.error(err);
    }
}

// Запускаем сразу и обновляем каждые 30 секунд
fetchStatus();
setInterval(fetchStatus, 30000);
