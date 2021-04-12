**bolsaMadridScraper** permite obtener información detallada sobre las empresas que cotizan en la bolsa de Madrid y sus valores de cotización diarios. Este proyecto ha sido realizado en el contexto de la práctica 1 de las asignatura "Tipología y Ciclo de Vida de los Datos" en el Máster de Ciencia de datos de la UOC.
# Dependencias y requerimientos previos
* Librerías:
* Se debe tener instalado Google Chrome y añadido al path el driver de Google Chrome en el directorio _../res/chromedriver_
# Estructura de carpetas y ficheros
La estructura de carpetas y ficheros dispone de los siguientes elementos:
* **data_scraped (folder)**: contiene los ficheros de salida que genera la solución. En la sección "Output" se explican en detalle.
* **src (folder)**: contiene los ficheros con extensión "py" que contienen el código de la solución. El fichero principal es "main.py"
* **README.md**: fichero README con documentación básica.
* **LICENSE (file)**: fichero que contiene la definición de la licencia de la solución.
* **"TCVD_Practica1.pdf" (file)**: contiene documentación detallada sobre la solución.
# Output
La solución genera 3 ficheros de salida:
* Script std out.txt
* corporation.csv
* market_price.csv

A continuación, se describe el contenido de cada uno de ellos.
## Script std out.txt
Informa del número de registros a analizar en base al número de empresas identificadas en la tabla principal. Si se identifican errores (por ejemplo, por _timeout_), también se detallan.
## corporation.csv
Ofrece la información general sobre las empresas identificadas en un fichero _CSV_ delimitado por "," sin cabeceras, presentando los siguientes campos (en el orden indicado): "isin", "nombre", "sector_subsector", "mercado", "indices"
## market_price.csv
Ofrece la información detallada sobre los valores de cotización en un fichero _CSV_ delimitado por "," sin cabeceras, presentando los siguientes campos (en el orden indicado): "isin", "fecha", "valor_cierre", "valor_referencia", "volumen_titulos_negociados", "efectivo_titulos_negociados", "valor_ultimo", "valor_maximo", "valor_minimo", "valor_medio" 
# Documentación
El documento "TCVD_Practica1.pdf" ofrece documentación detallada sobre la solución: contexto, descripción del conjunto de datos, representación gráfica, contenido, agradecimientos, inspiración y licencia.
