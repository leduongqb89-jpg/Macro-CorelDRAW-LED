Attribute VB_Name = "AutoLEDPro"
'======================================================================
'  AUTOLED PRO - Rai LED tu dong cho CorelDRAW (2018 - 2024)
'  Ban 3 - thuat toan "tu duy nguoi thiet ke" (xem KINH_NGHIEM.md)
'
'  Cai dat:  Alt+F11 > GlobalMacros > Import File > AutoLEDPro.bas
'            Chay macro AutoLED_CaiDat (1 lan) de tao cua so giao dien.
'  Su dung:  Chon chu > chay AutoLED (mo cua so) hoac AutoLED_RaiNhanh.
'
'  File nay duoc sinh tu src/AutoLEDPro.src.bas (chu co dau duoc ma hoa \uXXXX).
'======================================================================
Option Explicit

Public Const APP_NAME As String = "AutoLED Pro"
Private Const REG_APP As String = "AutoLEDPro3"
Private Const LAYER_LED As String = "LED"
Private Const LAYER_WIRE As String = "DAY"
Private Const LAYER_HOLE As String = "LO_CAT"
Private Const SAMPLE_NAME As String = "LED_MAU"
Private Const PI As Double = 3.14159265358979

'----------------------------------------------------------------------
'  KIEU DU LIEU
'----------------------------------------------------------------------
Public Type LedSpec
    Name As String
    Kind As Long            ' 0 = LED tron (hat), 1 = module
    L As Double             ' chieu dai (mm)
    W As Double             ' chieu rong (mm)
    Cn As Long              ' so bong theo chieu dai
    Rn As Long              ' so bong theo chieu rong
    P As Double             ' khoang cach TAM BONG muc tieu (mm)
    Margin As Double        ' cach mep chu (mm)
    MinGap As Double        ' khe toi thieu giua 2 LED (mm)
    Watt As Double          ' cong suat 1 LED (W)
    Price As Double         ' don gia 1 LED
End Type

Public Type LayoutOpts
    Stagger As Long         ' 0 tu dong, 1 thang hang, 2 so le
    FillDark As Boolean     ' lap cho toi (LED tron)
    AutoSym As Boolean      ' tu nhan chu doi xung
    DrawWires As Boolean
    MaxPerWire As Long
    MakeHoles As Boolean
    HoleD As Double
    Volt As Double
End Type

Private Type RunT
    n As Long
    px() As Double: py() As Double
    tx() As Double: ty() As Double
    nx() As Double: ny() As Double
    dp() As Double
    med As Double
    closed As Boolean
    straight As Boolean
    length As Double
End Type

'----------------------------------------------------------------------
'  TRANG THAI BO MAY XEP
'----------------------------------------------------------------------
Private T As LedSpec
Private O As LayoutOpts
Private curW As Curve
Private hl As Double, hw As Double
Private spreadU As Double, spreadV As Double
Private pitchU As Double, pitchV As Double
Private bx0 As Double, by0 As Double, bx1 As Double, by1 As Double
Private rowsY() As Double, nRows As Long
Private axisOn As Boolean, axisX As Double
Private ledN As Long
Private lx() As Double, ly() As Double, lux() As Double, luy() As Double, ltag() As Long
Private nodN As Long, nodX() As Double, nodY() As Double
Private vertN As Long, vertX() As Double
Private colsReady As Boolean, colsN As Long, colsX() As Double
Private knownN As Long, knownX() As Double
Private runs() As RunT, nRuns As Long
Private bU() As Double, bV() As Double, nB As Long      ' vi tri bong trong LED
Private sample As Shape, sampleRot As Double
Private Const STEP_LEN As Double = 2#
Private Const TAG_ROW As Long = 1, TAG_CURVE As Long = 2, TAG_MOD As Long = 3, TAG_FILL As Long = 4

'======================================================================
'  TIEN ICH CHUNG
'======================================================================
' Giai ma chuoi "\uXXXX" -> Unicode (chu tieng Viet co dau tren giao dien)
Public Function U(ByVal s As String) As String
    Dim i As Long, out As String, c As String
    i = 1
    Do While i <= Len(s)
        c = Mid$(s, i, 1)
        If c = "\" And Mid$(s, i + 1, 1) = "u" And i + 5 <= Len(s) Then
            out = out & ChrW(CLng("&H" & Mid$(s, i + 2, 4)))
            i = i + 6
        Else
            out = out & c
            i = i + 1
        End If
    Loop
    U = out
End Function

' Ma hoa Unicode -> "\uXXXX" (luu thu vien LED ra file)
Public Function EncU(ByVal s As String) As String
    Dim i As Long, c As Long, out As String
    For i = 1 To Len(s)
        c = AscW(Mid$(s, i, 1)) And &HFFFF&
        If c > 126 Or c = 92 Or c = 124 Then
            out = out & "\u" & Right$("0000" & Hex$(c), 4)
        Else
            out = out & ChrW(c)
        End If
    Next i
    EncU = out
End Function

Public Function Num(ByVal s As String) As Double
    Num = Val(Replace(Trim$(s), ",", "."))
End Function

Private Function Min2(ByVal a As Double, ByVal b As Double) As Double
    If a < b Then Min2 = a Else Min2 = b
End Function

Private Function Max2(ByVal a As Double, ByVal b As Double) As Double
    If a > b Then Max2 = a Else Max2 = b
End Function

Private Function Atan2(ByVal y As Double, ByVal x As Double) As Double
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

Private Function AngDiffDeg(ByVal a As Double, ByVal b As Double) As Double
    Dim d As Double
    d = a - b
    Do While d > PI: d = d - 2 * PI: Loop
    Do While d < -PI: d = d + 2 * PI: Loop
    AngDiffDeg = Abs(d) * 180 / PI
End Function

Private Function Hyp(ByVal x As Double, ByVal y As Double) As Double
    Hyp = Sqr(x * x + y * y)
End Function

Private Sub SortD(a() As Double, ByVal n As Long)
    ' Shell sort tang dan (phan tu 0..n-1)
    Dim gap As Long, i As Long, j As Long, tmp As Double
    gap = n \ 2
    Do While gap > 0
        For i = gap To n - 1
            tmp = a(i)
            j = i
            Do While j >= gap
                If a(j - gap) <= tmp Then Exit Do
                a(j) = a(j - gap)
                j = j - gap
            Loop
            a(j) = tmp
        Next i
        gap = gap \ 2
    Loop
End Sub

'======================================================================
'  KIEM TRA HINH HOC (chi dung ham co san cua CorelDRAW)
'======================================================================
Private Function InsideP(ByVal x As Double, ByVal y As Double) As Boolean
    InsideP = (curW.IsOnCurve(x, y, 0.01) = cdrInsideShape)
End Function

' Tam LED cach mep it nhat r (xap xi bang 9 diem)
Private Function ClearOf(ByVal x As Double, ByVal y As Double, ByVal r As Double) As Boolean
    Dim k As Long, a As Double
    If Not InsideP(x, y) Then Exit Function
    If r > 0 Then
        For k = 0 To 7
            a = k * PI / 4
            If Not InsideP(x + r * Cos(a), y + r * Sin(a)) Then Exit Function
        Next k
    End If
    ClearOf = True
End Function

Private Function CoreOK(ByVal x As Double, ByVal y As Double) As Boolean
    CoreOK = ClearOf(x, y, T.Margin + Min2(hl, hw) - 0.3)
End Function

' Ca than LED (noi rong them margin) nam trong chu
Private Function FitsLed(ByVal cx As Double, ByVal cy As Double, ByVal ux As Double, ByVal uy As Double) As Boolean
    Dim m As Double, k As Long, a As Double, r As Double
    Dim vx As Double, vy As Double, ex As Double, ey As Double
    Dim sgnA As Variant, sgnB As Variant, i As Long, nseg As Long, f As Double
    Dim x1 As Double, y1 As Double, x2 As Double, y2 As Double, dx As Double, dy As Double
    If Not CoreOK(cx, cy) Then Exit Function
    m = T.Margin - 0.4
    If T.Kind = 0 Then
        r = hl + m
        For k = 0 To 11
            a = k * PI / 6
            If Not InsideP(cx + r * Cos(a), cy + r * Sin(a)) Then Exit Function
        Next k
        FitsLed = True
        Exit Function
    End If
    vx = -uy: vy = ux
    ex = hl + m: ey = hw + m
    sgnA = Array(-1, 1, 1, -1)
    sgnB = Array(-1, -1, 1, 1)
    For i = 0 To 3
        x1 = cx + sgnA(i) * ex * ux + sgnB(i) * ey * vx
        y1 = cy + sgnA(i) * ex * uy + sgnB(i) * ey * vy
        x2 = cx + sgnA((i + 1) Mod 4) * ex * ux + sgnB((i + 1) Mod 4) * ey * vx
        y2 = cy + sgnA((i + 1) Mod 4) * ex * uy + sgnB((i + 1) Mod 4) * ey * vy
        nseg = Int(Hyp(x2 - x1, y2 - y1) / 4) + 1
        For k = 0 To nseg - 1
            f = k / nseg
            If Not InsideP(x1 + (x2 - x1) * f, y1 + (y2 - y1) * f) Then Exit Function
        Next k
    Next i
    ' dinh nhon cua chu khong duoc dam vao LED
    For i = 0 To nodN - 1
        dx = nodX(i) - cx: dy = nodY(i) - cy
        If Abs(dx * ux + dy * uy) < ex And Abs(dx * vx + dy * vy) < ey Then Exit Function
    Next i
    FitsLed = True
End Function

' 2 LED cung kich thuoc cach nhau < clr ? (dinh ly truc tach)
Private Function SatClose(ByVal ax As Double, ByVal ay As Double, ByVal aux As Double, ByVal auy As Double, _
                          ByVal bx As Double, ByVal by As Double, ByVal bux As Double, ByVal buy As Double, _
                          ByVal clr As Double) As Boolean
    Dim dx As Double, dy As Double, r As Double, k As Long
    Dim px As Double, py As Double, ra As Double, rb As Double
    dx = bx - ax: dy = by - ay
    r = 2 * (hl + hw) + clr
    If dx * dx + dy * dy > r * r Then Exit Function
    For k = 0 To 3
        Select Case k
            Case 0: px = aux: py = auy
            Case 1: px = -auy: py = aux
            Case 2: px = bux: py = buy
            Case 3: px = -buy: py = bux
        End Select
        ra = hl * Abs(aux * px + auy * py) + hw * Abs(-auy * px + aux * py)
        rb = hl * Abs(bux * px + buy * py) + hw * Abs(-buy * px + bux * py)
        If Abs(dx * px + dy * py) >= ra + rb + clr - 0.05 Then Exit Function
    Next k
    SatClose = True
End Function

Private Function DotLim() As Double
    DotLim = Max2(T.L + T.MinGap, 0.85 * Min2(T.P, pitchV))
End Function

Private Function FreeLed(ByVal cx As Double, ByVal cy As Double, ByVal ux As Double, ByVal uy As Double) As Boolean
    Dim i As Long, lim2 As Double
    If T.Kind = 0 Then
        lim2 = DotLim() ^ 2
        For i = 0 To ledN - 1
            If (cx - lx(i)) ^ 2 + (cy - ly(i)) ^ 2 < lim2 Then Exit Function
        Next i
    Else
        For i = 0 To ledN - 1
            If SatClose(lx(i), ly(i), lux(i), luy(i), cx, cy, ux, uy, T.MinGap) Then Exit Function
        Next i
    End If
    FreeLed = True
End Function

Private Function SideOK(ByVal cx As Double, ByVal cy As Double, ByVal ux As Double, ByVal uy As Double) As Boolean
    Dim mx As Double
    If Not axisOn Then SideOK = True: Exit Function
    If T.Kind = 0 Then
        SideOK = (cx <= axisX + 0.3 * pitchU)
        Exit Function
    End If
    If Abs(cx - axisX) < 0.000001 Then SideOK = True: Exit Function
    ' K26: module khong duoc vat qua truc doi xung
    mx = cx + hl * Abs(ux) + hw * Abs(uy)
    SideOK = (mx <= axisX - T.MinGap / 2)
End Function

Private Sub SnapLed(cx As Double, cy As Double, ux As Double, uy As Double)
    Dim sn As Double
    If Not axisOn Then Exit Sub
    If T.Kind = 0 Then sn = 0.3 * pitchU Else sn = 0.3 * pitchV
    If Abs(cx - axisX) < sn Then
        cx = axisX
        If Abs(ux) > Abs(uy) Then
            ux = 1: uy = 0
        Else
            ux = 0: uy = 1
        End If
    End If
End Sub

Private Sub PushLed(ByVal cx As Double, ByVal cy As Double, ByVal ux As Double, ByVal uy As Double, ByVal tg As Long)
    If ledN = 0 Then
        ReDim lx(0 To 511): ReDim ly(0 To 511): ReDim lux(0 To 511): ReDim luy(0 To 511): ReDim ltag(0 To 511)
    ElseIf ledN > UBound(lx) Then
        ReDim Preserve lx(0 To 2 * ledN): ReDim Preserve ly(0 To 2 * ledN)
        ReDim Preserve lux(0 To 2 * ledN): ReDim Preserve luy(0 To 2 * ledN)
        ReDim Preserve ltag(0 To 2 * ledN)
    End If
    lx(ledN) = cx: ly(ledN) = cy: lux(ledN) = ux: luy(ledN) = uy: ltag(ledN) = tg
    ledN = ledN + 1
End Sub

