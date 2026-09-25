Attribute VB_Name = "RaiLED"
'====================================================================
'  MACRO RAI LED TU DONG CHO CORELDRAW (X7 / 2017 / 2018 ... 2024)
'
'  Cach dung nhanh:
'    1. Chon chu (text hoac da convert to curves), co the chon ca group.
'    2. Chay macro "RaiLED".
'    3. LED duoc tao tren layer "LED", moi chu la 1 group rieng.
'
'  Cac macro co trong module:
'    RaiLED   - rai LED vao cac doi tuong dang chon
'    DemLED   - dem so LED (trong vung chon, hoac ca layer LED)
'    XoaLED   - xoa toan bo LED tren layer LED cua trang hien tai
'    CaiDat   - thay doi thong so ma khong rai LED
'
'  LED mau tuy chinh: ve 1 doi tuong bat ky (hinh module, hat LED...),
'  dat ten (Object Manager) la  LED_MAU  -> macro se dung hinh do.
'====================================================================
Option Explicit

Private Const APP_NAME As String = "RaiLED"
Private Const LAYER_NAME As String = "LED"
Private Const SAMPLE_NAME As String = "LED_MAU"
Private Const LED_NAME As String = "LED"
Private Const PI As Double = 3.14159265358979

Private Type LedCfg
    Mode As Long            ' 1 = chay theo net (vien trong), 2 = luoi
    LedType As Long         ' 1 = LED hat (tron), 2 = module (chu nhat)
    LedW As Double          ' duong kinh LED hat / chieu dai module (mm)
    LedH As Double          ' chieu rong module (mm)
    Spacing As Double       ' khoang cach giua 2 LED lien tiep (mm)
    RowSpacing As Double    ' khoang cach giua cac hang / cac vong (mm)
    Margin As Double        ' khoang cach tu mep LED toi mep chu (mm)
    MaxRings As Long        ' so vong toi da (che do 1)
    Watt As Double          ' cong suat 1 LED (W)
    Volt As Double          ' dien ap nguon (V)
End Type

Private cfg As LedCfg
Private curW As Curve                   ' duong cong cua chu dang xu ly
Private sample As Shape                 ' LED mau (neu co)
Private ptsX() As Double, ptsY() As Double, ptsN As Long

'====================================================================
'  MACRO CHINH
'====================================================================
Public Sub RaiLED()
    Dim oldUnit As cdrUnit, sel As ShapeRange, leaves As ShapeRange
    Dim lyr As Layer, total As Long, i As Long, errMsg As String

    If ActiveDocument Is Nothing Then
        MsgBox "Chua mo file CorelDRAW nao.", vbExclamation, APP_NAME
        Exit Sub
    End If
    Set sel = ActiveSelectionRange
    If sel.Count = 0 Then
        MsgBox "Hay chon chu can rai LED truoc khi chay macro.", vbExclamation, APP_NAME
        Exit Sub
    End If

    oldUnit = ActiveDocument.Unit
    ActiveDocument.Unit = cdrMillimeter

    LoadCfg
    If Not AskCfg(True) Then
        ActiveDocument.Unit = oldUnit
        Exit Sub
    End If

    Set leaves = CreateShapeRange
    CollectLeaves sel, leaves
    If leaves.Count = 0 Then
        ActiveDocument.Unit = oldUnit
        MsgBox "Khong tim thay chu / duong cong kin nao trong vung chon.", vbExclamation, APP_NAME
        Exit Sub
    End If

    ActiveDocument.BeginCommandGroup "Rai LED"
    Optimization = True
    EventsEnabled = False
    On Error GoTo Fail

    Set lyr = GetLedLayer()
    Set sample = FindSample()
    If Not sample Is Nothing Then
        cfg.LedW = sample.SizeWidth
        cfg.LedH = sample.SizeHeight
    End If

    For i = 1 To leaves.Count
        total = total + FillShape(leaves(i), lyr)
    Next i

