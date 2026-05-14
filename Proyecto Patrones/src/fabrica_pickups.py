"""
Patrón Factory: creadores concretos instancian pickups (curación / munición)
cuando un zombie muere, según probabilidades configurables.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from math import sin
from pathlib import Path
from random import random, uniform

from ursina import Entity, Vec3, color, destroy, distance, time


RUTAS_MODELO_CURACION = (
    'assets/models/Pickup Health.glb',
    'assets/models/Pickup_Health.glb',
    'assets/models/PickupHealing.glb',
    'assets/models/Pickup Health Pack.glb',
)

RUTAS_MODELO_BALAS = (
    'assets/models/Pickup Bullets.glb',
    'assets/models/Pickup_Bullets.glb',
    'assets/models/Pickup Ammo.glb',
    'assets/models/Pickup_Ammo.glb',
)


def _primera_ruta_existente(candidatos: tuple[str, ...]) -> str | None:
    for ruta in candidatos:
        if Path(ruta).is_file():
            return ruta
    return None


class CreadorPickup(ABC):
    """Factory Method: cada subclase sabe cómo construir su pickup."""

    radio_recogida: float = 1.45

    def __init__(self, jugador):
        self.jugador = jugador

    @abstractmethod
    def crear(self, posicion: Vec3) -> Entity | None:
        pass


class CreadorPickupCuracion(CreadorPickup):
    def __init__(self, jugador, cantidad_min: int = 12, cantidad_max: int = 28):
        super().__init__(jugador)
        self.cantidad_min = cantidad_min
        self.cantidad_max = cantidad_max

    def crear(self, posicion: Vec3) -> Entity | None:
        if not self.jugador or not self.jugador.estaVivo:
            return None
        ruta = _primera_ruta_existente(RUTAS_MODELO_CURACION)
        cantidad = int(uniform(self.cantidad_min, self.cantidad_max + 1))
        return PickupCuracion(
            posicion=posicion + Vec3(uniform(-0.12, 0.12), 0.12, uniform(-0.12, 0.12)),
            jugador=self.jugador,
            cantidad=cantidad,
            ruta_modelo=ruta,
        )


class CreadorPickupMunicion(CreadorPickup):
    def __init__(self, jugador, cantidad_min: int = 8, cantidad_max: int = 22):
        super().__init__(jugador)
        self.cantidad_min = cantidad_min
        self.cantidad_max = cantidad_max

    def crear(self, posicion: Vec3) -> Entity | None:
        if not self.jugador or not self.jugador.estaVivo:
            return None
        ruta = _primera_ruta_existente(RUTAS_MODELO_BALAS)
        cantidad = int(uniform(self.cantidad_min, self.cantidad_max + 1))
        return PickupMunicion(
            posicion=posicion + Vec3(uniform(-0.12, 0.12), 0.12, uniform(-0.12, 0.12)),
            jugador=self.jugador,
            cantidad=cantidad,
            ruta_modelo=ruta,
        )


class FabricaLootZombie:
    """
    Fábrica que orquesta los creadores: aplica probabilidades independientes
    para que aparezcan 0, 1 o 2 pickups al morir un enemigo.
    """

    def __init__(self, jugador, probabilidad_curacion: float = 0.22, probabilidad_municion: float = 0.32):
        self.jugador = jugador
        self.probabilidad_curacion = probabilidad_curacion
        self.probabilidad_municion = probabilidad_municion
        self._creador_curacion = CreadorPickupCuracion(jugador)
        self._creador_municion = CreadorPickupMunicion(jugador)

    def generar_drops(self, posicion: Vec3) -> None:
        if random() < self.probabilidad_curacion:
            self._creador_curacion.crear(posicion)
        if random() < self.probabilidad_municion:
            self._creador_municion.crear(posicion)


class PickupBase(Entity):
    def __init__(self, posicion: Vec3, jugador, ruta_modelo: str | None, escala_fallback: float, color_fallback):
        base_kw = dict(position=posicion, collider='sphere')
        if ruta_modelo:
            super().__init__(model=ruta_modelo, scale=0.35, color=color.white, **base_kw)
        else:
            super().__init__(model='sphere', scale=escala_fallback, color=color_fallback, **base_kw)

        self.jugador = jugador
        self.tiempo_inicio = time.time()
        self.radio = CreadorPickup.radio_recogida

    def update(self):
        if not self.jugador or not self.jugador.estaVivo:
            return

        self.y = self.y + sin((time.time() - self.tiempo_inicio) * 3.2) * 0.012
        self.rotation_y += time.dt * 55

        if distance(self.position, self.jugador.position) <= self.radio:
            self.aplicar_efecto()
            destroy(self)

    def aplicar_efecto(self):
        raise NotImplementedError


class PickupCuracion(PickupBase):
    def __init__(self, posicion: Vec3, jugador, cantidad: int, ruta_modelo: str | None):
        self.cantidad = cantidad
        super().__init__(
            posicion,
            jugador,
            ruta_modelo,
            escala_fallback=0.32,
            color_fallback=color.rgb(60, 220, 120),
        )
        if not ruta_modelo:
            self.color = color.rgb(60, 220, 120)

    def aplicar_efecto(self):
        if hasattr(self.jugador, 'aplicar_curacion'):
            self.jugador.aplicar_curacion(self.cantidad)


class PickupMunicion(PickupBase):
    def __init__(self, posicion: Vec3, jugador, cantidad: int, ruta_modelo: str | None):
        self.cantidad = cantidad
        super().__init__(
            posicion,
            jugador,
            ruta_modelo,
            escala_fallback=0.28,
            color_fallback=color.rgb(255, 200, 70),
        )
        if not ruta_modelo:
            self.color = color.rgb(255, 200, 70)

    def aplicar_efecto(self):
        if hasattr(self.jugador, 'aplicar_municion_reserva'):
            self.jugador.aplicar_municion_reserva(self.cantidad)
