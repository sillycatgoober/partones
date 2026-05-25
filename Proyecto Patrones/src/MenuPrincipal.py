from functools import partial
from pathlib import Path

from ursina import Button, Entity, InputField, Text, application, camera, color, invoke, mouse
from ursina.models.procedural.quad import Quad
from ursina.shaders.unlit_shader import unlit_shader
from ursina.texture_importer import load_texture


def _ruta_abs_en_assets(rel: str) -> Path:
    """Ursina usa application.asset_folder (carpeta de main.py), no el cwd del terminal."""
    return (Path(application.asset_folder) / rel.replace('\\', '/')).resolve()


def _primera_textura_existente(candidatos: tuple[str, ...]) -> str | None:
    for ruta in candidatos:
        if _ruta_abs_en_assets(ruta).is_file():
            return ruta
    return None


def _cargar_textura_menu(rel: str | None):
    """
    Carga la imagen con la misma API que Ursina usa internamente.
    use_cache=False evita quedarse con None en caché si antes falló una ruta.
    folder + nombre de archivo evita ambigüedad con globs largos.
    """
    if not rel:
        return None
    p = _ruta_abs_en_assets(rel)
    if not p.is_file():
        return None
    try:
        return load_texture(p.name, folder=p.parent, use_cache=False)
    except Exception:
        return None


def _texturas_candidatas_arma(ruta_modelo_glb: str) -> tuple[str, ...]:
    base = Path(ruta_modelo_glb).stem
    slug = base.replace(' ', '_')
    slug_lower = slug.lower()
    return (
        f'assets/textures/{base}.png',
        f'assets/textures/{base}.jpg',
        f'assets/textures/{base}.jpeg',
        f'assets/textures/{base}.webp',
        f'assets/textures/{slug}.png',
        f'assets/textures/{slug}.jpg',
        f'assets/textures/{slug}.webp',
        f'assets/textures/{slug_lower}.png',
        f'assets/textures/{slug_lower}.jpg',
        f'assets/textures/{slug_lower}.webp',
        f'assets/textures/arma_{slug_lower}.png',
        f'assets/textures/arma_{slug_lower}.jpg',
    )


def _textura_boton_arma(arma: dict):
    """Prioridad: textura_menu explícita → nombres derivados del .glb en modelo."""
    candidatos: list[str] = []
    if arma.get('textura_menu'):
        candidatos.append(arma['textura_menu'])
    candidatos.extend(_texturas_candidatas_arma(arma['modelo']))
    rel = _primera_textura_existente(tuple(candidatos))
    return _cargar_textura_menu(rel)


TEXTURAS_PANEL_MULTIJUGADOR = (
    'assets/textures/chinchillas.png',
    'assets/textures/chinchillas.jpg',
    'assets/textures/chinchillas.jpeg',
    'assets/textures/chinchillas.webp',
    'assets/textures/Chinchillas.png',
    'assets/textures/Chinchillas.jpg',
)


