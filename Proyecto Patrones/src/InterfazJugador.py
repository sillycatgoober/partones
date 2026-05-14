from ursina import Entity, Text, camera, color, time


class InterfazJugador(Entity):
    def __init__(self, jugador):
        super().__init__(parent=camera.ui)
        self.jugador = jugador

        self.fondo_vida = Entity(
            parent=self,
            model='quad',
            color=color.black,
            position=(-0.80, 0.45, 0),
            scale=(0.34, 0.04),
            origin=(-0.5, 0)
        )
        self.fondo_barra_vida = Entity(
            parent=self,
            model='quad',
            color=color.rgba(8, 10, 8, 255),
            position=(-0.795, 0.45, -0.01),
            scale=(0.33, 0.03),
            origin=(-0.5, 0)
        )
        self.barra_vida = Entity(
            parent=self,
            model='quad',
            color=color.rgb(0, 230, 95),
            position=(-0.795, 0.45, -0.02),
            scale=(0.33, 0.03),
            origin=(-0.5, 0)
        )
        self.texto_vida = Text(
            parent=self,
            text='',
            position=(-0.80, 0.445),
            scale=0.6,
            color=color.white,
            enabled=False
        )

        # Munición y arma: columna bajo la barra de vida (sin paneles grises abajo a la derecha)
        self.texto_arma = Text(
            parent=self,
            text='PISTOLA',
            position=(-0.795, 0.32),
            origin=(-0.5, 0),
            scale=0.62,
            color=color.rgb(200, 210, 185)
        )
        self.texto_municion = Text(
            parent=self,
            text='0 / 0',
            position=(-0.795, 0.255),
            origin=(-0.5, 0),
            scale=0.95,
            color=color.rgb(240, 215, 140)
        )
        self.barra_balas = Entity(
            parent=self,
            model='quad',
            texture='white_cube',
            color=color.rgb(255, 196, 55),
            position=(-0.795, 0.195, -0.02),
            scale=(0.28, 0.018),
            origin=(-0.5, 0)
        )
        self.icono_recargar = Entity(
            parent=self,
            model='quad',
            texture='assets/textures/recargar.png',
            position=(-0.52, 0.255, -0.12),
            scale=(0.048, 0.048),
            color=color.white,
            enabled=False
        )

        self.mira = Entity(
            parent=self,
            model='quad',
            position=(0, 0, -0.1),
            scale=(0.006, 0.006),
            color=color.rgba(225, 225, 210, 150)
        )

    def update(self):
        if not self.jugador:
            return

        porcentaje_vida = max(self.jugador.hpAct / self.jugador.hpMax, 0)
        porcentaje_balas = max(self.jugador.municion_cargador / max(self.jugador.cargador_max, 1), 0)

        self.barra_vida.scale_x = 0.33 * porcentaje_vida
        self.barra_balas.scale_x = 0.28 * porcentaje_balas
        self.texto_vida.text = f'VIDA {self.jugador.hpAct}/{self.jugador.hpMax}'

        if porcentaje_vida < 0.2:
            self.barra_vida.color = color.rgb(255, 45, 45)
        else:
            self.barra_vida.color = color.rgb(0, 230, 95)

        if porcentaje_balas > 0.35:
            self.barra_balas.color = color.rgb(255, 196, 55)
        else:
            self.barra_balas.color = color.rgb(255, 60, 45)

        if self.jugador.esta_recargando:
            self.texto_municion.text = 'RECARGANDO'
            self.texto_municion.scale = 0.72
            self.icono_recargar.enabled = True
        else:
            self.texto_municion.text = f'{self.jugador.municion_cargador} / {self.jugador.municion_reserva}'
            self.texto_municion.scale = 0.95

        if self.jugador.esta_recargando:
            pass
        elif porcentaje_balas <= 0:
            self.icono_recargar.enabled = True
        elif porcentaje_balas <= 0.25:
            self.icono_recargar.enabled = int(time.time() * 5) % 2 == 0
        else:
            self.icono_recargar.enabled = False

        self.texto_arma.text = self.jugador.nombre_arma.upper()
        self.mira.color = color.rgba(225, 225, 210, 235 if self.jugador.esta_apuntando else 145)
