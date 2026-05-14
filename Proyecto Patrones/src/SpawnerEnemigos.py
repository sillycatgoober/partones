from random import uniform

from ursina import Vec3, invoke

from src.Enemigo import Enemigo


class SpawnerEnemigos:
    def __init__(self, jugador, game_manager, puntos_spawn=None):
        self.jugador = jugador
        self.game_manager = game_manager
        self.game_manager.spawner = self
        self.oleada_actual = 0
        self.zombies_base = 3
        self.incremento_por_oleada = 2
        self.oleada_pendiente = False
        self.radio_variacion_spawn = 1.6
        self.puntos_spawn = puntos_spawn or [
            Vec3(6, 0, 8),
            Vec3(-9, 0, 11),
            Vec3(13, 0, -7),
            Vec3(-14, 0, -9),
            Vec3(2, 0, 18)
        ]

    def iniciar_oleada(self):
        self.oleada_pendiente = False

        if self.game_manager.estado != self.game_manager.ESTADO_JUGANDO:
            return

        self.oleada_actual += 1
        cantidad_zombies = self.zombies_base + ((self.oleada_actual - 1) * self.incremento_por_oleada)
        self.game_manager.actualizar_oleada(self.oleada_actual, cantidad_zombies)

        for indice in range(cantidad_zombies):
            punto_spawn = self.puntos_spawn[indice % len(self.puntos_spawn)]
            self.crear_zombie(self.obtener_posicion_spawn(punto_spawn))

    def programar_siguiente_oleada(self, delay=2.5):
        if self.oleada_pendiente:
            return

        self.oleada_pendiente = True
        invoke(self.iniciar_oleada, delay=delay)

    def reiniciar(self):
        self.oleada_actual = 0
        self.oleada_pendiente = False
        self.iniciar_oleada()

    def obtener_posicion_spawn(self, punto_spawn):
        return Vec3(
            punto_spawn.x + uniform(-self.radio_variacion_spawn, self.radio_variacion_spawn),
            punto_spawn.y,
            punto_spawn.z + uniform(-self.radio_variacion_spawn, self.radio_variacion_spawn)
        )

    def crear_zombie(self, punto_spawn):
        zombie = Enemigo(objetivo=self.jugador, posicion=punto_spawn)
        self.game_manager.registrar_enemigo(zombie)
        return zombie
