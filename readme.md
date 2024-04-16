# Clipboard History

Por  [gera Kessler](http://gera.ar)

Con la inestimable colaboración de Héctor Benítez.

Este complemento permite gestionar un historial del portapapeles alojado en una base de datos local, lo que impide que se pierdan los datos al reiniciar el sistema.
Añade comandos para la exploración del historial, así como funciones de búsqueda y visualización de los elementos.

Al instalarlo por primera vez e iniciar NVDA, se crea el archivo "clipboard_history" que contiene la base de datos. Este archivo se aloja en la raíz de la carpeta nvda en los directorios de la configuración del usuario.
También se crea un escuchador (listener) para capturar los cambios del portapapeles, y actualizar la base de datos cuando haya contenido de texto nuevo.
El historial no guarda duplicaciones para evitar un crecimiento innecesario de la base de datos. al copiar un texto existente, este se copia en la primera posición de la lista eliminando la anterior.

Para utilizar este complemento es necesario asignar un atajo a la función de activación de la capa de comandos en la configuración de los gestos de entrada, apartado clipboardHistory

## Uso

Una vez activa la capa de comandos con el gesto asignado previamente, tenemos los siguientes grupos de comandos. Si se pulsa alguna tecla diferente a las listadas a continuación, se desactiva la capa de comandos y las teclas vuelven a su funcionalidad por defecto.

### Movimiento en la lista

* Flecha arriba; anterior elemento de la lista
* Flecha abajo; siguiente elemento de la lista
* Inicio; primer elemento de la lista
* fin; último elemento de la lista

### Funcionalidades que afectan al elemento enfocado en la lista

* Retroceso; elimina el elemento
* Flecha derecha; copia el texto al portapapeles y lo desplaza al comienzo de la lista
* Flecha izquierda; abre el texto en una ventana de NVDA para su posterior revisión
* v; Pega el texto en la ventana con el foco

### Funciones de búsqueda

* f; activa la ventana para buscar elementos en la lista
* f3; avanza a la siguiente coincidencia  del texto buscado
* g; activa la ventana para enfocar el elemento por número de orden

### Otras funcionalidades

* e; verbaliza el número de índice del elemento actual, y el número total de la lista
* s; activa la ventana de configuración del complemento
z; elimina todo el historial de la base de datos
* escape; desactiva la capa de comandos

## Ventana de configuración

Al pulsar la letra s con la capa de comandos activa se muestra la interfaz de configuración.
En ella puede modificarse lo siguiente:

### Número de cadenas a guardar

Aquí se puede especificar hasta cuantos elementos se van a guardar en la base de datos. Cuando se supere este número, se van eliminando las entradas antiguas desde la última.
Si al configurar un número máximo de elementos la base de datos contiene una cantidad mayor a ese valor, cuando se ingresen nuevos datos se eliminarán las entradas antiguas pero manteniendo el número actual de elementos para que el usuario elimine los innecesarios.

### Sonidos

Activa o desactiva los sonidos del complemento

### Número de índice de los elementos

Si está activa esta casilla, al navegar por la lista de elementos se verbaliza el número de orden de los mismos.

### Exportar base de datos

Este botón activa el diálogo para guardar la base de datos en su estado actual para copia de seguridad de los datos alojados en ella, permitiéndo la posterior importación desde otro NVDA con este complemento.

### Importar base de datos

Esta opción activa un diálogo  para buscar una base de datos exportada previamente para recuperar los elementos inexistentes en la base de datos actual.
