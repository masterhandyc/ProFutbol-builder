# Pro Futbol

Plataforma web responsive de minijuegos futboleros multijugador. Incluye Infiltrado Futbolero y Subasta Futbolera; Torre Futbolera queda visible como próxima incorporación.

## Requisitos

- Python 3.12 o superior
- pip

## Instalación y ejecución

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Abrí `http://127.0.0.1:5000`. Para jugar desde otros dispositivos de la misma red, ejecutá `python app.py` y usá la dirección IP local del equipo anfitrión. No expongas el servidor a Internet sin agregar configuración de producción y controles de seguridad.

## Estructura

- `app.py`: aplicación Flask, salas y eventos Socket.IO.
- `juegos/infiltrado/`: lógica de rondas, roles privados y votación.
- `juegos/subasta/`: lógica de cartas, presupuesto, pujas y plantillas.
- `data/`: fuentes JSON editables.
- `templates/` y `static/`: interfaz del navegador.
- `spec.md`: especificación funcional de referencia.
- `docs/`: arquitectura, flujos y documentación académica.

## Reglas implementadas y decisiones configurables

Las salas se guardan en memoria y se pierden al reiniciar el servidor. Un jugador desconectado se elimina. El límite es de 8 jugadores; cada juego requiere al menos 4 para iniciar. Los temporizadores están en `app.py` (pistas 30 s; pujas 20 s). En Subasta, dos pases consecutivos cierran la puja y adjudican la carta a la oferta vigente; sin ofertas queda sin vender. El ganador final es quien complete 11 titulares y conserve más presupuesto. Los importes de JSON están expresados en millones (M), pese a que la especificación conceptual alterna entre M y valores absolutos.

Las imágenes de ejemplo se resuelven como rutas locales bajo `static/img/futbolistas/`; agregá los archivos allí. Si falta una imagen, la tarjeta muestra una alternativa visual.

## Nota sobre uso

Este repositorio es una base funcional de MVP y no incluye cuentas, persistencia, chat, ni garantías de operación de producción. Para una presentación académica, consultá `docs/`.
