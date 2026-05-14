from ursina import *

class Entidad(Entity):
    # CORRECCIÓN 1: Usar __init__ y corregir super()
    def __init__(self, hpMax, velBase, **kwargs):
        super().__init__(**kwargs) # Inicializa la Entity de Ursina

        self.hpMax = hpMax
        self.hpAct = hpMax
        self.velBase = velBase
        self.estaVivo = True

    # CORRECCIÓN 2: Meter los métodos DENTRO de la clase (identados)
    def recibirDano(self, cantidad):
        if not self.estaVivo:
            return

        self.hpAct -= cantidad
        print(f"Vida restante: {self.hpAct}")

        if self.hpAct <= 0:
            self.morir()

    def morir(self):
        self.estaVivo = False
        self.hpAct = 0
        print(f"{self.name} ha muerto.")
        # Aquí podrías desactivar el modelo o poner una animación
        # self.enabled = False