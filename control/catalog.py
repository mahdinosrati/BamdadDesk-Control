"""Explicit policy schema. Values are RustDesk option strings, not booleans."""
import base64
import re

PERMISSIONS = ["devices.read", "devices.write", "devices.connect", "policies.write", "enrollment.write",
               "releases.read", "releases.write", "admins.write", "audit.read"]

BOOL_OPTIONS = {
    "enable-keyboard": ("Keyboard and mouse", "صفحه‌کلید و ماوس"),
    "enable-clipboard": ("Clipboard", "کلیپ‌بورد"),
    "enable-file-transfer": ("File transfer", "انتقال فایل"),
    "enable-camera": ("Camera", "دوربین"),
    "enable-terminal": ("Terminal", "ترمینال"),
    "enable-audio": ("Audio", "صدا"),
    "enable-tunnel": ("TCP tunneling", "تونل TCP"),
    "enable-remote-restart": ("Remote restart", "راه‌اندازی مجدد"),
    "enable-record-session": ("Session recording", "ضبط نشست"),
    "enable-block-input": ("Block local input", "مسدود کردن ورودی محلی"),
    "enable-privacy-mode": ("Privacy mode", "حالت حریم خصوصی"),
    "enable-remote-printer": ("Remote printing (driver required)", "چاپ ریموت (نیازمند درایور)"),
    "enable-perm-change-in-accept-window": ("Change permissions in accept window", "تغییر دسترسی در پنجره پذیرش"),
    "hide-elevate-button-in-accept-window": ("Hide elevation button", "مخفی کردن دکمه ارتقای دسترسی"),
    "allow-remote-config-modification": ("Remote configuration changes", "تغییر تنظیمات از راه دور"),
    "enable-lan-discovery": ("LAN discovery", "کشف در شبکه داخلی"),
    "allow-auto-disconnect": ("Idle disconnection", "قطع اتصال در بیکاری"),
    "allow-only-conn-window-open": ("Require open connection window", "نیاز به پنجره اتصال باز"),
    "allow-auto-record-incoming": ("Record incoming sessions", "ضبط نشست‌های ورودی"),
    "allow-remove-wallpaper": ("Remove wallpaper", "حذف تصویر پس‌زمینه"),
    "enable-trusted-devices": ("Trusted devices", "دستگاه‌های مورد اعتماد"),
    "direct-server": ("Direct IP access", "دسترسی مستقیم با IP"),
    "allow-scope-violation-close": ("Close after scope violation", "بستن پس از خروج از محدوده"),
    "allow-scope-violation-alarm": ("Scope violation alarm", "هشدار خروج از محدوده"),
    "hide-general-settings": ("Hide general settings", "مخفی کردن تنظیمات عمومی"),
    "hide-security-settings": ("Hide security settings", "مخفی کردن تنظیمات امنیت"),
    "hide-network-settings": ("Hide network settings", "مخفی کردن تنظیمات شبکه"),
    "hide-server-settings": ("Hide server settings", "مخفی کردن تنظیمات سرور"),
    "hide-proxy-settings": ("Hide proxy settings", "مخفی کردن تنظیمات پروکسی"),
    "hide-remote-printer-settings": ("Hide printer settings", "مخفی کردن تنظیمات چاپگر"),
    "hide-websocket-settings": ("Hide WebSocket settings", "مخفی کردن تنظیمات وب‌سوکت"),
    "hide-stop-service": ("Hide stop service control", "مخفی کردن توقف سرویس"),
    "allow-command-line-settings-when-settings-disabled": ("Allow CLI settings changes", "اجازه تغییر تنظیمات با خط فرمان"),
    "allow-logon-screen-password": ("Allow Windows logon password", "اجازه رمز ورود ویندوز"),
    "allow-deep-link-password": ("Allow passwords in deep links", "اجازه رمز در لینک مستقیم"),
    "allow-deep-link-server-settings": ("Allow server settings in deep links", "اجازه سرور در لینک مستقیم"),
    "one-way-clipboard-redirection": ("One-way clipboard restriction", "محدودیت کلیپ‌بورد یک‌طرفه"),
    "one-way-file-transfer": ("One-way file transfer restriction", "محدودیت انتقال فایل یک‌طرفه"),
    "disable-change-id": ("Prevent local device ID changes", "جلوگیری از تغییر شناسه دستگاه"),
    "disable-unlock-pin": ("Disable local unlock PIN", "غیرفعال کردن پین بازکردن تنظیمات"),
}
ENUM_OPTIONS = {
    "verification-method": ["use-both-passwords", "use-permanent-password", "use-temporary-password"],
    "approve-mode": ["password", "click", "password-click"],
    "access-mode": ["custom"],
    "temporary-password-length": ["6", "8", "10"],
}
TEXT_OPTIONS = {
    "custom-rendezvous-server": ("ID server", "سرور شناسه"),
    "relay-server": ("Relay server", "سرور رله"),
    "key": ("Server public key", "کلید عمومی سرور"),
    "whitelist": ("IP allowlist", "فهرست IPهای مجاز"),
    "id-whitelist": ("ID allowlist", "فهرست شناسه‌های مجاز"),
    "auto-disconnect-timeout": ("Idle timeout (minutes)", "زمان بیکاری (دقیقه)"),
    "direct-access-port": ("Direct access port", "پورت دسترسی مستقیم"),
}


def catalog():
    return ([{"key": k, "en": v[0], "fa": v[1], "values": ["Y", "N"]} for k, v in BOOL_OPTIONS.items()]
            + [{"key": k, "en": k, "fa": k, "values": v} for k, v in ENUM_OPTIONS.items()]
            + [{"key": k, "en": v[0], "fa": v[1], "values": None} for k, v in TEXT_OPTIONS.items()])


def validate_options(options):
    if not isinstance(options, dict) or len(options) > 64:
        raise ValueError("Invalid policy options")
    for key, value in options.items():
        if not isinstance(value, str) or len(value) > 2048 or any(ord(c) < 32 for c in value):
            raise ValueError(f"Invalid value: {key}")
        if key in BOOL_OPTIONS:
            valid = value in ("Y", "N")
        elif key in ENUM_OPTIONS:
            valid = value in ENUM_OPTIONS[key]
        elif key in TEXT_OPTIONS:
            valid = True
            if key in ("custom-rendezvous-server", "relay-server"):
                valid = bool(re.fullmatch(r"[A-Za-z0-9.\-\[\]:]{1,253}", value))
            elif key == "key":
                try:
                    valid = len(base64.b64decode(value, validate=True)) == 32
                except ValueError:
                    valid = False
            elif key in ("auto-disconnect-timeout", "direct-access-port"):
                valid = value.isdecimal() and 1 <= int(value) <= 65535
        else:
            valid = False
        if not valid:
            raise ValueError(f"Unsupported option or value: {key}")
    return options
