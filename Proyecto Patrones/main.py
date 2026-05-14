from ursina import Entity, Sky, Ursina, color, mouse

from src.GameManager import GameManager
from src.InterfazJugador import InterfazJugador
from src.MenuPrincipal import MenuPrincipal
from src.Player import Player
from src.SpawnerEnemigos import SpawnerEnemigos
from src.red import SesionRed, SincronizadorRed

app = Ursina()
juego_iniciado = False


def _crear_escenario_base():
    Sky(texture='assets/textures/cielito.png')
    Entity(model='plane', scale=100, texture='assets/textures/Pasto.jpeg', collider='box')


def _iniciar_partida(modelo_arma: str, sesion_red: SesionRed | None = None) -> None:
    global juego_iniciado
    juego_iniciado = True

    arma = Entity(
        model=modelo_arma,
        scale=1,
        rotation=(0, 0, 0),
    )
    arma.ruta_modelo = modelo_arma

    jugador = Player(arma=arma)
    if sesion_red is not None:
        jugador.sesion_red = sesion_red

    InterfazJugador(jugador)
    game_manager = GameManager(jugador)
    SpawnerEnemigos(jugador, game_manager).iniciar_oleada()

    if sesion_red is not None:
        proxy = Entity(
            model='cube',
            color=color.azure,
            scale=(0.45, 1.75, 0.45),
            collider=None,
            name='JugadorRemoto',
        )
        SincronizadorRed(jugador=jugador, sesion=sesion_red, proxy_jugador_remoto=proxy)

    _crear_escenario_base()


def iniciar_un_jugador(modelo_arma='assets/weapons/Pistol.glb'):
    global juego_iniciado
    if juego_iniciado:
        return
    _iniciar_partida(modelo_arma, sesion_red=None)
    mouse.visible = False


def iniciar_multijugador(es_anfitrion: bool, ip_host: str | None, modelo_arma: str) -> tuple[bool, str]:
    """
    Arranca la partida con red TCP.
    Anfitrión: escucha en el puerto 7777 hasta que un cliente se conecte (el juego ya corre).
    Cliente: intenta conectar a ip_host (p. ej. 127.0.0.1 o la LAN del anfitrión).
    """
    global juego_iniciado
    if juego_iniciado:
        return True, ''

    if es_anfitrion:
        sesion = SesionRed.iniciar_como_anfitrion()
        print('Multijugador: anfitrión escuchando en el puerto 7777. Que el otro jugador pulse "Unirse" con tu IP.')
    else:
        ip = (ip_host or '127.0.0.1').strip()
        sesion, error = SesionRed.conectar_como_cliente(ip)
        if sesion is None:
            return False, error

    _iniciar_partida(modelo_arma, sesion_red=sesion)
    mouse.visible = False
    return True, ''


MenuPrincipal(iniciar_un_jugador, iniciar_multijugador)

app.run()
