# -*- coding: utf-8 -*-
# Copyright (C) 2021 Gerardo Kessler <ReaperYOtrasYerbas@gmail.com>
# This file is covered by the GNU General Public License.
# Código del script clipboard-monitor perteneciente a Héctor Benítez

from nvwave import playWaveFile
from keyboardHandler import KeyboardInputGesture
from threading import Thread
from time import sleep
import gui
import wx
import api
import globalPluginHandler
import speech
import core
import globalVars
root_path= globalVars.appArgs.configPath
import ui
from scriptHandler import script
import os
import shutil
from .database import *
from .keyFunc import pressKey, releaseKey
from .clipboard_monitor import ClipboardMonitor
import addonHandler

# Lína de traducción
addonHandler.initTranslation()

# Función para romper la cadena de verbalización y callar al sintetizador durante el tiempo especificado
def mute(time, msg= False):
	if msg:
		ui.message(msg)
		sleep(0.1)
	Thread(target=killSpeak, args=(time,), daemon= True).start()

def killSpeak(time):
	if speech.getState().speechMode != speech.SpeechMode.talk: return
	speech.setSpeechMode(speech.SpeechMode.off)
	sleep(time)
	speech.setSpeechMode(speech.SpeechMode.talk)

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
		playWaveFile(os.path.join(dirAddon, 'sounds', '{}.wav'.format(sound)))

	@script(
		category= 'clipboardHistory',
		# Translators: Descripción del elemento en el diálogo gestos de entrada
		description= _('Activa la capa de comandos. F1 muestra la lista de atajos'),
		gesture= None
	)
	def script_viewData(self, gesture):
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
		self.delete_dialog= Delete(gui.mainFrame)
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
		self.finish()
		self.settings_dialog= Settings(gui.mainFrame, self.sounds, self.max_elements, self.number)
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

