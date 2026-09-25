# Kinh nghiệm xếp LED – rút ra từ quá trình tự thử nghiệm

Tài liệu này ghi lại **30 quy tắc** mà AutoLED Pro đang áp dụng. Mỗi quy tắc đều xuất phát từ một lỗi cụ thể mà tôi đã thấy trong các vòng tự thử, sau đó sửa và kiểm tra lại.

Bộ thử nghiệm gồm:
- **Chữ:** 26 chữ, gồm chữ nét thẳng, nét xiên, nét cong, vừa thẳng vừa cong, và chữ có dấu tiếng Việt.
- **Cỡ chữ:** cao 1000, 600, 300 và 150 mm.
- **LED:** LED tròn F9, module 15×65 loại 3 bóng, module vuông 35×35 loại 4 bóng.
- **Chấm điểm:** mỗi bản xếp được máy chấm tự động theo các tiêu chí ở cuối tài liệu, và được tôi tự xem lại bằng mắt.

---

## A. Nguyên tắc nền tảng

| # | Quy tắc | Vì sao |
|---|---|---|
| Q1 | **Đo khoảng cách giữa tâm các bóng LED** (khoảng 35mm với module), không đo theo cạnh LED | Đây là quy tắc của xưởng. Ánh sáng phát ra từ bóng, không phát ra từ vỏ module |
| Q2 | **Tách chữ thành các đoạn mép**, cắt tại góc gãy. Xếp đoạn thẳng trước, dài trước | Mỗi nét chữ được giới hạn bởi các đoạn mép. Nét chính phải được xếp trước |
| Q3 | Trong mỗi nét, LED chạy trên các **"ray" song song với cạnh nét**. **Số ray được chia đều vừa khít bề rộng nét** | Khoảng dư được chia đều về hai bên, nên hàng LED sát mép luôn cách mép bằng nhau |
| Q6 | **Chữ đối xứng thì chỉ xếp nửa trái, rồi lật gương sang phải** | Đối xứng tuyệt đối là điều mắt người nhận ra đầu tiên |
| Q7 | **Không bao giờ để LED chồng nhau hay lấn mép.** Máy kiểm tra cả thân LED, không chỉ tâm | Đây là lỗi lớn nhất của eCut |

## B. Nét thẳng (chữ I, L, T, H, E, F)

| # | Kinh nghiệm |
|---|---|
| K1 | Bề rộng nét phải lấy **giá trị nhỏ (30% thấp nhất)**, không lấy trung bình, vì mép nét hay chạy qua chỗ giao với nét khác |
| K4 | Nét dọc dùng chung **hàng ngang** của cả chữ. Nét ngang dùng chung **cột dọc** của nét dọc, để LED thẳng hàng xuyên suốt cả chữ |
| K5 | Mép ở **đầu nét** (đầu cánh chữ E) không phải cạnh bên, nên không được tạo lưới. Nhận biết: bề rộng đo từ mép đó lớn hơn 1.5 lần chiều dài của nó |
| K6 | Với nét nằm ngang: mỗi hàng ngang chung nằm lọt trong nét thành một hàng LED |
| K7 | Nối tiếp cột của thân chữ, **phần cánh vươn ra ngoài thì chia đều lại**, để đầu cánh cách mép đúng chuẩn |
| K8 | Hàng ngang phải **neo vào mọi mép nằm ngang** (đáy, đỉnh, mép thanh ngang) |
| K11 | **Lấy điểm giữa của đoạn mép làm gốc để dựng lưới.** Điểm sát góc có thể lệch 2mm và làm lệch cả lưới |
| K12 | Nét quá hẹp để đặt 2 cột thì đặt **1 cột ở chính giữa nét**, không để 1 cột nằm sát mép |
| K13 | Ưu tiên **một bước hàng thống nhất cho cả chữ**: máy thử nhiều bước và nhiều điểm bắt đầu, chọn cách để mọi mép ngang đều có hàng LED cách mép gần đúng chuẩn |
| K14 | Bước LED bạn nhập là **"khoảng chừng"**. Máy được co giãn ±20% để cả chữ đều nhau |

## C. Nét xiên (chữ A, V, N, K, M, Z)

| # | Kinh nghiệm |
|---|---|
| K15 | Nét dốc hơn khoảng 53° thì dùng **hàng ngang chung** (cột song song cạnh xiên). Nét nghiêng ít hơn thì dùng **lưới vuông góc theo chính nét đó**, để dọc nét không bị thưa |
| K16 | Chỉ nối tiếp cột từ **nét thẳng đứng**. LED ở chân xiên không tạo thành cột thẳng đứng nào để nối |
| K9 | Với chữ đối xứng, cột ở phần nét ngang phải **chia đều tính tới trục giữa**: hoặc có một cột đúng trục, hoặc hai cột cách đều hai bên trục |
| K17 | **Bước "chỉnh hàng" sau cùng:** trên mỗi hàng, đoạn LED dày hoặc thưa bất thường (ở đỉnh chữ A, chỗ giao nét) được chia đều lại giữa hai LED tốt ở hai đầu |
| K30 | Với module trên nét xiên: **tìm đoạn xếp theo cột giữa**, cột bên nào vướng thì chỉ bỏ riêng module đó. Nhờ vậy nét chéo của N, M, V không bị bỏ trống |