Private Function AddLed(ByVal cx As Double, ByVal cy As Double, ByVal ux As Double, ByVal uy As Double, ByVal tg As Long) As Boolean
    Dim k As Long, d As Double, qx As Double, qy As Double, vx As Double, vy As Double
    SnapLed cx, cy, ux, uy
    If Not SideOK(cx, cy, ux, uy) Then Exit Function
    If FitsLed(cx, cy, ux, uy) Then
        If FreeLed(cx, cy, ux, uy) Then
            PushLed cx, cy, ux, uy, tg
            AddLed = True
            Exit Function
        End If
    End If
    ' K28: module tren net cong duoc nhich vao trong vai mm
    If T.Kind = 1 And tg = TAG_CURVE Then
        vx = -uy: vy = ux
        For k = 1 To 8
            d = ((k + 1) \ 2) * IIf(k Mod 2 = 1, 1, -1)
            qx = cx + vx * d: qy = cy + vy * d
            If SideOK(qx, qy, ux, uy) Then
                If FitsLed(qx, qy, ux, uy) Then
                    If FreeLed(qx, qy, ux, uy) Then
                        PushLed qx, qy, ux, uy, tg
                        AddLed = True
                        Exit Function
                    End If
                End If
            End If
        Next k
    End If
End Function

'======================================================================
'  DOAN BIEN (Q2)
'======================================================================
Private Function Depth(ByVal x As Double, ByVal y As Double, ByVal vx As Double, ByVal vy As Double) As Double
    Dim lo As Double, hi As Double, k As Long, md As Double
    lo = 0: hi = 4
    Do While hi < 6000
        If Not InsideP(x + vx * hi, y + vy * hi) Then Exit Do
        lo = hi: hi = hi + 4
    Loop
    For k = 1 To 5
        md = (lo + hi) / 2
        If InsideP(x + vx * md, y + vy * md) Then lo = md Else hi = md
    Next k
    Depth = lo
End Function

Private Sub LoadNodes()
    Dim nd As Node, i As Long
    nodN = curW.Nodes.Count
    If nodN = 0 Then Exit Sub
    ReDim nodX(0 To nodN - 1): ReDim nodY(0 To nodN - 1)
    i = 0
    For Each nd In curW.Nodes
        nodX(i) = nd.PositionX: nodY(i) = nd.PositionY
        i = i + 1
    Next nd
End Sub

Private Sub BuildRuns()
    Dim sp As SubPath, Lt As Double, n As Long, i As Long, k As Long, w As Long
    Dim sx() As Double, sy() As Double, ang() As Double, turn() As Double
    Dim x As Double, y As Double, isCut() As Boolean, cs() As Long, nc As Long
    Dim g As Long, a As Long, b As Long, cnt As Long, rx() As Double, ry() As Double, mx As Double
    nRuns = 0
    ReDim runs(0 To 63)
    For Each sp In curW.SubPaths
        If sp.Closed Then
            Lt = sp.Length
            n = CLng(Lt / STEP_LEN)
            If n < 12 Then n = 12
            ReDim sx(0 To n - 1): ReDim sy(0 To n - 1): ReDim ang(0 To n - 1): ReDim turn(0 To n - 1)
            For i = 0 To n - 1
                sp.GetPointPositionAt x, y, i * Lt / n, cdrAbsoluteSegmentOffset
                sx(i) = x: sy(i) = y
            Next i
            For i = 0 To n - 1
                ang(i) = Atan2(sy((i + 1) Mod n) - sy((i - 1 + n) Mod n), sx((i + 1) Mod n) - sx((i - 1 + n) Mod n))
            Next i
            w = 2
            For i = 0 To n - 1
                turn(i) = AngDiffDeg(ang((i + w) Mod n), ang((i - w + n) Mod n))
            Next i
            ' goc gay: turn > 28 do va la cuc dai dia phuong
            nc = 0
            ReDim cs(0 To n)
            For i = 0 To n - 1
                If turn(i) > 28 Then
                    mx = 0
                    For k = -w To w
                        mx = Max2(mx, turn((i + k + n) Mod n))
                    Next k
                    If turn(i) >= mx Then
                        If nc = 0 Then
                            cs(nc) = i: nc = nc + 1
                        ElseIf i - cs(nc - 1) > 2 * w Then
                            cs(nc) = i: nc = nc + 1
                        End If
                    End If
                End If
            Next i
            If nc > 1 Then
                If cs(0) + n - cs(nc - 1) <= 2 * w Then nc = nc - 1
            End If
            If nc = 0 Then
                AddRun sx, sy, 0, n, n, True
            Else
                For g = 0 To nc - 1
                    a = cs(g)
                    If g + 1 < nc Then b = cs(g + 1) Else b = cs(0) + n
                    cnt = b - a + 1
                    If cnt >= 4 Then AddRun sx, sy, a, cnt, n, False
                Next g
            End If
        End If
    Next sp
End Sub

Private Sub AddRun(sx() As Double, sy() As Double, ByVal a As Long, ByVal cnt As Long, ByVal n As Long, ByVal closed As Boolean)
    Dim i As Long, ia As Long, ib As Long, ux As Double, uy As Double, d As Double
    Dim vx As Double, vy As Double, tmp() As Double, u0x As Double, u0y As Double
    If nRuns > UBound(runs) Then ReDim Preserve runs(0 To 2 * nRuns)
    ReDim runs(nRuns).px(0 To cnt - 1): ReDim runs(nRuns).py(0 To cnt - 1)
    ReDim runs(nRuns).tx(0 To cnt - 1): ReDim runs(nRuns).ty(0 To cnt - 1)
    ReDim runs(nRuns).nx(0 To cnt - 1): ReDim runs(nRuns).ny(0 To cnt - 1)
    ReDim runs(nRuns).dp(0 To cnt - 1)
    With runs(nRuns)
        .n = cnt: .closed = closed
        For i = 0 To cnt - 1
            .px(i) = sx((a + i) Mod n): .py(i) = sy((a + i) Mod n)
        Next i
        .length = 0
        For i = 0 To cnt - 2
            .length = .length + Hyp(.px(i + 1) - .px(i), .py(i + 1) - .py(i))
        Next i
        For i = 0 To cnt - 1
            If closed Then
                ia = (i - 2 + cnt) Mod cnt: ib = (i + 2) Mod cnt
            Else
                ia = i - 2: If ia < 0 Then ia = 0
                ib = i + 2: If ib > cnt - 1 Then ib = cnt - 1
            End If
            ux = .px(ib) - .px(ia): uy = .py(ib) - .py(ia)
            d = Hyp(ux, uy): If d = 0 Then d = 1
            ux = ux / d: uy = uy / d
            vx = -uy: vy = ux
            If Not InsideP(.px(i) + vx * 0.8, .py(i) + vy * 0.8) Then vx = -vx: vy = -vy
            .tx(i) = ux: .ty(i) = uy: .nx(i) = vx: .ny(i) = vy
            .dp(i) = Depth(.px(i), .py(i), vx, vy)
        Next i
        ReDim tmp(0 To cnt - 1)
        For i = 0 To cnt - 1: tmp(i) = .dp(i): Next i
        SortD tmp, cnt
        .med = tmp(Int(cnt * 0.3))           ' be rong that cua net (K: bo qua cho giao net)
        ' net thang: bo qua 3 diem sat goc (K)
        .straight = Not closed
        u0x = .tx(cnt \ 2): u0y = .ty(cnt \ 2)
        If .straight Then
            For i = 3 To cnt - 4
                If u0x * .tx(i) + u0y * .ty(i) < Cos(7 * PI / 180) Then .straight = False: Exit For
            Next i
        End If
    End With
    nRuns = nRuns + 1
End Sub

' Thu tu xu ly: doan thang (dai truoc), roi doan cong (dai truoc)
Private Function RunOrder() As Long()
    Dim idx() As Long, i As Long, j As Long, tt As Long
    ReDim idx(0 To Max2(0, nRuns - 1))
    For i = 0 To nRuns - 1: idx(i) = i: Next i
    For i = 1 To nRuns - 1
        tt = idx(i)
        j = i - 1
        Do While j >= 0
            If RunKey(idx(j)) <= RunKey(tt) Then Exit Do
            idx(j + 1) = idx(j)
            j = j - 1
        Loop
        idx(j + 1) = tt
    Next i
    RunOrder = idx
End Function

Private Function RunKey(ByVal r As Long) As Double
    If runs(r).straight Then RunKey = -runs(r).length Else RunKey = 100000# - runs(r).length
End Function

'======================================================================
'  CHIA RAY (Q3)
'======================================================================
Private Function Tracks(ByVal D As Double, offs() As Double) As Long
    Dim e As Double, avail As Double, n As Long, bestN As Long, p As Double
    Dim err As Double, bestE As Double, minP As Double, k As Long
    If T.Kind = 1 Then e = T.Margin + hw Else e = T.Margin + hl
    avail = D - 2 * e
    If avail < 0 Then Tracks = 0: Exit Function
    If avail < 0.5 * pitchV Then
        ReDim offs(0 To 0): offs(0) = D / 2: Tracks = 1: Exit Function
    End If
    If T.Kind = 1 Then minP = T.W + T.MinGap Else minP = Max2(T.L + T.MinGap, 0.86 * Min2(T.P, pitchV))
    bestN = 0: bestE = 1E+30
    For n = 2 To 80
        p = avail / (n - 1)
        If p < minP Then Exit For
        err = Abs(p - pitchV)
        If err < bestE Then bestE = err: bestN = n
    Next n
    If bestN = 0 Then
        ReDim offs(0 To 0): offs(0) = D / 2: Tracks = 1: Exit Function
    End If
    ReDim offs(0 To bestN - 1)
    For k = 0 To bestN - 1
        offs(k) = e + k * avail / (bestN - 1)
    Next k
    Tracks = bestN
End Function

Private Function UseStagger(ByVal ntr As Long) As Boolean
    If T.Kind = 0 Then Exit Function
    Select Case O.Stagger
        Case 0: UseStagger = (ntr >= 3 And ntr Mod 2 = 1)   ' so le chi khi so cot le
        Case 1: UseStagger = False
        Case Else: UseStagger = True
    End Select
End Function

'======================================================================
'  HANG NGANG CHUNG (Q4, K8, K13, K14)
'======================================================================
Private Sub AnchorRows()
    Dim e As Double, ne As Long, eY() As Double, eS() As Long, r As Long, i As Long, m As Long
    Dim P As Double, minP As Double, tol As Double, p As Double, phi As Double, k As Long
    Dim cost As Double, worst As Double, d As Double, ex As Double
    Dim bestC As Double, bestP As Double, bestPhi As Double, bestW As Double, yb As Double, y As Double
    Dim anc() As Double, na As Long, mg() As Double, nm As Long, a As Double, b As Double, n As Long
    e = T.Margin + hw
    ReDim eY(0 To nRuns + 1): ReDim eS(0 To nRuns + 1)
    eY(0) = by0: eS(0) = 1: eY(1) = by1: eS(1) = -1: ne = 2
    For r = 0 To nRuns - 1
        With runs(r)
            If .straight And .length >= 0.8 * pitchU Then
                m = .n \ 2
                If Abs(.ty(m)) < 0.12 And .med >= 2 * e Then
                    yb = 0
                    For i = 0 To .n - 1: yb = yb + .py(i): Next i
                    eY(ne) = yb / .n
                    If .ny(m) > 0 Then eS(ne) = 1 Else eS(ne) = -1
                    ne = ne + 1
                End If
            End If
        End With
    Next r
    P = pitchV
    minP = Max2(T.L + T.MinGap, 0.78 * T.P)
    tol = 0.18 * P
    bestC = 1E+30
    p = Max2(minP, 0.78 * P)
    Do While p <= 1.22 * P + 0.000000001
        phi = 0
        Do While phi < p
            cost = 0: worst = 0
            For i = 0 To ne - 1
                If eS(i) > 0 Then
                    k = -Int(-((eY(i) + e - 0.3 - phi) / p))
                    d = phi + k * p - eY(i)
                Else
                    k = Int((eY(i) - e + 0.3 - phi) / p)
                    d = eY(i) - (phi + k * p)
                End If
                ex = Max2(0, d - e - tol)
                cost = cost + ex * ex + 0.02 * (d - e)
                worst = Max2(worst, d - e)
            Next i
            cost = cost + 0.5 * (p - P) ^ 2 / P
            If cost < bestC Then bestC = cost: bestP = p: bestPhi = phi: bestW = worst
            phi = phi + 0.25
        Loop
        p = p + 0.25
    Loop
    nRows = 0
    ReDim rowsY(0 To 4095)
    If bestC < 1E+29 And bestW <= tol + 0.5 Then
        pitchU = bestP: pitchV = bestP
        k = Int((by0 - bestPhi) / bestP)
        Do
            y = bestPhi + k * bestP
            If y > by1 - e + 0.5 Then Exit Do
            If y >= by0 + e - 0.5 Then rowsY(nRows) = y: nRows = nRows + 1
            k = k + 1
        Loop
        Exit Sub
    End If
    ' khong co buoc deu: neo tung doan
    ReDim anc(0 To ne - 1)
    na = 0
    For i = 0 To ne - 1
        a = eY(i) + eS(i) * e
        If a >= by0 + e - 1 And a <= by1 - e + 1 Then anc(na) = a: na = na + 1
    Next i
    SortD anc, na
    ReDim mg(0 To na)
    nm = 0
    For i = 0 To na - 1
        If nm > 0 Then
            If anc(i) - mg(nm - 1) < 0.45 * P Then
                mg(nm - 1) = (mg(nm - 1) + anc(i)) / 2
            Else
                mg(nm) = anc(i): nm = nm + 1
            End If
        Else
            mg(nm) = anc(i): nm = nm + 1
        End If
    Next i
    If nm = 0 Then Exit Sub
    rowsY(0) = mg(0): nRows = 1
    For i = 0 To nm - 2
        a = mg(i): b = mg(i + 1)
        n = CLng((b - a) / P): If n < 1 Then n = 1
        Do While n > 1 And (b - a) / n < minP: n = n - 1: Loop
        For k = 1 To n
            rowsY(nRows) = a + k * (b - a) / n: nRows = nRows + 1
        Next k
    Next i
