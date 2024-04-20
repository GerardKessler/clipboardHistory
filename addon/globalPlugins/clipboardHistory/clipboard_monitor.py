# -*- coding: utf-8 -*-
# Copyright (C) 2021 Gerardo Kessler <gera.ar@yahoo.com>
# This file is covered by the GNU General Public License.
# Código del script clipboard-monitor perteneciente a Héctor Benítez

import api
import ctypes
from ctypes import wintypes
import threading
from .database import connect, cursor

# Definición manual de tipos de datos necesarios
DWORD = ctypes.c_ulong
LONG = ctypes.c_long
ULONG_PTR = ctypes.POINTER(DWORD)
MAX_PATH = 260

# Constantes y tipos de Windows necesarios
WM_CLIPBOARDUPDATE = 0x031D
WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_long, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

class WNDCLASS(ctypes.Structure):
	"""Estructura que define las propiedades de la clase de ventana."""
	_fields_ = [
		("style", wintypes.UINT),
		("lpfnWndProc", WNDPROC),
		("cbClsExtra", ctypes.c_int),
		("cbWndExtra", ctypes.c_int),
		("hInstance", wintypes.HINSTANCE),
		("hIcon", wintypes.HANDLE),
		("hCursor", wintypes.HANDLE),
		("hbrBackground", wintypes.HANDLE),
		("lpszMenuName", wintypes.LPCWSTR),
		("lpszClassName", wintypes.LPCWSTR)
	]

class MSG(ctypes.Structure):
	"""Estructura que almacena mensajes de la cola de eventos de Windows."""
	_fields_ = [
		("hwnd", wintypes.HWND),
		("message", wintypes.UINT),
		("wParam", wintypes.WPARAM),
		("lParam", wintypes.LPARAM),
		("time", wintypes.DWORD),
		("pt", wintypes.POINT)
	]

class ClipboardMonitor:
	"""Clase para monitorear los cambios en el portapapeles de Windows."""

	def __init__(self):
		"""Inicializa la clase y prepara las estructuras necesarias."""
		self.hwnd = None
		self.msg = MSG()
		self.running = False
		self.thread = None
		self.wnd_proc_instance = WNDPROC(self.wnd_proc)  # Mantener una referencia al WNDPROC

	def create_window(self):
		"""Crea una ventana oculta que recibe mensajes del portapapeles."""
		wc = WNDCLASS()
		wc.lpfnWndProc = self.wnd_proc_instance  # Usar la instancia de WNDPROC
		wc.lpszClassName = "ClipboardListener"
		wc.hInstance = ctypes.windll.kernel32.GetModuleHandleW(None)
		wc.hIcon = wc.hCursor = wc.hbrBackground = None
		if not ctypes.windll.user32.RegisterClassW(ctypes.byref(wc)):
			raise ctypes.WinError()
		self.hwnd = ctypes.windll.user32.CreateWindowExW(0, wc.lpszClassName, "Clipboard Monitor", 0, 0, 0, 0, 0, None, None, wc.hInstance, None)

	def wnd_proc(self, hwnd, msg, wParam, lParam):
		"""Procedimiento de ventana que maneja los mensajes recibidos."""
		if msg == WM_CLIPBOARDUPDATE:
			try:
				content= api.getClipData()
			except OSError:
				content= None
			if content is None or content == '':
				# Si el contenido es None o está vacío, devolver el control a DefWindowProcW
				return ctypes.windll.user32.DefWindowProcW(hwnd, msg, wParam, lParam)
			else:
				cursor.execute('DELETE FROM strings WHERE string=?', (content,))
				connect.commit()
				cursor.execute('INSERT INTO strings (string, favorite) VALUES (?, ?)', (content, 0))
				connect.commit()
				cursor.execute('SELECT id FROM strings')
				counter= cursor.fetchall()
				cursor.execute('SELECT max_elements FROM settings')
				max_elements= cursor.fetchone()
				if max_elements[0] != 0 and len(counter) > max_elements[0]:
					cursor.execute('DELETE FROM strings WHERE id=?', (counter[0][0],))
					connect.commit()

		return ctypes.windll.user32.DefWindowProcW(hwnd, msg, wParam, lParam)

	def run(self):
		"""Cuerpo principal del monitoreo, diseñado para ejecutarse en un hilo."""
		self.create_window()
		ctypes.windll.user32.AddClipboardFormatListener(self.hwnd)
		self.running = True
		while self.running and ctypes.windll.user32.GetMessageW(ctypes.byref(self.msg), self.hwnd, 0, 0):
			ctypes.windll.user32.TranslateMessage(ctypes.byref(self.msg))
			ctypes.windll.user32.DispatchMessageW(ctypes.byref(self.msg))

	def start_monitoring(self, as_thread=False):
		"""Inicia el monitoreo del portapapeles, opcionalmente en un nuevo hilo."""
		if as_thread:
			self.thread = threading.Thread(target=self.run, daemon=True)
			self.thread.start()
		else:
			self.run()

	def stop_monitoring(self):
		"""Detiene el monitoreo del portapapeles."""
		self.running = False
		ctypes.windll.user32.PostQuitMessage(0)
		if self.thread:
			self.thread.join()