## D. Nét cong (chữ O, C, S, G, U, J)

| # | Kinh nghiệm |
|---|---|
| Q5 | Nét cong xếp các **vòng đồng tâm**. Trên mỗi vòng, LED chia đều, **hai đầu vòng neo đúng mép đầu nét** (hai đầu chữ C thẳng hàng) |
| K18 | **Mỗi nét chỉ do một mép quản lý.** Mép sau chỉ lấp phần còn trống, nên không bị hai bộ vòng chen nhau như chữ O ban đầu |
| K21 | Đoạn mép trơn (không có góc gãy) phải xếp **đồng tâm liền mạch**, như móng ngựa của chữ U. Không tách thành phần thẳng và phần cong |
| K22 | Vòng khép kín ở chữ đối xứng **bắt đầu chia từ điểm nằm trên trục**. Chữ không đối xứng thì bắt đầu từ điểm cao nhất |
| K23 | Khi co giãn theo bề rộng nét: **giữ nguyên khoảng cách tới mép**, chỉ co giãn khoảng cách giữa các vòng bên trong |
| K24 | Nét thay đổi bề rộng (chữ O dày hai bên, mỏng ở đỉnh và đáy) thì **số vòng thay đổi theo từng đoạn**. Đoạn ngắn được gộp vào đoạn bên cạnh |
| K28 | Module thẳng trên nét cong được phép **"nhích" vào trong vài mm**, vì hai đầu module gần mép cong hơn phần giữa |

## E. Riêng cho module

| # | Kinh nghiệm |
|---|---|
| K25 | Với module, **không tự lấp chỗ tối**. Một module đặt lệch hướng xấu hơn nhiều so với một khoảng tối nhỏ |
| K26 | Module có thân **vắt qua trục đối xứng** thì hoặc nằm đúng giữa trục, hoặc bỏ đi. Nếu không, module sẽ chồng lên bản lật gương của nó |
| K27 | Nét ngang chỉ xếp trong **phần còn trống** (sau khi thân đã xếp), chia đều module vừa khít phần đó |
| – | **So le chỉ khi số cột là số lẻ.** Số cột chẵn mà so le thì hàng sát mép trên và mép dưới khác nhau, nhìn lệch |

## F. Đi dây

| # | Kinh nghiệm |
|---|---|
| D1 | LED nối đuôi nhau **theo hướng trục** (lệch tối đa 30°) thành các chuỗi: mỗi cột hoặc mỗi vòng là một chuỗi |
| D2 | Thứ tự nối kiểu **zic-zắc**: từ điểm nguồn, luôn đi tới đầu chuỗi gần nhất. **Phạt nặng** đoạn dây chạy ra ngoài chữ |
| D3 | **Chia dây cân bằng**: số dây bằng tổng LED chia cho số LED tối đa trên một dây, làm tròn lên. Cắt dây ở **đầu chuỗi** |
| D4 | Mọi dây xuất phát từ **một điểm nguồn chung** |
| K29 | Nối giữa hai chuỗi quá xa, hoặc phải vắt qua lỗ chữ, thì **kéo dây mới từ nguồn** |

## G. Về cách tự đánh giá

- **K2:** thước đo chỉ tính khoảng cách tới LED gần nhất thì **không phát hiện được LED lệch lưới**. Phải thêm chỉ số "LED lệch lưới" (LED không có đủ 2 LED lân cận đúng bước).
- **Máy chấm điểm cao chưa chắc đã đẹp**: luôn phải xem lại bằng mắt, nhất là ở chỗ giao nét và đầu nét.
- Với module, các bóng trong module luôn cách nhau cố định, nên độ lệch khoảng cách "tự nhiên" cao hơn LED tròn. Vì vậy thang chấm của module khác thang chấm của LED tròn.

---

## Điểm còn yếu (sẽ cải thiện tiếp)

1. **Chữ nhỏ (cao 150–300mm) có nét dày ngang với 2 bước LED**, ví dụ cánh chữ E ở 300mm. Không có cách chia hoàn hảo, nên khoảng cách hàng giữa thân và cánh vẫn chênh nhau.
2. **Chỗ ba nét gặp nhau** (giữa chữ K, đáy chữ V với LED tròn) vẫn còn vài LED chưa thẳng hàng.
3. **Chữ O có nét dày mỏng khác nhau**: ở 4 chỗ chuyển từ 5 vòng sang 4 vòng, LED hơi gợn.
4. **Đi dây:** đôi khi vẫn sinh ra dây rất ngắn (1–2 LED), cần gộp vào dây bên cạnh.
5. **Font chữ viết tay, uốn lượn** chưa được thử nhiều.
