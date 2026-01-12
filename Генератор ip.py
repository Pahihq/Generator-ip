import sys
import random
import ipaddress

from PyQt5.QtCore import Qt, QTimer, QRectF
from PyQt5.QtGui import (
    QPainter, QColor, QPen, QBrush,
    QLinearGradient, QRadialGradient, QFont
)
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame,
    QGraphicsDropShadowEffect
)


I18N = {
    "ru": {
        "window_title": "Генератор IP-адресов",
        "title": "IP / Subnet Generator",
        "hint": "IPv4/IPv6 — выбирает режим. «Сгенерировать» — обновляет сеть.",
        "btn_generate": "Сгенерировать",
        "btn_copy": "Копировать",
        "btn_copied": "Скопировано ✓",
        "meta_v4": "Всего: {total}  •  доступных: {usable}",
        "meta_v6": "Всего: {total}",
        "badge_mode_v4": "MODE: IPv4",
        "badge_mode_v6": "MODE: IPv6",
        "badge_lang": "LANG",
    },
    "en": {
        "window_title": "IP Address Generator",
        "title": "IP / Subnet Generator",
        "hint": "IPv4/IPv6 selects mode. “Generate” refreshes the network.",
        "btn_generate": "Generate",
        "btn_copy": "Copy",
        "btn_copied": "Copied ✓",
        "meta_v4": "Total: {total}  •  usable: {usable}",
        "meta_v6": "Total: {total}",
        "badge_mode_v4": "MODE: IPv4",
        "badge_mode_v6": "MODE: IPv6",
        "badge_lang": "LANG",
    }
}


QSS = """
/* Base */
QWidget {
    color: #EAF6FF;
    font-family: Inter, Segoe UI, Arial;
}

/* Neon Card */
QFrame#NeonCard {
    background: rgba(14, 20, 40, 0.62);
    border-radius: 18px;
}

/* Typography */
QLabel#Title { font-size: 16px; font-weight: 800; letter-spacing: 0.4px; }
QLabel#Hint  { font-size: 11px; color: rgba(234,246,255,0.70); }
QLabel#IP    { font-size: 30px; font-weight: 900; letter-spacing: 1px; }
QLabel#IP    { font-family: "JetBrains Mono", "Cascadia Mono", "Consolas", monospace; }
QLabel#Meta  { font-size: 12px; color: rgba(234,246,255,0.85); }

/* Badges */
QLabel#Badge {
    padding: 6px 10px;
    border-radius: 999px;
    background: rgba(0, 255, 240, 0.10);
    border: 1px solid rgba(0, 255, 240, 0.22);
    color: rgba(234,246,255,0.92);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.8px;
}

/* Buttons base */
QPushButton {
    padding: 10px 14px;
    border-radius: 12px;
    font-weight: 700;
    letter-spacing: 0.6px;
    background: rgba(0, 255, 240, 0.06);
    border: 1px solid rgba(0, 255, 240, 0.18);
    color: rgba(234,246,255,0.92);
}
QPushButton:hover {
    background: rgba(0, 255, 240, 0.10);
    border: 1px solid rgba(0, 255, 240, 0.30);
}
QPushButton:pressed {
    background: rgba(0, 255, 240, 0.05);
    border: 1px solid rgba(0, 255, 240, 0.14);
}

/* Segmented (IPv4/IPv6, RU/EN) */
QPushButton#Seg { padding: 9px 12px; }
QPushButton#Seg[active="true"] {
    background: rgba(0, 255, 240, 0.14);
    border: 1px solid rgba(0, 255, 240, 0.50);
}

/* Primary Neon (Copy) */
QPushButton#Primary {
    background: rgba(92, 120, 255, 0.20);
    border: 1px solid rgba(92, 120, 255, 0.55);
}
QPushButton#Primary:hover {
    background: rgba(92, 120, 255, 0.28);
    border: 1px solid rgba(92, 120, 255, 0.70);
}

/* Accent Neon (Generate) */
QPushButton#Accent {
    background: rgba(255, 0, 214, 0.14);
    border: 1px solid rgba(255, 0, 214, 0.55);
}
QPushButton#Accent:hover {
    background: rgba(255, 0, 214, 0.20);
    border: 1px solid rgba(255, 0, 214, 0.75);
}
"""


def count_usable_ipv4(net: ipaddress.IPv4Network) -> int:
    if net.prefixlen >= 31:
        return net.num_addresses
    return max(0, net.num_addresses - 2)