End Sub

'======================================================================
'  COT DOC CHUNG (K4, K7, K9, K16)
'======================================================================
Private Sub ColumnsX()
    Dim xs() As Double, i As Long, g As Long, gs As Double, gc As Long, p As Double
    Dim cx() As Double, nc As Long, df() As Double, nd As Long, a As Double, e As Double, Wd As Double, n As Long, k As Long
    If colsReady Then Exit Sub
    colsReady = True
    knownN = 0: colsN = 0
    If vertN > 0 Then
        ReDim xs(0 To vertN - 1)
        For i = 0 To vertN - 1: xs(i) = vertX(i): Next i
        SortD xs, vertN
        ReDim cx(0 To vertN)
        nc = 0: gs = xs(0): gc = 1
        For i = 1 To vertN
            If i < vertN Then
                If xs(i) - xs(i - 1) < 0.3 * pitchU Then
                    gs = gs + xs(i): gc = gc + 1
                    GoTo NextI
                End If
            End If
            If gc >= 2 Then cx(nc) = gs / gc: nc = nc + 1
            If i < vertN Then gs = xs(i): gc = 1
NextI:
        Next i
        If nc >= 1 Then
            knownN = nc
            ReDim knownX(0 To nc - 1)
            For i = 0 To nc - 1: knownX(i) = cx(i): Next i
        End If
    End If
    ' luoi du phong: chia deu be ngang chu
    e = T.Margin + hl
    Wd = bx1 - bx0 - 2 * e
    n = CLng(Wd / pitchU) + 1: If n < 1 Then n = 1
    colsN = n
    ReDim colsX(0 To n - 1)
    For k = 0 To n - 1
        If n > 1 Then colsX(k) = bx0 + e + k * Wd / (n - 1) Else colsX(k) = bx0 + e + Wd / 2
    Next k
End Sub

' Cot cho 1 net ngang [xa, xb]: noi tiep cot net doc, phan vuon ra chia deu lai
Private Function StrokeColumns(ByVal xa As Double, ByVal xb As Double, out() As Double) As Long
    Dim ins() As Double, ni As Long, i As Long, n As Long, k As Long, cnt As Long
    Dim a As Double, b As Double, span As Double, sp As Double, n1 As Long, n2 As Long, p1 As Double, p2 As Double
    Dim part As Long, mn As Double, mxv As Double
    ColumnsX
    ReDim out(0 To 511)
    cnt = 0
    ni = 0
    If knownN > 0 Then
        ReDim ins(0 To knownN - 1)
        For i = 0 To knownN - 1
            If knownX(i) >= xa - 1 And knownX(i) <= xb + 1 Then ins(ni) = knownX(i): ni = ni + 1
        Next i
    End If
    If ni = 0 Then
        n = CLng((xb - xa) / pitchU) + 1: If n < 1 Then n = 1
        For k = 0 To n - 1
            If n > 1 Then out(cnt) = xa + k * (xb - xa) / (n - 1) Else out(cnt) = (xa + xb) / 2
            cnt = cnt + 1
        Next k
        StrokeColumns = cnt
        Exit Function
    End If
    mn = ins(0): mxv = ins(0)
    For i = 0 To ni - 1
        out(cnt) = ins(i): cnt = cnt + 1
        mn = Min2(mn, ins(i)): mxv = Max2(mxv, ins(i))
    Next i
    For part = 0 To 1
        If part = 0 Then a = mxv: b = xb Else a = xa: b = mn
        span = b - a
        If span > 0.6 * pitchU Then
            If axisOn And a < axisX And b > axisX Then
                ' K9: chia deu toi truc
                sp = axisX - a
                n1 = CLng(sp / pitchU): If n1 < 1 Then n1 = 1
                n2 = CLng(sp / pitchU - 0.5): If n2 < 1 Then n2 = 1
                p1 = sp / n1: p2 = sp / (n2 + 0.5)
                If Abs(p1 - pitchU) <= Abs(p2 - pitchU) Then
                    For k = 1 To n1: out(cnt) = a + k * p1: cnt = cnt + 1: Next k
                Else
                    For k = 1 To n2: out(cnt) = a + k * p2: cnt = cnt + 1: Next k
                    out(cnt) = axisX + p2 / 2: cnt = cnt + 1
                End If
            Else
                n = CLng(span / pitchU): If n < 1 Then n = 1
                If part = 0 Then
                    For k = 1 To n: out(cnt) = a + k * span / n: cnt = cnt + 1: Next k
                Else
                    For k = 0 To n - 1: out(cnt) = a + k * span / n: cnt = cnt + 1: Next k
                End If
            End If
        End If
    Next part
    StrokeColumns = cnt
End Function

'======================================================================
'  NET THANG
'======================================================================
Private Sub StraightRun(ByVal r As Long)
    Dim ux As Double, uy As Double, vx As Double, vy As Double, ax As Double, ay As Double
    Dim D As Double, offs() As Double, nt As Long, sn As Double, ext As Double, midO As Double
    Dim s As Double, sLo As Double, sHi As Double, found As Boolean, k As Long, j As Long, y As Double
    Dim m As Long, vert As Boolean, e As Double, loY As Double, hiY As Double, ib() As Double, nb As Long
    Dim xa As Double, xb As Double, cols() As Double, nc As Long, x As Double
    Dim span As Double, cnt As Long, stp As Double, q As Long
    With runs(r)
        m = .n \ 2
        ux = .tx(m): uy = .ty(m): vx = .nx(m): vy = .ny(m)
        ax = .px(m): ay = .py(m)                  ' K11: goc = diem giua doan
        D = .med
    End With
    nt = Tracks(D, offs)
    If nt = 0 Then Exit Sub
    If T.Kind = 1 Then
        StraightModules r, ax, ay, ux, uy, vx, vy, offs, nt
        Exit Sub
    End If
    sn = Abs(uy)
    ext = D
    midO = offs(nt \ 2)
    ' khuc hop le lien tuc chua diem giua cua ray giua
    If Not SpanOnTrack(ax, ay, ux, uy, vx, vy, midO, runs(r).length / 2 + ext, sLo, sHi) Then Exit Sub
    If sn >= 0.8 Then
        ' Q4/K15: net doc / xien doc -> hang ngang chung
        vert = (sn > 0.985)
        For k = 0 To nt - 1
            For j = 0 To nRows - 1
                y = rowsY(j)
                s = (y - (ay + vy * offs(k))) / uy
                If s >= sLo - pitchU And s <= sHi + pitchU Then
                    If AddLed(ax + ux * s + vx * offs(k), y, ux, uy, TAG_ROW) Then
                        If vert Then PushVert lx(ledN - 1)
                    End If
                End If
            Next j
        Next k
        Exit Sub
    End If
    If sn < 0.3 And Abs(vy) > 0.5 Then
        ' K6: net ngang -> moi hang ngang chung nam lot trong net la 1 ray
        e = T.Margin + hl
        loY = Min2(ay + vy * e, ay + vy * (D - e)) - 0.3 * pitchV
        hiY = Max2(ay + vy * e, ay + vy * (D - e)) + 0.3 * pitchV
        ReDim ib(0 To nRows)
        nb = 0
        For j = 0 To nRows - 1
            If rowsY(j) >= loY And rowsY(j) <= hiY Then ib(nb) = (rowsY(j) - ay) / vy: nb = nb + 1
        Next j
        If nb = 0 Then
            nb = nt
            ReDim ib(0 To nt - 1)
            For k = 0 To nt - 1: ib(k) = offs(k): Next k
        End If
        xa = Min2(ax + ux * sLo, ax + ux * sHi): xb = Max2(ax + ux * sLo, ax + ux * sHi)
        nc = StrokeColumns(xa, xb, cols)
        For k = 0 To nb - 1
            For j = 0 To nc - 1
                x = cols(j)
                If Abs(ux) > 0.000001 Then
                    s = (x - (ax + vx * ib(k))) / ux
                    AddLed x, ay + uy * s + vy * ib(k), ux, uy, TAG_ROW
                End If
            Next j
        Next k
        Exit Sub
    End If
    ' net xien it (< 53 do): luoi vuong goc theo net, chia deu doc net
    span = sHi - sLo
    cnt = CLng(span / pitchU) + 1: If cnt < 1 Then cnt = 1
    Do While cnt > 1 And span / (cnt - 1) < pitchU * 0.85: cnt = cnt - 1: Loop
    If cnt > 1 Then stp = span / (cnt - 1) Else stp = 0
    For k = 0 To nt - 1
        For q = 0 To cnt - 1
            If cnt > 1 Then s = sLo + q * stp Else s = sLo + span / 2
            AddLed ax + ux * s + vx * offs(k), ay + uy * s + vy * offs(k), ux, uy, 0
        Next q
    Next k
End Sub

Private Sub PushVert(ByVal x As Double)
    If vertN = 0 Then ReDim vertX(0 To 255)
    If vertN > UBound(vertX) Then ReDim Preserve vertX(0 To 2 * vertN)
    vertX(vertN) = x: vertN = vertN + 1
End Sub

' Khuc lien tuc (buoc 2mm) tren ray chua s = 0
Private Function SpanOnTrack(ByVal ax As Double, ByVal ay As Double, ByVal ux As Double, ByVal uy As Double, _
                             ByVal vx As Double, ByVal vy As Double, ByVal o As Double, ByVal half As Double, _
                             sLo As Double, sHi As Double) As Boolean
    Dim s As Double, ok As Boolean, bestLo As Double, bestHi As Double, curLo As Double, inRun As Boolean, bestD As Double, d As Double
    bestD = 1E+30
    s = -half
    Do While s <= half + 0.001
        ok = CoreOK(ax + ux * s + vx * o, ay + uy * s + vy * o)
        If ok Then
            If Not inRun Then curLo = s: inRun = True
        End If
        If (Not ok Or s + 2 > half + 0.001) And inRun Then
            Dim hiS As Double
            If ok Then hiS = s Else hiS = s - 2
            If curLo <= 0 And hiS >= 0 Then d = 0 Else d = Min2(Abs(curLo), Abs(hiS))
            If d < bestD Then bestD = d: bestLo = curLo: bestHi = hiS
            inRun = False
        End If
        s = s + 2
    Loop
    If bestD < 1E+29 Then sLo = bestLo: sHi = bestHi: SpanOnTrack = True
End Function

' K27: module doc theo net thang, chia deu trong khuc tu do dai nhat
Private Sub StraightModules(ByVal r As Long, ByVal ax As Double, ByVal ay As Double, ByVal ux As Double, ByVal uy As Double, _
                            ByVal vx As Double, ByVal vy As Double, offs() As Double, ByVal nt As Long)
    Dim sn As Double, slanted As Boolean, midO As Double, ext As Double, s As Double, half As Double
    Dim okArr() As Boolean, ns As Long, i As Long, c As Long, good As Boolean, oo(0 To 2) As Double, q As Long
    Dim gLo As Long, gHi As Long, j As Long, span As Double, cnt As Long, stp As Double, k As Long
    Dim stg As Boolean, cx As Double, cy As Double, u1 As Double, u2 As Double, sLo As Double, anyChk As Boolean
    Dim used() As Boolean, bestLen As Long, bi As Long, bj As Long
    sn = Abs(uy)
    slanted = (sn >= 0.7 And sn <= 0.985)
    midO = offs(nt \ 2)
    ext = runs(r).med
    half = runs(r).length / 2 + ext
    ns = CLng(2 * half / 4) + 1
    ReDim okArr(0 To ns - 1)
    ' K30: chi dung ray giua de tim khuc tu do; ray ben vuong thi chi bo LED do
    oo(0) = midO: oo(1) = offs(0): oo(2) = offs(nt - 1)
    For i = 0 To ns - 1
        s = -half + i * 4
        good = False
        For q = 0 To 2
            ModAt ax, ay, ux, uy, vx, vy, s, oo(q), midO, slanted, cx, cy
            u1 = ux: u2 = uy
            SnapLed cx, cy, u1, u2
            If SideOK(cx, cy, u1, u2) Then
                If FitsLed(cx, cy, u1, u2) Then good = FreeLed(cx, cy, u1, u2)
                Exit For
            End If
        Next q
        okArr(i) = good
    Next i
    stg = UseStagger(nt)
    ReDim used(0 To ns - 1)
    ' cac khuc tu do, dai truoc
    Do
        bestLen = 0
        i = 0
        Do While i < ns
            If okArr(i) And Not used(i) Then
                j = i
                Do While j + 1 < ns
                    If Not (okArr(j + 1) And Not used(j + 1)) Then Exit Do
                    j = j + 1
                Loop
                If j - i + 1 > bestLen Then bestLen = j - i + 1: bi = i: bj = j
                i = j + 1
            Else
                i = i + 1
            End If
        Loop
        If bestLen = 0 Then Exit Do
        For i = bi To bj: used(i) = True: Next i
        sLo = -half + bi * 4
        span = (bj - bi) * 4
        cnt = CLng(span / pitchU) + 1: If cnt < 1 Then cnt = 1
        Do While cnt > 1 And span / (cnt - 1) < T.L + T.MinGap: cnt = cnt - 1: Loop
        If cnt > 1 Then stp = span / (cnt - 1) Else stp = 0
        For k = 0 To nt - 1
            If stg And (k Mod 2 = 1) And cnt > 1 Then
                For c = 0 To cnt - 2
                    s = sLo + c * stp + stp / 2
                    ModAt ax, ay, ux, uy, vx, vy, s, offs(k), midO, slanted, cx, cy
                    AddLed cx, cy, ux, uy, TAG_MOD
                Next c
            Else
                For c = 0 To cnt - 1
                    If cnt > 1 Then s = sLo + c * stp Else s = sLo + span / 2
                    ModAt ax, ay, ux, uy, vx, vy, s, offs(k), midO, slanted, cx, cy
                    AddLed cx, cy, ux, uy, TAG_MOD
                Next c
            End If
        Next k
    Loop
