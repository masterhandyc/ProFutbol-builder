"""Servidor web y coordinación de salas para Pro Futbol."""
from __future__ import annotations

import secrets
import string
import threading
from pathlib import Path

from flask import Flask, abort, jsonify, render_template, request, session
from flask_socketio import SocketIO, emit, join_room

from juegos.infiltrado.juego import Infiltrado
from juegos.subasta.juego import Subasta

BASE = Path(__file__).resolve().parent
app = Flask(__name__)
app.config["SECRET_KEY"] = secrets.token_hex(32)
socketio = SocketIO(app, cors_allowed_origins=[])
rooms: dict[str, dict] = {}
timers: dict[str, threading.Timer] = {}
disconnect_timers: dict[tuple[str, str], threading.Timer] = {}
clue_timers: dict[str, threading.Timer] = {}
LOCK = threading.RLock()
MIN_PLAYERS, MAX_PLAYERS = 4, 8


def room_code() -> str:
    alphabet = string.ascii_uppercase + string.digits
    while True:
        code = "".join(secrets.choice(alphabet) for _ in range(5))
        if code not in rooms:
            return code


def public_room(code: str) -> dict:
    room = rooms[code]
    return {"code": code, "game": room["game"], "phase": room["phase"], "host": room["host"],
            "players": [{"name": p["name"], "is_host": p["sid"] == room["host_sid"]} for p in room["players"].values()],
            "min_players": MIN_PLAYERS, "max_players": MAX_PLAYERS}


def broadcast(code: str, event: str = "room_update", extra: dict | None = None) -> None:
    if code not in rooms:
        return
    payload = public_room(code)
    if extra:
        payload.update(extra)
    socketio.emit(event, payload, to=code)


def personal_state(code: str, sid: str) -> dict:
    room = rooms[code]
    player = room["players"].get(sid)
    state = {"room": public_room(code), "game_state": {}}
    if not player:
        return state
    if room["game"] == "infiltrado" and room.get("game_state"):
        state["game_state"] = room["game_state"].view_for(sid)
    elif room["game"] == "subasta" and room.get("game_state"):
        state["game_state"] = room["game_state"].view_for(sid)
    return state


def push_state(code: str) -> None:
    if code not in rooms:
        return
    for sid in list(rooms[code]["players"]):
        socketio.emit("game_state", personal_state(code, sid), to=sid)


def schedule_auction(code: str) -> None:
    old = timers.pop(code, None)
    if old:
        old.cancel()
    timer = threading.Timer(20, lambda: socketio.start_background_task(close_auction, code))
    timer.daemon = True
    timers[code] = timer
    timer.start()


def schedule_clue_timer(code: str) -> None:
    old = clue_timers.pop(code, None)
    if old:
        old.cancel()
    timer = threading.Timer(30, lambda: socketio.start_background_task(open_infiltrado_vote, code))
    timer.daemon = True
    clue_timers[code] = timer
    timer.start()


def open_infiltrado_vote(code: str) -> None:
    with LOCK:
        room = rooms.get(code)
        if not room or room["game"] != "infiltrado" or room["phase"] != "playing":
            return
        game: Infiltrado = room["game_state"]
        if game.phase != "clues":
            return
        game.begin_vote()
        clue_timers.pop(code, None)
    broadcast(code)
    push_state(code)


def close_auction(code: str) -> None:
    with LOCK:
        room = rooms.get(code)
        if not room or room["phase"] != "playing":
            return
        game: Subasta = room["game_state"]
        game.close_bid()
        if game.finished:
            room["phase"] = "result"
        broadcast(code)
        push_state(code)
        if room["phase"] == "playing":
            schedule_auction(code)


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/crear/<game>")
def create_page(game: str):
    if game not in ("infiltrado", "subasta"):
        abort(404)
    return render_template("crear.html", game=game)


@app.get("/unirse")
def join_page():
    return render_template("unirse.html")


@app.get("/sala/<code>")
def lobby_page(code: str):
    if code.upper() not in rooms:
        abort(404)
    return render_template("lobby.html", code=code.upper())


@app.get("/partida/<code>")
def game_page(code: str):
    code = code.upper()
    if code not in rooms:
        abort(404)
    game = rooms[code]["game"]
    template = "infiltrado/juego.html" if game == "infiltrado" else "subasta/juego.html"
    return render_template(template, code=code, game=game)


@app.get("/api/sala/<code>")
def room_api(code: str):
    code = code.upper()
    return jsonify(public_room(code)) if code in rooms else (jsonify({"error": "Sala inexistente"}), 404)


@socketio.on("create_room")
def create_room(data):
    name, game = str(data.get("name", "")).strip()[:20], data.get("game")
    if not name or game not in ("infiltrado", "subasta"):
        return emit("error_message", {"message": "Ingresá un nombre y un juego válido."})
    with LOCK:
        code = room_code()
        rooms[code] = {"game": game, "phase": "lobby", "host": name, "host_sid": request.sid,
                       "players": {request.sid: {"sid": request.sid, "name": name}}, "game_state": None}
        session["room"] = code
        join_room(code)
    emit("room_created", {"code": code, "url": f"/sala/{code}"})
    broadcast(code)


