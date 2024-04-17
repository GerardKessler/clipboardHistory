﻿# -*- coding: utf-8 -*-
# Copyright (C) 2021 Gerardo Kessler <ReaperYOtrasYerbas@gmail.com>
# This file is covered by the GNU General Public License.
# Código del script clipboard-monitor perteneciente a Héctor Benítez

import ui
import gui
import speech
import wx
from time import sleep
from threading import Thread
from .database import *

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

class Settings(wx.Dialog):
	def __init__(self, parent, sounds, max_elements, number):
		super().__init__(parent, title=_('Configuraciones'))
		
		self.sounds= sounds
		self.max_elements= max_elements
		self.number= number
		
		# Panel principal
		panel = wx.Panel(self)

		# Creación de controles
		max_elements_label = wx.StaticText(panel, label=_('Selecciona el número máximo de cadenas a guardar en la base de datos. 0 indica sin límite:'))
		self.max_elements_listbox = wx.ListBox(panel, choices=['0', '250', '500', '1000', '2000', '5000'])
		self.max_elements_listbox.SetStringSelection(str(self.max_elements))
		self.max_elements_listbox.SetFocus()

		self.sounds_checkbox = wx.CheckBox(panel, label=_('Activar los sonidos del complemento'))
		self.sounds_checkbox.SetValue(self.sounds)

		self.number_checkbox = wx.CheckBox(panel, label=_('Verbalizar el número de índice de los elementos de la lista'))
		self.number_checkbox.SetValue(self.number)

		export_button = wx.Button(panel, label='&Exportar base de datos')
		import_button = wx.Button(panel, label='&Importar base de datos')
		save_button = wx.Button(panel, label='&Guardar cambios')
		cancel_button = wx.Button(panel, label='&Cancelar')

		# Eventos de botones
		save_button.Bind(wx.EVT_BUTTON, self.onSave)
		cancel_button.Bind(wx.EVT_BUTTON, self.onCancel)
		export_button.Bind(wx.EVT_BUTTON, self.onExport)
		import_button.Bind(wx.EVT_BUTTON, self.onImport)
		# Maneja el cierre con la tecla Escape y otras teclas.
		self.Bind(wx.EVT_CHAR_HOOK, self.onKeyPress)

		# Organización con Sizers
		v_sizer = wx.BoxSizer(wx.VERTICAL)
		h_sizer = wx.BoxSizer(wx.HORIZONTAL)

		# Añadir controles al sizer vertical
		v_sizer.Add(max_elements_label, 0, wx.ALL, 10)
		v_sizer.Add(self.max_elements_listbox, 1, wx.EXPAND | wx.ALL, 10)
		v_sizer.Add(self.sounds_checkbox, 0, wx.ALL, 10)
		v_sizer.Add(self.number_checkbox, 0, wx.ALL, 10)

		# Añadir botones al sizer horizontal
		h_sizer.Add(import_button, 0, wx.ALL, 10)
		h_sizer.Add(export_button, 0, wx.ALL, 10)
		h_sizer.Add(save_button, 0, wx.ALL, 10)
		h_sizer.Add(cancel_button, 0, wx.ALL, 10)

		# Añadir el sizer horizontal al vertical
		v_sizer.Add(h_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)

		panel.SetSizer(v_sizer)
		v_sizer.Fit(self)
		self.CenterOnScreen()

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

	def onKeyPress(self, event):
		"""
		Manejador de eventos para teclas presionadas en el diálogo.

		Args:
			event: El evento de teclado.
		"""
		if event.GetKeyCode() == wx.WXK_ESCAPE:
			self.onCancel(None)
		else:
			event.Skip()

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
		gui.mainFrame.postPopup()

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
						mute(0.5, _('{} elementos agregados'.format(len(unique_strings) - len(existing_strings))))
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
			gui.mainFrame.postPopup()

class Delete(wx.Dialog):
	def __init__(self, parent):
		super().__init__(parent, title=_('Eliminar elementos'))
		
		cursor.execute('SELECT id FROM strings')
		self.counter= cursor.fetchall()
		
		# Panel principal del diálogo
		panel = wx.Panel(self)

		# Texto estático que indica la acción
		static_text = wx.StaticText(panel, label=_('Selecciona el número de elementos a eliminar'))

		# Control para seleccionar el número de elementos a eliminar
		self.split_ctrl = wx.SpinCtrl(panel, value=str(len(self.counter)), min=1, max=len(self.counter))
		
		# Botones para eliminar y cancelar
		delete_button = wx.Button(panel, label=_('&Eliminar'))
		cancel_button = wx.Button(panel, label=_('&Cancelar'))

		# Sizer principal en vertical
		main_sizer = wx.BoxSizer(wx.VERTICAL)
		button_sizer = wx.BoxSizer(wx.HORIZONTAL)  # Sizer horizontal para los botones

		# Agrega los elementos al sizer principal
		main_sizer.Add(static_text, 0, wx.ALL, 10)
		main_sizer.Add(self.split_ctrl, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
		button_sizer.Add(delete_button, 1, wx.EXPAND | wx.RIGHT, 5)  # Añade el botón con expansión
		button_sizer.Add(cancel_button, 1, wx.EXPAND | wx.LEFT, 5)   # Añade el botón con expansión
		
		# Agrega el sizer de botones al sizer principal
		main_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)

		# Configura el sizer en el panel y ajusta el tamaño
		panel.SetSizer(main_sizer)
		main_sizer.Fit(self)

		# Vincula eventos de los botones a sus funciones
		delete_button.Bind(wx.EVT_BUTTON, self.onDelete)
		cancel_button.Bind(wx.EVT_BUTTON, self.onCancel)
		# Maneja el cierre con la tecla Escape y otras teclas.
		self.Bind(wx.EVT_CHAR_HOOK, self.onKeyPress)

		self.CenterOnScreen()

	def onDelete(self, event):
		num= self.split_ctrl.GetValue()
		if num == len(self.counter):
			cursor.execute('DELETE FROM strings')
		else:
			cursor.execute('DELETE FROM strings WHERE id IN (SELECT id FROM strings ORDER BY id ASC LIMIT ?)', (num,))
		connect.commit()
		mute(0.3, _('{} elementos eliminados'.format(num)))
		self.Destroy()
		gui.mainFrame.postPopup()

	def onKeyPress(self, event):
		"""
		Manejador de eventos para teclas presionadas en el diálogo.

		Args:
			event: El evento de teclado.
		"""
		if event.GetKeyCode() == wx.WXK_ESCAPE:
			self.onCancel(None)
		else:
			event.Skip()

	def onCancel(self, event):
		self.Destroy()
		gui.mainFrame.postPopup()