End Sub

Private Sub ModAt(ByVal ax As Double, ByVal ay As Double, ByVal ux As Double, ByVal uy As Double, ByVal vx As Double, ByVal vy As Double, _
                  ByVal s As Double, ByVal o As Double, ByVal midO As Double, ByVal slanted As Boolean, cx As Double, cy As Double)
    ' hang module nam ngang cho net xien 45-85 do
    If slanted Then s = s + (vy * (midO - o)) / uy
    cx = ax + ux * s + vx * o
    cy = ay + uy * s + vy * o
End Sub

'======================================================================
'  NET CONG (Q5, K18, K21-K24)
'======================================================================
Private Sub CurvedRun(ByVal r As Long)
    Dim n As Long, i As Long, j As Long, w As Long, win() As Double, dsm() As Double, cnt() As Long
    Dim cap As Double, minLen As Long, changed As Boolean, offs() As Double, nt As Long
    Dim segA() As Long, segB() As Long, ns As Long, a As Long, b As Long, q As Long, prevC As Long
    Dim wholeLoop As Boolean, allSame As Boolean, k As Long, ntr As Long, idx As Long
    Dim lnX() As Double, lnY() As Double, valid() As Boolean, npt As Long, e0 As Double, oTmp() As Double, oo As Double
    Dim clr2 As Double, allValid As Boolean
    n = runs(r).n
    If n < 4 Then Exit Sub
    ' be rong loc trung vi
    w = 7
    ReDim dsm(0 To n - 1): ReDim win(0 To 2 * w)
    For i = 0 To n - 1
        For j = -w To w
            If runs(r).closed Then
                win(j + w) = runs(r).dp((i + j + n) Mod n)
            Else
                win(j + w) = runs(r).dp(Min2(n - 1, Max2(0, i + j)))
            End If
        Next j
        SortD win, 2 * w + 1
        dsm(i) = Min2(win(w), runs(r).med * 1.35)
    Next i
    ReDim cnt(0 To n - 1)
    For i = 0 To n - 1: cnt(i) = Tracks(dsm(i), offs): Next i
    ' gop doan qua ngan
    minLen = CLng(1.6 * pitchU / STEP_LEN): If minLen < 3 Then minLen = 3
    Do
        changed = False
        i = 0
        Do While i < n
            j = i
            Do While j + 1 < n
                If cnt(j + 1) <> cnt(i) Then Exit Do
                j = j + 1
            Loop
            If j - i + 1 < minLen And Not (i = 0 And j = n - 1) Then
                If i > 0 Then prevC = cnt(i - 1) Else prevC = cnt(Min2(n - 1, j + 1))
                If runs(r).closed And i = 0 Then prevC = cnt(n - 1)
                If prevC <> cnt(i) Then
                    For q = i To j: cnt(q) = prevC: Next q
                    changed = True
                    Exit Do
                End If
            End If
            i = j + 1
        Loop
        If Not changed Then Exit Do
    Loop
    allSame = True
    For i = 1 To n - 1
        If cnt(i) <> cnt(0) Then allSame = False: Exit For
    Next i
    wholeLoop = runs(r).closed And allSame
    ' doan cung so ray
    ReDim segA(0 To n): ReDim segB(0 To n)
    ns = 0: i = 0
    Do While i < n
        j = i
        Do While j + 1 < n
            If cnt(j + 1) <> cnt(i) Then Exit Do
            j = j + 1
        Loop
        segA(ns) = i: segB(ns) = j: ns = ns + 1
        i = j + 1
    Loop
    If runs(r).closed And ns > 1 And cnt(0) = cnt(n - 1) Then
        segA(0) = segA(ns - 1) - n
        ns = ns - 1
    End If
    If T.Kind = 0 Then clr2 = (0.9 * pitchU) ^ 2 Else clr2 = (0.8 * Min2(pitchU, pitchV)) ^ 2
    nt = Tracks(runs(r).med, oTmp)
    If nt > 0 Then e0 = oTmp(0) Else e0 = T.Margin + hw
    For q = 0 To ns - 1
        a = segA(q): b = segB(q)
        ntr = cnt((a + n) Mod n)
        If ntr > 0 Then
            npt = b - a + 1
            ReDim lnX(0 To npt - 1): ReDim lnY(0 To npt - 1): ReDim valid(0 To npt - 1)
            For k = 0 To ntr - 1
                allValid = True
                For j = 0 To npt - 1
                    idx = (a + j + n) Mod n
                    If Tracks(dsm(idx), offs) = ntr Then
                        oo = offs(k)
                    ElseIf ntr > 1 Then
                        oo = e0 + k * (dsm(idx) - 2 * e0) / (ntr - 1)
                    Else
                        oo = dsm(idx) / 2
                    End If
                    lnX(j) = runs(r).px(idx) + runs(r).nx(idx) * oo
                    lnY(j) = runs(r).py(idx) + runs(r).ny(idx) * oo
                    valid(j) = False
                    If CoreOK(lnX(j), lnY(j)) Then valid(j) = PtFree(lnX(j), lnY(j), clr2)
                    If Not valid(j) Then allValid = False
                Next j
                PlacePieces lnX, lnY, valid, npt, wholeLoop And allValid
            Next k
        End If
    Next q
End Sub

Private Function PtFree(ByVal x As Double, ByVal y As Double, ByVal clr2 As Double) As Boolean
    Dim i As Long
    For i = 0 To ledN - 1
        If (x - lx(i)) ^ 2 + (y - ly(i)) ^ 2 < clr2 Then Exit Function
    Next i
    PtFree = True
End Function

Private Sub PlacePieces(lnX() As Double, lnY() As Double, valid() As Boolean, ByVal npt As Long, ByVal isLoop As Boolean)
    Dim i As Long, a As Long, px() As Double, py() As Double, m As Long, k As Long
    If isLoop Then
        PlaceOnPolyline lnX, lnY, npt, True
        Exit Sub
    End If
    i = 0
    Do While i < npt
        If valid(i) Then
            a = i
            Do While i + 1 < npt
                If Not valid(i + 1) Then Exit Do
                i = i + 1
            Loop
            m = i - a + 1
            If m >= 2 Then
                ReDim px(0 To m - 1): ReDim py(0 To m - 1)
                For k = 0 To m - 1: px(k) = lnX(a + k): py(k) = lnY(a + k): Next k
                PlaceOnPolyline px, py, m, False
            End If
        End If
        i = i + 1
    Loop
End Sub

Private Sub PlaceOnPolyline(px() As Double, py() As Double, ByVal m As Long, ByVal isLoop As Boolean)
    Dim acc() As Double, i As Long, Lp As Double, e As Double, usable As Double, cnt As Long, q As Long
    Dim s As Double, cx As Double, cy As Double, ax As Double, ay As Double, bx As Double, by As Double
    Dim ux As Double, uy As Double, d As Double, top As Long, bestV As Double, v As Double
    Dim qx() As Double, qy() As Double, mm As Long
    ' K22: vong kin bat dau tu diem tren truc (chu doi xung) / diem cao nhat
    mm = m
    ReDim qx(0 To m): ReDim qy(0 To m)
    If isLoop Then
        bestV = -1E+30: top = 0
        For i = 0 To m - 1
            If axisOn Then v = py(i) - 50 * Abs(px(i) - axisX) Else v = py(i)
            If v > bestV Then bestV = v: top = i
        Next i
        For i = 0 To m - 1
            qx(i) = px((top + i) Mod m): qy(i) = py((top + i) Mod m)
        Next i
        If axisOn Then qx(0) = axisX
        qx(m) = qx(0): qy(m) = qy(0)
        mm = m + 1
    Else
        For i = 0 To m - 1: qx(i) = px(i): qy(i) = py(i): Next i
    End If
    ReDim acc(0 To mm - 1)
    acc(0) = 0
    For i = 1 To mm - 1
        acc(i) = acc(i - 1) + Hyp(qx(i) - qx(i - 1), qy(i) - qy(i - 1))
    Next i
    Lp = acc(mm - 1)
    If T.Kind = 1 Then e = hl - hw Else e = 0
    If isLoop Then
        cnt = CLng(Lp / pitchU): If cnt < 1 Then cnt = 1
    Else
        usable = Lp - 2 * e
        If usable < 0 Then usable = 0: e = Lp / 2
        cnt = CLng(usable / pitchU) + 1: If cnt < 1 Then cnt = 1
    End If
    For q = 0 To cnt - 1
        If isLoop Then
            s = q * Lp / cnt
        ElseIf cnt > 1 Then
            s = e + q * usable / (cnt - 1)
        Else
            s = e + usable / 2
        End If
        If T.Kind = 1 Then
            PolyAt qx, qy, acc, mm, Max2(0, s - hl), ax, ay
            PolyAt qx, qy, acc, mm, Min2(Lp, s + hl), bx, by
            cx = (ax + bx) / 2: cy = (ay + by) / 2
        Else
            PolyAt qx, qy, acc, mm, s, cx, cy
            PolyAt qx, qy, acc, mm, Max2(0, s - 1), ax, ay
            PolyAt qx, qy, acc, mm, Min2(Lp, s + 1), bx, by
        End If
        ux = bx - ax: uy = by - ay
        d = Hyp(ux, uy): If d = 0 Then d = 1
        AddLed cx, cy, ux / d, uy / d, TAG_CURVE
    Next q
End Sub

Private Sub PolyAt(qx() As Double, qy() As Double, acc() As Double, ByVal mm As Long, ByVal s As Double, x As Double, y As Double)
    Dim lo As Long, hi As Long, md As Long, f As Double, seg As Double
    lo = 0: hi = mm - 1
    Do While hi - lo > 1
        md = (lo + hi) \ 2
        If acc(md) <= s Then lo = md Else hi = md
    Loop
    seg = acc(hi) - acc(lo): If seg = 0 Then seg = 1
    f = (s - acc(lo)) / seg
    x = qx(lo) + (qx(hi) - qx(lo)) * f
    y = qy(lo) + (qy(hi) - qy(lo)) * f
End Sub

'======================================================================
'  LAP CHO TOI (Q8, K10) - chi LED tron
'======================================================================
Private Sub FillDark(ByVal thr As Double)
    Dim g As Double, x As Double, y As Double, n As Long, gx() As Double, gy() As Double, dd() As Double
    Dim tried() As Boolean, i As Long, j As Long, it As Long, best As Long, bestD As Double, rc As Double
    Dim d As Double, a As Long, ux As Double, uy As Double, nearI As Long, nd As Double
    g = Max2(3, T.P / 4)
    rc = T.Margin + Min2(hl, hw)
    ReDim gx(0 To 20000): ReDim gy(0 To 20000)
    y = by0 + rc
    Do While y <= by1 - rc
        x = bx0 + rc
        Do While x <= bx1 - rc
            If Not axisOn Or x <= axisX + 0.01 Then
                If ClearOf(x, y, rc) Then
                    If n > UBound(gx) Then ReDim Preserve gx(0 To 2 * n): ReDim Preserve gy(0 To 2 * n)
                    gx(n) = x: gy(n) = y: n = n + 1
                End If
            End If
            x = x + g
        Loop
        y = y + g
        DoEvents
    Loop
    If n = 0 Then Exit Sub
    ReDim dd(0 To n - 1): ReDim tried(0 To n - 1)
    For i = 0 To n - 1
        dd(i) = 1E+30
        For j = 0 To ledN - 1
            d = (gx(i) - lx(j)) ^ 2 + (gy(i) - ly(j)) ^ 2
            If d < dd(i) Then dd(i) = d
        Next j
    Next i
    For it = 1 To 400
        best = -1: bestD = (thr * T.P) ^ 2
        For i = 0 To n - 1
            If Not tried(i) And dd(i) > bestD Then bestD = dd(i): best = i
        Next i
        If best < 0 Then Exit For
        tried(best) = True
        ux = 1: uy = 0: nd = 1E+30
        For j = 0 To ledN - 1
            d = (gx(best) - lx(j)) ^ 2 + (gy(best) - ly(j)) ^ 2
            If d < nd Then nd = d: ux = lux(j): uy = luy(j)
        Next j
        If AddLed(gx(best), gy(best), ux, uy, TAG_FILL) Then
            For i = 0 To n - 1
                d = (gx(i) - lx(ledN - 1)) ^ 2 + (gy(i) - ly(ledN - 1)) ^ 2
                If d < dd(i) Then dd(i) = d
            Next i
        End If
    Next it
End Sub