Cleanup:
    On Error Resume Next
    Optimization = False
    EventsEnabled = True
    ActiveDocument.EndCommandGroup
    ActiveDocument.Unit = oldUnit
    Set curW = Nothing
    Set sample = Nothing
    ActiveWindow.Refresh
    Refresh
    On Error GoTo 0

    If errMsg <> "" Then
        MsgBox "Co loi xay ra: " & errMsg & vbCrLf & _
               "Da rai duoc " & total & " LED truoc khi loi.", vbCritical, APP_NAME
    Else
        MsgBox Report(total), vbInformation, APP_NAME
    End If
    Exit Sub

Fail:
    errMsg = Err.Description
    Resume Cleanup
End Sub

'--------------------------------------------------------------------
' Dem LED: trong vung chon (neu co) hoac tren layer LED cua trang
'--------------------------------------------------------------------
Public Sub DemLED()
    Dim n As Long, lyr As Layer
    If ActiveDocument Is Nothing Then Exit Sub
    LoadCfg
    If ActiveSelectionRange.Count > 0 Then
        n = CountLeds(ActiveSelectionRange)
    Else
        Set lyr = FindLayer(LAYER_NAME)
        If Not lyr Is Nothing Then n = CountLeds(lyr.Shapes.All)
    End If
    MsgBox Report(n), vbInformation, APP_NAME
End Sub

'--------------------------------------------------------------------
' Xoa toan bo LED tren layer LED cua trang hien tai
'--------------------------------------------------------------------
Public Sub XoaLED()
    Dim lyr As Layer
    If ActiveDocument Is Nothing Then Exit Sub
    Set lyr = FindLayer(LAYER_NAME)
    If lyr Is Nothing Then
        MsgBox "Trang nay chua co layer LED.", vbInformation, APP_NAME
        Exit Sub
    End If
    If lyr.Shapes.Count = 0 Then Exit Sub
    If MsgBox("Xoa toan bo " & CountLeds(lyr.Shapes.All) & " LED tren layer '" & _
              LAYER_NAME & "'?", vbYesNo + vbQuestion, APP_NAME) <> vbYes Then Exit Sub
    ActiveDocument.BeginCommandGroup "Xoa LED"
    lyr.Shapes.All.Delete
    ActiveDocument.EndCommandGroup
End Sub

'--------------------------------------------------------------------
' Chi thay doi thong so
'--------------------------------------------------------------------
Public Sub CaiDat()
    LoadCfg
    AskCfg False
End Sub

'====================================================================
'  XU LY TUNG CHU
'====================================================================
Private Function FillShape(src As Shape, lyr As Layer) As Long
    Dim work As Shape, isTmp As Boolean, leds As ShapeRange, g As Shape

    If src.Type = cdrCurveShape Then
        Set work = src
    Else
        Set work = src.Duplicate
        work.ConvertToCurves
        isTmp = True
    End If

    If work.Type = cdrCurveShape Then
        If work.Curve.Closed Then
            Set curW = work.Curve
            Set leds = CreateShapeRange
            ptsN = 0
            If cfg.Mode = 1 Then FillContour work, lyr, leds
            ' Che do luoi, hoac net qua manh khong chay vien duoc -> dung luoi
            If leds.Count = 0 Then FillGrid work, lyr, leds
            If leds.Count > 1 Then
                Set g = leds.Group
            ElseIf leds.Count = 1 Then
                Set g = leds(1)
            End If
            If Not g Is Nothing Then g.Name = "LED x" & leds.Count
            FillShape = leds.Count
        End If
    End If

    If isTmp Then work.Delete
End Function

