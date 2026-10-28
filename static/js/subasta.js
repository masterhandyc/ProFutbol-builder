(() => {
  const cfg = window.PRO_CONFIG;
  const socket = window.proSocket;
  const app = document.getElementById('auction-app');
  if (!socket || !app) return;
  socket.on('connect', () => socket.emit('join_room', {code: cfg.code, name: sessionStorage.getItem('proName') || ''}));
  socket.on('game_state', ({game_state:g}) => {
    if (!g || !g.phase) return;
    if (g.finished) {
      app.innerHTML = `<p class="eyebrow">RESULTADO FINAL</p><h1>🏆 ${esc(g.winner || 'Partida terminada')}</h1><div class="team-grid">${Object.entries(g.teams || {}).map(([name, team]) => `<article class="card"><h2>${esc(name)} · ${team.length}/11</h2>${team.map((p) => `<p>${esc(p.jugador)} — ${esc(p.posicion)}</p>`).join('')}</article>`).join('')}</div><a class="button" href="/">Volver al menú</a>`;
      return;
    }
    const card = g.current;
    if (!card) return;
    app.innerHTML = `<p class="eyebrow">SUBASTA FUTBOLERA · CARTA ${g.auction_number}</p><h1>¡A subastar!</h1><article class="football-card"><div class="card-image"><img src="/static/img/futbolistas/${encodeURIComponent(card.imagen)}" alt="Imagen de ${esc(card.jugador)}" onerror="this.style.display='none';this.parentElement.textContent='⚽'"></div><h2>${esc(card.jugador)}</h2><p>${esc(String(card.anio))} · ${esc(card.club)}</p><span class="badge">${esc(card.tipo)}</span><p class="price">Base ${card.precio_inicial} M</p></article><div class="bid-box"><p>Oferta actual: <strong>${g.high_bid ? `${g.high_bid} M · ${esc(g.high_bidder)}` : 'Sin ofertas'}</strong></p><p>Tu saldo: ${g.money} M · Equipo: ${g.team.length}/11 · Pases: ${g.passes}/2</p><div class="bid-controls"><button class="button" data-bid="5">+5 M</button><label>Salto <select id="jump">${[10,20,50,100].map(n=>`<option value="${n}">+${n} M</option>`).join('')}</select></label><button class="button secondary" id="custom">Ofertar salto</button><button class="button secondary" id="pass">Pasar</button></div></div><div class="players-strip">${g.players.map(p=>`<span>${esc(p.name)} · ${p.squad_size}/11 ${p.passed?'· pasó':''}</span>`).join('')}</div><section><h2>Mi equipo</h2><div class="team-grid">${g.team.map(p=>`<span class="player">${esc(p.posicion)} · ${esc(p.jugador)} (${p.precio_pagado} M)</span>`).join('') || '<p class="hint">Todavía no tenés futbolistas.</p>'}</div></section>`;
    app.querySelector('[data-bid]')?.addEventListener('click', () => bid(g, 5));
    app.querySelector('#custom')?.addEventListener('click', () => bid(g, Number(app.querySelector('#jump').value)));
    app.querySelector('#pass')?.addEventListener('click', () => socket.emit('auction_pass', {code:cfg.code}));
  });
  function bid(g, jump) { const amount = Math.max(g.current.precio_inicial, g.high_bid ? g.high_bid + jump : g.current.precio_inicial); socket.emit('auction_bid', {code:cfg.code, amount}); }
  function esc(s='') { const d=document.createElement('div'); d.textContent=s; return d.innerHTML; }
})();
