Option Explicit

Dim fso, base
Set fso  = CreateObject("Scripting.FileSystemObject")
base = fso.GetParentFolderName(WScript.ScriptFullName)

ClearFolder base & "\src"
ClearFolder base & "\out"

Sub ClearFolder(path)
  On Error Resume Next
  If fso.FolderExists(path) Then
    Dim fld, f, subf
    Set fld = fso.GetFolder(path)
    For Each f In fld.Files
      f.Delete True
    Next
    For Each subf In fld.SubFolders
      subf.Delete True
    Next
  End If
End Sub