'--------------------------------------------------------------------
' Che do 1: rai LED chay theo net chu (cac vong vien thu vao trong)
'--------------------------------------------------------------------
Private Sub FillContour(work As Shape, lyr As Layer, leds As ShapeRange)
    Dim k As Long, off As Double, rings As ShapeRange, cs As Shape, placed As Long

    For k = 0 To cfg.MaxRings - 1
        off = cfg.Margin + LedHalfAcross() + k * cfg.RowSpacing
        Set rings = MakeInset(work, off)
        If rings Is Nothing Then Exit For
        placed = 0
        For Each cs In rings
            placed = placed + PlaceAlong(cs, lyr, leds)
        Next cs
        rings.Delete
        If placed = 0 Then Exit For
    Next k
End Sub

' Tao duong vien thu vao trong 1 khoang "off" (dung hieu ung Contour)
Private Function MakeInset(work As Shape, off As Double) As ShapeRange
    Dim eff As Effect, sr As ShapeRange, res As ShapeRange, s As Shape

    On Error GoTo Fail
    Set eff = work.CreateContour(cdrContourInside, off, 1)
    Set sr = eff.Separate
    Set res = CreateShapeRange
    For Each s In sr
        If s.StaticID <> work.StaticID Then
            If s.Type = cdrGroupShape Then
                res.AddRange s.UngroupAllEx
            Else
                res.Add s
            End If
        End If
    Next s
    For Each s In res
        If s.Type <> cdrCurveShape Then s.ConvertToCurves
    Next s
    If res.Count = 0 Then Exit Function
    Set MakeInset = res
    Exit Function
Fail:
    Set MakeInset = Nothing
End Function

' Rai LED deu tren tung duong con (subpath) cua duong vien
Private Function PlaceAlong(cs As Shape, lyr As Layer, leds As ShapeRange) As Long
    Dim sp As SubPath, L As Double, n As Long, i As Long
    Dim t As Double, d As Double, px As Double, py As Double
    Dim ax As Double, ay As Double, bx As Double, by As Double
    Dim ang As Double, fm As Double

    If cs.Type <> cdrCurveShape Then Exit Function
    ' Duong vien da cach mep dung khoang Margin, nen cho phep lech nhe
    fm = cfg.Margin * 0.5 - 0.3

    For Each sp In cs.Curve.SubPaths
        L = sp.Length
        If L > 0.5 Then
            n = CLng(L / cfg.Spacing)
            If n < 1 Then n = 1
            d = Min2(1, L / 20)
            For i = 0 To n - 1
                t = (i + 0.5) * L / n
                sp.GetPointPositionAt px, py, t, cdrAbsoluteSegmentOffset
                sp.GetPointPositionAt ax, ay, WrapOff(t - d, L, sp.Closed), cdrAbsoluteSegmentOffset
                sp.GetPointPositionAt bx, by, WrapOff(t + d, L, sp.Closed), cdrAbsoluteSegmentOffset
                ang = Atan2(by - ay, bx - ax) * 180 / PI
                If Fits(px, py, ang, fm) Then
                    If AddLed(lyr, leds, px, py, ang) Then PlaceAlong = PlaceAlong + 1
                End If
            Next i
        End If
    Next sp
End Function

'--------------------------------------------------------------------
' Che do 2: rai LED theo luoi (hang ngang), can giua trong tung doan net
'--------------------------------------------------------------------
Private Sub FillGrid(work As Shape, lyr As Layer, leds As ShapeRange)
    Dim x As Double, y As Double, w As Double, h As Double
    Dim nr As Long, r As Long, y0 As Double, py As Double
    Dim stp As Double, px As Double, runA As Double, inRun As Boolean
    Dim lastOk As Double

    work.GetBoundingBox x, y, w, h
    nr = Int(h / cfg.RowSpacing) + 1
    y0 = y + (h - (nr - 1) * cfg.RowSpacing) / 2
    stp = Max2(0.3, Min2(cfg.LedW, cfg.Spacing) / 4)

    For r = 0 To nr - 1
        py = y0 + r * cfg.RowSpacing
        inRun = False
        px = x
        Do While px <= x + w + stp
            If Fits(px, py, 0, cfg.Margin) Then
                If Not inRun Then runA = px: inRun = True
                lastOk = px
            ElseIf inRun Then
                PlaceRun lyr, leds, runA, lastOk, py
                inRun = False
            End If
            px = px + stp
        Loop
        If inRun Then PlaceRun lyr, leds, runA, lastOk, py
    Next r
