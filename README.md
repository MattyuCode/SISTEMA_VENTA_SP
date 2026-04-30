<img src="imagenes/image.png" alt="">


### Descargar la aplicación INNO SETUP
* https://jrsoftware.org/isdl.php

### INSTALAR PRIMERO PyInstaller 
* https://pyinstaller.org/en/stable/
````bash
pip install -U pyinstaller
````

### Descargar el NODEJS en zip 
* https://nodejs.org/en/download


# build 
```bash 
pyinstaller --onefile --noconsole --icon=imagenes/icono.ico --name SISTEMA_SP --add-data "imagenes;imagenes" main.py
``` 


http://localhost:5001/