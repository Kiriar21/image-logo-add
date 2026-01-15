' run.vbs
Option Explicit
Dim fso, sh, base, pyPath, args, i
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh  = CreateObject("WScript.Shell")

base = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = base
pyPath = base & "\.venv\Scripts\python.exe"

args = ""
For i = 0 To WScript.Arguments.Count - 1
  args = args & " """ & WScript.Arguments(i) & """"
Next

If Not fso.FileExists(pyPath) Then
  sh.Run "py -m venv .venv", 0, True
End If

If fso.FileExists(pyPath) Then
  If fso.FileExists(base & "\requirements.txt") Then
    sh.Run """" & pyPath & """ -m pip install --upgrade pip", 0, True
    sh.Run """" & pyPath & """ -m pip install -r requirements.txt", 0, True
  End If
  sh.Run """" & pyPath & """ """ & base & "\main.py""" & args, 0, False
Else
  sh.Run "cmd /c py -m pip install --upgrade pip && py -m pip install -r requirements.txt && py ""main.py""" & args, 0, False
End If