End Sub

' Dat LED deu, can giua trong doan [a, b] cua 1 hang
Private Sub PlaceRun(lyr As Layer, leds As ShapeRange, a As Double, b As Double, py As Double)
    Dim k As Long, i As Long, x0 As Double, px As Double
    k = Int((b - a) / cfg.Spacing + 0.0001) + 1
    x0 = (a + b) / 2 - (k - 1) * cfg.Spacing / 2
    For i = 0 To k - 1
        px = x0 + i * cfg.Spacing
        If Fits(px, py, 0, cfg.Margin) Then AddLed lyr, leds, px, py, 0
    Next i
End Sub

'====================================================================
'  KIEM TRA VI TRI & TAO LED
'====================================================================
' LED dat tai (cx, cy), xoay "ang" do, co nam gon trong chu (cach mep m) khong?
Private Function Fits(cx As Double, cy As Double, ang As Double, m As Double) As Boolean
    Dim hw As Double, hh As Double, i As Long, a As Double, r As Double
    Dim c As Double, s As Double, dx As Double, dy As Double
    Dim offX As Variant, offY As Variant

    If Not Inside(cx, cy) Then Exit Function

    If cfg.LedType = 1 And sample Is Nothing Then
        r = cfg.LedW / 2 + m
        If r <= 0 Then Fits = True: Exit Function
        For i = 0 To 7
            a = i * PI / 4
            If Not Inside(cx + r * Cos(a), cy + r * Sin(a)) Then Exit Function
        Next i
    Else
        hw = cfg.LedW / 2 + m
        hh = cfg.LedH / 2 + m
        If hw <= 0 Or hh <= 0 Then Fits = True: Exit Function
        c = Cos(ang * PI / 180): s = Sin(ang * PI / 180)
        offX = Array(-1, -0.5, 0, 0.5, 1, -1, -0.5, 0, 0.5, 1, -1, 1)
        offY = Array(-1, -1, -1, -1, -1, 1, 1, 1, 1, 1, 0, 0)
        For i = 0 To 11
            dx = offX(i) * hw: dy = offY(i) * hh
            If Not Inside(cx + dx * c - dy * s, cy + dx * s + dy * c) Then Exit Function
        Next i
    End If
    Fits = True
End Function

Private Function Inside(x As Double, y As Double) As Boolean
    Inside = (curW.IsOnCurve(x, y, 0.01) = cdrInsideShape)
End Function

' Tao 1 LED; bo qua neu qua sat LED da co (tranh chong cheo)
Private Function AddLed(lyr As Layer, leds As ShapeRange, cx As Double, cy As Double, ByVal ang As Double) As Boolean
    Dim s As Shape, i As Long, minD As Double

    minD = Min2(cfg.Spacing, cfg.RowSpacing) * 0.7
    For i = 0 To ptsN - 1
        If (ptsX(i) - cx) ^ 2 + (ptsY(i) - cy) ^ 2 < minD * minD Then Exit Function
    Next i

    ' Giu goc trong khoang (-90, 90] de module khong bi lat nguoc
    Do While ang > 90: ang = ang - 180: Loop
    Do While ang <= -90: ang = ang + 180: Loop

    If Not sample Is Nothing Then
        Set s = sample.Duplicate
        s.MoveToLayer lyr
        s.SetPositionEx cdrCenter, cx, cy
        If Abs(ang) > 0.01 Then s.Rotate ang
    ElseIf cfg.LedType = 1 Then
        Set s = lyr.CreateEllipse2(cx, cy, cfg.LedW / 2)
        s.Fill.UniformColor.RGBAssign 255, 0, 0
        s.Outline.SetNoOutline
    Else
        Set s = lyr.CreateRectangle2(cx - cfg.LedW / 2, cy - cfg.LedH / 2, cfg.LedW, cfg.LedH)
        If Abs(ang) > 0.01 Then s.Rotate ang
        s.Fill.UniformColor.RGBAssign 0, 112, 192
        s.Outline.SetProperties 0.1
        s.Outline.Color.RGBAssign 0, 0, 0
    End If
    s.Name = LED_NAME
    leds.Add s

    If ptsN = 0 Then
        ReDim ptsX(0 To 255): ReDim ptsY(0 To 255)
    ElseIf ptsN > UBound(ptsX) Then
        ReDim Preserve ptsX(0 To 2 * ptsN): ReDim Preserve ptsY(0 To 2 * ptsN)
    End If
    ptsX(ptsN) = cx: ptsY(ptsN) = cy
    ptsN = ptsN + 1
    AddLed = True
