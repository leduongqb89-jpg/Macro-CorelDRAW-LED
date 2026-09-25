# AutoLED Pro: rải LED tự động cho CorelDRAW

Macro này tự động xếp LED (LED hạt hoặc LED module) vào trong chữ để đi gia công chữ nổi và hộp đèn. Bạn không phải xếp tay từng con nữa.

## Cài đặt (làm một lần)

1. Tải file **`AutoLEDPro.bas`** về máy.
2. Mở CorelDRAW, bấm **Alt + F11** (hoặc vào *Tools → Macros → Macro Editor*).
3. Ở khung bên trái, bấm chuột phải vào **GlobalMacros (GlobalMacros.gms)** → **Import File…** → chọn `AutoLEDPro.bas`.
4. Bấm **Save** rồi đóng Macro Editor.
5. *(Nên làm)* Gắn macro vào nút hoặc phím tắt: *Tools → Options → Customization → Commands*, chọn **Macros** trong danh sách, rồi kéo `AutoLEDPro.AutoLED_Fill` lên thanh công cụ hoặc gán phím tắt.

> Nếu không thấy mục Macro, bạn cần cài thêm thành phần **VBA** khi cài CorelDRAW.

## Cách dùng

1. Chọn các chữ cần rải LED. Được chọn chữ thường (text), chữ đã Convert to Curves hoặc cả group.
2. Chạy macro **`AutoLED_Fill`**.
3. Một bảng hiện ra cho biết thông số đang dùng:
   - **YES**: rải LED ngay
   - **NO**: nhập lại thông số
   - **CANCEL**: hủy
4. Xong việc, bảng kết quả cho biết **tổng số LED**, **công suất** và **nguồn đề xuất**.

Macro đặt LED lên một layer riêng tên **`LED`**, mỗi chữ là một group tên `LED x <số lượng>`. Nếu thấy chưa ưng ý, bạn bấm **Ctrl+Z** một lần là bỏ toàn bộ lần rải đó.

### Các macro có trong module

| Macro | Chức năng |
|---|---|
| `AutoLED_Fill` | Rải LED vào các chữ đang chọn |
| `AutoLED_Count` | Đếm LED trong vùng chọn. Nếu không chọn gì thì đếm cả layer LED. Kèm công suất và nguồn |
| `AutoLED_Clear` | Xóa toàn bộ LED trên layer LED của trang hiện tại |
| `AutoLED_Settings` | Chỉ đổi thông số, không rải LED |

## Thông số

| Thông số | Ý nghĩa | Mặc định |
|---|---|---|
| Chế độ | **1 = Chạy theo nét**: LED chạy theo viền trong của chữ, thành từng vòng (hợp với chữ nét mảnh hoặc vừa). **2 = Lưới**: xếp LED thành hàng ngang, căn giữa trong từng đoạn nét (hợp với chữ to, mặt chữ rộng) | 1 |
| Loại LED | 1 = LED hạt (tròn), 2 = LED module (chữ nhật, tự xoay theo hướng nét) | 1 |
| Kích thước | Đường kính LED hạt, hoặc dài × rộng module (mm) | 9 mm |
| Khoảng cách LED | Khoảng cách giữa tâm 2 LED liền nhau (mm) | 20 |
| Khoảng cách hàng/vòng | Khoảng cách giữa các hàng (chế độ 2) hoặc giữa các vòng (chế độ 1) | 20 |
| Cách mép | Khoảng cách từ mép LED tới mép chữ (mm) | 3 |
| Số vòng tối đa | Số vòng LED nhiều nhất trong một nét (chế độ 1) | 10 |
| Công suất / Điện áp | Dùng để tính tổng công suất và nguồn | 0.2 W, 5 V |

Macro tự lưu thông số, lần sau mở lên vẫn giữ nguyên.

**Gợi ý thông số hay dùng:**
- Chữ nổi LED hạt 9 mm: chế độ 1, khoảng cách 15–20 mm, cách mép 3 mm.
- Hộp đèn module 3 bóng (khoảng 70×15 mm): chế độ 2, loại 2, khoảng cách 80 mm, hàng 60–80 mm.

## Dùng hình LED của riêng bạn

Bạn vẽ một hình LED (ví dụ module có chân dây, hoặc logo LED), rồi đặt tên cho hình đó là **`LED_MAU`** trong *Object Manager* (Window → Dockers → Objects). Khi rải, macro sẽ nhân bản đúng hình đó, tự lấy kích thước của nó, và xoay theo hướng nét ở chế độ 1.

## Lưu ý

- Chữ phải là **đường cong kín**. Nét hở (open path) sẽ bị bỏ qua.
- Ở chế độ 1, nếu một nét chữ quá mảnh không đủ chỗ chạy viền, macro tự chuyển nét đó sang chế độ lưới.
- Chữ rất to hoặc rất nhiều chữ có thể mất vài giây để chạy.
- Chữ trong bảng thông báo của macro viết không dấu, để không bị lỗi font trong VBA.
