from datetime import datetime
from pathlib import Path

from ursina import Entity, Text, Vec3, camera, color, destroy, time

from src.fabrica_pickups import FabricaLootZombie


class GameManager(Entity):
    ESTADO_JUGANDO = 'jugando'
    ESTADO_GAME_OVER = 'game_over'
    ESTADO_VICTORIA = 'victoria'

    def __init__(self, jugador):
        super().__init__(parent=camera.ui)
        self.jugador = jugador
        self.jugador.game_manager = self
        self.estado = self.ESTADO_JUGANDO
        self.puntaje = 0
        self.bajas = 0
        self.oleada_actual = 0
        self.enemigos_oleada_actual = 0
        self.enemigos = []
        self.puntos_spawn_enemigos = []
        self.spawner = None
        self.puntuacion_guardada = False
        self.archivo_puntuaciones = Path('puntuaciones.txt')
        self.posicion_inicial_jugador = Vec3(jugador.position)
        self.fabrica_loot = FabricaLootZombie(jugador)

        self.texto_puntaje = Text(
            parent=self,
            text='PUNTOS 0  |  BAJAS 0',
            position=(-0.22, 0.46),
            origin=(0, 0),
            scale=0.75,
            color=color.rgb(235, 230, 210)
        )
        self.texto_oleada = Text(
            parent=self,
            text='OLEADA 0',
            position=(0.36, 0.46),
            origin=(0, 0),
            scale=0.75,
            color=color.rgb(255, 210, 120)
        )
        self.fondo_estado = Entity(
            parent=self,
            model='quad',
            color=color.rgba(0, 0, 0, 175),
            scale=(1.25, 0.42),
            position=(0, 0, 0.05),
            enabled=False
        )
        self.texto_estado = Text(
            parent=self,
            text='',
            position=(0, 0.06),
            origin=(0, 0),
            scale=1.8,
            color=color.white,
            enabled=False
        )
        self.texto_accion = Text(
            parent=self,
            text='ENTER PARA REINICIAR',
            position=(0, -0.08),
            origin=(0, 0),
            scale=0.85,
            color=color.rgb(215, 205, 170),
            enabled=False
        )
        self.fondo_empujar = Entity(
            parent=self,
            model='quad',
            color=color.rgba(10, 10, 10, 190),
            position=(0, -0.26, 0.04),
            scale=(0.32, 0.085),
            enabled=False
        )
        self.texto_empujar = Text(
            parent=self,
            text='F  EMPUJAR',
            position=(0, -0.275),
            origin=(0, 0),
            scale=1.05,
            color=color.rgb(255, 235, 145),
            enabled=False
        )

    def update(self):
        self.actualizar_aviso_empujar()

    def input(self, key):
        if key == 'enter' and self.estado != self.ESTADO_JUGANDO:
            self.reiniciar_partida()

    def registrar_enemigo(self, enemigo):
        if enemigo in self.enemigos:
            return

        enemigo.game_manager = self
        self.enemigos.append(enemigo)

        if not self.spawner:
            punto_spawn = Vec3(enemigo.position)
            if punto_spawn not in self.puntos_spawn_enemigos:
                self.puntos_spawn_enemigos.append(punto_spawn)

    def enemigo_eliminado(self, enemigo):
        if self.estado != self.ESTADO_JUGANDO:
            return

        if enemigo in self.enemigos:
            self.enemigos.remove(enemigo)

        posicion_drop = Vec3(enemigo.x, getattr(enemigo, 'y_base', enemigo.y), enemigo.z)
        self.fabrica_loot.generar_drops(posicion_drop)

        self.bajas += 1
        self.puntaje += 100
        self.actualizar_puntaje()

        if not self.enemigos:
            if self.spawner:
                self.spawner.programar_siguiente_oleada()
            else:
                self.mostrar_victoria()

    def jugador_eliminado(self):
        if self.estado != self.ESTADO_JUGANDO:
            return

        self.estado = self.ESTADO_GAME_OVER
        self.jugador.speed = 0
        self.guardar_puntuacion()
        self.mostrar_estado('GAME OVER', color.rgb(255, 65, 55))

    def mostrar_victoria(self):
        self.estado = self.ESTADO_VICTORIA
        self.jugador.speed = 0
        self.mostrar_estado('VICTORIA', color.rgb(95, 230, 120))

    def mostrar_estado(self, texto, color_texto):
        self.fondo_estado.enabled = True
        self.texto_estado.enabled = True
        self.texto_accion.enabled = True
        self.texto_estado.text = texto
        self.texto_estado.color = color_texto

    def ocultar_estado(self):
        self.fondo_estado.enabled = False
        self.texto_estado.enabled = False
        self.texto_accion.enabled = False

    def actualizar_aviso_empujar(self):
        puede_empujar = (
            self.estado == self.ESTADO_JUGANDO
            and self.jugador
            and self.jugador.estaVivo
            and self.hay_zombie_aturdido_cerca()
        )

        self.fondo_empujar.enabled = puede_empujar
        self.texto_empujar.enabled = puede_empujar

        if puede_empujar:
            pulso = 0.95 + (time.time() % 0.8) * 0.12
            self.texto_empujar.scale = pulso

    def hay_zombie_aturdido_cerca(self):
        for enemigo in self.enemigos:
            if (
                hasattr(enemigo, 'puede_recibir_empujon_ragdoll')
                and enemigo.puede_recibir_empujon_ragdoll(self.jugador)
            ):
                return True

        return False

    def actualizar_puntaje(self):
        self.texto_puntaje.text = f'PUNTOS {self.puntaje}  |  BAJAS {self.bajas}'

    def actualizar_oleada(self, numero_oleada, cantidad_zombies):
        self.oleada_actual = numero_oleada
        self.enemigos_oleada_actual = cantidad_zombies
        self.texto_oleada.text = f'OLEADA {numero_oleada}  |  ZOMBIES {cantidad_zombies}'

    def guardar_puntuacion(self):
        if self.puntuacion_guardada:
            return

        self.puntuacion_guardada = True
        fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        linea = (
            f'{fecha} | puntos={self.puntaje} | bajas={self.bajas} '
            f'| oleada={self.oleada_actual}\n'
        )
        with self.archivo_puntuaciones.open('a', encoding='utf-8') as archivo:
            archivo.write(linea)

    def reiniciar_partida(self):
        self.estado = self.ESTADO_JUGANDO
        self.puntaje = 0
        self.bajas = 0
        self.oleada_actual = 0
        self.enemigos_oleada_actual = 0
        self.puntuacion_guardada = False
        self.actualizar_puntaje()
        self.actualizar_oleada(0, 0)
        self.ocultar_estado()
        self.reiniciar_jugador()
        self.reiniciar_enemigos()

    def reiniciar_jugador(self):
        self.jugador.estaVivo = True
        self.jugador.hpAct = self.jugador.hpMax
        self.jugador.position = Vec3(self.posicion_inicial_jugador)
        self.jugador.speed = self.jugador.velBase
        self.jugador.esta_recargando = False

        if self.jugador.arma:
            self.jugador.configurar_arma(self.jugador.arma)

    def reiniciar_enemigos(self):
        for enemigo in tuple(self.enemigos):
            destroy(enemigo)

        self.enemigos.clear()

        if self.spawner:
            self.puntos_spawn_enemigos = []
            self.spawner.reiniciar()
            return

        puntos_spawn = self.puntos_spawn_enemigos or [Vec3(6, 0, 8)]
        self.puntos_spawn_enemigos = []

        from src.Enemigo import Enemigo
        for punto_spawn in puntos_spawn:
            self.registrar_enemigo(Enemigo(objetivo=self.jugador, posicion=punto_spawn))
