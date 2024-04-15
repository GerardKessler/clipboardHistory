import globalVars
root_path= globalVars.appArgs.configPath
import os
import sys
dirAddon= os.path.dirname(__file__)
sys.path.append(dirAddon)
sys.path.append(os.path.join(dirAddon, "lib"))
if sys.version.startswith("3.11"):
	sys.path.append(os.path.join(dirAddon, "lib", "_311"))
	from .lib._311 import sqlite3 as sql
	sql.__path__.append(os.path.join(dirAddon, "lib", "_311", "sqlite3"))
else:
	sys.path.append(os.path.join(dirAddon, "lib", "_37"))
	from .lib._37 import sqlite3 as sql
	sql.__path__.append(os.path.join(dirAddon, "lib", "_37", "sqlite3"))
del sys.path[-3:]

if not os.path.exists(os.path.join(root_path, 'clipboard_history')):
	connect= sql.connect(os.path.join(root_path, "clipboard_history"), check_same_thread= False)
	cursor= connect.cursor()
	cursor.execute('CREATE TABLE strings (string TEXT, id INTEGER PRIMARY KEY AUTOINCREMENT)')
	connect.commit()
	cursor.execute('VACUUM')
	connect.commit()
else:
	connect= sql.connect(os.path.join(root_path, 'clipboard_history'), check_same_thread= False)
	cursor= connect.cursor()