@socketio.on("join_room")
def join_game(data):
    code, name = str(data.get("code", "")).strip().upper(), str(data.get("name", "")).strip()[:20]
    with LOCK:
        room = rooms.get(code)
        if not room:
            return emit("error_message", {"message": "No encontramos esa partida."})
        if not name:
            return emit("error_message", {"message": "Ingresá tu nombre."})
        # Una navegación entre lobby y juego abre un socket nuevo. Reconectar con
        # el mismo nombre recupera el asiento y conserva el estado de la partida.
        old_sid = next((sid for sid, p in room["players"].items() if p["name"].casefold() == name.casefold()), None)
        if room["phase"] != "lobby" and old_sid is None:
            return emit("error_message", {"message": "La partida ya comenzó."})
        if old_sid and old_sid != request.sid:
            pending = disconnect_timers.pop((code, old_sid), None)
            if pending:
                pending.cancel()
            room["players"].pop(old_sid)
            room["players"][request.sid] = {"sid": request.sid, "name": name}
            if room["host_sid"] == old_sid:
                room["host_sid"] = request.sid
            if room.get("game_state"):
                room["game_state"].rekey_player(old_sid, request.sid)
        elif len(room["players"]) >= MAX_PLAYERS:
            return emit("error_message", {"message": "La sala está completa."})
        else:
            if any(p["name"].casefold() == name.casefold() for p in room["players"].values()):
                return emit("error_message", {"message": "Ese nombre ya está en uso en esta sala."})
            room["players"][request.sid] = {"sid": request.sid, "name": name}
        session["room"] = code
        join_room(code)
    emit("room_joined", {"code": code, "url": f"/sala/{code}"})
    broadcast(code)


@socketio.on("start_game")
def start_game(data):
    code = str(data.get("code", "")).upper()
    with LOCK:
        room = rooms.get(code)
        if not room or request.sid != room["host_sid"]:
            return emit("error_message", {"message": "Solo el host puede iniciar."})
        if len(room["players"]) < MIN_PLAYERS:
            return emit("error_message", {"message": "Se necesitan al menos 4 jugadores."})
        names = {sid: p["name"] for sid, p in room["players"].items()}
        if room["game"] == "infiltrado":
            impostors = int(data.get("impostors", 1))
            if not 1 <= impostors < len(names):
                return emit("error_message", {"message": "La cantidad de impostores no es válida."})
            room["game_state"] = Infiltrado(names, impostors, BASE / "data" / "infiltrado.json")
        else:
            room["game_state"] = Subasta(names, BASE / "data" / "futbolistas.json")
        room["phase"] = "playing"
        if room["game"] == "subasta":
            schedule_auction(code)
        else:
            schedule_clue_timer(code)
    broadcast(code)
    push_state(code)


@socketio.on("infiltrado_next")
def infiltrado_next(data):
    code = str(data.get("code", "")).upper()
    room = rooms.get(code)
    if not room or room["game"] != "infiltrado" or room["host_sid"] != request.sid:
        return emit("error_message", {"message": "Acción no permitida."})
    game: Infiltrado = room["game_state"]
    if game.phase == "clues":
        timer = clue_timers.pop(code, None)
        if timer:
            timer.cancel()
        game.begin_vote()
    elif game.phase in ("result_round", "tie_result"):
        game.next_round()
        schedule_clue_timer(code)
    elif game.phase == "tie_vote":
        game.resolve_tie()
    if game.finished:
        room["phase"] = "result"
    broadcast(code)
    push_state(code)


@socketio.on("infiltrado_vote")
def infiltrado_vote(data):
    code, target = str(data.get("code", "")).upper(), str(data.get("target", ""))
    room = rooms.get(code)
    if not room or room["game"] != "infiltrado":
        return emit("error_message", {"message": "Partida no disponible."})
    game: Infiltrado = room["game_state"]
    try:
        outcome = game.vote(request.sid, target)
        if outcome and game.finished:
            room["phase"] = "result"
    except ValueError as exc:
        return emit("error_message", {"message": str(exc)})
    broadcast(code)
    push_state(code)


@socketio.on("auction_bid")
def auction_bid(data):
    code = str(data.get("code", "")).upper()
    room = rooms.get(code)
    if not room or room["game"] != "subasta" or room["phase"] != "playing":
        return emit("error_message", {"message": "Subasta no disponible."})
    try:
        room["game_state"].bid(request.sid, int(data.get("amount", 0)))
    except (ValueError, TypeError) as exc:
        return emit("error_message", {"message": str(exc)})
    broadcast(code)
    push_state(code)


@socketio.on("auction_pass")
def auction_pass(data):
    code = str(data.get("code", "")).upper()
    room = rooms.get(code)
    if not room or room["game"] != "subasta" or room["phase"] != "playing":
        return emit("error_message", {"message": "Subasta no disponible."})
    try:
        game: Subasta = room["game_state"]
        game.pass_turn(request.sid)
        if game.bid_round_closed:
            close_auction(code)
        else:
            broadcast(code)
            push_state(code)
    except ValueError as exc:
        emit("error_message", {"message": str(exc)})


@socketio.on("disconnect")
def disconnect():
    code = session.get("room")
    if not code or code not in rooms:
        return
    with LOCK:
        room = rooms[code]
        removed = room["players"].get(request.sid)
        if not removed:
            return
        # Give a page navigation a moment to reconnect its socket. A real
        # disconnect is eliminated after the short grace period.
        disconnected_sid = request.sid
        pending = threading.Timer(5, lambda: socketio.start_background_task(expire_player, code, disconnected_sid))
        pending.daemon = True
        disconnect_timers[(code, request.sid)] = pending
        pending.start()


def expire_player(code: str, sid: str) -> None:
    with LOCK:
        disconnect_timers.pop((code, sid), None)
        room = rooms.get(code)
        if not room or sid not in room["players"]:
            return
        room["players"].pop(sid, None)
        if room.get("game_state"):
            room["game_state"].remove_player(sid)
        if not room["players"]:
            auction_timer = timers.pop(code, None)
            if auction_timer:
                auction_timer.cancel()
            clue_timer = clue_timers.pop(code, None)
            if clue_timer:
                clue_timer.cancel()
            rooms.pop(code, None)
            return
    broadcast(code)
    push_state(code)


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, use_reloader=False)