'======================================================================
'  CHINH HANG SAU CUNG (K17, K20) - LED tron thuoc luoi hang
'======================================================================
Private Sub SmoothRows()
    Dim p As Double, i As Long, j As Long, k As Long, idx() As Long, nr As Long, y As Double
    Dim used() As Boolean, row() As Long, rn As Long, tmp As Long, g0 As Long, g1 As Long
    Dim gaps() As Double, bad() As Boolean, a As Long, b As Long, xa As Double, xb As Double, n As Long
    Dim keep() As Boolean, okMid As Boolean, f As Double, q As Long, st As Long
    Dim nxN As Long, nxX() As Double, nxY() As Double, nxU() As Double, nxV() As Double
    p = pitchU
    ReDim used(0 To Max2(0, ledN - 1)): ReDim keep(0 To Max2(0, ledN - 1))
    For i = 0 To ledN - 1: keep(i) = True: Next i
    ReDim nxX(0 To 1023): ReDim nxY(0 To 1023): ReDim nxU(0 To 1023): ReDim nxV(0 To 1023)
    ReDim row(0 To Max2(0, ledN - 1))
    For i = 0 To ledN - 1
        If ltag(i) = TAG_ROW And Not used(i) Then
            y = ly(i): rn = 0
            For j = 0 To ledN - 1
                If ltag(j) = TAG_ROW And Not used(j) Then
                    If Abs(ly(j) - y) < 0.5 Then row(rn) = j: rn = rn + 1: used(j) = True
                End If
            Next j
            ' sap theo x
            For j = 1 To rn - 1
                tmp = row(j): k = j - 1
                Do While k >= 0
                    If lx(row(k)) <= lx(tmp) Then Exit Do
                    row(k + 1) = row(k): k = k - 1
                Loop
                row(k + 1) = tmp
            Next j
            ' tach nhom lien tuc trong chu
            g0 = 0
            For j = 1 To rn
                okMid = False
                If j < rn Then
                    If lx(row(j)) - lx(row(j - 1)) < 2.2 * p Then
                        okMid = True
                        For q = 1 To 3
                            f = q / 4
                            If Not InsideP(lx(row(j - 1)) + (lx(row(j)) - lx(row(j - 1))) * f, y) Then okMid = False
                        Next q
                    End If
                End If
                If Not okMid Then
                    g1 = j - 1
                    If g1 - g0 + 1 >= 3 Then
                        st = g0
                        Do While st < g1
                            Dim d0 As Double
                            d0 = lx(row(st + 1)) - lx(row(st))
                            If d0 >= 0.84 * p And d0 <= 1.2 * p Then
                                st = st + 1
                            Else
                                a = st: b = st + 1
                                Do While b < g1
                                    d0 = lx(row(b + 1)) - lx(row(b))
                                    If d0 >= 0.84 * p And d0 <= 1.2 * p Then Exit Do
                                    b = b + 1
                                Loop
                                xa = lx(row(a)): xb = lx(row(b))
                                n = CLng((xb - xa) / p): If n < 1 Then n = 1
                                Do While n > 1 And (xb - xa) / n < 0.84 * p: n = n - 1: Loop
                                For k = a + 1 To b - 1: keep(row(k)) = False: Next k
                                For k = 1 To n - 1
                                    If nxN > UBound(nxX) Then
                                        ReDim Preserve nxX(0 To 2 * nxN): ReDim Preserve nxY(0 To 2 * nxN)
                                        ReDim Preserve nxU(0 To 2 * nxN): ReDim Preserve nxV(0 To 2 * nxN)
                                    End If
                                    nxX(nxN) = xa + k * (xb - xa) / n: nxY(nxN) = y
                                    nxU(nxN) = lux(row(a)): nxV(nxN) = luy(row(a))
                                    nxN = nxN + 1
                                Next k
                                st = b
                            End If
                        Loop
                    End If
                    g0 = j
                End If
            Next j
        End If
    Next i
    ' xay lai danh sach
    Dim ox() As Double, oy() As Double, ou() As Double, ov() As Double, ot() As Long, nOut As Long
    ReDim ox(0 To ledN + nxN): ReDim oy(0 To ledN + nxN): ReDim ou(0 To ledN + nxN): ReDim ov(0 To ledN + nxN): ReDim ot(0 To ledN + nxN)
    For i = 0 To ledN - 1
        If keep(i) Then ox(nOut) = lx(i): oy(nOut) = ly(i): ou(nOut) = lux(i): ov(nOut) = luy(i): ot(nOut) = ltag(i): nOut = nOut + 1
    Next i
    ledN = 0
    For i = 0 To nOut - 1: PushLed ox(i), oy(i), ou(i), ov(i), ot(i): Next i
    For i = 0 To nxN - 1
        If FitsLed(nxX(i), nxY(i), nxU(i), nxV(i)) Then
            If FreeLed(nxX(i), nxY(i), nxU(i), nxV(i)) Then PushLed nxX(i), nxY(i), nxU(i), nxV(i), TAG_ROW
        End If
    Next i
End Sub

'======================================================================
'  DOI XUNG (Q6)
'======================================================================
Private Function DetectAxis(ax As Double) As Boolean
    Dim gx As Long, gy As Long, i As Long, j As Long, c As Long, x As Double, y As Double
    Dim cand As Double, inter As Long, uni As Long, a As Boolean, b As Boolean, best As Double, bestA As Double, iou As Double
    Const NG As Long = 44
    best = 0
    For c = -6 To 6
        cand = (bx0 + bx1) / 2 + c * 0.005 * (bx1 - bx0)
        inter = 0: uni = 0
        For i = 0 To NG - 1
            x = bx0 + (i + 0.5) * (bx1 - bx0) / NG
            For j = 0 To NG - 1
                y = by0 + (j + 0.5) * (by1 - by0) / NG
                a = InsideP(x, y)
                b = InsideP(2 * cand - x, y)
                If a And b Then inter = inter + 1
                If a Or b Then uni = uni + 1
            Next j
        Next i
        If uni > 0 Then
            iou = inter / uni
            If iou > best Then best = iou: bestA = cand
        End If
    Next c
    If best >= 0.985 Then ax = bestA: DetectAxis = True
End Function

Private Sub MirrorLeds()
    Dim i As Long, n0 As Long
    n0 = ledN
    For i = 0 To n0 - 1
        If lx(i) < axisX - 0.01 Then PushLed 2 * axisX - lx(i), ly(i), -lux(i), luy(i), ltag(i)
    Next i
End Sub

'======================================================================
'  CHAY BO MAY CHO 1 HINH  ->  so LED (ket qua nam trong lx/ly/lux/luy)
'======================================================================
Private Sub PrepareSpec()
    Dim i As Long, j As Long, mnU As Double, mxU As Double, mnV As Double, mxV As Double
    hl = T.L / 2: hw = T.W / 2
    If T.Kind = 0 Then hw = hl: T.W = T.L: T.Cn = 1: T.Rn = 1
    If T.Cn < 1 Then T.Cn = 1
    If T.Rn < 1 Then T.Rn = 1
    nB = T.Cn * T.Rn
    ReDim bU(0 To nB - 1): ReDim bV(0 To nB - 1)
    For i = 0 To T.Cn - 1
        For j = 0 To T.Rn - 1
            bU(i * T.Rn + j) = -T.L / 2 + (i + 0.5) * T.L / T.Cn
            bV(i * T.Rn + j) = -T.W / 2 + (j + 0.5) * T.W / T.Rn
        Next j
    Next i
    mnU = 1E+30: mxU = -1E+30: mnV = 1E+30: mxV = -1E+30
    For i = 0 To nB - 1
        mnU = Min2(mnU, bU(i)): mxU = Max2(mxU, bU(i)): mnV = Min2(mnV, bV(i)): mxV = Max2(mxV, bV(i))
    Next i
    spreadU = mxU - mnU: spreadV = mxV - mnV
    If T.Kind = 0 Then
        pitchU = Max2(T.L + T.MinGap, T.P): pitchV = pitchU
    Else
        pitchU = Max2(T.L + T.MinGap, spreadU + T.P)       ' Q1: bong qua khe ~ P
        pitchV = Max2(T.W + T.MinGap, spreadV + T.P)
    End If
End Sub

Public Function LayoutShape(ByVal shp As Shape, spec As LedSpec, opts As LayoutOpts) As Long
    Dim ord() As Long, i As Long, r As Long, x As Double, y As Double, w As Double, h As Double
    T = spec: O = opts
    Set curW = shp.Curve
    PrepareSpec
    ledN = 0: vertN = 0: colsReady = False: knownN = 0
    shp.GetBoundingBox x, y, w, h
    bx0 = x: by0 = y: bx1 = x + w: by1 = y + h
    LoadNodes
    axisOn = False
    If O.AutoSym Then axisOn = DetectAxis(axisX)
    BuildRuns
    If T.Kind = 0 Then
        AnchorRows
    Else
        nRows = 0
    End If
    ord = RunOrder()
    For i = 0 To nRuns - 1
        r = ord(i)
        If runs(r).length >= 1.2 * pitchU Or runs(r).closed Then
            If Not (runs(r).straight And runs(r).med > 1.5 * runs(r).length) Then   ' K5: mep dau net
                If runs(r).straight Then StraightRun r Else CurvedRun r
            End If
        End If
        DoEvents
    Next i
    If O.FillDark And T.Kind = 0 Then FillDark 1.2
    If axisOn Then MirrorLeds
    If T.Kind = 0 Then SmoothRows
    LayoutShape = ledN
End Function

' Lay ket qua cho module khac (tao hinh, di day)
Public Function LedCount() As Long
    LedCount = ledN
End Function

Public Sub GetLed(ByVal i As Long, cx As Double, cy As Double, ux As Double, uy As Double)
    cx = lx(i): cy = ly(i): ux = lux(i): uy = luy(i)
End Sub

Public Function CurInside(ByVal x As Double, ByVal y As Double) As Boolean
    CurInside = InsideP(x, y)
End Function

Public Function CurPitch() As Double
    CurPitch = pitchU
End Function

'######################################################################
'  PHAN 2 - TAO HINH TRONG COREL, DI DAY, THU VIEN, GIAO DIEN
'######################################################################
Public gForm As Object
Public gReport As String
Private libN As Long, lib() As LedSpec

'----------------------------------------------------------------------
'  MACRO CHINH (goi tu Tools > Macros hoac nut tren thanh cong cu)
'----------------------------------------------------------------------
Public Sub AutoLED()
    On Error GoTo NoForm
    If gForm Is Nothing Then Set gForm = VBA.UserForms.Add("frmAutoLED")
    gForm.Show vbModeless
    Exit Sub
NoForm:
    Set gForm = Nothing
    MsgBox "Chua co cua so giao dien. Hay chay macro AutoLED_CaiDat mot lan truoc." & vbCrLf & _
           "(Hoac dung AutoLED_RaiNhanh de rai voi thong so da luu.)", vbExclamation, APP_NAME
End Sub

' Rai voi thong so da luu, khong can cua so
Public Sub AutoLED_RaiNhanh()
    Dim s As LedSpec, o2 As LayoutOpts
    LoadLibrary
    LoadUI s, o2
    MsgBox Replace(RunLayout(s, o2), "|", vbCrLf), vbInformation, APP_NAME
End Sub

Public Sub AutoLED_XoaLED()
    Dim nm As Variant, lyr As Layer, n As Long
    If ActiveDocument Is Nothing Then Exit Sub
    ActiveDocument.BeginCommandGroup "Xoa LED"
    For Each nm In Array(LAYER_LED, LAYER_WIRE, LAYER_HOLE)
        Set lyr = FindLayer(CStr(nm))
        If Not lyr Is Nothing Then n = n + lyr.Shapes.Count: lyr.Shapes.All.Delete
    Next nm
    ActiveDocument.EndCommandGroup
    gReport = "Da xoa " & n & " doi tuong tren cac layer LED / DAY / LO_CAT."
End Sub

Public Function AutoLED_Dem() As String
    Dim lyr As Layer, n As Long, s As LedSpec, o2 As LayoutOpts
    LoadLibrary
    LoadUI s, o2
    Set lyr = FindLayer(LAYER_LED)
    If Not lyr Is Nothing Then n = CountNamed(lyr.Shapes.All, "LED")
    AutoLED_Dem = ReportText(n, 0, s, o2)
End Function

Public Sub AutoLED_DemLED()
    MsgBox Replace(AutoLED_Dem(), "|", vbCrLf), vbInformation, APP_NAME
End Sub

'----------------------------------------------------------------------
'  CHAY TREN VUNG CHON
'----------------------------------------------------------------------
Public Function RunLayout(spec As LedSpec, opts As LayoutOpts) As String
    Dim sel As ShapeRange, leaves As ShapeRange, oldUnit As cdrUnit, i As Long
    Dim lyrL As Layer, lyrW As Layer, lyrH As Layer, total As Long, wires As Long, errMsg As String
    Dim t0 As Single
    If ActiveDocument Is Nothing Then RunLayout = "Chua mo file CorelDRAW nao.": Exit Function
    Set sel = ActiveSelectionRange
    If sel.Count = 0 Then RunLayout = "Hay chon chu can rai LED truoc.": Exit Function
    oldUnit = ActiveDocument.Unit
    ActiveDocument.Unit = cdrMillimeter
    Set leaves = CreateShapeRange
    CollectLeaves sel, leaves
    If leaves.Count = 0 Then
        ActiveDocument.Unit = oldUnit
        RunLayout = "Khong tim thay chu / duong cong kin trong vung chon."
        Exit Function
    End If
    t0 = Timer
    ActiveDocument.BeginCommandGroup "AutoLED Pro"
    Optimization = True
    EventsEnabled = False
    On Error GoTo Fail
    Set lyrL = GetLayer(LAYER_LED)
    If opts.DrawWires Then Set lyrW = GetLayer(LAYER_WIRE)
    If opts.MakeHoles And spec.Kind = 0 Then Set lyrH = GetLayer(LAYER_HOLE)
    Set sample = FindSample()
    If Not sample Is Nothing Then
        spec.L = Max2(sample.SizeWidth, sample.SizeHeight)
        spec.W = Min2(sample.SizeWidth, sample.SizeHeight)
        If sample.SizeHeight > sample.SizeWidth Then sampleRot = -90 Else sampleRot = 0
    End If
    For i = 1 To leaves.Count
        Status "Dang xep chu " & i & " / " & leaves.Count & " ..."
        total = total + DoOneShape(leaves(i), spec, opts, lyrL, lyrW, lyrH, wires)
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
        RunLayout = "LOI: " & errMsg & "|Da xep duoc " & total & " LED truoc khi loi."
    Else
        RunLayout = ReportText(total, wires, spec, opts) & "|Thoi gian: " & Format(Timer - t0, "0.0") & " giay"
    End If
    Exit Function