class Settings(wx.Dialog):
	def __init__(self, parent, sounds, max_elements, number):
		super().__init__(parent, title=_('Configuraciones'))
		
		self.sounds= sounds
		self.max_elements= max_elements
		self.number= number
		
		# Panel principal
		panel = wx.Panel(self)

		# StaticText y ListBox para seleccionar el número máximo de cadenas
		max_elements_label = wx.StaticText(panel, label=_('Selecciona el número máximo de cadenas a guardar en la base de datos. 0 indica sin límite:'))
		self.max_elements_listbox = wx.ListBox(panel, choices=['0', '250', '500', '1000', '2000', '5000'])
		self.max_elements_listbox.SetStringSelection(str(self.max_elements))
		self.max_elements_listbox.SetFocus()

		# Checkbox para activar los sonidos
		self.sounds_checkbox = wx.CheckBox(panel, label=_('Activar los sonidos del complemento'))
		self.sounds_checkbox.SetValue(self.sounds)

		# Checkbox para activar la numeración de los elementos de la lista
		self.number_checkbox = wx.CheckBox(panel, label=_('Verbalizar el número de índice de los elementos de la lista'))
		self.number_checkbox.SetValue(self.number)

		# Botones Guardar cambios, Cancelar, Exportar base de datos e Importar base de datos
		export_button = wx.Button(panel, label='&Exportar base de datos')
		import_button = wx.Button(panel, label='&Importar base de datos')
		save_button = wx.Button(panel, label='&Guardar cambios')
		cancel_button = wx.Button(panel, label='&Cancelar')

		save_button.Bind(wx.EVT_BUTTON, self.onSave)
		cancel_button.Bind(wx.EVT_BUTTON, self.onCancel)
		export_button.Bind(wx.EVT_BUTTON, self.onExport)
		import_button.Bind(wx.EVT_BUTTON, self.onImport)

		# Sizer para organizar los elementos
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(self.sounds_checkbox, 0, wx.ALL, 10)
		sizer.Add(self.number_checkbox, 0, wx.ALL, 10)
		sizer.Add(max_elements_label, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
		sizer.Add(self.max_elements_listbox, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
		sizer.Add(save_button, 0, wx.ALIGN_RIGHT | wx.RIGHT, 10)
		sizer.Add(cancel_button, 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM, 10)
		sizer.Add(export_button, 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM, 10)
		sizer.Add(import_button, 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM, 10)

		panel.SetSizer(sizer)
		sizer.Fit(self)

	def onSave(self, event):
		sounds = self.sounds_checkbox.GetValue()
		max_elements = int(self.max_elements_listbox.GetStringSelection())
		number = self.number_checkbox.GetValue()
		if sounds == self.sounds and max_elements == self.max_elements and number == self.number:
			mute(0.3, _('Sin cambios en la configuración'))
		else:
			cursor.execute('UPDATE settings SET sounds=?, max_elements=?, number=?', (sounds, max_elements, number))
			connect.commit()
			mute(0.3, _('Cambios guardados correctamente'))
		self.Destroy()
		gui.mainFrame.postPopup()

	def onCancel(self, event):
		self.Destroy()
		gui.mainFrame.postPopup()

	def onExport(self, event):
		export_dialog= wx.FileDialog(self, _('Exportar base de datos'), '', 'clipboard_history', '', wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
		if export_dialog.ShowModal() == wx.ID_CANCEL: return
		file_path= export_dialog.GetPath()
		shutil.copy(os.path.join(root_path, 'clipboard_history'), file_path)
		mute(0.5, _('Base de datos exportada'))
		export_dialog.Destroy()
		self.Destroy()

	def onImport(self, event):
		import_dialog= wx.FileDialog(self, _('Importar base de datos'), '', '', '', wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
		if import_dialog.ShowModal() == wx.ID_OK:
			file_path= import_dialog.GetPath()
			try:
				cn= sql.connect(file_path)
				cr= cn.cursor()
				cr.execute('SELECT string FROM strings')
				imported_strings= cr.fetchall()
				cn.close()
				
				cursor.execute('SELECT string FROM strings')
				existing_strings= cursor.fetchall()
				existing_set= set(existing_strings)
				
				# Filtramos las cadenas importadas para incluir solo las que no están en la base de datos actual
				unique_strings= [s for s in imported_strings if s not in existing_set]
				
				if len(unique_strings) > 0:
					modal = wx.MessageDialog(None, _('Hay {} elementos diferentes en el archivo de respaldo. ¿Quieres añadirlos a la base de datos?'.format(len(unique_strings))), _('Atención'), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
					if modal.ShowModal() == wx.ID_YES:
						unique_strings.extend(existing_strings)
						cursor.execute('DELETE FROM strings')
						cursor.executemany('INSERT INTO strings (string) VALUES (?)', unique_strings)
						connect.commit()
						mute(0.5, _('{} elementos agregados'.format(len(unique_strings))))
				else:
					mute(0.3, _('No hay elementos únicos para agregar'))
			except sql.DatabaseError as e:
				mute(0.4, _('Error al intentar acceder a la base de datos de respaldo. El archivo no es válido o está corrupto'))
			except Exception as e:
				mute(0.4, _('Error inesperado: {}').format(str(e)))
			finally:
				if 'cn' in locals() and cn:
					cn.close()
			self.Destroy()

class Delete(wx.Dialog):
	def __init__(self, parent):
		super().__init__(parent, title=_('Eliminar elementos'))
		
		cursor.execute('SELECT id FROM strings')
		self.counter= cursor.fetchall()
		
		panel= wx.Panel(self)

		static_text= wx.StaticText(panel, label=_('Selecciona el número de elementos a eliminar'))
		self.split_ctrl= wx.SpinCtrl(panel, value=str(len(self.counter)), min=1, max=len(self.counter))
		
		delete_button = wx.Button(panel, label=_('&Eliminar'))
		cancel_button = wx.Button(panel, label=_('&Cancelar'))

		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(static_text, 0, wx.ALL, 10)
		sizer.Add(self.split_ctrl, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
		sizer.Add(delete_button, 0, wx.ALIGN_RIGHT | wx.RIGHT, 10)
		sizer.Add(cancel_button, 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM, 10)

		panel.SetSizer(sizer)
		sizer.Fit(self)

		delete_button.Bind(wx.EVT_BUTTON, self.onDelete)
		cancel_button.Bind(wx.EVT_BUTTON, self.onCancel)

	def onDelete(self, event):
		num= self.split_ctrl.GetValue()
		if num == len(self.counter):
			cursor.execute('DELETE FROM strings')
		else:
			cursor.execute('DELETE FROM strings WHERE id IN (SELECT id FROM strings ORDER BY id ASC LIMIT ?)', (num,))
		connect.commit()
		mute(0.3, _('{} elementos eliminados'.format(num)))
		self.Destroy()


	def onCancel(self, event):
		self.Destroy()
		gui.mainFrame.postPopup()