End Function

' Nua be ngang cua LED (vuong goc voi huong chay)
Private Function LedHalfAcross() As Double
    If cfg.LedType = 1 And sample Is Nothing Then
        LedHalfAcross = cfg.LedW / 2
    Else
        LedHalfAcross = cfg.LedH / 2
    End If
End Function

'====================================================================
'  THONG SO
'====================================================================
Private Sub LoadCfg()
    cfg.Mode = CLng(GetSetting(APP_NAME, "Cfg", "Mode", "1"))
    cfg.LedType = CLng(GetSetting(APP_NAME, "Cfg", "LedType", "1"))
    cfg.LedW = Num(GetSetting(APP_NAME, "Cfg", "LedW", "9"))
    cfg.LedH = Num(GetSetting(APP_NAME, "Cfg", "LedH", "9"))
    cfg.Spacing = Num(GetSetting(APP_NAME, "Cfg", "Spacing", "20"))
    cfg.RowSpacing = Num(GetSetting(APP_NAME, "Cfg", "RowSpacing", "20"))
    cfg.Margin = Num(GetSetting(APP_NAME, "Cfg", "Margin", "3"))
    cfg.MaxRings = CLng(GetSetting(APP_NAME, "Cfg", "MaxRings", "10"))
    cfg.Watt = Num(GetSetting(APP_NAME, "Cfg", "Watt", "0.2"))
    cfg.Volt = Num(GetSetting(APP_NAME, "Cfg", "Volt", "5"))
End Sub

Private Sub SaveCfg()
    SaveSetting APP_NAME, "Cfg", "Mode", CStr(cfg.Mode)
    SaveSetting APP_NAME, "Cfg", "LedType", CStr(cfg.LedType)
    SaveSetting APP_NAME, "Cfg", "LedW", Str(cfg.LedW)
    SaveSetting APP_NAME, "Cfg", "LedH", Str(cfg.LedH)
    SaveSetting APP_NAME, "Cfg", "Spacing", Str(cfg.Spacing)
    SaveSetting APP_NAME, "Cfg", "RowSpacing", Str(cfg.RowSpacing)
    SaveSetting APP_NAME, "Cfg", "Margin", Str(cfg.Margin)
    SaveSetting APP_NAME, "Cfg", "MaxRings", CStr(cfg.MaxRings)
    SaveSetting APP_NAME, "Cfg", "Watt", Str(cfg.Watt)
    SaveSetting APP_NAME, "Cfg", "Volt", Str(cfg.Volt)
End Sub

