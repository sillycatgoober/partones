from math import sin

from ursina import Vec3, color, curve, destroy, time


class EstadoEnemigo:
    nombre = 'base'

    def entrar(self, enemigo):
        pass

    def ejecutar(self, enemigo):
        pass

    def salir(self, enemigo):
        pass


class EstadoIdle(EstadoEnemigo):
    nombre = 'idle'

    def ejecutar(self, enemigo):
        enemigo.y += (enemigo.y_base - enemigo.y) * min(time.dt * 8, 1)
        enemigo.rotation_z = sin(enemigo.tiempo_animacion * 2) * 2


class EstadoPersiguiendo(EstadoEnemigo):
    nombre = 'persiguiendo'

    def ejecutar(self, enemigo):
        direccion = enemigo.objetivo.position - enemigo.position
        direccion.y = 0

        if direccion.length() > 0:
            direccion = direccion.normalized()
            enemigo.position += direccion * enemigo.velBase * time.dt
            enemigo.look_at(Vec3(enemigo.objetivo.x, enemigo.y, enemigo.objetivo.z))

        paso = sin(enemigo.tiempo_animacion * 10)
        enemigo.y = enemigo.y_base + abs(paso) * 0.08
        enemigo.rotation_z = paso * 4


class EstadoAtacando(EstadoEnemigo):
    nombre = 'atacando'

    def ejecutar(self, enemigo):
        if getattr(enemigo, 'esta_aturdido', False):
            return

        enemigo.look_at(Vec3(enemigo.objetivo.x, enemigo.y, enemigo.objetivo.z))
        enemigo.y += (enemigo.y_base - enemigo.y) * min(time.dt * 10, 1)
        enemigo.rotation_z *= max(1 - time.dt * 8, 0)

        if time.time() - enemigo.tiempo_ultimo_ataque < enemigo.tiempo_entre_ataques:
            return

        enemigo.tiempo_ultimo_ataque = time.time()
        enemigo.objetivo.recibirDano(enemigo.dano)
        if hasattr(enemigo.objetivo, 'recibir_empujon'):
            direccion_empujon = enemigo.objetivo.position - enemigo.position
            enemigo.objetivo.recibir_empujon(direccion_empujon)

        enemigo.blink(color.red, duration=0.12)
        enemigo.animate_rotation_x(12, duration=0.08, curve=curve.out_quad)
        enemigo.animate_rotation_x(0, duration=0.16, delay=0.08, curve=curve.in_out_quad)


class EstadoAturdido(EstadoEnemigo):
    nombre = 'aturdido'

    def entrar(self, enemigo):
        enemigo.rotation_x = 18
        enemigo.rotation_z = 8
        enemigo.blink(color.azure, duration=0.18)

    def ejecutar(self, enemigo):
        if enemigo.velocidad_ragdoll.length() > 0.05:
            enemigo.position += enemigo.velocidad_ragdoll * time.dt
            enemigo.velocidad_ragdoll += (Vec3(0, 0, 0) - enemigo.velocidad_ragdoll) * min(time.dt * 3.5, 1)
            enemigo.rotation_z += enemigo.velocidad_ragdoll.length() * time.dt * 4
        else:
            enemigo.y += (enemigo.y_base - enemigo.y) * min(time.dt * 6, 1)
            enemigo.rotation_x += (18 - enemigo.rotation_x) * min(time.dt * 8, 1)
            enemigo.rotation_z = sin(enemigo.tiempo_animacion * 7) * 7

    def salir(self, enemigo):
        enemigo.velocidad_ragdoll = Vec3(0, 0, 0)
        enemigo.rotation_x = 0
        enemigo.rotation_z = 0


class EstadoMuerto(EstadoEnemigo):
    nombre = 'muerto'

    def entrar(self, enemigo):
        enemigo.collider = None
        enemigo.color = color.gray
        enemigo.animate_scale(Vec3(0, 0, 0), duration=0.25)
        destroy(enemigo, delay=0.25)
