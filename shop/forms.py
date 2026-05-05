from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django import forms
from django.conf import settings

from .models import UserProfile


VIETNAM_PROVINCES = [
    ("", "Chọn tỉnh/thành phố"),
    ("An Giang", "An Giang"),
    ("Bà Rịa - Vũng Tàu", "Bà Rịa - Vũng Tàu"),
    ("Bắc Giang", "Bắc Giang"),
    ("Bắc Kạn", "Bắc Kạn"),
    ("Bạc Liêu", "Bạc Liêu"),
    ("Bắc Ninh", "Bắc Ninh"),
    ("Bến Tre", "Bến Tre"),
    ("Bình Định", "Bình Định"),
    ("Bình Dương", "Bình Dương"),
    ("Bình Phước", "Bình Phước"),
    ("Bình Thuận", "Bình Thuận"),
    ("Cà Mau", "Cà Mau"),
    ("Cần Thơ", "Cần Thơ"),
    ("Cao Bằng", "Cao Bằng"),
    ("Đà Nẵng", "Đà Nẵng"),
    ("Đắk Lắk", "Đắk Lắk"),
    ("Đắk Nông", "Đắk Nông"),
    ("Điện Biên", "Điện Biên"),
    ("Đồng Nai", "Đồng Nai"),
    ("Đồng Tháp", "Đồng Tháp"),
    ("Gia Lai", "Gia Lai"),
    ("Hà Giang", "Hà Giang"),
    ("Hà Nam", "Hà Nam"),
    ("Hà Nội", "Hà Nội"),
    ("Hà Tĩnh", "Hà Tĩnh"),
    ("Hải Dương", "Hải Dương"),
    ("Hải Phòng", "Hải Phòng"),
    ("Hậu Giang", "Hậu Giang"),
    ("Hòa Bình", "Hòa Bình"),
    ("Hưng Yên", "Hưng Yên"),
    ("Khánh Hòa", "Khánh Hòa"),
    ("Kiên Giang", "Kiên Giang"),
    ("Kon Tum", "Kon Tum"),
    ("Lai Châu", "Lai Châu"),
    ("Lâm Đồng", "Lâm Đồng"),
    ("Lạng Sơn", "Lạng Sơn"),
    ("Lào Cai", "Lào Cai"),
    ("Long An", "Long An"),
    ("Nam Định", "Nam Định"),
    ("Nghệ An", "Nghệ An"),
    ("Ninh Bình", "Ninh Bình"),
    ("Ninh Thuận", "Ninh Thuận"),
    ("Phú Thọ", "Phú Thọ"),
    ("Phú Yên", "Phú Yên"),
    ("Quảng Bình", "Quảng Bình"),
    ("Quảng Nam", "Quảng Nam"),
    ("Quảng Ngãi", "Quảng Ngãi"),
    ("Quảng Ninh", "Quảng Ninh"),
    ("Quảng Trị", "Quảng Trị"),
    ("Sóc Trăng", "Sóc Trăng"),
    ("Sơn La", "Sơn La"),
    ("Tây Ninh", "Tây Ninh"),
    ("Thái Bình", "Thái Bình"),
    ("Thái Nguyên", "Thái Nguyên"),
    ("Thanh Hóa", "Thanh Hóa"),
    ("Thừa Thiên Huế", "Thừa Thiên Huế"),
    ("Tiền Giang", "Tiền Giang"),
    ("TP. Hồ Chí Minh", "TP. Hồ Chí Minh"),
    ("Trà Vinh", "Trà Vinh"),
    ("Tuyên Quang", "Tuyên Quang"),
    ("Vĩnh Long", "Vĩnh Long"),
    ("Vĩnh Phúc", "Vĩnh Phúc"),
    ("Yên Bái", "Yên Bái"),
]


class RegisterForm(UserCreationForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "w-full rounded-2xl border border-slate-200 bg-white px-4 py-3.5 text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-accent focus:ring-4 focus:ring-orange-100",
                "placeholder": "Tên đăng nhập",
            }
        )
    )
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": "w-full rounded-2xl border border-slate-200 px-4 py-3 outline-none focus:border-accent"}))
    first_name = forms.CharField(required=False, widget=forms.TextInput(attrs={"class": "w-full rounded-2xl border border-slate-200 px-4 py-3 outline-none focus:border-accent"}))
    last_name = forms.CharField(required=False, widget=forms.TextInput(attrs={"class": "w-full rounded-2xl border border-slate-200 px-4 py-3 outline-none focus:border-accent"}))
    password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "w-full rounded-2xl border border-slate-200 bg-white px-4 py-3.5 text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-accent focus:ring-4 focus:ring-orange-100",
                "placeholder": "Mật khẩu",
            }
        )
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "w-full rounded-2xl border border-slate-200 bg-white px-4 py-3.5 text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-accent focus:ring-4 focus:ring-orange-100",
                "placeholder": "Xác nhận mật khẩu",
            }
        )
    )

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Email này đã được sử dụng.")
        return email

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = UserProfile.ROLE_CUSTOMER
            profile.save(update_fields=["role"])
        return user


