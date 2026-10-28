"""Motor de subasta futbolera en memoria."""
import json
import random
from pathlib import Path


class Subasta:
    def __init__(self, players: dict[str, str], data_path: Path):
        self.names = dict(players)
        self.players = {sid: {"money": 1000, "team": [], "passed": False} for sid in players}
        groups = json.loads(data_path.read_text(encoding="utf-8"))
        self.available = []
        for base in groups:
            version = random.choice(base["versiones"])
            self.available.append(dict(version, jugador=base["jugador"], base_id=base["id"]))
        random.shuffle(self.available)
        self.current = None
        self.high_bid = 0
        self.high_bidder = None
        self.passes = 0
        self.bid_round_closed = False
        self.finished = False
        self.auction_number = 0
        self._draw()

    def _draw(self):
        if all(len(p["team"]) >= 11 for p in self.players.values()):
            self.finished = True
            return
        need_keeper = any(not any(c["posicion"] == "ARQ" for c in p["team"]) for p in self.players.values())
        idx = next((i for i, c in enumerate(self.available) if c["posicion"] == "ARQ"), None) if need_keeper else None
        if idx is None:
            idx = 0 if self.available else None
        self.current = self.available.pop(idx) if idx is not None else None
        self.high_bid, self.high_bidder, self.passes = 0, None, 0
        for p in self.players.values():
            p["passed"] = False
        self.bid_round_closed = self.current is None
        self.auction_number += 1
        if self.current is None:
            self.finished = True

    def bid(self, sid: str, amount: int):
        if self.finished or sid not in self.players or self.bid_round_closed or self.players[sid]["passed"]:
            raise ValueError("No podés ofertar en este momento.")
        if amount < self.current["precio_inicial"] or amount % 5:
            raise ValueError("La oferta debe ser múltiplo de 5 M y alcanzar el precio inicial.")
        if amount <= self.high_bid:
            raise ValueError("La oferta debe superar la oferta actual.")
        if amount > self.players[sid]["money"]:
            raise ValueError("No tenés saldo suficiente.")
        self.high_bid, self.high_bidder = amount, sid
        self.passes = 0
        for p in self.players.values():
            p["passed"] = False

    def pass_turn(self, sid: str):
        if sid not in self.players or self.bid_round_closed or self.players[sid]["passed"]:
            raise ValueError("No podés pasar en este momento.")
        self.players[sid]["passed"] = True
        self.passes += 1
        if self.passes >= 2:
            self.bid_round_closed = True

    def close_bid(self):
        if self.finished:
            return
        if self.high_bidder:
            player = self.players[self.high_bidder]
            player["money"] -= self.high_bid
            player["team"].append(dict(self.current, precio_pagado=self.high_bid))
        self._draw()

    def remove_player(self, sid: str):
        self.players.pop(sid, None)
        self.names.pop(sid, None)
        if not self.players or all(len(p["team"]) >= 11 for p in self.players.values()):
            self.finished = True

    def rekey_player(self, old: str, new: str):
        if old not in self.players:
            return
        self.players[new] = self.players.pop(old)
        self.names[new] = self.names.pop(old)
        if self.high_bidder == old:
            self.high_bidder = new

    def view_for(self, sid: str):
        ranking = sorted(self.players, key=lambda p: (len(self.players[p]["team"]) == 11, self.players[p]["money"], -sum(c["precio_pagado"] for c in self.players[p]["team"])), reverse=True)
        return {"phase": "result" if self.finished else "auction", "current": self.current,
                "high_bid": self.high_bid, "high_bidder": self.names.get(self.high_bidder), "passes": self.passes,
                "money": self.players.get(sid, {}).get("money", 0), "team": self.players.get(sid, {}).get("team", []),
                "players": [{"id": p, "name": self.names[p], "money": v["money"], "squad_size": len(v["team"]), "passed": v["passed"]} for p, v in self.players.items()],
                "auction_number": self.auction_number, "finished": self.finished,
                "winner": self.names.get(ranking[0]) if self.finished and ranking else None,
                "teams": {self.names[p]: self.players[p]["team"] for p in self.players} if self.finished else None,
                "can_bid": sid in self.players and not self.players[sid]["passed"]}
