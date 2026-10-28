# Especificación del MVP — Pro Futbol

## Propósito y alcance

Plataforma web multijugador de juegos futboleros. El MVP ofrece Infiltrado Futbolero y Subasta Futbolera; Torre Futbolera se muestra como “Próximamente”. No hay cuentas, base de datos ni persistencia entre ejecuciones.

## Tecnología

- Python 3.12+, Flask y Flask-SocketIO en servidor.
- HTML5, CSS3, JavaScript y Socket.IO en cliente.
- JSON local para palabras y futbolistas.

## Plataforma

Un host crea una sala con código único y elige un juego. Los demás se unen con código y nombre. Las salas admiten de 4 a 8 participantes para iniciar. Los nombres no se repiten dentro de una sala. Las desconexiones eliminan al jugador.

## Infiltrado Futbolero

El host configura al menos un impostor y menos impostores que jugadores. Los jugadores normales reciben palabra y categoría; el impostor recibe solo su rol. En cada ronda se baraja el orden, se da tiempo para pistas verbales, y luego cada participante vota una vez por otra persona. Empates activan una votación entre los empatados. Si se descubre un impostor, ganan los jugadores; de lo contrario comienza otra ronda.

## Subasta Futbolera

Entre 4 y 8 jugadores empiezan con 1000 M y deben reunir 11 titulares en formación 4-3-3. Se sortea una carta por jugador base, evitando repetir versiones del mismo futbolista. Las ofertas se validan en múltiplos de 5 M, no pueden superar el saldo y el servidor cierra la ronda por temporizador o al alcanzar dos pases consecutivos. Una adjudicación descuenta el dinero de inmediato. Los futbolistas sin oferta quedan fuera de la partida. Se garantiza una oportunidad de arquero para cada jugador antes de continuar con otras posiciones. El ganador es quien completa 11 puestos y conserva más dinero; empate se resuelve por el mayor total ofertado (menor gasto) y luego empate compartido.

## Interfaz y privacidad

La interfaz es responsive. Los eventos del servidor actualizan lobby y partida en tiempo real. La palabra secreta se envía solo al jugador no impostor. Las imágenes se sirven desde rutas locales del proyecto.

## Parámetros iniciales

- Temporizador de pista: 30 segundos.
- Temporizador de puja: 20 segundos.
- Salto personalizado de oferta: selector de 5 a 100 M.
- Sala: mínimo 4 y máximo 8 jugadores.

Estos valores se pueden ajustar durante la implementación.