class CheckoutForm(forms.Form):
    full_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"class": "w-full rounded-2xl border border-slate-200 px-4 py-3 outline-none focus:border-accent", "placeholder": "Họ và tên"}),
    )
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={"class": "w-full rounded-2xl border border-slate-200 px-4 py-3 outline-none focus:border-accent", "placeholder": "Số điện thoại"}),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "w-full rounded-2xl border border-slate-200 px-4 py-3 outline-none focus:border-accent", "placeholder": "Email"}),
    )
    address_lookup = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "w-full rounded-2xl border border-slate-200 px-4 py-3 outline-none focus:border-accent",
                "placeholder": "Nhập địa chỉ hoặc chọn trên bản đồ",
                "autocomplete": "off",
                "data-address-lookup": "true",
            }
        ),
    )
    delivery_place_name = forms.CharField(required=False, widget=forms.HiddenInput())
    delivery_place_id = forms.CharField(required=False, widget=forms.HiddenInput())
    delivery_map_provider = forms.CharField(required=False, widget=forms.HiddenInput())
    delivery_latitude = forms.DecimalField(required=False, widget=forms.HiddenInput())
    delivery_longitude = forms.DecimalField(required=False, widget=forms.HiddenInput())
    province = forms.ChoiceField(
        choices=VIETNAM_PROVINCES,
        required=False,
        widget=forms.Select(attrs={"class": "w-full rounded-2xl border border-slate-200 px-4 py-3 outline-none focus:border-accent"}),
    )
    district = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"class": "w-full rounded-2xl border border-slate-200 px-4 py-3 outline-none focus:border-accent", "placeholder": "Quận/Huyện"}),
    )
    ward = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"class": "w-full rounded-2xl border border-slate-200 px-4 py-3 outline-none focus:border-accent", "placeholder": "Phường/Xã"}),
    )
    street_address = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"class": "w-full rounded-2xl border border-slate-200 px-4 py-3 outline-none focus:border-accent", "placeholder": "Số nhà, tên đường"}),
    )
    payment_method = forms.ChoiceField(
        choices=(
            ("COD", "Thanh toán khi nhận hàng"),
            ("BANK_TRANSFER", "Chuyển khoản ngân hàng"),
        ),
        widget=forms.Select(attrs={"class": "w-full rounded-2xl border border-slate-200 px-4 py-3 outline-none focus:border-accent"}),
        initial="COD",
    )
    note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2, "class": "w-full rounded-2xl border border-slate-200 px-4 py-3 outline-none focus:border-accent", "placeholder": "Ghi chú"}),
    )

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        digits = "".join(char for char in phone if char.isdigit())
        if len(digits) < 9 or len(digits) > 11:
            raise forms.ValidationError("Số điện thoại không hợp lệ.")
        return phone

    def clean(self):
        cleaned_data = super().clean()
        street_address = cleaned_data.get("street_address", "").strip()
        district = cleaned_data.get("district", "").strip()
        ward = cleaned_data.get("ward", "").strip()
        province = cleaned_data.get("province", "").strip()
        # Prefer structured street address when all parts present
        delivery_place_name = cleaned_data.get("delivery_place_name", "").strip()
        delivery_place_id = cleaned_data.get("delivery_place_id", "").strip()
        delivery_map_provider = cleaned_data.get("delivery_map_provider", "").strip()
        lat = cleaned_data.get("delivery_latitude")
        lon = cleaned_data.get("delivery_longitude")

        if street_address and district and ward and province:
            cleaned_data["shipping_address"] = ", ".join([street_address, ward, district, province])
        elif delivery_place_id:
            # If a place_id from Google (or other provider) exists, accept it
            cleaned_data["shipping_address"] = delivery_place_name or cleaned_data.get("address_lookup", "")
        elif lat and lon:
            # coordinates provided (map pick) - accept with best-effort address text
            cleaned_data["shipping_address"] = cleaned_data.get("address_lookup", "") or f"{lat},{lon}"
        else:
            raise forms.ValidationError(
                "Vui lòng cung cấp địa chỉ giao hàng đầy đủ (số nhà, phường/xã, quận/huyện, tỉnh/thành) hoặc chọn vị trí trên bản đồ."
            )

        cleaned_data["delivery_place_name"] = delivery_place_name
        cleaned_data["delivery_place_id"] = delivery_place_id
        cleaned_data["delivery_map_provider"] = delivery_map_provider
        return cleaned_data


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={"class": "w-full rounded-2xl border border-slate-200 bg-white px-4 py-3.5 text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-accent focus:ring-4 focus:ring-orange-100", "placeholder": "Tên đăng nhập"})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "w-full rounded-2xl border border-slate-200 bg-white px-4 py-3.5 text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-accent focus:ring-4 focus:ring-orange-100", "placeholder": "Mật khẩu"})
    )

