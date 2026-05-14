# SGU-K22-DCT122C3-CNLTHD

## ZENITH FITNESS

Website thương mại điện tử bán dụng cụ và phụ kiện thể thao được xây dựng bằng Django, MySQL, Tailwind CDN và Alpine.js. Hệ thống tập trung vào trải nghiệm mua hàng thực tế và vận hành bán hàng: giỏ hàng, đặt hàng, theo dõi đơn, thanh toán VNPay sandbox, phân quyền người dùng, chọn vị trí giao hàng chính xác trên mini map và trang quản trị được thiết kế riêng cho nghiệp vụ.

## Tính năng chính

- Danh mục sản phẩm, chi tiết sản phẩm và giao diện mua hàng responsive.
- Giỏ hàng theo tài khoản đăng nhập, hỗ trợ cập nhật số lượng và xoá sản phẩm.
- Quy trình checkout có kiểm tra thông tin giao hàng và tạo đơn hàng theo nghiệp vụ thực tế.
- Theo dõi trạng thái đơn hàng và mã tracking.
- Phân quyền người dùng theo vai trò `CUSTOMER`, `STAFF`, `MANAGER`.
- Trang quản trị riêng cho sản phẩm và đơn hàng, dùng giao diện đồng bộ với website bán hàng.
- Changelist đơn hàng/sản phẩm có badge, bảng và bộ lọc được tinh chỉnh để dễ theo dõi nghiệp vụ.
- Form sửa đơn hàng được chia khối rõ hơn cho giao hàng, thanh toán và xử lý trạng thái.
- Giá và tổng tiền hiển thị theo định dạng VND thống nhất trên cả storefront và admin.
- Mini map để chọn trực tiếp vị trí giao hàng, kéo thả pin hoặc lấy vị trí hiện tại.
- Script khởi tạo dữ liệu và file SQL hỗ trợ dựng hệ thống nhanh.

## Công nghệ sử dụng

- Backend: Django 5.x
- Database: MySQL
- Giao diện: Tailwind CSS CDN, Alpine.js CDN
- Bản đồ: Leaflet + OpenStreetMap
- Thanh toán: COD + Chuyển khoản
- Quản trị: Unfold Admin, Chart.js cho dashboard doanh thu, CSS tuỳ biến riêng cho trang quản trị

## Cấu trúc dự án

- `fitness_shop/`: cấu hình project Django, routing, settings và WSGI/ASGI.
- `shop/`: ứng dụng chính của hệ thống bán hàng.
  - `models.py`: sản phẩm, giỏ hàng, đơn hàng, user profile và các trường nghiệp vụ.
  - `views.py`: logic checkout, thanh toán, tracking, tra cứu địa chỉ và API hỗ trợ.
  - `forms.py`: form đăng ký, đăng nhập, checkout và validate dữ liệu.
  - `urls.py`: định tuyến cho app `shop`.
  - `admin.py`: cấu hình changelist, changeform và hành động nghiệp vụ cho sản phẩm, đơn hàng.
  - `admin_site.py`: dashboard quản trị, số liệu doanh thu và trạng thái đơn hàng.
  - `tests.py`: test cho checkout, payment, tracking, phân quyền và địa chỉ.
  - `migrations/`: lịch sử migration của database.
- `templates/`: giao diện HTML.
  - `base.html`: layout chung.
  - `home.html`, `index.html`: trang chủ.
  - `cart.html`: giỏ hàng.
  - `checkout.html`: trang thanh toán (địa chỉ gợi ý + lưu tọa độ ngầm).
  - `payment.html`: trang trung gian thanh toán.
  - `orders.html`, `order_detail.html`: tra cứu trạng thái và danh sách đơn.
  - `product_detail.html`, `category_detail.html`: trang sản phẩm và danh mục.
  - `admin/`: giao diện quản trị riêng, gồm dashboard, shell admin và trang đăng nhập.
  - `registration/`: các trang đăng nhập, đăng ký, khôi phục mật khẩu nếu có.
- `static/`: tài nguyên tĩnh như CSS, JS, ảnh hoặc file front-end khác.
  - `admin/zenith-admin.css`: stylesheet riêng cho admin, đồng bộ bảng, badge, form và dashboard.
- `seed_demo_data.sql`: script SQL để tạo bảng và dữ liệu mẫu nhanh.
- `requirements.txt`: các thư viện Python cần cài.
- `.env.example`: file mẫu biến môi trường.

## Yêu cầu hệ thống

- Python 3.10+.
- MySQL 8+.
- Trình duyệt hiện đại để dùng giao diện.

## Cài đặt nhanh

### 1. Tạo môi trường và cài thư viện

```powershell
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Tạo file môi trường

Sao chép `.env.example` thành `.env` và cấu hình các giá trị phù hợp với máy của bạn.

```powershell
copy .env.example .env
```

Các biến quan trọng:

```text
MYSQL_DATABASE=fitness_shop_db
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
```

### 3. Tạo database

Tạo một database MySQL tên `fitness_shop_db` hoặc đổi theo biến môi trường bạn đã cấu hình.

### 4. Chạy migration

```powershell
python manage.py makemigrations
python manage.py migrate
```

### 5. Nạp dữ liệu khởi tạo

Bạn có thể dùng một trong hai cách sau:

```powershell
python manage.py seed_demo_data
```

hoặc import trực tiếp file SQL:

```sql
seed_demo_data.sql
```

### 6. Chạy ứng dụng

```powershell
python manage.py runserver
```

Sau đó mở trình duyệt tại `http://127.0.0.1:8000/`.

## Chạy kiểm thử

```powershell
python manage.py test shop.tests
```

## Luồng nghiệp vụ chính

- Người dùng đăng ký hoặc đăng nhập.
- Chọn sản phẩm, thêm vào giỏ hàng và điều chỉnh số lượng.
- Vào checkout, nhập thông tin nhận hàng và chọn vị trí giao hàng trên mini map.
- Nếu thanh toán online, hệ thống chỉ ghi nhận đơn thành công khi VNPay xác nhận hợp lệ.
- Người dùng có thể theo dõi trạng thái đơn hàng bằng trang tracking.

## Quản trị bán hàng

- Trang admin được thiết kế riêng theo nhận diện ZENITH FITNESS, không dùng cảm giác mặc định của Django admin.
- Danh sách sản phẩm và đơn hàng hiển thị theo badge, bảng và bộ lọc đã tinh chỉnh cho nghiệp vụ bán hàng.
- Trang sửa đơn hàng tách rõ các khối khách hàng, địa chỉ giao hàng, vị trí giao hàng, thanh toán và mốc xử lý.
- Dashboard quản trị hiển thị doanh thu, trạng thái đơn và danh sách đơn gần đây theo dữ liệu thực.

##  Thông tin chung
* **Giảng viên hướng dẫn:**  Đỗ Như Loan
* **Lớp:** DCT122C3

###  Nhóm sinh viên thực hiện: Nhóm 17
| MSSV | Họ và tên |
| --- | --- |
| 3122411036 | Phan Thành Đại |
| 3122411167 | Huỳnh Minh Quân |