Fail:
    errMsg = Err.Description
    Resume Cleanup
End Function

Private Function DoOneShape(src As Shape, spec As LedSpec, opts As LayoutOpts, lyrL As Layer, lyrW As Layer, _
                            lyrH As Layer, wires As Long) As Long
    Dim work As Shape, isTmp As Boolean, n As Long, grp As ShapeRange, i As Long
    If src.Type = cdrCurveShape Then
        Set work = src
    Else
        Set work = src.Duplicate
        work.ConvertToCurves
        isTmp = True
    End If
    If work.Type = cdrCurveShape Then
        If work.Curve.Closed Then
            n = LayoutShape(work, spec, opts)
            If n > 0 Then
                Set grp = DrawLeds(lyrL)
                If grp.Count > 1 Then grp.Group.Name = "LED x " & n Else grp(1).Name = "LED"
                If Not lyrH Is Nothing Then DrawHoles lyrH, opts.HoleD
                If Not lyrW Is Nothing Then wires = wires + DrawWiring(lyrW, opts.MaxPerWire)
            End If
        End If
    End If
    If isTmp Then work.Delete
    DoOneShape = n
End Function

'----------------------------------------------------------------------
'  VE LED, LO CAT
'----------------------------------------------------------------------
Private Function DrawLeds(lyr As Layer) As ShapeRange
    Dim sr As ShapeRange, i As Long, s As Shape, ang As Double
    Set sr = CreateShapeRange
    For i = 0 To ledN - 1
        ang = Atan2(luy(i), lux(i)) * 180 / PI
        Do While ang > 90: ang = ang - 180: Loop
        Do While ang <= -90: ang = ang + 180: Loop
        If Not sample Is Nothing Then
            Set s = sample.Duplicate
            s.MoveToLayer lyr
            s.SetPositionEx cdrCenter, lx(i), ly(i)
            If Abs(ang + sampleRot) > 0.01 Then s.Rotate ang + sampleRot
        ElseIf T.Kind = 0 Then
            Set s = lyr.CreateEllipse2(lx(i), ly(i), hl)
            s.Fill.UniformColor.RGBAssign 230, 30, 30
            s.Outline.SetNoOutline
        Else
            Set s = lyr.CreateRectangle2(lx(i) - hl, ly(i) - hw, T.L, T.W)
            If Abs(ang) > 0.01 Then s.Rotate ang
            s.Fill.UniformColor.RGBAssign 60, 150, 240
            s.Outline.SetProperties 0.15
            s.Outline.Color.RGBAssign 0, 40, 110
        End If
        s.Name = "LED"
        sr.Add s
    Next i
    Set DrawLeds = sr
End Function

Private Sub DrawHoles(lyr As Layer, ByVal d As Double)
    Dim i As Long, s As Shape, sr As ShapeRange
    Set sr = CreateShapeRange
    If d <= 0 Then d = T.L
    For i = 0 To ledN - 1
        Set s = lyr.CreateEllipse2(lx(i), ly(i), d / 2)
        s.Fill.ApplyNoFill
        s.Outline.SetProperties 0.1
        s.Outline.Color.RGBAssign 0, 0, 0
        s.Name = "LO"
        sr.Add s
    Next i
    If sr.Count > 1 Then sr.Group.Name = "LO CAT x " & sr.Count
End Sub

'----------------------------------------------------------------------
'  DI DAY (D1 - D4, K29)
'----------------------------------------------------------------------
Private Sub LedEnds(ByVal i As Long, ax As Double, ay As Double, bx As Double, by As Double)
    If T.Kind = 0 Then
        ax = lx(i): ay = ly(i): bx = ax: by = ay
    Else
        ax = lx(i) - lux(i) * hl: ay = ly(i) - luy(i) * hl
        bx = lx(i) + lux(i) * hl: by = ly(i) + luy(i) * hl
    End If
End Sub

Private Function SegOut(ByVal ax As Double, ByVal ay As Double, ByVal bx As Double, ByVal by As Double) As Double
    Dim k As Long, bad As Long
    For k = 1 To 7
        If Not InsideP(ax + (bx - ax) * k / 8, ay + (by - ay) * k / 8) Then bad = bad + 1
    Next k
    SegOut = bad / 7
End Function

Private Function DrawWiring(lyr As Layer, ByVal maxPer As Long) As Long
    Dim n As Long, i As Long, j As Long, stp As Double, dx As Double, dy As Double, d As Double, c As Double
    Dim cw() As Double, ca() As Long, cb() As Long, nc As Long, nxt() As Long, prv() As Long, k As Long
    Dim chS() As Long, chE() As Long, nch As Long, used() As Boolean, ord() As Long, rev() As Boolean, no As Long
    Dim curX As Double, curY As Double, best As Double, bi As Long, br As Boolean, px As Double, py As Double
    Dim seq() As Long, ns As Long, wireStart() As Long, nw As Long, target As Double, cnt As Long
    Dim feedX As Double, feedY As Double, a As Long, b As Long, tmpD As Double, tmpA As Long, tmpB As Long
    n = ledN
    If n = 0 Then Exit Function
    If maxPer < 1 Then maxPer = 20
    stp = pitchU
    ' D1: noi LED theo huong truc -> chuoi
    ReDim cw(0 To 8 * n): ReDim ca(0 To 8 * n): ReDim cb(0 To 8 * n)
    For i = 0 To n - 1
        For j = 0 To n - 1
            If i <> j Then
                dx = lx(j) - lx(i): dy = ly(j) - ly(i)
                If Abs(dx) < 1.7 * stp And Abs(dy) < 1.7 * stp Then
                    d = Hyp(dx, dy)
                    If d > 0.000001 And d <= 1.7 * stp Then
                        c = (dx * lux(i) + dy * luy(i)) / d
                        If c >= Cos(30 * PI / 180) Then
                            If T.Kind = 0 Or Abs(lux(i) * lux(j) + luy(i) * luy(j)) >= Cos(35 * PI / 180) Then
                                If nc > UBound(cw) Then
                                    ReDim Preserve cw(0 To 2 * nc): ReDim Preserve ca(0 To 2 * nc): ReDim Preserve cb(0 To 2 * nc)
                                End If
                                cw(nc) = d * (2 - c): ca(nc) = i: cb(nc) = j: nc = nc + 1
                            End If
                        End If
                    End If
                End If
            End If
        Next j
    Next i
    ' sap canh theo trong so (shell sort)
    Dim gp As Long
    gp = nc \ 2
    Do While gp > 0
        For i = gp To nc - 1
            tmpD = cw(i): tmpA = ca(i): tmpB = cb(i): j = i
            Do While j >= gp
                If cw(j - gp) <= tmpD Then Exit Do
                cw(j) = cw(j - gp): ca(j) = ca(j - gp): cb(j) = cb(j - gp)
                j = j - gp
            Loop
            cw(j) = tmpD: ca(j) = tmpA: cb(j) = tmpB
        Next i
        gp = gp \ 2
    Loop
    ReDim nxt(0 To n - 1): ReDim prv(0 To n - 1)
    For i = 0 To n - 1: nxt(i) = -1: prv(i) = -1: Next i
    For i = 0 To nc - 1
        a = ca(i): b = cb(i)
        If nxt(a) = -1 And prv(b) = -1 Then
            k = b
            Do While nxt(k) <> -1: k = nxt(k): Loop
            If k <> a Then nxt(a) = b: prv(b) = a
        End If
    Next i
    ReDim chS(0 To n - 1): ReDim chE(0 To n - 1)
    nch = 0
    For i = 0 To n - 1
        If prv(i) = -1 Then
            k = i
            Do While nxt(k) <> -1: k = nxt(k): Loop
            chS(nch) = i: chE(nch) = k: nch = nch + 1
        End If
    Next i
    ' D2: thu tu chuoi tu diem nguon (goc duoi trai)
    best = 1E+30
    For i = 0 To n - 1
        If ly(i) + 0.5 * lx(i) < best Then best = ly(i) + 0.5 * lx(i): curX = lx(i): curY = ly(i)
    Next i
    ReDim used(0 To nch - 1): ReDim ord(0 To nch - 1): ReDim rev(0 To nch - 1)
    For no = 0 To nch - 1
        best = 1E+30
        For i = 0 To nch - 1
            If Not used(i) Then
                For k = 0 To 1
                    If k = 0 Then j = chS(i) Else j = chE(i)
                    d = Hyp(lx(j) - curX, ly(j) - curY) * (1 + 20 * SegOut(curX, curY, lx(j), ly(j)))
                    If d < best Then best = d: bi = i: br = (k = 1)
                Next k
            End If
        Next i
        used(bi) = True: ord(no) = bi: rev(no) = br
        If br Then j = chS(bi) Else j = chE(bi)
        curX = lx(j): curY = ly(j)
    Next no
    ' trai phang thanh day LED
    ReDim seq(0 To n - 1): ReDim wireStart(0 To n)
    ns = 0
    Dim chainStart() As Long
    ReDim chainStart(0 To nch)
    For no = 0 To nch - 1
        chainStart(no) = ns
        If rev(no) Then
            k = chE(ord(no))
            Do
                seq(ns) = k: ns = ns + 1
                If k = chS(ord(no)) Then Exit Do
                k = prv(k)
            Loop
        Else
            k = chS(ord(no))
            Do
                seq(ns) = k: ns = ns + 1
                If nxt(k) = -1 Then Exit Do
                k = nxt(k)
            Loop
        End If
    Next no
    chainStart(nch) = ns
    ' D3 + K29: chia day can bang, cat o dau chuoi; noi qua xa / ra ngoai -> day moi
    nw = -Int(-(ns / maxPer)): If nw < 1 Then nw = 1
    target = ns / nw
    Dim wN As Long
    wireStart(0) = 0: wN = 1: cnt = 0
    For no = 0 To nch - 1
        a = chainStart(no): b = chainStart(no + 1)
        If cnt > 0 Then
            Dim farJ As Boolean
            farJ = Hyp(lx(seq(a)) - lx(seq(a - 1)), ly(seq(a)) - ly(seq(a - 1))) > 3 * stp
            If Not farJ Then farJ = SegOut(lx(seq(a - 1)), ly(seq(a - 1)), lx(seq(a)), ly(seq(a))) > 0
            If farJ Or (cnt + (b - a) > target * 1.12 And wN < nw) Then
                wireStart(wN) = a: wN = wN + 1: cnt = 0
            End If
        End If
        For k = a To b - 1
            If cnt >= maxPer Then wireStart(wN) = k: wN = wN + 1: cnt = 0
            cnt = cnt + 1
        Next k
    Next no
    wireStart(wN) = ns
    ' D4: ve day + nguon chung
    feedX = (bx0 + bx1) / 2: feedY = by0 - 40
    Dim psu As Shape, tx As Shape, sr As ShapeRange, wi As Long, crv As Curve, spth As SubPath
    Dim ax As Double, ay As Double, bxx As Double, byy As Double, px0 As Double, py0 As Double
    Dim inX As Double, inY As Double, outX As Double, outY As Double, first As Boolean, col As Long
    Set sr = CreateShapeRange
    Set psu = lyr.CreateRectangle2(feedX - 20, feedY - 10, 40, 20)
    psu.Fill.UniformColor.RGBAssign 40, 40, 40
    psu.Name = "NGUON"
    sr.Add psu
    For wi = 0 To wN - 1
        a = wireStart(wi): b = wireStart(wi + 1)
        If b > a Then
            Set crv = CreateCurve(ActiveDocument)
            first = True
            For k = a To b - 1
                LedEnds seq(k), ax, ay, bxx, byy
                If first Then
                    If k + 1 < b Then
                        If Hyp(bxx - lx(seq(k + 1)), byy - ly(seq(k + 1))) <= Hyp(ax - lx(seq(k + 1)), ay - ly(seq(k + 1))) Then
                            inX = ax: inY = ay: outX = bxx: outY = byy
                        Else
                            inX = bxx: inY = byy: outX = ax: outY = ay
                        End If
                    Else
                        inX = ax: inY = ay: outX = bxx: outY = byy
                    End If
                    Set spth = crv.CreateSubPath(inX, inY)
                    px0 = inX: py0 = inY
                    first = False
                Else
                    If Hyp(ax - px0, ay - py0) <= Hyp(bxx - px0, byy - py0) Then
                        inX = ax: inY = ay: outX = bxx: outY = byy
                    Else
                        inX = bxx: inY = byy: outX = ax: outY = ay
                    End If
                    spth.AppendLineSegment inX, inY
                End If
                If Hyp(outX - inX, outY - inY) > 0.01 Then spth.AppendLineSegment outX, outY
                px0 = outX: py0 = outY
            Next k
            col = wi Mod 6
            Dim wsh As Shape
            Set wsh = lyr.CreateCurve(crv)
            wsh.Outline.SetProperties 0.5
            WireColor wsh, col
            wsh.Name = "DAY " & (wi + 1) & " (" & (b - a) & " LED)"
            sr.Add wsh
            ' day cap nguon toi dau vao
            LedEnds seq(a), ax, ay, bxx, byy
            Set wsh = lyr.CreateLineSegment(feedX, feedY + 10, spth.StartNode.PositionX, spth.StartNode.PositionY)
            wsh.Outline.SetProperties 0.25
            WireColor wsh, col
            sr.Add wsh
            Set tx = lyr.CreateArtisticText(spth.StartNode.PositionX + 2, spth.StartNode.PositionY + 2, "IN" & (wi + 1), , , "Arial", Max2(6, stp * 0.35 * 2.835))
            WireColor tx, col, True
            sr.Add tx
        End If
    Next wi
    If sr.Count > 1 Then sr.Group.Name = "DAY x " & wN
    DrawWiring = wN
