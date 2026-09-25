VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "clsAutoLEDEvt"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = False
Public WithEvents Btn As MSForms.CommandButton
Public WithEvents Cbo As MSForms.ComboBox
Public Key As String
Private Sub Btn_Click()
    AutoLEDUI_Click Key
End Sub
Private Sub Cbo_Change()
    AutoLEDUI_Change Key
End Sub