class MenuPrincipal(Entity):
    # modelo = .glb del arma en partida. textura_menu = miniatura en el menú (opcional).
    ARMAS = [
        {
            'nombre': 'PISTOLA',
            'modelo': 'assets/weapons/classic.obj',
            'textura_menu': 'assets/textures/classic.jpeg',
            'detalle': 'The classico'
        },
        {
            'nombre': 'REVOLVER',
            'modelo': 'assets/weapons/sheriffFinal.obj',
            'textura_menu': 'assets/textures/sheriff.jpeg',
            'detalle': 'Una bala, por cabeza'
        },
        {
            'nombre': 'ESCOPETA',
            'modelo': 'assets/weapons/escopeta.obj',
            'textura_menu': 'assets/textures/escopeta.jpeg',
            'detalle': 'Corto alcance'
        },
        {
            'nombre': 'RIFLE',
            'modelo': 'assets/weapons/phantom.obj',
            'textura_menu': 'assets/textures/m4.jpeg',
            'detalle': 'El mas confiable'
        },
        {
            'nombre': 'RIFLE PESADO',
            'modelo': 'assets/weapons/vandal.obj',
            'textura_menu': 'assets/textures/ak.jpeg',
            'detalle': 'Mas municion, mas poder, menos control'
        }
    ]

    def __init__(self, iniciar_un_jugador, iniciar_multijugador):
        super().__init__(parent=camera.ui)
        self.iniciar_un_jugador = iniciar_un_jugador
        self.iniciar_multijugador = iniciar_multijugador
        self.arma_seleccionada = self.ARMAS[0]
        self.botones_armas = []

        self.fondo = Entity(
            parent=self,
            model=Quad,
            texture='assets/textures/cielito.png',
            color=color.rgba(120, 120, 120, 255),
            scale=(2.2, 1.25),
            shader=unlit_shader,
            z=0.2,
        )
        self.sombra = Entity(
            parent=self,
            model=Quad,
            color=color.rgba(0, 0, 0, 155),
            scale=(2.2, 1.25),
            shader=unlit_shader,
            z=0.1,
        )
        self.titulo = Text(
            parent=self,
            text='PROYECTO PATRONES',
            position=(0, 0.25),
            origin=(0, 0),
            scale=2.0,
            color=color.rgb(240, 235, 210)
        )
        self.subtitulo = Text(
            parent=self,
            text='SUPERVIVENCIA ZOMBIE',
            position=(0, 0.16),
            origin=(0, 0),
            scale=0.85,
            color=color.rgb(180, 205, 165)
        )
        self.boton_un_jugador = Button(
            parent=self,
            model='quad',
            texture='assets/textures/UnJugador.jpeg',
            position=(-0.25, -0.31),
            scale=(0.42, 0.12),
            color=color.white,
            highlight_color=color.rgb(220, 220, 220),
            pressed_color=color.rgb(150, 150, 150),
            on_click=self.seleccionar_un_jugador
        )
        self.boton_multijugador = Button(
            parent=self,
            model='quad',
            texture='assets/textures/Multijugador.jpeg',
            position=(0.25, -0.31),
            scale=(0.42, 0.12),
            color=color.white,
            highlight_color=color.rgb(220, 220, 220),
            pressed_color=color.rgb(150, 150, 150),
            on_click=self.abrir_panel_multijugador
        )
        self.texto_armeria = Text(
            parent=self,
            text='ARMERIA',
            position=(0, 0.055),
            origin=(0, 0),
            scale=1.05,
            color=color.rgb(245, 235, 190)
        )
        self.texto_arma_actual = Text(
            parent=self,
            text='',
            position=(0, -0.02),
            origin=(0, 0),
            scale=0.72,
            color=color.rgb(180, 220, 155)
        )
        for indice, arma in enumerate(self.ARMAS):
            x = -0.36 + (indice % 3) * 0.36
            y = -0.10 - (indice // 3) * 0.10
            tex_obj = _textura_boton_arma(arma)
            kwargs_boton = dict(
                parent=self,
                model=Quad,
                text=arma['nombre'],
                position=(x, y),
                scale=(0.30, 0.095),
                shader=unlit_shader,
                highlight_color=color.rgb(95, 125, 78),
                pressed_color=color.rgb(65, 95, 55),
                text_color=color.rgb(255, 252, 245),
                text_size=0.68,
                on_click=partial(self.seleccionar_arma, arma),
            )
            if tex_obj is not None:
                kwargs_boton['texture'] = tex_obj
                kwargs_boton['color'] = color.white
            else:
                kwargs_boton['color'] = color.rgba(28, 34, 30, 235)
            boton = Button(**kwargs_boton)
            boton._menu_arma_con_textura = tex_obj is not None
            self.botones_armas.append((boton, arma))

        self.aviso = Text(
            parent=self,
            text='',
            position=(0, -0.43),
            origin=(0, 0),
            scale=0.72,
            color=color.rgb(255, 210, 120),
            enabled=False
        )

        self._construir_panel_multijugador()

        mouse.locked = False
        mouse.visible = True
        self.actualizar_armeria()

    def _construir_panel_multijugador(self):
        self.panel_red = Entity(parent=self, enabled=False, z=-0.08)
        rel_panel = _primera_textura_existente(TEXTURAS_PANEL_MULTIJUGADOR) or _primera_textura_existente(
            ('assets/textures/cielito.png',)
        )
        tex_panel = _cargar_textura_menu(rel_panel)
        if tex_panel is not None:
            Entity(
                parent=self.panel_red,
                model=Quad,
                texture=tex_panel,
                scale=(0.94, 0.60),
                position=(0, -0.02),
                z=0.01,
                color=color.white,
                shader=unlit_shader,
            )
        else:
            Entity(
                parent=self.panel_red,
                model=Quad,
                scale=(0.94, 0.60),
                position=(0, -0.02),
                z=0.01,
                color=color.rgb(32, 38, 48),
                shader=unlit_shader,
            )
        Entity(
            parent=self.panel_red,
            model=Quad,
            color=color.rgba(8, 10, 14, 72),
            scale=(0.94, 0.60),
            position=(0, -0.02),
            z=0.02,
            shader=unlit_shader,
        )
        Text(
            parent=self.panel_red,
            text='MULTIJUGADOR (SOCKET TCP / JSON)',
            position=(0, 0.18),
            origin=(0, 0),
            scale=0.95,
            color=color.rgb(255, 248, 235),
            z=-0.01,
        )
        Text(
            parent=self.panel_red,
            text='IP del anfitrion (solo cliente):',
            position=(0, 0.08),
            origin=(0, 0),
            scale=0.65,
            color=color.rgb(240, 245, 235),
            z=-0.01,
        )
        self.campo_ip = InputField(
            parent=self.panel_red,
            default_value='127.0.0.1',
            position=(0, 0.02),
            scale=(0.52, 0.055),
            character_limit=40,
        )
        Button(
            parent=self.panel_red,
            text='ANFITRION (ESCUCHA :7777)',
            position=(0, -0.07),
            scale=(0.58, 0.062),
            color=color.rgb(42, 72, 48),
            highlight_color=color.rgb(62, 105, 72),
            text_color=color.rgb(245, 250, 240),
            text_size=0.78,
            on_click=self._iniciar_red_anfitrion,
        )
        Button(
            parent=self.panel_red,
            text='UNIRSE CON ESTA IP',
            position=(0, -0.165),
            scale=(0.68, 0.095),
            color=color.rgb(255, 214, 48),
            highlight_color=color.rgb(255, 235, 120),
            pressed_color=color.rgb(230, 175, 25),
            text_color=color.rgb(18, 22, 28),
            text_size=1.05,
            on_click=self._iniciar_red_cliente,
        )
        Button(
            parent=self.panel_red,
            text='VOLVER',
            position=(0, -0.275),
            scale=(0.36, 0.048),
            color=color.rgb(55, 55, 58),
            highlight_color=color.rgb(75, 75, 78),
            text_color=color.rgb(235, 235, 238),
            text_size=0.75,
            on_click=self._cerrar_panel_multijugador,
        )

    def abrir_panel_multijugador(self):
        self.panel_red.enabled = True

    def _cerrar_panel_multijugador(self):
        self.panel_red.enabled = False

    def _iniciar_red_anfitrion(self):
        ok, mensaje = self.iniciar_multijugador(True, None, self.arma_seleccionada['modelo'])
        if ok:
            self.panel_red.enabled = False
            self.enabled = False
            mouse.visible = False
        elif mensaje:
            self._mostrar_aviso(mensaje)

    def _iniciar_red_cliente(self):
        ip = self.campo_ip.text_field.text.strip() or '127.0.0.1'
        ok, mensaje = self.iniciar_multijugador(False, ip, self.arma_seleccionada['modelo'])
        if ok:
            self.panel_red.enabled = False
            self.enabled = False
            mouse.visible = False
        else:
            self._mostrar_aviso(mensaje or 'No se pudo conectar.')

    def _mostrar_aviso(self, texto: str):
        self.aviso.text = texto
        self.aviso.enabled = True
        invoke(setattr, self.aviso, 'enabled', False, delay=3.5)

    def seleccionar_arma(self, arma):
        self.arma_seleccionada = arma
        self.actualizar_armeria()

    def actualizar_armeria(self):
        self.texto_arma_actual.text = f"ARMA: {self.arma_seleccionada['nombre']}  |  {self.arma_seleccionada['detalle']}"

        for boton, arma in self.botones_armas:
            tiene_textura = getattr(boton, '_menu_arma_con_textura', False)
            if arma is self.arma_seleccionada:
                boton.color = color.rgba(120, 255, 140, 255) if tiene_textura else color.rgb(75, 105, 58)
                boton.text_color = color.rgb(15, 40, 18) if tiene_textura else color.white
            else:
                boton.color = color.rgba(255, 255, 255, 210) if tiene_textura else color.rgba(28, 34, 30, 235)
                boton.text_color = color.rgb(255, 252, 245) if tiene_textura else color.rgb(235, 230, 205)

    def seleccionar_un_jugador(self):
        self.enabled = False
        mouse.visible = False
        self.iniciar_un_jugador(self.arma_seleccionada['modelo'])