End Function

Private Sub WireColor(s As Shape, ByVal k As Long, Optional ByVal asFill As Boolean = False)
    Dim r As Long, g As Long, b As Long
    Select Case k
        Case 0: r = 228: g = 26: b = 28
        Case 1: r = 255: g = 127: b = 0
        Case 2: r = 44: g = 160: b = 44
        Case 3: r = 148: g = 103: b = 189
        Case 4: r = 140: g = 86: b = 75
        Case Else: r = 227: g = 119: b = 194
    End Select
    If asFill Then
        s.Fill.UniformColor.RGBAssign r, g, b
    Else
        s.Outline.Color.RGBAssign r, g, b
    End If
End Sub

'----------------------------------------------------------------------
'  TIEN ICH COREL
'----------------------------------------------------------------------
Private Sub CollectLeaves(sr As ShapeRange, out As ShapeRange)
    Dim s As Shape, ln As String
    For Each s In sr
        ln = s.Layer.Name
        If ln <> LAYER_LED And ln <> LAYER_WIRE And ln <> LAYER_HOLE And s.Name <> SAMPLE_NAME Then
            Select Case s.Type
                Case cdrGroupShape
                    CollectLeaves s.Shapes.All, out
                Case cdrCurveShape, cdrTextShape, cdrRectangleShape, cdrEllipseShape, cdrPolygonShape, cdrPerfectShape
                    out.Add s
            End Select
        End If
    Next s
End Sub

Private Function CountNamed(sr As ShapeRange, ByVal nm As String) As Long
    Dim s As Shape
    For Each s In sr
        If s.Type = cdrGroupShape Then
            CountNamed = CountNamed + CountNamed(s.Shapes.All, nm)
        ElseIf s.Name = nm Then
            CountNamed = CountNamed + 1
        End If
    Next s
End Function

Private Function FindLayer(ByVal nm As String) As Layer
    Dim l As Layer
    For Each l In ActivePage.Layers
        If l.Name = nm Then Set FindLayer = l: Exit Function
    Next l
End Function

Private Function GetLayer(ByVal nm As String) As Layer
    Dim l As Layer
    Set l = FindLayer(nm)
    If l Is Nothing Then Set l = ActivePage.CreateLayer(nm)
    l.Visible = True
    l.Editable = True
    Set GetLayer = l
End Function

Private Function FindSample() As Shape
    On Error Resume Next
    Set FindSample = ActivePage.FindShape(SAMPLE_NAME)
End Function

Private Function ReportText(ByVal n As Long, ByVal wires As Long, s As LedSpec, o2 As LayoutOpts) As String
    Dim w As Double, v As Double
    w = n * s.Watt
    v = o2.Volt: If v <= 0 Then v = 12
    ReportText = "So LED: " & n & "  (" & s.Name & ")" & _
                 "|Cong suat: " & Format(w, "0.0") & " W   -   Nguon de xuat (du 20%): " & Format(w * 1.2, "0") & " W (~" & Format(w * 1.2 / v, "0.0") & " A @ " & v & " V)" & _
                 "|Thanh tien LED: " & Format(n * s.Price, "#,##0") & _
                 IIf(wires > 0, "|So day noi: " & wires, "")
End Function

Private Sub Status(ByVal s As String)
    On Error Resume Next
    If Not gForm Is Nothing Then gForm.Controls("lblStatus").Caption = s: DoEvents
End Sub

'----------------------------------------------------------------------
'  THU VIEN LED (luu file, ten co dau ma hoa \uXXXX)
'----------------------------------------------------------------------
Private Function LibPath() As String
    Dim d As String
    d = Environ$("APPDATA") & "\AutoLEDPro"
    On Error Resume Next
    If Dir(d, vbDirectory) = "" Then MkDir d
    LibPath = d & "\thu_vien_led.txt"
End Function

Private Sub AddLib(ByVal nm As String, ByVal kind As Long, ByVal L As Double, ByVal W As Double, ByVal cn As Long, ByVal rn As Long, _
                   ByVal P As Double, ByVal m As Double, ByVal gap As Double, ByVal watt As Double, ByVal price As Double)
    If libN = 0 Then ReDim lib(0 To 63)
    If libN > UBound(lib) Then ReDim Preserve lib(0 To 2 * libN)
    With lib(libN)
        .Name = nm: .Kind = kind: .L = L: .W = W: .Cn = cn: .Rn = rn
        .P = P: .Margin = m: .MinGap = gap: .Watt = watt: .Price = price
    End With
    libN = libN + 1
End Sub

Public Sub LoadLibrary()
    Dim f As Integer, ln As String, a() As String, p As String
    libN = 0
    p = LibPath()
    If Dir(p) <> "" Then
        f = FreeFile
        Open p For Input As #f
        Do While Not EOF(f)
            Line Input #f, ln
            a = Split(ln, "|")
            If UBound(a) >= 10 Then
                AddLib U(a(0)), CLng(Num(a(1))), Num(a(2)), Num(a(3)), CLng(Num(a(4))), CLng(Num(a(5))), _
                       Num(a(6)), Num(a(7)), Num(a(8)), Num(a(9)), Num(a(10))
            End If
        Loop
        Close #f
    End If
    If libN = 0 Then
        ' thu vien mac dinh (sua lai theo LED cua xuong)
        AddLib U("LED tròn F9"), 0, 9, 9, 1, 1, 25, 6, 5, 0.2, 500
        AddLib U("LED tròn F12"), 0, 12, 12, 1, 1, 30, 8, 5, 0.3, 800
        AddLib U("Module 15x65 (3 bóng)"), 1, 65, 15, 3, 1, 35, 10, 5, 0.72, 3000
        AddLib U("Module 12x45 (2 bóng)"), 1, 45, 12, 2, 1, 30, 8, 5, 0.48, 2000
        AddLib U("Module vuông 35x35 (4 bóng)"), 1, 35, 35, 2, 2, 35, 8, 5, 1, 5000
        SaveLibrary
    End If
End Sub

Public Sub SaveLibrary()
    Dim f As Integer, i As Long
    On Error Resume Next
    f = FreeFile
    Open LibPath() For Output As #f
    For i = 0 To libN - 1
        With lib(i)
            Print #f, EncU(.Name) & "|" & .Kind & "|" & Str(.L) & "|" & Str(.W) & "|" & .Cn & "|" & .Rn & "|" & _
                      Str(.P) & "|" & Str(.Margin) & "|" & Str(.MinGap) & "|" & Str(.Watt) & "|" & Str(.Price)
        End With
    Next i
    Close #f
End Sub

'----------------------------------------------------------------------
'  THONG SO GIAO DIEN (luu registry)
'----------------------------------------------------------------------
Private Sub LoadUI(s As LedSpec, o2 As LayoutOpts)
    Dim i As Long
    i = CLng(GetSetting(REG_APP, "UI", "Led", "2"))
    If i < 0 Or i >= libN Then i = 0
    s = lib(i)
    s.P = Num(GetSetting(REG_APP, "UI", "P", Str(s.P)))
    s.Margin = Num(GetSetting(REG_APP, "UI", "M", Str(s.Margin)))
    s.MinGap = Num(GetSetting(REG_APP, "UI", "Gap", Str(s.MinGap)))
    o2.Stagger = CLng(GetSetting(REG_APP, "UI", "Stagger", "0"))
    o2.AutoSym = GetSetting(REG_APP, "UI", "Sym", "1") = "1"
    o2.FillDark = GetSetting(REG_APP, "UI", "Fill", "1") = "1"
    o2.DrawWires = GetSetting(REG_APP, "UI", "Wire", "1") = "1"
    o2.MaxPerWire = CLng(Num(GetSetting(REG_APP, "UI", "MaxW", "20")))
    o2.Volt = Num(GetSetting(REG_APP, "UI", "Volt", "12"))
    o2.MakeHoles = GetSetting(REG_APP, "UI", "Hole", "0") = "1"
    o2.HoleD = Num(GetSetting(REG_APP, "UI", "HoleD", Str(s.L)))
End Sub

'----------------------------------------------------------------------
'  GIAO DIEN (tao dong luc chay - chu tieng Viet co dau)
'----------------------------------------------------------------------
Private Function AddCtl(f As Object, ByVal prog As String, ByVal nm As String, ByVal x As Single, ByVal y As Single, _
                        ByVal w As Single, ByVal h As Single, Optional ByVal cap As String = "") As Object
    Dim c As Object
    Set c = f.Controls.Add(prog, nm, True)
    c.Left = x: c.Top = y: c.Width = w: c.Height = h
    If cap <> "" Then
        On Error Resume Next
        c.Caption = cap
        On Error GoTo 0
    End If
    Set AddCtl = c
End Function

Private Sub Hook(ByVal c As Object, ByVal key As String, ByVal kind As Long)
    ' Lop su kien nam trong code cua cua so (tranh loi bien dich truoc khi cai dat)
    gForm.HookCtl c, key, kind
End Sub

Private Sub Lbl(f As Object, ByVal x As Single, ByVal y As Single, ByVal w As Single, ByVal cap As String, Optional ByVal bold As Boolean = False)
    Dim c As Object
    Static k As Long
    k = k + 1
    Set c = AddCtl(f, "Forms.Label.1", "lblA" & k, x, y + 2, w, 14, cap)
    If bold Then c.Font.Bold = True
End Sub

Private Sub Txt(f As Object, ByVal nm As String, ByVal x As Single, ByVal y As Single, ByVal w As Single, ByVal v As String)
    Dim c As Object
    Set c = AddCtl(f, "Forms.TextBox.1", nm, x, y, w, 18)
    c.Text = v
End Sub

