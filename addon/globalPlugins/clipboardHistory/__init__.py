# -*- coding: utf-8 -*-
# Copyright (C) 2021 Gerardo Kessler <ReaperYOtrasYerbas@gmail.com>
# This file is covered by the GNU General Public License.
# Código del script clipboard-monitor perteneciente a Héctor Benítez

from nvwave import playWaveFile
from threading import Thread, Timer
from time import sleep
import gui
import wx
import api
import globalPluginHandler
import core
import globalVars
import ui
from scriptHandler import script
import os
import shutil
from .database import *
from .dialogs import *
from .keyFunc import pressKey, releaseKey
from .clipboard_monitor import ClipboardMonitor
import addonHandler

# Lína de traducción
addonHandler.initTranslation()

def disableInSecureMode(decoratedCls):
	if globalVars.appArgs.secure:
		return globalPluginHandler.GlobalPlugin
	return decoratedCls

@disableInSecureMode
class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	def __init__(self, *args, **kwargs):
		super(GlobalPlugin, self).__init__(*args, **kwargs)
		self.data= []
		self.search_text= None
		self.x= 0
		self.switch= False
		self.dialogs= False
		self.timer= Timer(0.2, self.main)
		self.monitor= None
		self.sounds= None
		self.max_elements= None
		self.number= None
		
		if hasattr(globalVars, 'clipboardHistory'):
			self.postStartupHandler()
		core.postNvdaStartup.register(self.postStartupHandler)
		globalVars.clipboardHistory= None

	def postStartupHandler(self):
		Thread(target=self._start, daemon=True).start()

	def _start(self):
		self.monitor= ClipboardMonitor()
		self.monitor.start_monitoring(as_thread=False)

	def getScript(self, gesture):
		if not self.switch: return globalPluginHandler.GlobalPlugin.getScript(self, gesture)
		script= globalPluginHandler.GlobalPlugin.getScript(self, gesture)
		if not script:
			mute(0.3, _('Historial Cerrado'))
			self.finish()
			return
		return globalPluginHandler.GlobalPlugin.getScript(self, gesture)

	def finish(self, sound='close'):
		self.switch= False
		self.clearGestureBindings()
		if self.sounds: self.play(sound)

	def play(self, sound):
		if sound: playWaveFile(os.path.join(dirAddon, 'sounds', '{}.wav'.format(sound)))

	@script(
		category= 'clipboardHistory',
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Activa la capa de comandos. Doble pulsación rápida muestra el diálogo de configuración'),
		gesture= None
	)
	def script_viewData(self, gesture):
		if self.switch or self.dialogs: return
		if self.timer.is_alive():
			self.timer.cancel()
			self.script_settings(gesture)
		else:
			self.timer.start()

	def main(self):
		self.timer= Timer(0.2, self.main)
		cursor.execute('SELECT string FROM strings ORDER BY id DESC')
		self.data= cursor.fetchall()
		cursor.execute('SELECT sounds, max_elements, number FROM settings')
		settings= cursor.fetchone()
		self.sounds, self.max_elements, self.number= settings[0], settings[1], settings[2]
		if len(self.data) < 1:
			ui.message(_('Historial vacío'))
			return
		if self.sounds: self.play('start')
		self.switch= True
		self.bindGestures(self.__newGestures)
		ui.message(_('Historial abierto'))

	def script_items(self, gesture):
		key= gesture.mainKeyName
		if key == 'downArrow':
			self.x+=1
			if self.x >= len(self.data):
				self.x= 0
		elif key == 'upArrow':
			self.x-=1
			if self.x < 0:
				self.x= len(self.data)-1
		elif key == 'home':
			self.x= 0
		elif key == 'end':
			self.x= len(self.data)-1
		if self.sounds: self.play('click')
		self.speak()

	def script_copyItem(self, gesture):
		api.copyToClip(self.data[self.x][0])
		ui.message(_('Elemento copiado'))
		self.finish('copy')

	def script_viewItem(self, gesture):
		ui.browseableMessage(self.data[self.x][0], _('Contenido'))
		self.finish('open')
		mute(0.1, _('Mostrando el contenido'))

	def script_deleteItem(self, gesture):
		cursor.execute('DELETE FROM strings WHERE string=?', (self.data[self.x][0],))
		connect.commit()
		self.data.pop(self.x)
		if self.sounds: self.play('delete')
		if len(self.data) < 1:
			ui.message(_('Lista vacía'))
			self.finish()
			return
		if self.x == len(self.data): self.x-=1
		self.speak()

	def speak(self):
		if self.number:
			ui.message(f'{self.x+1}; {self.data[self.x][0]}')
		else:
			ui.message(self.data[self.x][0])

	def script_pasteItem(self, gesture):
		api.copyToClip(self.data[self.x][0])
		self.finish('paste')
		mute(0.2, _('Pegado'))
		pressKey(0x11)
		pressKey(0x56)
		releaseKey(0x56)
		releaseKey(0x11)

	def script_findItem(self, gesture):
		self.finish()
		get_search= wx.TextEntryDialog(
			gui.mainFrame,
			_('Escriba la búsqueda y pulse intro'),
			_('Buscador')
		)
		def callback(result):
			if result == wx.ID_OK:
				self.search_text= get_search.GetValue()
				self.startSearch()
		gui.runScriptModalDialog(get_search, callback)

	def script_searchNextItem(self, gesture):
		self.startSearch()

	def startSearch(self):
		if self.search_text is None:
			ui.message(_('Sin texto de búsqueda'))
			return

		# Intentar encontrar la coincidencia comenzando desde el siguiente elemento
		for i in range(self.x + 1, len(self.data)):
			if self.search_text.lower() in self.data[i][0].lower():
				self.x = i
				mute(0.2, f'{self.x + 1}; {self.data[self.x][0]}')
				self.bindGestures(self.__newGestures)
				return

		# Si no se encuentra, busca desde el comienzo hasta el elemento actual
		for i in range(0, self.x + 1):
			if self.search_text.lower() in self.data[i][0].lower():
				self.x = i
				mute(0.2, f'{self.x + 1}; {self.data[self.x][0]}')
				self.bindGestures(self.__newGestures)
				return

		# Si no se encuentra nada después de buscar todo el rango
		mute(0.2, _('Sin resultados'))
		self.bindGestures(self.__newGestures)

	def script_close(self, gesture):
		mute(0.3, _('Historial cerrado'))
		self.finish()

	def script_historyDelete(self, gesture):
		self.finish()
		self.delete_dialog= Delete(gui.mainFrame, self)
		gui.mainFrame.prePopup()
		self.delete_dialog.Show()

	def script_commandList(self, gesture):
		self.finish()
		string= _('''
Flecha arriba; anterior elemento de la lista
Flecha abajo; siguiente elemento de la lista
Inicio; primer elemento de la lista
fin; último elemento de la lista
Flecha derecha; copia el elemento actual al portapapeles y lo desplaza al comienzo de la lista
Flecha izquierda; abre el contenido del elemento actual en una ventana de NVDA
Retroceso; elimina el actual elemento de la lista
v; Pega el contenido del elemento actual en la ventana con el foco
f; activa la ventana para buscar elementos en la lista
f3; avanza a la siguiente coincidencia  del texto buscado
g; activa la ventana para enfocar el elemento por número de órden
e; verbaliza el número de índice del elemento actual, y el número total de la lista
s; activa el diálogo de configuración del complemento
z; activa el diálogo para la eliminación de elementos de la lista
escape; desactiva la capa de comandos
		''')
		ui.browseableMessage(string, _('Lista de comandos'))

	def script_indexSearch(self, gesture):
		self.finish()
		get_search= wx.TextEntryDialog(
			gui.mainFrame,
			_('Escriba el número y pulse intro'),
			_('Hay {} elementos en el historial'.format(len(self.data)))
		)
		def callback(result):
			if result == wx.ID_OK:
				index= get_search.GetValue()
				if index.isdigit() and int(index) > 0 and int(index) <= len(self.data):  # Ajuste aquí
					self.x= int(index)-1
					mute(0.5, f'{index}; {self.data[self.x][0]}')
					self.bindGestures(self.__newGestures)
				else:
					mute(0.3, _('Dato incorrecto o fuera de rango'))
		gui.runScriptModalDialog(get_search, callback)

	def script_settings(self, gesture):
		self.timer= Timer(0.2, self.main)
		self.finish('open')
		if not self.sounds:
			cursor.execute('SELECT string FROM strings ORDER BY id DESC')
			self.data= cursor.fetchall()
			cursor.execute('SELECT sounds, max_elements, number FROM settings')
			settings= cursor.fetchone()
			self.sounds, self.max_elements, self.number= settings[0], settings[1], settings[2]

		self.settings_dialog= Settings(gui.mainFrame, self, self.sounds, self.max_elements, self.number)
		gui.mainFrame.prePopup()
		self.settings_dialog.Show()

	def script_indexAnnounce(self, gesture):
		ui.message(f'{self.x+1} de {len(self.data)}')

	def terminate(self):
		if cursor and connect:
			cursor.close()
			connect.close()
			self.monitor.stop_monitoring()

	__newGestures= {'kb:f1': 'commandList',
		'kb:downArrow': 'items',
		'kb:upArrow': 'items',
		'kb:home': 'items',
		'kb:end': 'items',
		'kb:rightArrow': 'copyItem',
		'kb:leftArrow': 'viewItem',
		'kb:backspace': 'deleteItem',
		'kb:v': 'pasteItem',
		'kb:f': 'findItem',
		'kb:f3': 'searchNextItem',
		'kb:g': 'indexSearch',
		'kb:e': 'indexAnnounce',
		'kb:s': 'settings',
		'kb:z': 'historyDelete',
		'kb:escape': 'close'}

