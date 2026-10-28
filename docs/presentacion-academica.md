# Guía para la presentación académica

## Problema y propuesta

Pro Futbol reúne minijuegos futboleros en una plataforma web de acceso simple para grupos. El alcance inicial prioriza una experiencia multijugador con salas por código, privacidad de roles y reglas validadas en servidor.

## Objetivos

- Crear y unirse a salas sin cuentas.
- Sincronizar cambios de juego en tiempo real.
- Implementar un juego de deducción y una subasta de plantillas.
- Mantener módulos separados y datos extensibles mediante JSON.

## Tecnologías y motivo

Python y Flask simplifican la construcción del servidor y la entrega web. Flask-SocketIO proporciona comunicación de baja latencia para lobby, votos y pujas. HTML, CSS y JavaScript permiten uso desde computadora y celular. JSON evita incorporar una base de datos al MVP.

## Alcance

Incluye dos juegos funcionales, creación y unión mediante código, estados privados, votaciones, pujas, presupuestos y resultado. Torre Futbolera aparece en el menú como futura ampliación. Persistencia, cuentas y ranking quedan fuera del MVP.

## Evidencias recomendadas

Para la entrega académica, ejecutar el proyecto y añadir capturas propias del menú, lobby, rol privado, votación, carta de subasta y resultado. Las capturas no se inventan: deben tomarse de una instancia en funcionamiento.

## Conclusión

La arquitectura demuestra cómo separar la coordinación multijugador de las reglas específicas de cada juego y permite incorporar otros minijuegos sin rehacer la plataforma.
