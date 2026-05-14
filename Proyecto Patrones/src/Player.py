from math import sin
from random import uniform
from time import sleep

from ursina import Vec3, camera, clamp, color, curve, distance_xz, held_keys, raycast, time, destroy, Entity
from ursina.prefabs.first_person_controller import FirstPersonController

# 1 = arma a la derecha de la pantalla (espacio de cámara), -1 = a la izquierda
LADO_ARMA_EN_PANTALLA = 1

CONFIG_ARMAS = {
    'Pistola': {
        'cargador_max': 12,
        'municion_inicial': 36,
        'dano': 20,
        'tiempo_recarga': 1.2,
        'tiempo_entre_disparos': 0.28,
        'dispersion_apuntando': 0,
        'dispersion_quieto': 0.18,
        'dispersion_caminando': 0.65,
        'retroceso': 2
    },
    'Escopeta': {
        'cargador_max': 6,
        'municion_inicial': 24,
        'dano': 45,
        'tiempo_recarga': 2.4,
        'tiempo_entre_disparos': 0.95,
        'dispersion_apuntando': 0,
        'dispersion_quieto': 0.28,
        'dispersion_caminando': 0.85,
        'retroceso': 4
    },
    'Rifle': {
        'cargador_max': 30,
        'municion_inicial': 90,
        'dano': 15,
        'tiempo_recarga': 1.8,
        'tiempo_entre_disparos': 0.09,
        'dispersion_apuntando': 0,
        'dispersion_quieto': 0.12,
        'dispersion_caminando': 0.42,
        'retroceso': 2
    },
    'Revolver': {
        'cargador_max': 6,
        'municion_inicial': 24,
        'dano': 34,
        'tiempo_recarga': 1.6,
        'tiempo_entre_disparos': 0.52,
        'dispersion_apuntando': 0,
        'dispersion_quieto': 0.16,
        'dispersion_caminando': 0.55,
        'retroceso': 3
    },
    'Rifle Pesado': {
        'cargador_max': 60,
        'municion_inicial': 120,
        'dano': 18,
        'tiempo_recarga': 2.1,
        'tiempo_entre_disparos': 0.11,
        'dispersion_apuntando': 0,
        'dispersion_quieto': 0.14,
        'dispersion_caminando': 0.48,
        'retroceso': 4
    }
}

CONFIG_VISUAL_ARMAS = {
    'Pistola': {
        'scale': 10,
        'rotation': Vec3(0, 90, 3),
        'normal': Vec3(0.56, -0.46, 0.92),
        'apuntando': Vec3(0.14, -0.28, 0.78)
    },
    'Revolver': {
        'scale': 4,
        'rotation': Vec3(0, 90, 4),
        'normal': Vec3(0.50, -0.50, 0.98),
        'apuntando': Vec3(0.12, -0.30, 0.80)
    },
    'Escopeta': {
        'scale': 10,
        'rotation': Vec3(0, 90, 2),
        'normal': Vec3(0.62, -0.58, 1.08),
        'apuntando': Vec3(0.16, -0.36, 0.94)
    },
    'Rifle': {
        'scale': 10,
        'rotation': Vec3(0, 90, 2),
        'normal': Vec3(0.60, -0.55, 1.04),
        'apuntando': Vec3(0.15, -0.32, 0.90)
    },
    'Rifle Pesado': {
        'scale': 10,
        'rotation': Vec3(0, 90, 2),
        'normal': Vec3(0.64, -0.58, 1.12),
        'apuntando': Vec3(0.17, -0.36, 0.96)
    }
}


