"""Estado de una partida de Infiltrado."""
import json
import random
from pathlib import Path


class Infiltrado:
    def __init__(self, players: dict[str, str], impostor_count: int, data_path: Path):
        if len(players) < 4 or not 1 <= impostor_count < len(players):
            raise ValueError("Cantidad de jugadores o impostores inválida.")
        self.players = dict(players)
        self.impostor_count = impostor_count
        self.data = json.loads(data_path.read_text(encoding="utf-8"))["categorias"]
        self.round = 1
        self.phase = "clues"
        self.finished = False
        self.word = ""
        self.category = ""
        self.impostors: set[str] = set()
        self.order: list[str] = []
        self.votes: dict[str, str] = {}
        self.tie_candidates: list[str] = []
        self.last_result: dict | None = None
        self._new_round()

    def _new_round(self):
        item = random.choice(self.data)
        self.category, self.word = item["nombre"], random.choice(item["palabras"])
        self.impostors = set(random.sample(list(self.players), self.impostor_count))
        self.order = random.sample(list(self.players), len(self.players))
        self.votes = {}
        self.tie_candidates = []
        self.last_result = None
        self.phase = "clues"

    def begin_vote(self):
        if self.phase != "clues":
            return
        self.phase, self.votes = "vote", {}

    def vote(self, voter: str, target: str):
        if self.phase not in ("vote", "tie_vote"):
            raise ValueError("La votación no está abierta.")
        choices = self.tie_candidates if self.phase == "tie_vote" else list(self.players)
        if voter not in self.players or target not in choices or voter == target:
            raise ValueError("Voto inválido: no podés votarte ni elegir esa persona.")
        if voter in self.votes:
            raise ValueError("Ya emitiste tu voto.")
        self.votes[voter] = target
        if len(self.votes) == len(self.players):
            return self._count_votes()
        return None

    def _count_votes(self):
        counts = {p: 0 for p in self.players}
        for target in self.votes.values():
            counts[target] = counts.get(target, 0) + 1
        high = max(counts.values())
        top = [p for p, count in counts.items() if count == high]
        if len(top) > 1:
            self.tie_candidates = top
            self.votes = {}
            self.phase = "tie_vote"
            return {"tie": [self.players[p] for p in top]}
        return self._resolve_elimination(top[0])

    def resolve_tie(self):
        if self.phase != "tie_result":
            return
        self._new_round()

    def _resolve_elimination(self, selected: str):
        caught = selected in self.impostors
        self.last_result = {"selected": self.players.get(selected, "Jugador"), "caught": caught,
                            "impostors": [self.players[p] for p in self.impostors],
                            "winner": "Jugadores" if caught else "Impostor(es)"}
        if caught:
            self.phase, self.finished = "result", True
        else:
            self.phase = "result_round"
        return self.last_result

    def resolve_manual(self):
        if self.phase == "tie_vote" and len(self.votes) == len(self.players):
            return self._count_votes()

    def next_round(self):
        if self.phase in ("result_round", "tie_result"):
            self.round += 1
            self._new_round()

    def remove_player(self, sid: str):
        self.players.pop(sid, None)
        self.impostors.discard(sid)
        self.order = [p for p in self.order if p != sid]
        self.votes.pop(sid, None)
        if self.phase in ("vote", "tie_vote") and len(self.votes) >= len(self.players) and self.players:
            self._count_votes()

    def rekey_player(self, old: str, new: str):
        if old not in self.players:
            return
        self.players[new] = self.players.pop(old)
        if old in self.impostors:
            self.impostors.remove(old)
            self.impostors.add(new)
        self.order = [new if p == old else p for p in self.order]
        self.votes = {(new if voter == old else voter): (new if target == old else target)
                      for voter, target in self.votes.items()}
        self.tie_candidates = [new if p == old else p for p in self.tie_candidates]

    def view_for(self, sid: str):
        return {"phase": self.phase, "round": self.round, "category": self.category,
                "secret": None if sid in self.impostors else self.word,
                "is_impostor": sid in self.impostors, "order": [self.players[p] for p in self.order if p in self.players],
                "players": [{"id": p, "name": n} for p, n in self.players.items()],
                "voted": sid in self.votes, "tie_candidates": [{"id": p, "name": self.players[p]} for p in self.tie_candidates if p in self.players],
                "vote_count": len(self.votes), "player_count": len(self.players), "result": self.last_result,
                "finished": self.finished}
