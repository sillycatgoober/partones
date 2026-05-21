from random import randint, uniform

from PIL import Image, ImageSequence
from ursina import Entity, Func, Sequence, Texture, Vec3, Wait, camera, color, curve, destroy, distance_xz, time

from src.Entidad import Entidad
from src.EstadoEnemigo import EstadoAtacando, EstadoAturdido, EstadoIdle, EstadoMuerto, EstadoPersiguiendo


class Enemigo(Entidad):
    frames_headshot = None
    duraciones_headshot = None

    def __init__(self, objetivo, posicion=(0, 0, 0)):
        self.escala_normal = 0.28
        self.altura_impactos = 2.2
        self.limite_piernas = 0.42
        self.inicio_cabeza = 0.90

        super().__init__(
            hpMax=150,
            velBase=2.2,
            model='assets/models/Zombie.obj',
            position=posicion,
            scale=self.escala_normal,
            collider='box',
            name='Zombie',
            unlit=True,
        )
        self.game_manager = None
        self.objetivo = objetivo
        self.rango_deteccion = 14
        self.rango_ataque = 1.7
        self.dano = 30
        self.tiempo_entre_ataques = 1.2
        self.tiempo_ultimo_ataque = 0
        self.tiempo_animacion = 0
        self.y_base = self.y
        self.esta_aturdido = False
        self.duracion_aturdimiento = 5
        self.tiempo_fin_aturdimiento = 0
        self.headshots_recibidos = 0
        self.headshots_para_aturdir = randint(1, 3)
        self.rango_empujon_jugador = 2.15
        self.velocidad_ragdoll = Vec3(0, 0, 0)
        self.estados = {
            'idle': EstadoIdle(),
            'persiguiendo': EstadoPersiguiendo(),
            'atacando': EstadoAtacando(),
            'aturdido': EstadoAturdido(),
            'muerto': EstadoMuerto()
        }
        self.estado_actual = self.estados['idle']

    def recibir_disparo(self, dano_base, punto_impacto=None):
        zona, multiplicador = self.obtener_zona_impacto(punto_impacto)
        dano_final = round(dano_base * multiplicador)
        print(f"Impacto en {zona}: x{multiplicador} -> {dano_final} de dano.")

        if zona == 'cabeza':
            self.crear_efecto_headshot(punto_impacto)

        self.recibirDano(dano_final)

        if zona == 'cabeza' and self.estaVivo:
            self.registrar_headshot()

    def obtener_zona_impacto(self, punto_impacto):
        if punto_impacto is None:
            return 'pecho', 1

        altura_relativa = max(punto_impacto.y - self.y_base, 0)
        porcentaje_altura = altura_relativa / self.altura_impactos

        if porcentaje_altura >= self.inicio_cabeza:
            return 'cabeza', 1.5

        if porcentaje_altura <= self.limite_piernas:
            return 'piernas', 0.70

        return 'pecho', 1

    def crear_efecto_headshot(self, punto_impacto):
        if punto_impacto is None:
            punto_impacto = self.position + Vec3(0, self.altura_impactos, 0)

        frames, duraciones = self.obtener_frames_headshot()
        if not frames:
            return

        direccion_camara = camera.world_position - punto_impacto
        if direccion_camara.length() > 0:
            direccion_camara = direccion_camara.normalized()
        else:
            direccion_camara = Vec3(0, 0, -1)

        efecto = Entity(
            model='quad',
            texture=frames[0],
            position=punto_impacto + direccion_camara * 0.08,
            scale=(0.55, 0.55, 0.55),
            billboard=True,
            color=color.white,
            double_sided=True
        )
        efecto.look_at(camera.world_position)
        efecto.animate_scale((0.72, 0.72, 0.72), duration=0.18, curve=curve.out_quad)

        secuencia = Sequence(loop=False, auto_destroy=True)
        for frame, duracion in zip(frames, duraciones):
            secuencia.append(Func(setattr, efecto, 'texture', frame))
            secuencia.append(Wait(duracion))

        secuencia.append(Func(destroy, efecto))
        efecto.secuencia_headshot = secuencia
        secuencia.start()

    def obtener_frames_headshot(self):
        if Enemigo.frames_headshot is not None:
            return Enemigo.frames_headshot, Enemigo.duraciones_headshot

        imagen = Image.open('assets/textures/hs.gif')
        frames = []
        duraciones = []

        for frame in ImageSequence.Iterator(imagen):
            frames.append(Texture(frame.convert('RGBA').copy()))
            duraciones.append(max(frame.info.get('duration', 60) / 1000, 0.03))

        Enemigo.frames_headshot = frames
        Enemigo.duraciones_headshot = duraciones
        return frames, duraciones

    def registrar_headshot(self):
        if self.esta_aturdido:
            return

        self.headshots_recibidos += 1
        print(f"Headshots para aturdir: {self.headshots_recibidos}/{self.headshots_para_aturdir}")

        if self.headshots_recibidos >= self.headshots_para_aturdir:
            self.aturdir()

    def aturdir(self):
        self.esta_aturdido = True
        self.tiempo_fin_aturdimiento = time.time() + self.duracion_aturdimiento
        self.headshots_recibidos = 0
        self.velocidad_ragdoll = Vec3(0, 0, 0)
        self.cambiar_estado('aturdido')
        print("Zombie aturdido. Acercate y presiona F para empujarlo.")

    def terminar_aturdimiento(self):
        self.esta_aturdido = False
        self.tiempo_fin_aturdimiento = 0
        self.headshots_recibidos = 0
        self.headshots_para_aturdir = randint(1, 3)
        self.rotation_x = 0
        self.rotation_z = 0

    def puede_recibir_empujon_ragdoll(self, jugador):
        return (
            self.estaVivo
            and self.esta_aturdido
            and distance_xz(self.position, jugador.position) <= self.rango_empujon_jugador
        )

    def recibir_empujon_ragdoll(self, jugador):
        if not self.puede_recibir_empujon_ragdoll(jugador):
            return False

        direccion = self.position - jugador.position
        direccion.y = 0
        if direccion.length() == 0:
            direccion = jugador.forward
            direccion.y = 0

        porcentaje_dano = uniform(0.25, 0.50)
        dano = round(self.hpMax * porcentaje_dano)
        self.velocidad_ragdoll = direccion.normalized() * 7
        self.tiempo_fin_aturdimiento = time.time() + 2.2
        self.rotation_x = 35
        self.rotation_z = uniform(-30, 30)
        print(f"Empujon al zombie: {round(porcentaje_dano * 100)}% -> {dano} de dano.")
        self.recibirDano(dano)
        return True

    def update(self):
        if getattr(self, 'game_manager', None) and self.game_manager.estado != self.game_manager.ESTADO_JUGANDO:
            return

        if not self.estaVivo or not self.objetivo or not self.objetivo.estaVivo:
            return

        self.tiempo_animacion += time.dt

        if self.esta_aturdido:
            if time.time() >= self.tiempo_fin_aturdimiento:
                self.terminar_aturdimiento()
            else:
                self.cambiar_estado('aturdido')
                self.estado_actual.ejecutar(self)
                return

        distancia = distance_xz(self.position, self.objetivo.position)

        if distancia <= self.rango_ataque:
            self.cambiar_estado('atacando')
        elif distancia <= self.rango_deteccion:
            self.cambiar_estado('persiguiendo')
        else:
            self.cambiar_estado('idle')

        self.estado_actual.ejecutar(self)

    def cambiar_estado(self, nombre_estado):
        nuevo_estado = self.estados[nombre_estado]
        if self.estado_actual is nuevo_estado:
            return

        self.estado_actual.salir(self)
        self.estado_actual = nuevo_estado
        self.estado_actual.entrar(self)

    def morir(self):
        super().morir()
        if self.game_manager:
            self.game_manager.enemigo_eliminado(self)
        self.cambiar_estado('muerto')