class NeonCard(QFrame):
    """Карточка со светящейся неоновой рамкой."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("NeonCard")

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        r = QRectF(self.rect()).adjusted(1.0, 1.0, -1.0, -1.0)
        radius = 18.0

        # Neon gradient border
        g = QLinearGradient(r.topLeft(), r.bottomRight())
        g.setColorAt(0.0, QColor(0, 255, 240, 180))
        g.setColorAt(0.5, QColor(92, 120, 255, 170))
        g.setColorAt(1.0, QColor(255, 0, 214, 160))

        pen = QPen(QBrush(g), 1.6)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)

        # Outer glow (draw a couple of soft strokes)
        glow_pen = QPen(QBrush(g), 6.0)
        glow_pen.setColor(QColor(0, 255, 240, 35))
        p.setPen(glow_pen)
        p.drawRoundedRect(r, radius, radius)

        glow_pen2 = QPen(QBrush(g), 3.0)
        glow_pen2.setColor(QColor(255, 0, 214, 28))
        p.setPen(glow_pen2)
        p.drawRoundedRect(r, radius, radius)

        # Crisp border
        p.setPen(pen)
        p.drawRoundedRect(r, radius, radius)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.lang = "ru"
        self.current_version = 4
        self._last_total = None
        self._last_usable = None

        self._copied_timer = QTimer(self)
        self._copied_timer.setSingleShot(True)
        self._copied_timer.timeout.connect(self._reset_copy_button)

        self.setStyleSheet(QSS)
        self.resize(860, 460)

        self.build_ui()
        self.set_language(self.lang)
        self.generate_ip(4)

    def tr(self, key: str) -> str:
        return I18N[self.lang][key]

    # Futuristic background
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()

        # Base gradient
        bg = QLinearGradient(rect.topLeft(), rect.bottomRight())
        bg.setColorAt(0.0, QColor(6, 10, 24))
        bg.setColorAt(0.55, QColor(10, 14, 34))
        bg.setColorAt(1.0, QColor(4, 8, 20))
        p.fillRect(rect, bg)

        # Radial glow
        rg = QRadialGradient(rect.center(), rect.width() * 0.65)
        rg.setColorAt(0.0, QColor(0, 255, 240, 28))
        rg.setColorAt(0.6, QColor(92, 120, 255, 18))
        rg.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.fillRect(rect, rg)

        # Grid
        grid_pen = QPen(QColor(0, 255, 240, 18), 1)
        p.setPen(grid_pen)
        step = 28
        for x in range(0, rect.width(), step):
            p.drawLine(x, 0, x, rect.height())
        for y in range(0, rect.height(), step):
            p.drawLine(0, y, rect.width(), y)

        # Scanlines
        scan_pen = QPen(QColor(255, 255, 255, 10), 1)
        p.setPen(scan_pen)
        for y in range(0, rect.height(), 3):
            p.drawLine(0, y, rect.width(), y)

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(18)

        card = NeonCard(self)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(12)

        # Soft shadow under card
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(36)
        shadow.setOffset(0, 16)
        shadow.setColor(QColor(0, 0, 0, 160))
        card.setGraphicsEffect(shadow)

        # Header row
        top = QHBoxLayout()
        top.setSpacing(10)

        self.title_label = QLabel("", self)
        self.title_label.setObjectName("Title")

        self.badge_mode = QLabel("MODE: IPv4", self)
        self.badge_mode.setObjectName("Badge")

        self.badge_lang = QLabel("LANG", self)
        self.badge_lang.setObjectName("Badge")

        self.ru_button = QPushButton("RU", self)
        self.ru_button.setObjectName("Seg")
        self.ru_button.clicked.connect(lambda: self.set_language("ru"))

        self.en_button = QPushButton("EN", self)
        self.en_button.setObjectName("Seg")
        self.en_button.clicked.connect(lambda: self.set_language("en"))

        top.addWidget(self.title_label)
        top.addStretch(1)
        top.addWidget(self.badge_mode)
        top.addSpacing(6)
        top.addWidget(self.badge_lang)
        top.addWidget(self.ru_button)
        top.addWidget(self.en_button)

        self.hint_label = QLabel("", self)
        self.hint_label.setObjectName("Hint")

        self.ip_label = QLabel("—", self)
        self.ip_label.setObjectName("IP")
        self.ip_label.setAlignment(Qt.AlignCenter)

        self.meta_label = QLabel("", self)
        self.meta_label.setObjectName("Meta")
        self.meta_label.setAlignment(Qt.AlignCenter)

        # Controls row
        controls = QHBoxLayout()
        controls.setSpacing(10)

        self.ipv4_button = QPushButton("IPv4", self)
        self.ipv4_button.setObjectName("Seg")
        self.ipv4_button.clicked.connect(lambda: self.generate_ip(4))

        self.ipv6_button = QPushButton("IPv6", self)
        self.ipv6_button.setObjectName("Seg")
        self.ipv6_button.clicked.connect(lambda: self.generate_ip(6))

        self.generate_button = QPushButton("", self)
        self.generate_button.setObjectName("Accent")
        self.generate_button.clicked.connect(self.generate_again)

        self.copy_button = QPushButton("", self)
        self.copy_button.setObjectName("Primary")
        self.copy_button.clicked.connect(self.copy_ip)

        controls.addWidget(self.ipv4_button)
        controls.addWidget(self.ipv6_button)
        controls.addStretch(1)
        controls.addWidget(self.generate_button)
        controls.addWidget(self.copy_button)

        card_layout.addLayout(top)
        card_layout.addWidget(self.hint_label)
        card_layout.addSpacing(4)
        card_layout.addWidget(self.ip_label)
        card_layout.addWidget(self.meta_label)
        card_layout.addSpacing(6)
        card_layout.addLayout(controls)

        root.addStretch(1)
        root.addWidget(card)
        root.addStretch(1)

    def _refresh_btn(self, btn: QPushButton):
        btn.style().unpolish(btn)
        btn.style().polish(btn)

    def _set_active_seg(self, v: int):
        self.ipv4_button.setProperty("active", v == 4)
        self.ipv6_button.setProperty("active", v == 6)
        self._refresh_btn(self.ipv4_button)
        self._refresh_btn(self.ipv6_button)

        self.badge_mode.setText(self.tr("badge_mode_v4") if v == 4 else self.tr("badge_mode_v6"))

    def _set_active_lang(self):
        self.ru_button.setProperty("active", self.lang == "ru")
        self.en_button.setProperty("active", self.lang == "en")
        self._refresh_btn(self.ru_button)
        self._refresh_btn(self.en_button)

    def set_language(self, lang: str):
        self.lang = lang
        self._set_active_lang()

        self.setWindowTitle(self.tr("window_title"))
        self.title_label.setText(self.tr("title"))
        self.hint_label.setText(self.tr("hint"))
        self.badge_lang.setText(self.tr("badge_lang"))

        self.generate_button.setText(self.tr("btn_generate"))
        self._reset_copy_button()
        self._render_meta()
        self._set_active_seg(self.current_version)

    def _render_meta(self):
        if self._last_total is None:
            self.meta_label.setText("")
            return

        if self.current_version == 4:
            self.meta_label.setText(
                self.tr("meta_v4").format(total=self._last_total, usable=self._last_usable)
            )
        else:
            self.meta_label.setText(
                self.tr("meta_v6").format(total=self._last_total)
            )

    def generate_again(self):
        self.generate_ip(self.current_version)

    def generate_ip(self, version: int):
        self.current_version = version
        self._set_active_seg(version)

        if version == 4:
            prefix = random.randint(8, 30)
            host_bits = 32 - prefix
            net_int = random.getrandbits(32) & (~((1 << host_bits) - 1))
            net = ipaddress.IPv4Network((net_int, prefix), strict=True)

            self.ip_label.setText(str(net))
            self._last_total = net.num_addresses
            self._last_usable = count_usable_ipv4(net)
        else:
            prefix = random.randint(32, 124)
            host_bits = 128 - prefix
            net_int = random.getrandbits(128) & (~((1 << host_bits) - 1))
            net = ipaddress.IPv6Network((net_int, prefix), strict=True)

            self.ip_label.setText(str(net.compressed))
            self._last_total = net.num_addresses
            self._last_usable = None

        self._render_meta()
        self._reset_copy_button()

    def copy_ip(self):
        text = self.ip_label.text().strip()
        if not text or text == "—":
            return
        QApplication.clipboard().setText(text)
        self.copy_button.setText(self.tr("btn_copied"))
        self._copied_timer.start(1200)

    def _reset_copy_button(self):
        self.copy_button.setText(self.tr("btn_copy"))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
