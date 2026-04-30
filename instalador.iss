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
Source: "APP_FINAL\iniciar_api.vbs"; DestDir: "{app}"
Source: "APP_FINAL\icono.ico"; DestDir: "{app}"
Source: "APP_FINAL\node\*"; DestDir: "{app}\node"; Flags: recursesubdirs createallsubdirs

; ── API de WhatsApp — EXCLUYENDO carpetas de sesión ─────────────────────────
Source: "APP_FINAL\API_WhatsApp\*"; DestDir: "{app}\API_WhatsApp"; \
    Excludes: ".wwebjs_auth\*,.wwebjs_cache\*,.wwebjs_auth,.wwebjs_cache,*.log"; \
    Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\SISTEMA SP"; Filename: "{sys}\wscript.exe"; Parameters: """{app}\iniciar_api.vbs"""; IconFilename: "{app}\icono.ico"
Name: "{group}\Desinstalar SISTEMA SP"; Filename: "{uninstallexe}"
Name: "{commondesktop}\SISTEMA SP"; Filename: "{sys}\wscript.exe"; Parameters: """{app}\iniciar_api.vbs"""; IconFilename: "{app}\icono.ico"

[UninstallRun]
Filename: "taskkill"; Parameters: "/F /IM node.exe"; Flags: runhidden

[UninstallDelete]
; Borrar carpetas de sesión al desinstalar
Type: filesandordirs; Name: "{app}\API_WhatsApp\.wwebjs_auth"
Type: filesandordirs; Name: "{app}\API_WhatsApp\.wwebjs_cache"
Type: filesandordirs; Name: "{app}\API_WhatsApp\node_modules\.cache"

[Run]
; Abrir el navegador para vincular WhatsApp después de instalar
Filename: "http://localhost:5001"; Description: "Vincular WhatsApp ahora"; Flags: postinstall shellexec skipifsilent unchecked
Filename: "{sys}\wscript.exe"; Parameters: """{app}\iniciar_api.vbs"""; Flags: runhidden

[UninstallRun]
Filename: "taskkill"; Parameters: "/F /IM node.exe"; Flags: runhidden