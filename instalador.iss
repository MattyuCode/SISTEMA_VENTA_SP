[Setup]
AppName=SISTEMA SP
AppVersion=1.0
DefaultDirName={pf}\SISTEMA_SP
DefaultGroupName=SISTEMA SP
OutputDir=.
OutputBaseFilename=Install_SISTEMA_SP
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin
UninstallDisplayIcon={app}\SISTEMA_SP.exe
SetupIconFile=APP_FINAL\icono.ico

[Files]
Source: "APP_FINAL\SISTEMA_SP.exe"; DestDir: "{app}"
Source: "APP_FINAL\icono.ico"; DestDir: "{app}"
Source: "APP_FINAL\node\*"; DestDir: "{app}\node"; Flags: recursesubdirs createallsubdirs

; API WhatsApp completa — excluyendo cache de sesión y daemon viejo
Source: "APP_FINAL\API_WhatsApp\*"; DestDir: "{app}\API_WhatsApp"; \
    Excludes: ".wwebjs_auth\*,.wwebjs_cache\*,.wwebjs_auth,.wwebjs_cache,daemon\*,daemon,*.log"; \
    Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\SISTEMA SP"; Filename: "{app}\SISTEMA_SP.exe"; IconFilename: "{app}\icono.ico"
Name: "{group}\Desinstalar SISTEMA SP"; Filename: "{uninstallexe}"
Name: "{commondesktop}\SISTEMA SP"; Filename: "{app}\SISTEMA_SP.exe"; IconFilename: "{app}\icono.ico"

[Run]
; 1. Instalar el servicio de Windows (silencioso, espera a terminar)
Filename: "{app}\node\node.exe"; \
    Parameters: """{app}\API_WhatsApp\instalar-servicio.js"""; \
    WorkingDir: "{app}\API_WhatsApp"; \
    Flags: runhidden waituntilterminated; \
    StatusMsg: "Instalando servicio de WhatsApp..."

; 2. Esperar 8 segundos para que el servicio termine de iniciar
Filename: "{cmd}"; \
    Parameters: "/c timeout /t 8 /nobreak"; \
    Flags: runhidden waituntilterminated; \
    StatusMsg: "Esperando que el servicio inicie..."

; 3. Abrir navegador para vincular WhatsApp (opcional, marcable)
Filename: "http://localhost:5001"; \
    Description: "Vincular WhatsApp ahora (escanear QR)"; \
    Flags: postinstall shellexec skipifsilent

; 4. Abrir la aplicación al final
Filename: "{app}\SISTEMA_SP.exe"; \
    Description: "Iniciar Sistema SP"; \
    Flags: postinstall nowait skipifsilent unchecked

[UninstallRun]
; 1. Desinstalar el servicio
Filename: "{app}\node\node.exe"; \
    Parameters: """{app}\API_WhatsApp\desinstalar-servicio.js"""; \
    WorkingDir: "{app}\API_WhatsApp"; \
    Flags: runhidden waituntilterminated; \
    RunOnceId: "DesinstalarServicio"

; 2. Matar cualquier proceso de node que quede
Filename: "taskkill"; Parameters: "/F /IM node.exe"; Flags: runhidden; RunOnceId: "MatarNode"

; 3. Esperar 3 segundos
Filename: "{cmd}"; Parameters: "/c timeout /t 3 /nobreak"; Flags: runhidden waituntilterminated; RunOnceId: "Esperar"

[UninstallDelete]
Type: filesandordirs; Name: "{app}\API_WhatsApp\.wwebjs_auth"
Type: filesandordirs; Name: "{app}\API_WhatsApp\.wwebjs_cache"
Type: filesandordirs; Name: "{app}\API_WhatsApp\node_modules\.cache"
Type: filesandordirs; Name: "{app}\API_WhatsApp\daemon"