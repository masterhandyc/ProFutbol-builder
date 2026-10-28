(() => {
  const cfg = window.PRO_CONFIG;
  const socket = window.proSocket;
  const app = document.getElementById('infiltrado-app');
  if (!socket || !app) return;
  socket.on('connect', () => socket.emit('join_room', {code: cfg.code, name: sessionStorage.getItem('proName') || ''}));
  socket.on('game_state', ({room, game_state: g}) => {
    if (!g || !g.phase) return;
    const host = room.players.some((p) => p.is_host && p.name === sessionStorage.getItem('proName'));
    let html = `<p class="eyebrow">INFILTRADO FUTBOLERO · RONDA ${g.round}</p>`;
    if (g.finished || g.phase === 'result') {
      html += `<h1>🏆 ${g.result?.winner || 'Partida finalizada'}</h1><p>Impostor(es): <strong>${(g.result?.impostors || []).join(', ')}</strong></p><a class="button" href="/">Volver al menú</a>`;
    } else if (g.phase === 'clues') {
      html += `<div class="secret ${g.is_impostor ? 'secret-danger' : ''}"><p>${g.is_impostor ? 'TU ROL' : `CATEGORÍA · ${esc(g.category)}`}</p><h2>${g.is_impostor ? 'IMPOSTOR' : esc(g.secret)}</h2></div><h2>Orden de pistas</h2><ol class="ordered">${g.order.map((n) => `<li>${esc(n)}</li>`).join('')}</ol>${host ? '<button class="button" data-action="vote">Terminar pistas y votar</button>' : '<p class="hint">Esperá a que el host abra la votación.</p>'}`;
    } else if (g.phase === 'vote' || g.phase === 'tie_vote') {
      const choices = g.phase === 'tie_vote' ? g.tie_candidates : g.players;
      html += `<h1>${g.phase === 'tie_vote' ? 'Votación de desempate' : '¿Quién es el impostor?'}</h1><p>${g.vote_count} de ${g.player_count} votos emitidos</p><div class="choice-grid">${choices.filter((p) => p.id !== socket.id).map((p) => `<button class="choice" data-vote="${esc(p.id)}" ${g.voted ? 'disabled' : ''}>${esc(p.name)}</button>`).join('')}</div>`;
    } else {
      html += `<h1>${g.result?.caught ? '¡Impostor descubierto!' : 'El impostor sigue oculto'}</h1><p>Votaron a ${esc(g.result?.selected || '')}. ${g.result?.caught ? 'Ganan los jugadores.' : 'Comienza una nueva ronda.'}</p>${host ? '<button class="button" data-action="next">Siguiente ronda</button>' : '<p class="hint">Esperando al host…</p>'}`;
    }
    app.innerHTML = html;
    app.querySelector('[data-action="vote"]')?.addEventListener('click', () => socket.emit('infiltrado_next', {code: cfg.code}));
    app.querySelector('[data-action="next"]')?.addEventListener('click', () => socket.emit('infiltrado_next', {code: cfg.code}));
    app.querySelectorAll('[data-vote]').forEach((b) => b.addEventListener('click', () => socket.emit('infiltrado_vote', {code: cfg.code, target: b.dataset.vote})));
  });
  function esc(s='') { const d=document.createElement('div'); d.textContent=s; return d.innerHTML; }
})();