Public Sub AutoLEDUI_Build(f As Object)
    Dim i As Long, c As Object, y As Single, s As LedSpec, o2 As LayoutOpts
    Set gForm = f
    LoadLibrary
    LoadUI s, o2
    f.Caption = U("AutoLED Pro – Rải LED tự động")
    f.Width = 540: f.Height = 470
    ' ---------------- cot trai: LED
    Lbl f, 10, 8, 240, U("1. CHỌN LOẠI LED"), True
    Set c = AddCtl(f, "Forms.ComboBox.1", "cboLed", 10, 26, 240, 18)
    c.Style = 2
    For i = 0 To libN - 1: c.AddItem lib(i).Name: Next i
    Hook c, "led", 1
    Lbl f, 10, 52, 70, U("Tên LED")
    Txt f, "txtName", 90, 50, 160, ""
    Lbl f, 10, 74, 70, U("Kiểu")
    Set c = AddCtl(f, "Forms.ComboBox.1", "cboKind", 90, 72, 160, 18)
    c.Style = 2
    c.AddItem U("LED tròn (hạt)"): c.AddItem U("Module chữ nhật / vuông")
    Lbl f, 10, 96, 80, U("Dài × Rộng (mm)")
    Txt f, "txtL", 110, 94, 60, "": Txt f, "txtW", 190, 94, 60, ""
    Lbl f, 10, 118, 100, U("Số bóng dọc × ngang")
    Txt f, "txtCn", 110, 116, 60, "": Txt f, "txtRn", 190, 116, 60, ""
    Lbl f, 10, 140, 100, U("Công suất (W) / Giá")
    Txt f, "txtWatt", 110, 138, 60, "": Txt f, "txtPrice", 190, 138, 60, ""
    Hook AddCtl(f, "Forms.CommandButton.1", "btnNew", 10, 164, 76, 22, U("Thêm mới")), "new", 0
    Hook AddCtl(f, "Forms.CommandButton.1", "btnSave", 92, 164, 76, 22, U("Lưu LED")), "save", 0
    Hook AddCtl(f, "Forms.CommandButton.1", "btnDel", 174, 164, 76, 22, U("Xóa LED")), "del", 0
    Hook AddCtl(f, "Forms.CommandButton.1", "btnSample", 10, 192, 240, 22, U("Dùng hình đang chọn làm LED")), "sample", 0
    Lbl f, 10, 216, 240, U("(Đổi tên hình đó thành LED_MAU; xóa hình để bỏ)")
    ' ---------------- cot phai: thong so
    Lbl f, 270, 8, 250, U("2. THÔNG SỐ XẾP"), True
    Lbl f, 270, 30, 170, U("Khoảng cách tâm bóng (mm)")
    Txt f, "txtP", 450, 28, 70, Str(s.P)
    Lbl f, 270, 52, 170, U("Cách mép chữ (mm)")
    Txt f, "txtM", 450, 50, 70, Str(s.Margin)
    Lbl f, 270, 74, 170, U("Khe tối thiểu giữa 2 LED (mm)")
    Txt f, "txtGap", 450, 72, 70, Str(s.MinGap)
    Lbl f, 270, 96, 170, U("Xếp module")
    Set c = AddCtl(f, "Forms.ComboBox.1", "cboStagger", 400, 94, 120, 18)
    c.Style = 2
    c.AddItem U("Tự động"): c.AddItem U("Thẳng hàng"): c.AddItem U("So le")
    c.ListIndex = o2.Stagger
    Set c = AddCtl(f, "Forms.CheckBox.1", "chkSym", 270, 118, 250, 18, U("Tự nhận chữ đối xứng (lật gương)"))
    c.Value = o2.AutoSym
    Set c = AddCtl(f, "Forms.CheckBox.1", "chkFill", 270, 138, 250, 18, U("Lấp chỗ tối (LED tròn)"))
    c.Value = o2.FillDark
    Lbl f, 270, 164, 250, U("3. ĐI DÂY & ĐỤC LỖ"), True
    Set c = AddCtl(f, "Forms.CheckBox.1", "chkWire", 270, 184, 250, 18, U("Vẽ đường đi dây (layer DAY)"))
    c.Value = o2.DrawWires
    Lbl f, 270, 206, 170, U("Tối đa LED trên 1 dây")
    Txt f, "txtMaxW", 450, 204, 70, CStr(o2.MaxPerWire)
    Lbl f, 270, 228, 170, U("Điện áp nguồn (V)")
    Txt f, "txtVolt", 450, 226, 70, Str(o2.Volt)
    Set c = AddCtl(f, "Forms.CheckBox.1", "chkHole", 270, 250, 180, 18, U("Tạo lỗ cắt, đường kính (mm)"))
    c.Value = o2.MakeHoles
    Txt f, "txtHoleD", 450, 250, 70, Str(o2.HoleD)
    ' ---------------- nut chinh
    Set c = AddCtl(f, "Forms.CommandButton.1", "btnRun", 10, 286, 170, 34, U("RẢI LED"))
    c.Font.Bold = True: c.Font.Size = 12
    Hook c, "run", 0
    Hook AddCtl(f, "Forms.CommandButton.1", "btnCount", 190, 286, 110, 34, U("Đếm / Báo giá")), "count", 0
    Hook AddCtl(f, "Forms.CommandButton.1", "btnClear", 310, 286, 110, 34, U("Xóa LED + dây")), "clear", 0
    Hook AddCtl(f, "Forms.CommandButton.1", "btnClose", 430, 286, 90, 34, U("Đóng")), "close", 0
    Set c = AddCtl(f, "Forms.Label.1", "lblStatus", 10, 330, 510, 100, U("Chọn chữ cần rải LED rồi bấm RẢI LED. Bấm Ctrl+Z một lần để hủy cả lần rải."))
    c.WordWrap = True
    c.BorderStyle = 1
    f.Controls("cboLed").ListIndex = CLng(GetSetting(REG_APP, "UI", "Led", "2")) Mod Max2(1, libN)
End Sub

Private Sub ShowLed(ByVal i As Long)
    Dim f As Object
    Set f = gForm
    If i < 0 Or i >= libN Then Exit Sub
    With lib(i)
        f.Controls("txtName").Text = .Name
        f.Controls("cboKind").ListIndex = .Kind
        f.Controls("txtL").Text = Str(.L): f.Controls("txtW").Text = Str(.W)
        f.Controls("txtCn").Text = CStr(.Cn): f.Controls("txtRn").Text = CStr(.Rn)
        f.Controls("txtWatt").Text = Str(.Watt): f.Controls("txtPrice").Text = Str(.Price)
        f.Controls("txtP").Text = Str(.P): f.Controls("txtM").Text = Str(.Margin): f.Controls("txtGap").Text = Str(.MinGap)
        f.Controls("txtHoleD").Text = Str(.L)
    End With
End Sub

Private Sub ReadForm(s As LedSpec, o2 As LayoutOpts)
    Dim f As Object
    Set f = gForm
    s.Name = f.Controls("txtName").Text
    s.Kind = Max2(0, f.Controls("cboKind").ListIndex)
    s.L = Num(f.Controls("txtL").Text): s.W = Num(f.Controls("txtW").Text)
    s.Cn = CLng(Num(f.Controls("txtCn").Text)): s.Rn = CLng(Num(f.Controls("txtRn").Text))
    s.Watt = Num(f.Controls("txtWatt").Text): s.Price = Num(f.Controls("txtPrice").Text)
    s.P = Num(f.Controls("txtP").Text): s.Margin = Num(f.Controls("txtM").Text): s.MinGap = Num(f.Controls("txtGap").Text)
    If s.L <= 0 Then s.L = 9
    If s.W <= 0 Then s.W = s.L
    If s.P <= 0 Then s.P = 25
    If s.MinGap <= 0 Then s.MinGap = 3
    o2.Stagger = Max2(0, f.Controls("cboStagger").ListIndex)
    o2.AutoSym = f.Controls("chkSym").Value
    o2.FillDark = f.Controls("chkFill").Value
    o2.DrawWires = f.Controls("chkWire").Value
    o2.MaxPerWire = CLng(Num(f.Controls("txtMaxW").Text)): If o2.MaxPerWire < 1 Then o2.MaxPerWire = 20
    o2.Volt = Num(f.Controls("txtVolt").Text): If o2.Volt <= 0 Then o2.Volt = 12
    o2.MakeHoles = f.Controls("chkHole").Value
    o2.HoleD = Num(f.Controls("txtHoleD").Text)
    SaveSetting REG_APP, "UI", "Led", CStr(Max2(0, f.Controls("cboLed").ListIndex))
    SaveSetting REG_APP, "UI", "P", Str(s.P)
    SaveSetting REG_APP, "UI", "M", Str(s.Margin)
    SaveSetting REG_APP, "UI", "Gap", Str(s.MinGap)
    SaveSetting REG_APP, "UI", "Stagger", CStr(o2.Stagger)
    SaveSetting REG_APP, "UI", "Sym", IIf(o2.AutoSym, "1", "0")
    SaveSetting REG_APP, "UI", "Fill", IIf(o2.FillDark, "1", "0")
    SaveSetting REG_APP, "UI", "Wire", IIf(o2.DrawWires, "1", "0")
    SaveSetting REG_APP, "UI", "MaxW", CStr(o2.MaxPerWire)
    SaveSetting REG_APP, "UI", "Volt", Str(o2.Volt)
    SaveSetting REG_APP, "UI", "Hole", IIf(o2.MakeHoles, "1", "0")
    SaveSetting REG_APP, "UI", "HoleD", Str(o2.HoleD)
End Sub

' Goi tu clsAutoLEDEvt
Public Sub AutoLEDUI_Change(ByVal key As String)
    If key = "led" Then ShowLed gForm.Controls("cboLed").ListIndex
End Sub

Public Sub AutoLEDUI_Click(ByVal key As String)
    Dim s As LedSpec, o2 As LayoutOpts, i As Long, c As Object, sh As Shape
    Set c = gForm.Controls("cboLed")
    Select Case key
        Case "run"
            ReadForm s, o2
            gForm.Controls("lblStatus").Caption = U("Đang xếp LED...")
            DoEvents
            gForm.Controls("lblStatus").Caption = ViText(RunLayout(s, o2))
        Case "count"
            ReadForm s, o2
            gForm.Controls("lblStatus").Caption = ViText(AutoLED_Dem())
        Case "clear"
            AutoLED_XoaLED
            gForm.Controls("lblStatus").Caption = ViText(gReport)
        Case "close"
            gForm.Hide
        Case "new", "save"
            ReadForm s, o2
            If Trim$(s.Name) = "" Then s.Name = "LED moi"
            If key = "new" Or c.ListIndex < 0 Then
                AddLib s.Name, s.Kind, s.L, s.W, s.Cn, s.Rn, s.P, s.Margin, s.MinGap, s.Watt, s.Price
                c.AddItem s.Name
                c.ListIndex = libN - 1
            Else
                i = c.ListIndex
                lib(i) = s
                c.List(i) = s.Name
            End If
            SaveLibrary
            gForm.Controls("lblStatus").Caption = U("Đã lưu thư viện LED.")
        Case "del"
            i = c.ListIndex
            If i >= 0 And libN > 1 Then
                For i = c.ListIndex To libN - 2: lib(i) = lib(i + 1): Next i
                libN = libN - 1
                c.RemoveItem c.ListIndex
                c.ListIndex = 0
                SaveLibrary
            End If
        Case "sample"
            If ActiveSelectionRange.Count = 1 Then
                Set sh = ActiveSelectionRange(1)
                sh.Name = SAMPLE_NAME
                gForm.Controls("lblStatus").Caption = U("Đã lưu hình tùy chỉnh (LED_MAU). Macro sẽ nhân bản hình này làm LED.")
            Else
                gForm.Controls("lblStatus").Caption = U("Hãy chọn đúng 1 hình (có thể là nhóm) rồi bấm lại.")
            End If
    End Select
End Sub

' Bao cao khong dau (MsgBox) -> co dau cho giao dien
Private Function ViText(ByVal s As String) As String
    s = Replace(s, "So LED", U("Số LED"))
    s = Replace(s, "Cong suat", U("Công suất"))
    s = Replace(s, "Nguon de xuat (du 20%)", U("Nguồn đề xuất (dư 20%)"))
    s = Replace(s, "Thanh tien LED", U("Thành tiền LED"))
    s = Replace(s, "So day noi", U("Số dây nối"))
    s = Replace(s, "Thoi gian", U("Thời gian"))
    s = Replace(s, "giay", U("giây"))
    ViText = Replace(s, "|", vbCrLf)
End Function

'----------------------------------------------------------------------
'  CAI DAT: tao cua so frmAutoLED + lop su kien clsAutoLEDEvt
'----------------------------------------------------------------------
Public Sub AutoLED_CaiDat()
    Dim vbp As Object, comp As Object, p As Object, found As Boolean, code As String
    On Error GoTo Manual
    For Each p In Application.VBE.VBProjects
        On Error Resume Next
        Set comp = Nothing
        Set comp = p.VBComponents("AutoLEDPro")
        On Error GoTo Manual
        If Not comp Is Nothing Then Set vbp = p: found = True: Exit For
    Next p
    If Not found Then GoTo Manual
    On Error Resume Next
    vbp.VBComponents.Remove vbp.VBComponents("clsAutoLEDEvt")
    vbp.VBComponents.Remove vbp.VBComponents("frmAutoLED")
    On Error GoTo Manual
    ' lop su kien
    Set comp = vbp.VBComponents.Add(2)
    comp.Name = "clsAutoLEDEvt"
    code = ClassCode()
    ' cua so
    Set p = vbp.VBComponents.Add(3)
    p.Name = "frmAutoLED"
    p.CodeModule.AddFromString FormCode()
    comp.CodeModule.AddFromString code
    MsgBox "Da cai dat xong cua so AutoLED Pro." & vbCrLf & vbCrLf & _
           "Buoc cuoi: mo Macro Editor (Alt+F11), bam Save (Ctrl+S) de luu GlobalMacros." & vbCrLf & _
           "Sau do chay macro AutoLED de mo cua so.", vbInformation, APP_NAME
    Exit Sub
Manual:
    MsgBox "Khong tu cai dat duoc (" & Err.Description & ")." & vbCrLf & vbCrLf & _
           "Cai tay trong Macro Editor (Alt+F11):" & vbCrLf & _
           "1. File > Import File > chon clsAutoLEDEvt.cls" & vbCrLf & _
           "2. Insert > UserForm, doi (Name) thanh frmAutoLED" & vbCrLf & _
           "3. Mo code cua frmAutoLED, dan noi dung file frmAutoLED_code.txt" & vbCrLf & _
           "4. Save. Chay macro AutoLED.", vbExclamation, APP_NAME
End Sub

Private Function ClassCode() As String
    ClassCode = "Public WithEvents Btn As MSForms.CommandButton" & vbCrLf & _
                "Public WithEvents Cbo As MSForms.ComboBox" & vbCrLf & _
                "Public Key As String" & vbCrLf & _
                "Private Sub Btn_Click()" & vbCrLf & "    AutoLEDUI_Click Key" & vbCrLf & "End Sub" & vbCrLf & _
                "Private Sub Cbo_Change()" & vbCrLf & "    AutoLEDUI_Change Key" & vbCrLf & "End Sub" & vbCrLf
End Function

Private Function FormCode() As String
    FormCode = "Private evs As New Collection" & vbCrLf & _
               "Public Sub HookCtl(ByVal c As Object, ByVal key As String, ByVal kind As Long)" & vbCrLf & _
               "    Dim ev As New clsAutoLEDEvt" & vbCrLf & _
               "    ev.Key = key" & vbCrLf & _
               "    If kind = 0 Then Set ev.Btn = c Else Set ev.Cbo = c" & vbCrLf & _
               "    evs.Add ev" & vbCrLf & _
               "End Sub" & vbCrLf & _
               "Private Sub UserForm_Initialize()" & vbCrLf & _
               "    AutoLEDUI_Build Me" & vbCrLf & _
               "End Sub" & vbCrLf & _
               "Private Sub UserForm_QueryClose(Cancel As Integer, CloseMode As Integer)" & vbCrLf & _
               "    If CloseMode = 0 Then Cancel = True: Me.Hide" & vbCrLf & _
               "End Sub" & vbCrLf
End Function
