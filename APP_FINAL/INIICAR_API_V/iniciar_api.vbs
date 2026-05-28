Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

ruta = fso.GetParentFolderName(WScript.ScriptFullName)

' Ejecutar API (oculta)
comando = """" & ruta & "\node\node.exe"" """ & ruta & "\API_WhatsApp\app.js"""
WshShell.Run comando, 0, False

' Esperar a que levante
WScript.Sleep 5000

' Abrir sistema
WshShell.Run """" & ruta & "\SISTEMA_SP.exe""", 1, False