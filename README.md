# SGU-K22-DCT122C3-CNLTHD

## ZENITH FITNESS

Website thương mại điện tử bán dụng cụ và phụ kiện thể thao được xây dựng bằng Django, MySQL, Tailwind CDN và Alpine.js. Dự án tập trung vào trải nghiệm mua hàng thực tế: giỏ hàng, đặt hàng, theo dõi đơn, thanh toán VNPay sandbox, phân quyền người dùng và chọn vị trí giao hàng chính xác trên mini map.

## Tính năng chính

- Danh mục sản phẩm, chi tiết sản phẩm và giao diện mua hàng responsive.
- Giỏ hàng theo tài khoản đăng nhập, hỗ trợ cập nhật số lượng và xoá sản phẩm.
- Quy trình checkout có kiểm tra thông tin giao hàng và tạo đơn hàng theo nghiệp vụ thực tế.
- Theo dõi trạng thái đơn hàng và mã tracking.
- Thanh toán VNPay sandbox, chỉ ghi nhận thành công khi có xác nhận hợp lệ.
- Phân quyền người dùng theo vai trò `CUSTOMER`, `STAFF`, `MANAGER`.
- Gợi ý địa chỉ thật khi nhập, ưu tiên Google Places nếu có `GOOGLE_MAPS_API_KEY`.
- Mini map để chọn trực tiếp vị trí giao hàng, kéo thả pin hoặc lấy vị trí hiện tại.
- Dữ liệu mẫu và script SQL hỗ trợ khởi tạo nhanh.

## Công nghệ sử dụng

- Backend: Django 5.x
- Database: MySQL
- Giao diện: Tailwind CSS CDN, Alpine.js CDN
- Bản đồ: Leaflet + OpenStreetMap
- Địa chỉ: Google Places API, Google Geocoding API, Nominatim fallback
- Thanh toán: VNPay sandbox

## Cấu trúc dự án

- `fitness_shop/`: cấu hình project Django, routing, settings và WSGI/ASGI.
- `shop/`: ứng dụng chính của hệ thống bán hàng.
  - `models.py`: sản phẩm, giỏ hàng, đơn hàng, user profile và các trường nghiệp vụ.
  - `views.py`: logic checkout, thanh toán, tracking, tra cứu địa chỉ và API hỗ trợ.
  - `forms.py`: form đăng ký, đăng nhập, checkout và validate dữ liệu.
  - `urls.py`: định tuyến cho app `shop`.
  - `admin.py`: cấu hình trang quản trị.
  - `tests.py`: test cho checkout, payment, tracking, phân quyền và địa chỉ.
  - `migrations/`: lịch sử migration của database.
- `templates/`: giao diện HTML.
  - `base.html`: layout chung.
  - `home.html`, `index.html`: trang chủ.
  - `cart.html`: giỏ hàng.
  - `checkout.html`: trang thanh toán và mini map chọn vị trí.
  - `payment.html`: trang trung gian thanh toán.
  - `orders.html`, `order_detail.html`, `tracking.html`: danh sách và theo dõi đơn.
  - `product_detail.html`, `category_detail.html`: trang sản phẩm và danh mục.
  - `registration/`: các trang đăng nhập, đăng ký, khôi phục mật khẩu nếu có.
- `static/`: tài nguyên tĩnh như CSS, JS, ảnh hoặc file front-end khác.
- `seed_demo_data.sql`: script SQL để tạo bảng và dữ liệu mẫu nhanh.
- `requirements.txt`: các thư viện Python cần cài.
- `.env.example`: file mẫu biến môi trường.

## Yêu cầu hệ thống

- Python 3.10+.
- MySQL 8+.
- Trình duyệt hiện đại để dùng giao diện và bản đồ.

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

VNPAY_URL=https://sandbox.vnpayment.vn/paymentv2/vpcpay.html
VNPAY_TMN_CODE=your_tmn_code
VNPAY_HASH_SECRET=your_hash_secret

GOOGLE_MAPS_API_KEY=your_google_maps_api_key
```

### 3. Tạo database

Tạo một database MySQL tên `fitness_shop_db` hoặc đổi theo biến môi trường bạn đã cấu hình.

### 4. Chạy migration

```powershell
python manage.py makemigrations
python manage.py migrate
```

### 5. Tạo tài khoản quản trị

```powershell
python manage.py createsuperuser
```

### 6. Nạp dữ liệu mẫu

Bạn có thể dùng một trong hai cách sau:

```powershell
python manage.py seed_demo_data
```

hoặc import trực tiếp file SQL:

```sql
seed_demo_data.sql
```

### 7. Chạy ứng dụng

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

##  Thông tin chung
* **Giảng viên hướng dẫn:**  Đỗ Như Loan
* **Lớp:** DCT122C3

###  Nhóm sinh viên thực hiện: Nhóm 3
| MSSV | Họ và tên |
| --- | --- |
| 3122411036 | Phan Thành Đại |
| 3122411167 | Huỳnh Minh Quân |