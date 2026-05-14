from ursina import Entity, Vec3, color, time

from src.red.sesion_red import SesionRed, TIPO_ESTADO_JUGADOR


class SincronizadorRed(Entity):
    """Envía la pose del jugador local y aplica la del remoto sobre un proxy en escena."""

    def __init__(self, jugador, sesion: SesionRed, proxy_jugador_remoto: Entity, intervalo_envio: float = 1 / 15):
        super().__init__()
        self.jugador = jugador
        self.sesion = sesion
        self.proxy = proxy_jugador_remoto
        self.intervalo_envio = intervalo_envio
        self._acumulador = 0.0
        self.proxy.enabled = False

    def update(self):
        if not self.sesion or self.sesion.modo == 'offline':
            return

        for mensaje in self.sesion.drenar_mensajes():
            if mensaje.get('tipo') != TIPO_ESTADO_JUGADOR:
                continue
            self.proxy.enabled = True
            self.proxy.position = Vec3(
                float(mensaje.get('x', 0)),
                float(mensaje.get('y', 0)),
                float(mensaje.get('z', 0)),
            )
            self.proxy.rotation_y = float(mensaje.get('ry', 0))

        if not self.jugador or not self.jugador.estaVivo:
            return

        self._acumulador += time.dt
        if self._acumulador < self.intervalo_envio:
            return
        self._acumulador = 0.0

        if not self.sesion.conectado():
            return

        self.sesion.enviar_estado_jugador(
            self.jugador.x,
            self.jugador.y,
            self.jugador.z,
            self.jugador.rotation_y,
            self.jugador.camera_pivot.rotation_x,
        )

    def on_destroy(self):
        if self.sesion:
            self.sesion.cerrar()
