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
Source: "APP_FINAL\API_WhatsApp\*"; DestDir: "{app}\API_WhatsApp"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\SISTEMA SP"; Filename: "{sys}\wscript.exe"; Parameters: """{app}\iniciar_api.vbs"""; IconFilename: "{app}\icono.ico"
Name: "{group}\Desinstalar SISTEMA SP"; Filename: "{uninstallexe}"
Name: "{commondesktop}\SISTEMA SP"; Filename: "{sys}\wscript.exe"; Parameters: """{app}\iniciar_api.vbs"""; IconFilename: "{app}\icono.ico"

[Run]
Filename: "{sys}\wscript.exe"; Parameters: """{app}\iniciar_api.vbs"""; Flags: runhidden

[UninstallRun]
Filename: "taskkill"; Parameters: "/F /IM node.exe"; Flags: runhidden