"""
Capa de transporte TCP + mensajes JSON por línea (NDJSON).
Base para multijugador: anfitrión escucha un cliente; el cliente se conecta al anfitrión.
"""
from __future__ import annotations

import json
import queue
import socket
import threading
from typing import Any

TIPO_ESTADO_JUGADOR = 'estado_jugador'


class SesionRed:
    """Sesión de red opcional: modo 'host', 'cliente' o sin usar (_peer None)."""

    PUERTO_PREDETERMINADO = 7777

    def __init__(self):
        self.modo = 'offline'
        self._socket_escucha: socket.socket | None = None
        self._peer: socket.socket | None = None
        self._entrada: queue.Queue[dict[str, Any]] = queue.Queue()
        self._cerrar = threading.Event()
        self._hilos: list[threading.Thread] = []
        self.ultimo_error: str | None = None

    @classmethod
    def iniciar_como_anfitrion(cls, puerto: int = PUERTO_PREDETERMINADO) -> SesionRed:
        sesion = cls()
        sesion.modo = 'host'
        sesion._socket_escucha = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sesion._socket_escucha.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sesion._socket_escucha.bind(('0.0.0.0', puerto))
        sesion._socket_escucha.listen(1)
        hilo = threading.Thread(target=sesion._aceptar_cliente, daemon=True)
        hilo.start()
        sesion._hilos.append(hilo)
        return sesion

    @classmethod
    def conectar_como_cliente(cls, host: str, puerto: int = PUERTO_PREDETERMINADO, tiempo_espera: float = 10.0) -> tuple[SesionRed | None, str]:
        sesion = cls()
        sesion.modo = 'cliente'
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(tiempo_espera)
        try:
            sock.connect((host, puerto))
        except OSError as e:
            sesion.ultimo_error = str(e)
            try:
                sock.close()
            except OSError:
                pass
            return None, sesion.ultimo_error or 'Error de conexion'
        sock.settimeout(None)
        sesion._peer = sock
        sesion._iniciar_hilo_recepcion(sock)
        return sesion, ''

    @classmethod
    def iniciar_como_cliente(cls, host: str, puerto: int = PUERTO_PREDETERMINADO, tiempo_espera: float = 10.0) -> SesionRed | None:
        """Compatibilidad: devuelve solo la sesión o None."""
        sesion, _err = cls.conectar_como_cliente(host, puerto, tiempo_espera)
        return sesion

    def _aceptar_cliente(self) -> None:
        assert self._socket_escucha is not None
        try:
            conn, _addr = self._socket_escucha.accept()
        except OSError:
            return
        self._peer = conn
        try:
            self._socket_escucha.close()
        except OSError:
            pass
        self._socket_escucha = None
        self._iniciar_hilo_recepcion(conn)

    def _iniciar_hilo_recepcion(self, sock: socket.socket) -> None:
        hilo = threading.Thread(target=self._bucle_recepcion, args=(sock,), daemon=True)
        hilo.start()
        self._hilos.append(hilo)

    def _bucle_recepcion(self, sock: socket.socket) -> None:
        buffer = b''
        while not self._cerrar.is_set():
            try:
                chunk = sock.recv(4096)
            except OSError:
                break
            if not chunk:
                break
            buffer += chunk
            while True:
                idx = buffer.find(b'\n')
                if idx < 0:
                    break
                linea, buffer = buffer[:idx], buffer[idx + 1 :]
                texto = linea.decode('utf-8', errors='ignore').strip()
                if not texto:
                    continue
                try:
                    self._entrada.put(json.loads(texto))
                except json.JSONDecodeError:
                    continue

    def conectado(self) -> bool:
        return self._peer is not None

    def drenar_mensajes(self) -> list[dict[str, Any]]:
        salida: list[dict[str, Any]] = []
        while True:
            try:
                salida.append(self._entrada.get_nowait())
            except queue.Empty:
                break
        return salida

    def enviar_estado_jugador(self, x: float, y: float, z: float, rotation_y: float, cam_rx: float) -> None:
        if self._peer is None:
            return
        mensaje = {
            'tipo': TIPO_ESTADO_JUGADOR,
            'x': x,
            'y': y,
            'z': z,
            'ry': rotation_y,
            'cam_rx': cam_rx,
        }
        self._enviar_dict(mensaje)

    def _enviar_dict(self, datos: dict[str, Any]) -> None:
        if self._peer is None:
            return
        linea = json.dumps(datos, separators=(',', ':')) + '\n'
        try:
            self._peer.sendall(linea.encode('utf-8'))
        except OSError:
            pass

    def cerrar(self) -> None:
        self._cerrar.set()
        if self._socket_escucha:
            try:
                self._socket_escucha.close()
            except OSError:
                pass
            self._socket_escucha = None
        if self._peer:
            try:
                self._peer.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                self._peer.close()
            except OSError:
                pass
            self._peer = None