Private Function CfgText() As String
    Dim t As String
    t = "Che do:      " & IIf(cfg.Mode = 1, "1 - Chay theo net chu", "2 - Luoi hang ngang") & vbCrLf
    If cfg.LedType = 1 Then
        t = t & "Loai LED:    1 - LED hat, duong kinh " & cfg.LedW & " mm" & vbCrLf
    Else
        t = t & "Loai LED:    2 - Module " & cfg.LedW & " x " & cfg.LedH & " mm" & vbCrLf
    End If
    t = t & "Khoang cach: " & cfg.Spacing & " mm,  giua hang/vong: " & cfg.RowSpacing & " mm" & vbCrLf
    t = t & "Cach mep:    " & cfg.Margin & " mm" & vbCrLf
    If cfg.Mode = 1 Then t = t & "So vong toi da: " & cfg.MaxRings & vbCrLf
    t = t & "Cong suat:   " & cfg.Watt & " W/LED,  nguon " & cfg.Volt & " V"
    CfgText = t
End Function

' Hoi thong so. Tra ve False neu nguoi dung bam Huy.
Private Function AskCfg(runAfter As Boolean) As Boolean
    Dim r As VbMsgBoxResult, v As Double

    If runAfter Then
        r = MsgBox("Thong so hien tai:" & vbCrLf & vbCrLf & CfgText() & vbCrLf & vbCrLf & _
                   "YES = Rai LED ngay" & vbCrLf & "NO = Thay doi thong so" & vbCrLf & _
                   "CANCEL = Huy", vbYesNoCancel + vbQuestion, APP_NAME)
        If r = vbCancel Then Exit Function
        If r = vbYes Then AskCfg = True: Exit Function
    End If

    v = cfg.Mode
    If Not AskNum("Che do rai LED:" & vbCrLf & _
                  "  1 = Chay theo net chu (vien trong, hop chu mong / chu nhieu net)" & vbCrLf & _
                  "  2 = Luoi hang ngang (hop chu to, mat chu rong)", v) Then Exit Function
    cfg.Mode = IIf(v = 2, 2, 1)

    v = cfg.LedType
    If Not AskNum("Loai LED:" & vbCrLf & "  1 = LED hat (hinh tron)" & vbCrLf & _
                  "  2 = LED module (hinh chu nhat)" & vbCrLf & vbCrLf & _
                  "(Neu trong file co doi tuong ten '" & SAMPLE_NAME & _
                  "' thi macro se dung hinh do lam LED)", v) Then Exit Function
    cfg.LedType = IIf(v = 2, 2, 1)

    If cfg.LedType = 1 Then
        If Not AskNum("Duong kinh LED hat (mm):", cfg.LedW) Then Exit Function
        cfg.LedH = cfg.LedW
    Else
        If Not AskNum("Chieu dai module (mm):", cfg.LedW) Then Exit Function
        If Not AskNum("Chieu rong module (mm):", cfg.LedH) Then Exit Function
    End If

    If Not AskNum("Khoang cach giua 2 LED lien tiep, tinh tu tam (mm):", cfg.Spacing) Then Exit Function
    If Not AskNum("Khoang cach giua cac hang / cac vong (mm):", cfg.RowSpacing) Then Exit Function
    If Not AskNum("Khoang cach tu mep LED toi mep chu (mm):", cfg.Margin) Then Exit Function
    If cfg.Mode = 1 Then
        v = cfg.MaxRings
        If Not AskNum("So vong LED toi da trong moi net chu:", v) Then Exit Function
        cfg.MaxRings = IIf(v < 1, 1, CLng(v))
    End If
    If Not AskNum("Cong suat 1 LED (W):", cfg.Watt) Then Exit Function
    If Not AskNum("Dien ap nguon (V):", cfg.Volt) Then Exit Function

    If cfg.LedW <= 0 Then cfg.LedW = 1
    If cfg.LedH <= 0 Then cfg.LedH = 1
    If cfg.Spacing < 1 Then cfg.Spacing = 1
    If cfg.RowSpacing < 1 Then cfg.RowSpacing = 1
    If cfg.Volt <= 0 Then cfg.Volt = 12

    SaveCfg
    If runAfter Then
        AskCfg = (MsgBox("Thong so moi:" & vbCrLf & vbCrLf & CfgText() & vbCrLf & vbCrLf & _
                         "Rai LED ngay?", vbOKCancel + vbQuestion, APP_NAME) = vbOK)
    Else
        MsgBox "Da luu thong so:" & vbCrLf & vbCrLf & CfgText(), vbInformation, APP_NAME
        AskCfg = True
    End If
