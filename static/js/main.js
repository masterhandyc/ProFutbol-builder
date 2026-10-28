(() => {
  const config = window.PRO_CONFIG || {};
  let socket;
  const toast = (message) => {
    const box = document.getElementById('toast');
    if (!box) return;
    box.textContent = message;
    box.classList.add('show');
    clearTimeout(window.toastTimer);
    window.toastTimer = setTimeout(() => box.classList.remove('show'), 3500);
  };
  window.proToast = toast;
  if (!window.io) return;
  socket = window.proSocket = io();
  socket.on('error_message', (data) => toast(data.message || 'Ocurrió un error.'));
  if (config.page === 'create') {
    document.getElementById('create')?.addEventListener('click', () => {
      const name = document.getElementById('name').value.trim();
      if (!name) return toast('Ingresá tu nombre.');
      socket.emit('create_room', {name, game: config.game});
    });
    socket.on('room_created', (data) => { location.href = data.url; });
  }
  if (config.page === 'join') {
    document.getElementById('join')?.addEventListener('click', () => {
      socket.emit('join_room', {code: document.getElementById('code').value.trim(), name: document.getElementById('name').value.trim()});
    });
    socket.on('room_joined', (data) => { location.href = data.url; });
    document.getElementById('code')?.addEventListener('input', (e) => { e.target.value = e.target.value.toUpperCase(); });
  }
  if (config.page === 'lobby') {
    const render = (room) => {
      document.getElementById('game-title').textContent = room.game === 'infiltrado' ? '🕵️ Infiltrado Futbolero' : '⚽ Subasta Futbolera';
      const list = document.getElementById('players');
      list.innerHTML = room.players.map((p) => `<div class="player"><span class="dot"></span>${escapeHtml(p.name)} ${p.is_host ? '<span class="badge">HOST</span>' : ''}</div>`).join('');
      const host = room.players.some((p) => p.is_host && socket.id === window.hostSid);
      const own = room.players.find((p) => p.is_host);
      if (own) window.hostSid = socket.id; // host identity is established on this connection below
      const isHost = window.isRoomHost === true;
      document.getElementById('host-controls').hidden = !isHost;
      document.getElementById('impostors').hidden = room.game !== 'infiltrado';
      document.getElementById('lobby-hint').textContent = `${room.players.length} de ${room.max_players} jugadores · se necesitan ${room.min_players} para empezar.`;
      if (room.phase !== 'lobby') location.href = `/partida/${config.code}`;
      window.currentRoom = room;
    };
    socket.on('connect', () => socket.emit('join_room', {code: config.code, name: sessionStorage.getItem('proName') || ''}));
    socket.on('room_update', render);
    socket.on('room_joined', () => { window.isRoomHost = false; });
    socket.on('room_created', () => { window.isRoomHost = true; });
    socket.on('room_update', (room) => {
      // The creator is recognized by the name saved during creation.
      const storedName = sessionStorage.getItem('proName');
      window.isRoomHost = Boolean(storedName && room.players.some((p) => p.is_host && p.name === storedName));
      render(room);
    });
    document.getElementById('start').addEventListener('click', () => socket.emit('start_game', {code: config.code, impostors: Number(document.getElementById('impostors').value)}));
  }
  function escapeHtml(s) { const el = document.createElement('span'); el.textContent = s; return el.innerHTML; }
  // Keep names between the form redirect and lobby websocket reconnect.
  document.getElementById('create')?.addEventListener('click', () => sessionStorage.setItem('proName', document.getElementById('name').value.trim()));
  document.getElementById('join')?.addEventListener('click', () => sessionStorage.setItem('proName', document.getElementById('name').value.trim()));
})();