class Player(FirstPersonController):
    def __init__(self, arma=None):
        super().__init__(
            height=2,
            model='assets/models/Suit.gltf',
            collider='box'
        )
        self.model = None
        self.cursor.enabled = False
        self.hpMax = 100
        self.hpAct = self.hpMax
        self.velBase = 7
        self.speed = self.velBase
        self.estaVivo = True
        self.game_manager = None
        self.sesion_red = None

        self.arma = arma
        self.altura_normal = 2
        self.altura_agachado = 1.2
        self.vel_agachado = self.velBase * 0.45
        self.vel_apuntando = self.velBase * 0.35
        self.esta_agachado = False
        self.esta_apuntando = False
        self.nombre_arma = 'Pistola'
        self.cargador_max = 10
        self.municion_cargador = 10
        self.municion_reserva = 40
        self.dano_arma = 20
        self.tiempo_recarga = 1.2
        self.esta_recargando = False
        self.tiempo_fin_recarga = 0
        self.dispersion_apuntando = 0
        self.dispersion_quieto = 0.18
        self.dispersion_caminando = 0.65
        self.tiempo_movimiento = 0
        self.offset_camara_animacion = Vec3(0, 0, 0)
        self.offset_arma_animacion = Vec3(0, 0, 0)
        self.offset_retroceso_arma = Vec3(0, 0, 0)
        self.offset_golpe_camara = Vec3(0, 0, 0)
        self.arma_recoil_pitch = 0
        self.tiempo_entre_disparos = 0.28
        self.intensidad_retroceso = 2
        self.tiempo_proximo_disparo = 0
        self.velocidad_empujon = Vec3(0, 0, 0)
        self.posicion_arma_normal = Vec3(0.48, -0.5, 0.9)
        self.posicion_arma_apuntando = Vec3(0.08, -0.32, 0.75)
        self.rotacion_arma_base = Vec3(0, 90, 0)

        if self.arma:
            self.equipar_arma(self.arma)

    def update(self):
        if not self.estaVivo:
            return

        self.cursor.enabled = False
        self.actualizar_recarga()
        self.actualizar_apuntado()
        self.actualizar_animacion_movimiento()
        self.actualizar_postura()
        self.actualizar_empujon()
        super().update()

    def input(self, key):
        if not self.estaVivo:
            return

        super().input(key)

        if key == 'left mouse down' and self.arma:
            self.disparar()

        if key == 'r':
            self.recargar()

        if key == 'f':
            self.intentar_empujar_zombie_aturdido()

    def actualizar_postura(self):
        debe_agacharse = held_keys['left control'] or held_keys['control']
        nueva_altura = self.altura_agachado if debe_agacharse else self.altura_normal
        nueva_velocidad = self.velBase

        if debe_agacharse:
            nueva_velocidad = min(nueva_velocidad, self.vel_agachado)

        if self.esta_apuntando:
            nueva_velocidad = min(nueva_velocidad, self.vel_apuntando)

        self.esta_agachado = debe_agacharse
        self.height = nueva_altura
        self.speed = nueva_velocidad
        altura_camara = nueva_altura + self.offset_camara_animacion.y
        self.camera_pivot.y += (altura_camara - self.camera_pivot.y) * min(time.dt * 12, 1)

        if self.arma:
            if self.esta_apuntando:
                posicion_objetivo = Vec3(self.posicion_arma_apuntando)
            else:
                posicion_objetivo = Vec3(self.posicion_arma_normal)

            if debe_agacharse:
                posicion_objetivo.y += 0.14

            posicion_objetivo += self.offset_arma_animacion
            posicion_objetivo += self.offset_retroceso_arma
            self.arma.position += (posicion_objetivo - self.arma.position) * min(time.dt * 14, 1)
            rotacion_x_objetivo = self.rotacion_arma_base.x + self.arma_recoil_pitch
            self.arma.rotation_x += (rotacion_x_objetivo - self.arma.rotation_x) * min(time.dt * 12, 1)
            self.arma.rotation_y = self.rotacion_arma_base.y
            self.arma.rotation_z = self.rotacion_arma_base.z

    def actualizar_apuntado(self):
        self.esta_apuntando = held_keys['right mouse']
        fov_objetivo = 70 if self.esta_apuntando else 90
        camera.fov += (fov_objetivo - camera.fov) * min(time.dt * 10, 1)

    def actualizar_animacion_movimiento(self):
        esta_caminando = (
            held_keys['w'] or held_keys['a'] or held_keys['s'] or held_keys['d']
        )

        if esta_caminando and self.grounded:
            velocidad_animacion = 4 if self.esta_agachado else 7
            intensidad = 0.35 if self.esta_apuntando else 1
            self.tiempo_movimiento += time.dt * velocidad_animacion

            balanceo_vertical = sin(self.tiempo_movimiento * 2) * 0.035 * intensidad
            balanceo_lateral = sin(self.tiempo_movimiento) * 0.025 * intensidad
            self.offset_camara_animacion = Vec3(0, balanceo_vertical, 0)
            self.offset_arma_animacion = Vec3(balanceo_lateral, abs(balanceo_vertical) * -0.7, 0)
        else:
            respiracion = sin(time.time() * 1.8) * 0.008
            self.offset_camara_animacion += (Vec3(0, respiracion, 0) - self.offset_camara_animacion) * min(time.dt * 8, 1)
            self.offset_arma_animacion += (Vec3(0, respiracion * 1.5, 0) - self.offset_arma_animacion) * min(time.dt * 8, 1)

        self.offset_retroceso_arma += (Vec3(0, 0, 0) - self.offset_retroceso_arma) * min(time.dt * 16, 1)
        self.arma_recoil_pitch += (0 - self.arma_recoil_pitch) * min(time.dt * 9, 1)
        self.offset_golpe_camara += (Vec3(0, 0, 0) - self.offset_golpe_camara) * min(time.dt * 10, 1)
        camera.rotation_z += (self.offset_golpe_camara.z - camera.rotation_z) * min(time.dt * 12, 1)

    def equipar_arma(self, arma):
        self.arma = arma
        self.configurar_arma(arma)
        self.configurar_visual_arma()
        self.arma.parent = camera
        self.arma.position = Vec3(self.posicion_arma_normal)
        self.arma.rotation = Vec3(self.rotacion_arma_base)

    def configurar_arma(self, arma):
        ruta_modelo = str(getattr(arma, 'ruta_modelo', getattr(arma, 'model', ''))).lower()

        if 'assault rifle 2' in ruta_modelo:
            self.nombre_arma = 'Rifle Pesado'
        elif 'shotgun' in ruta_modelo:
            self.nombre_arma = 'Escopeta'
        elif 'revolver' in ruta_modelo:
            self.nombre_arma = 'Revolver'
        elif 'rifle' in ruta_modelo:
            self.nombre_arma = 'Rifle'
        else:
            self.nombre_arma = 'Pistola'

        config = CONFIG_ARMAS[self.nombre_arma]
        self.cargador_max = config['cargador_max']
        self.municion_cargador = config['cargador_max']
        self.municion_reserva = config['municion_inicial']
        self.dano_arma = config['dano']
        self.tiempo_recarga = config['tiempo_recarga']
        self.dispersion_apuntando = config['dispersion_apuntando']
        self.dispersion_quieto = config['dispersion_quieto']
        self.dispersion_caminando = config['dispersion_caminando']
        self.tiempo_entre_disparos = config['tiempo_entre_disparos']
        self.intensidad_retroceso = config['retroceso']

    def configurar_visual_arma(self):
        visual = CONFIG_VISUAL_ARMAS[self.nombre_arma]
        self.arma.scale = visual['scale']
        self.rotacion_arma_base = Vec3(visual['rotation'])
        lado = LADO_ARMA_EN_PANTALLA
        self.posicion_arma_normal = Vec3(visual['normal'].x * lado, visual['normal'].y, visual['normal'].z)
        self.posicion_arma_apuntando = Vec3(visual['apuntando'].x * lado, visual['apuntando'].y, visual['apuntando'].z)

    def disparar(self):
        if self.esta_recargando:
            print("No puedes disparar mientras recargas.")
            return

        if time.time() < self.tiempo_proximo_disparo:
            return

        if self.municion_cargador <= 0:
            print("Sin balas en el cargador. Presiona R para recargar.")
            return

        self.tiempo_proximo_disparo = time.time() + self.tiempo_entre_disparos
        self.municion_cargador -= 1
        self.arma.blink(color.orange, duration=0.08)

        factor_arma = self.intensidad_retroceso / 3
        mitad = 0.55 if self.esta_apuntando else 1
        retroceso_camara = (0.35 if self.esta_apuntando else 0.85) * factor_arma * mitad
        self.camera_pivot.rotation_x = clamp(
            self.camera_pivot.rotation_x + retroceso_camara,
            -90,
            90
        )
        self.rotation_y += uniform(-0.35, 0.35) * factor_arma * mitad

        retroceso_pos = 0.06 if self.esta_apuntando else 0.11
        self.offset_retroceso_arma = Vec3(
            uniform(-0.02, 0.02) * factor_arma,
            retroceso_pos * 0.45 * factor_arma,
            -retroceso_pos * factor_arma
        )
        self.arma_recoil_pitch -= (4 if self.esta_apuntando else 9) * factor_arma

        direccion_disparo = self.obtener_direccion_disparo()

        impacto = raycast(
            camera.world_position,
            direccion_disparo,
            distance=40,
            ignore=[self, self.arma],
            debug=False
        )

        if impacto.hit:
            if hasattr(impacto.entity, 'recibir_disparo'):
                impacto.entity.recibir_disparo(self.dano_arma, impacto.world_point)
            elif hasattr(impacto.entity, 'recibirDano'):
                impacto.entity.recibirDano(self.dano_arma)

        bala = Entity(
            model='sphere',
            color=color.yellow,
            scale=0.04,
            position=camera.world_position + direccion_disparo * 0.8,
            collider=None
        )

        bala.animate_position(bala.position + direccion_disparo * 35, duration=0.45, curve=curve.linear)
        destroy(bala, delay=0.5)

    def recargar(self):
        if self.esta_recargando or self.municion_cargador == self.cargador_max or self.municion_reserva <= 0:
            return

        self.esta_recargando = True
        self.tiempo_fin_recarga = time.time() + self.tiempo_recarga
        self.offset_retroceso_arma = Vec3(-0.05, -0.08, -0.12)
        print(f"Recargando {self.nombre_arma}...")

    def actualizar_recarga(self):
        if not self.esta_recargando or time.time() < self.tiempo_fin_recarga:
            return

        self.esta_recargando = False
        balas_necesarias = self.cargador_max - self.municion_cargador
        balas_a_recargar = min(balas_necesarias, self.municion_reserva)
        self.municion_cargador += balas_a_recargar
        self.municion_reserva -= balas_a_recargar
        print(f"Recargaste {balas_a_recargar} balas.")

    def obtener_direccion_disparo(self):
        esta_caminando = (
            held_keys['w'] or held_keys['a'] or held_keys['s'] or held_keys['d']
        )

        if self.esta_apuntando:
            dispersion = self.dispersion_apuntando
        elif esta_caminando:
            dispersion = self.dispersion_caminando
        else:
            dispersion = self.dispersion_quieto

        desviacion_x = uniform(-dispersion, dispersion)
        desviacion_y = uniform(-dispersion, dispersion)
        return (camera.forward + camera.right * desviacion_x + camera.up * desviacion_y).normalized()

    def recibir_empujon(self, direccion, fuerza=4.5):
        if not self.estaVivo:
            return

        direccion.y = 0
        if direccion.length() == 0:
            return

        self.velocidad_empujon = direccion.normalized() * fuerza

    def actualizar_empujon(self):
        if self.velocidad_empujon.length() <= 0.05:
            self.velocidad_empujon = Vec3(0, 0, 0)
            return

        self.position += self.velocidad_empujon * time.dt
        self.velocidad_empujon += (Vec3(0, 0, 0) - self.velocidad_empujon) * min(time.dt * 8, 1)

    def intentar_empujar_zombie_aturdido(self):
        if not self.game_manager:
            return

        zombie_cercano = None
        distancia_cercana = 999

        for enemigo in self.game_manager.enemigos:
            if not hasattr(enemigo, 'puede_recibir_empujon_ragdoll'):
                continue

            if not enemigo.puede_recibir_empujon_ragdoll(self):
                continue

            distancia = distance_xz(self.position, enemigo.position)
            if distancia < distancia_cercana:
                distancia_cercana = distancia
                zombie_cercano = enemigo

        if zombie_cercano:
            zombie_cercano.recibir_empujon_ragdoll(self)

    def aplicar_curacion(self, cantidad: int):
        if not self.estaVivo or cantidad <= 0:
            return
        self.hpAct = min(self.hpAct + cantidad, self.hpMax)

    def aplicar_municion_reserva(self, cantidad: int):
        if not self.estaVivo or cantidad <= 0:
            return
        self.municion_reserva += cantidad

    def recibirDano(self, cantidad):
        if not self.estaVivo:
            return

        self.hpAct -= cantidad
        print(f"Vida del jugador: {self.hpAct}")
        self.offset_golpe_camara = Vec3(0, 0, uniform(-4, 4))

        if self.hpAct <= 0:
            self.morir()

    def morir(self):
        self.estaVivo = False
        self.hpAct = 0
        print("El jugador ha muerto.")
        if self.game_manager:
            self.game_manager.jugador_eliminado()