End Function

Private Function AskNum(prompt As String, ByRef v As Double) As Boolean
    Dim s As String
    s = InputBox(prompt, APP_NAME, CStr(v))
    If Trim$(s) = "" Then Exit Function
    v = Num(s)
    AskNum = True
End Function

'====================================================================
'  TIEN ICH
'====================================================================
Private Sub CollectLeaves(sr As ShapeRange, out As ShapeRange)
    Dim s As Shape
    For Each s In sr
        If s.Layer.Name <> LAYER_NAME And s.Name <> SAMPLE_NAME Then
            Select Case s.Type
                Case cdrGroupShape
                    CollectLeaves s.Shapes.All, out
                Case cdrCurveShape, cdrTextShape, cdrRectangleShape, _
                     cdrEllipseShape, cdrPolygonShape, cdrPerfectShape
                    out.Add s
            End Select
        End If
    Next s
End Sub

Private Function CountLeds(sr As ShapeRange) As Long
    Dim s As Shape
    For Each s In sr
        If s.Type = cdrGroupShape Then
            CountLeds = CountLeds + CountLeds(s.Shapes.All)
        ElseIf s.Name = LED_NAME Then
            CountLeds = CountLeds + 1
        End If
    Next s
End Function

Private Function Report(n As Long) As String
    Dim w As Double
    w = n * cfg.Watt
    Report = "So LED: " & n & vbCrLf & vbCrLf & _
             "Cong suat: " & n & " x " & cfg.Watt & " W = " & Format(w, "0.0") & " W" & vbCrLf & _
             "Nguon de xuat (du 20%): " & Format(w * 1.2, "0") & " W  (~" & _
             Format(w * 1.2 / cfg.Volt, "0.0") & " A @ " & cfg.Volt & " V)"
End Function

Private Function FindLayer(nm As String) As Layer
    Dim l As Layer
    For Each l In ActivePage.Layers
        If l.Name = nm Then Set FindLayer = l: Exit Function
    Next l
End Function

Private Function GetLedLayer() As Layer
    Dim l As Layer
    Set l = FindLayer(LAYER_NAME)
    If l Is Nothing Then Set l = ActivePage.CreateLayer(LAYER_NAME)
    l.Visible = True
    l.Editable = True
    Set GetLedLayer = l
End Function

Private Function FindSample() As Shape
    On Error Resume Next
    Set FindSample = ActivePage.FindShape(SAMPLE_NAME)
    If FindSample Is Nothing Then Set FindSample = ActiveDocument.MasterPage.FindShape(SAMPLE_NAME)
End Function

Private Function Num(ByVal s As String) As Double
    Num = Val(Replace(Trim$(s), ",", "."))
End Function

Private Function WrapOff(t As Double, L As Double, closed As Boolean) As Double
    If closed Then
        If t < 0 Then t = t + L
        If t > L Then t = t - L
    Else
        If t < 0 Then t = 0
        If t > L Then t = L
    End If
    WrapOff = t
End Function

Private Function Atan2(y As Double, x As Double) As Double
    If x > 0 Then
        Atan2 = Atn(y / x)
    ElseIf x < 0 Then
        If y >= 0 Then Atan2 = Atn(y / x) + PI Else Atan2 = Atn(y / x) - PI
    ElseIf y > 0 Then
        Atan2 = PI / 2
    ElseIf y < 0 Then
        Atan2 = -PI / 2
    End If
End Function

Private Function Min2(a As Double, b As Double) As Double
    If a < b Then Min2 = a Else Min2 = b
End Function

Private Function Max2(a As Double, b As Double) As Double
    If a > b Then Max2 = a Else Max2 = b
End Function
