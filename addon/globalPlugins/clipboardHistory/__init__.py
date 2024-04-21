# -*- coding: utf-8 -*-
# Copyright (C) 2021 Gerardo Kessler <gera.ar@yahoo.com>
# This file is covered by the GNU General Public License.
# Código del script clipboard-monitor perteneciente a Héctor Benítez

from nvwave import playWaveFile
from threading import Thread
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
from re import findall
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

	# Translators: Mensaje de lista vacía
	empty= _('Lista vacía')
	def __init__(self, *args, **kwargs):
		super(GlobalPlugin, self).__init__(*args, **kwargs)
		self.data= []
		self.x= 0
		self.y= 0
		self.temporary_index_data= 0
		self.temporary_index_favorites= 0
		self.search_text= None
		self.switch= False
		self.dialogs= False
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
			# Translators: Mensaje de historial cerrado
			mute(0.3, _('Historial Cerrado'))
			self.finish()
			return
		return globalPluginHandler.GlobalPlugin.getScript(self, gesture)

	# método que elimina los gestos asignados, y desactiva la bandera switch
	def finish(self, sound='close'):
		self.switch= False
		self.clearGestureBindings()
		if self.sounds: self.play(sound)

	def play(self, sound):
		if sound: playWaveFile(os.path.join(dirAddon, 'sounds', '{}.wav'.format(sound)))

	@script(
		category= 'clipboardHistory',
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Activa la interfaz gráfica con el historial del portapapeles'),
		gesture= None
	)
	def script_basicGui(self, gesture):
		simple_gui= Gui(gui.mainFrame, self)
		gui.mainFrame.prePopup()
		simple_gui.Show()

	@script(
		category= 'clipboardHistory',
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Activa la capa de comandos'),
		gesture= None
	)
	def script_viewData(self, gesture):
		if self.switch or self.dialogs: return
		cursor.execute('SELECT string, favorite FROM strings ORDER BY id DESC')
		data= cursor.fetchall()
		favorites= [x for x in data if x[1] == 1]
		self.data= [data, favorites]
		cursor.execute('SELECT sounds, max_elements, number FROM settings')
		settings= cursor.fetchone()
		self.sounds, self.max_elements, self.number= settings[0], settings[1], settings[2]
		if self.sounds: self.play('start')
		self.switch= True
		self.bindGestures(self.__newGestures)
		# Translators: Aviso de historial abierto
		ui.message(_('Historial abierto'))

	def script_items(self, gesture):
		if len(self.data[self.y]) < 1:
			ui.message(self.empty)
			return
		key= gesture.mainKeyName
		if key == 'downArrow':
			self.x+=1
			if self.x >= len(self.data[self.y]):
				self.x= 0
		elif key == 'upArrow':
			self.x-=1
			if self.x < 0 or self.x > len(self.data[self.y]):
				self.x= len(self.data[self.y])-1
		elif key == 'home':
			self.x= 0
		elif key == 'end':
			self.x= len(self.data[self.y])-1
		if self.sounds: self.play('click')
		self.speak()

	def script_copyItem(self, gesture):
		if len(self.data[self.y]) < 1: return
		api.copyToClip(self.data[self.y][self.x][0])
		# Translators: Mensaje de elemento copiado
		ui.message(_('Elemento copiado'))
		self.finish('copy')

	def script_viewItem(self, gesture):
		if len(self.data[self.y]) < 1: return
		# Translators: Título de la ventana con el contenido
		ui.browseableMessage(self.data[self.y][self.x][0], _('Contenido'))
		self.finish('open')
		# Translators: Mensaje que avisa que se está mostrando el contenido
		mute(0.1, _('Mostrando el contenido'))

	def script_deleteItem(self, gesture):
		if len(self.data[self.y]) < 1: return
		if self.y == 1:
			index= self.data[0].index(self.data[1][self.x])
			self.data[0][index]= (self.data[1][self.x][0], 0)
			cursor.execute('UPDATE strings SET favorite=0 WHERE string=?', (self.data[0][index][0],))
			connect.commit()
			self.data[1].pop(self.x)
			# Translators: Mensaje de favorito eliminado
			ui.message(_('Eliminado de favoritos'))
			return
		try:
			self.data[1].remove(self.data[0][self.x])
		except ValueError:
			pass
		cursor.execute('DELETE FROM strings WHERE string=?', (self.data[0][self.x][0],))
		connect.commit()
		self.data[0].pop(self.x)
		if self.sounds: self.play('delete')
		if len(self.data[self.y]) < 1:
			ui.message(self.empty)
			return
		if self.x == len(self.data[self.y]): self.x-=1
		self.speak()

	def speak(self):
		if self.number:
			ui.message(f'{self.x+1}; {self.data[self.y][self.x][0]}')
		else:
			ui.message(self.data[self.y][self.x][0])

	def script_pasteItem(self, gesture):
		if len(self.data[self.y]) < 1: return
		api.copyToClip(self.data[self.y][self.x][0])
		self.finish('paste')
		# Translators: Aviso de mensaje pegado
		mute(0.2, _('Pegado'))
		pressKey(0x11)
		pressKey(0x56)
		releaseKey(0x56)
		releaseKey(0x11)

	def script_findItem(self, gesture):
		if len(self.data[self.y]) < 1: return
		self.finish()
		get_search= wx.TextEntryDialog(
			gui.mainFrame,
			# Translators: Etiqueta del campo para ingresar el texto de búsqueda
			_('Escriba la búsqueda y pulse intro'),
			# Translators: Texto del título del buscador
			_('Buscador')
		)
		def callback(result):
			if result == wx.ID_OK:
				self.search_text= get_search.GetValue()
				self.startSearch()
		gui.runScriptModalDialog(get_search, callback)

	def script_searchNextItem(self, gesture):
		if len(self.data[self.y]) < 1: return
		self.startSearch()

	def startSearch(self):
		if self.search_text is None:
			# Translators: Aviso de texto de búsqueda inexistente
			ui.message(_('Sin texto de búsqueda'))
			return

		for i in range(self.x + 1, len(self.data[self.y])):
			if self.search_text.lower() in self.data[self.y][i][0].lower():
				self.x = i
				mute(0.2, f'{self.x + 1}; {self.data[self.y][self.x][0]}')
				self.bindGestures(self.__newGestures)
				return

		for i in range(0, self.x + 1):
			if self.search_text.lower() in self.data[self.y][i][0].lower():
				self.x = i
				mute(0.2, f'{self.x + 1}; {self.data[self.y][self.x][0]}')
				self.bindGestures(self.__newGestures)
				return

		# Translators: Mensaje de aviso para cuando no se encuentran resultados de búsqueda
		mute(0.2, _('Sin resultados'))
		self.bindGestures(self.__newGestures)

	def script_close(self, gesture):
		# Translators: Mensaje de historial cerrado
		mute(0.3, _('Historial cerrado'))
		self.finish()

	def script_historyDelete(self, gesture):
		if self.y == 1 or len(self.data[self.y]) < 1: return
		self.finish()
		self.delete_dialog= Delete(gui.mainFrame, self)
		gui.mainFrame.prePopup()
		self.delete_dialog.Show()

	def script_commandList(self, gesture):
		self.finish()
		# Translators: Texto de ayuda con la lista de comandos
		string= _('''
Flecha arriba; anterior elemento de la lista
Flecha abajo; siguiente elemento de la lista
Inicio; primer elemento de la lista
fin; último elemento de la lista
Flecha derecha; copia el elemento actual al portapapeles y lo desplaza al comienzo de la lista
Flecha izquierda; abre el contenido del elemento actual en una ventana de NVDA
Retroceso; elimina el actual elemento de la lista
v; Pega el contenido del elemento actual en la ventana con el foco
tab; conmuta entre la lista general y la de favoritos
f; conmuta entre el estado favorito y no favorito del elemento
b; activa la ventana para buscar elementos en la lista
f3; avanza a la siguiente coincidencia  del texto buscado
g; activa la ventana para enfocar el elemento por número de órden
e; verbaliza el número de índice del elemento actual, y el número total de la lista
c; verbaliza el número de caracteres excluyendo los espacios, los espacios en blanco, las palabras y las líneas
s; activa el diálogo de configuración del complemento
z; activa el diálogo para la eliminación de elementos de la lista
escape; desactiva la capa de comandos
		''')
		# Translators: Título de la ventana con la lista de comandos
		ui.browseableMessage(string, _('Lista de comandos'))

	def script_indexSearch(self, gesture):
		if len(self.data[self.y]) < 1: return
		self.finish()
		get_search= wx.TextEntryDialog(
			gui.mainFrame,
			# Translators: Etiqueta del campo para ingresar un número
			_('Escriba el número y pulse intro'),
			# Translators: Título de la ventana  con la cantidad de elementos en el historial
			_('Hay {} elementos en el historial'.format(len(self.data[self.y])))
		)
		def callback(result):
			if result == wx.ID_OK:
				index= get_search.GetValue()
				if index.isdigit() and int(index) > 0 and int(index) <= len(self.data):  # Ajuste aquí
					self.x= int(index)-1
					mute(0.5, f'{index}; {self.data[self.y][self.x][0]}')
					self.bindGestures(self.__newGestures)
				else:
					# Translators: Mensaje de aviso para datos incorrectos o número fuera de rango
					mute(0.3, _('Dato incorrecto o fuera de rango'))
		gui.runScriptModalDialog(get_search, callback)

	def script_settings(self, gesture):
		if self.switch:
			self.finish('open')
		self.settings_dialog= Settings(gui.mainFrame, self, self.sounds, self.max_elements, self.number)
		gui.mainFrame.prePopup()
		self.settings_dialog.Show()

	def script_indexAnnounce(self, gesture):
		if len(self.data[self.y]) < 1:
			ui.message(self.empty)
			return
		# Translators: Mensaje de aviso de índice del elemento  total del historial
		msg= _('{} de {}'.format(self.x+1, len(self.data[self.y])))
		if self.y == 0 and self.data[self.y][self.x][1] == 1:
			# Translators: texto favorito
			msg= _('favorito- ') + msg
		ui.message(msg)

	def script_counter(self, gesture):
		if len(self.data[self.y]) < 1: return
		str= self.data[self.y][self.x][0]
		counter_func= lambda x: len(findall(x, str))
		chars= counter_func(r'[^\s]')
		spaces= counter_func(r'[ ^\s]')
		words= counter_func(r'\b\w+')
		lines= len(str.splitlines())
		# Translators: Formateo del mensaje donde se especifica el número de caracteres, espacios en blanco, palabras y líneas
		ui.message(_('{} caracteres, {} espacios, {} palabras, {} líneas'.format(chars, spaces, words, lines)))

	def script_tabs(self, gesture):
		if self.y == 0:
			self.temporary_index_data= self.x
			self.x= self.temporary_index_favorites
			self.y= 1
			# Translators: aviso de pestaña favoritos
			ui.message(_('Favoritos'))
		else:
			self.temporary_index_favorites= self.x
			self.x= self.temporary_index_data
			self.y= 0
			# Translators: aviso de pestaña general
			ui.message(_('General'))

	def script_favorite(self, gesture):
		if self.y == 1 or len(self.data[self.y]) < 1: return
		if self.data[0][self.x][1] == 0:
			self.data[0][self.x]= (self.data[0][self.x][0], 1)
			self.data[1].append(self.data[0][self.x])
			cursor.execute('UPDATE strings SET favorite=1 WHERE string=?', (self.data[0][self.x][0],))
			connect.commit()
			# Translators: Mensaje de marcado como favorito
			ui.message(_('Marcado como favorito'))
		else:
			self.data[1].remove(self.data[0][self.x])
			self.data[0][self.x]= (self.data[0][self.x][0], 0)
			cursor.execute('UPDATE strings SET favorite=0 WHERE string=?', (self.data[0][self.x][0],))
			connect.commit()
			# Translators: Mensaje de no favorito
			ui.message(_('No favorito'))

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
		'kb:b': 'findItem',
		'kb:f': 'favorite',
		'kb:f3': 'searchNextItem',
		'kb:g': 'indexSearch',
		'kb:e': 'indexAnnounce',
		'kb:c': 'counter',
		'kb:tab': 'tabs',
		'kb:s': 'settings',
		'kb:z': 'historyDelete',
		'kb:escape': 'close'}

