import sys
import random
import ipaddress
import math

from PyQt5.QtCore import Qt, QTimer, QRectF
from PyQt5.QtGui import (
    QPainter, QColor, QPen, QBrush,
    QLinearGradient, QRadialGradient
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
        "hint": "1/2 — IPv4/IPv6 • G — сгенерировать • C — копировать • R/E — язык • Esc — выход",
        "btn_generate": "Сгенерировать",
        "btn_copy": "Копировать",
        "btn_copied": "Скопировано ✓",
        "meta_v4": "Всего: {total}  •  доступных: {usable}",
        "meta_v6": "Всего: {total}",
        "badge_mode_v4": "MODE: IPv4",
        "badge_mode_v6": "MODE: IPv6",
        "badge_lang": "LANG",
        "status": "STATUS: ONLINE",
    },
    "en": {
        "window_title": "IP Address Generator",
        "title": "IP / Subnet Generator",
        "hint": "1/2 — IPv4/IPv6 • G — generate • C — copy • R/E — language • Esc — exit",
        "btn_generate": "Generate",
        "btn_copy": "Copy",
        "btn_copied": "Copied ✓",
        "meta_v4": "Total: {total}  •  usable: {usable}",
        "meta_v6": "Total: {total}",
        "badge_mode_v4": "MODE: IPv4",
        "badge_mode_v6": "MODE: IPv6",
        "badge_lang": "LANG",
        "status": "STATUS: ONLINE",
    }
}

QSS = """
QWidget { color: #EAF6FF; font-family: Inter, Segoe UI, Arial; }

/* Card */
QFrame#NeonCard { background: rgba(14, 20, 40, 0.62); border-radius: 18px; }

/* Top bar */
QFrame#TopBar {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
}
QLabel#TopText {
    font-size: 11px;
    color: rgba(234,246,255,0.80);
    letter-spacing: 0.9px;
    font-weight: 700;
}
QLabel#Title { font-size: 16px; font-weight: 900; letter-spacing: 0.6px; }
QLabel#Hint  { font-size: 11px; color: rgba(234,246,255,0.70); }
QLabel#IP    { font-size: 30px; font-weight: 900; letter-spacing: 1px;
              font-family: "JetBrains Mono","Cascadia Mono","Consolas",monospace; }
QLabel#Meta  { font-size: 12px; color: rgba(234,246,255,0.85); }

/* Badges */
QLabel#Badge {
    padding: 6px 10px;
    border-radius: 999px;
    background: rgba(0, 255, 240, 0.10);
    border: 1px solid rgba(0, 255, 240, 0.22);
    color: rgba(234,246,255,0.92);
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.8px;
}

/* Buttons */
QPushButton {
    padding: 10px 14px;
    border-radius: 12px;
    font-weight: 800;
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

/* Seg */
QPushButton#Seg { padding: 9px 12px; }
QPushButton#Seg[active="true"] {
    background: rgba(0, 255, 240, 0.14);
    border: 1px solid rgba(0, 255, 240, 0.50);
}

/* Primary (Copy) */
QPushButton#Primary {
    background: rgba(92, 120, 255, 0.20);
    border: 1px solid rgba(92, 120, 255, 0.55);
}
QPushButton#Primary:hover {
    background: rgba(92, 120, 255, 0.28);
    border: 1px solid rgba(92, 120, 255, 0.70);
}

/* Accent (Generate) */
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

class PulseDot(QWidget):
    """Пульсирующая точка-индикатор."""
    def __init__(self, color: QColor, parent=None):
        super().__init__(parent)
        self.base = color
        self.phase = 0.0
        self.setFixedSize(12, 12)

    def set_phase(self, phase: float):
        self.phase = phase
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # 0..1
        t = (math.sin(self.phase) + 1.0) / 2.0
        glow_alpha = int(35 + 70 * t)
        core_alpha = int(160 + 70 * t)

        r = QRectF(0.5, 0.5, self.width() - 1.0, self.height() - 1.0)

        # glow
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(self.base.red(), self.base.green(), self.base.blue(), glow_alpha))
        p.drawEllipse(r.adjusted(-2.5, -2.5, 2.5, 2.5))

        # core
        p.setBrush(QColor(self.base.red(), self.base.green(), self.base.blue(), core_alpha))
        p.drawEllipse(r)

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

        g = QLinearGradient(r.topLeft(), r.bottomRight())
        g.setColorAt(0.0, QColor(0, 255, 240, 180))
        g.setColorAt(0.5, QColor(92, 120, 255, 170))
        g.setColorAt(1.0, QColor(255, 0, 214, 160))

        # soft glow strokes
        p.setPen(QPen(QColor(0, 255, 240, 28), 6.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        p.drawRoundedRect(r, radius, radius)
        p.setPen(QPen(QColor(255, 0, 214, 22), 3.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        p.drawRoundedRect(r, radius, radius)

        # crisp border
        pen = QPen(QBrush(g), 1.6)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
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

        self._anim_phase = 0.0
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._tick_anim)
        self._anim_timer.start(40)

        self.setStyleSheet(QSS)
        self.resize(900, 500)

        self.build_ui()
        self.set_language(self.lang)
        self.generate_ip(4)

    def tr(self, key: str) -> str:
        return I18N[self.lang][key]

    # Futuristic background
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()

        bg = QLinearGradient(rect.topLeft(), rect.bottomRight())
        bg.setColorAt(0.0, QColor(6, 10, 24))
        bg.setColorAt(0.55, QColor(10, 14, 34))
        bg.setColorAt(1.0, QColor(4, 8, 20))
        p.fillRect(rect, bg)

        rg = QRadialGradient(rect.center(), rect.width() * 0.65)
        rg.setColorAt(0.0, QColor(0, 255, 240, 26))
        rg.setColorAt(0.6, QColor(92, 120, 255, 16))
        rg.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.fillRect(rect, rg)

        # grid
        p.setPen(QPen(QColor(0, 255, 240, 16), 1))
        step = 28
        for x in range(0, rect.width(), step):
            p.drawLine(x, 0, x, rect.height())
        for y in range(0, rect.height(), step):
            p.drawLine(0, y, rect.width(), y)

        # scanlines
        p.setPen(QPen(QColor(255, 255, 255, 9), 1))
        for y in range(0, rect.height(), 3):
            p.drawLine(0, y, rect.width(), y)

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(18)

        card = NeonCard(self)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 18, 18, 18)
        card_layout.setSpacing(12)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 18)
        shadow.setColor(QColor(0, 0, 0, 170))
        card.setGraphicsEffect(shadow)

        # --- TopBar (terminal-like) ---
        topbar = QFrame(self)
        topbar.setObjectName("TopBar")
        topbar_l = QHBoxLayout(topbar)
        topbar_l.setContentsMargins(12, 10, 12, 10)
        topbar_l.setSpacing(10)

        # left "window dots" (static look)
        dots = QHBoxLayout()
        dots.setSpacing(8)
        self.dot_red = PulseDot(QColor(255, 80, 105), self)
        self.dot_yel = PulseDot(QColor(255, 210, 90), self)
        self.dot_grn = PulseDot(QColor(70, 255, 160), self)
        dots.addWidget(self.dot_red)
        dots.addWidget(self.dot_yel)
        dots.addWidget(self.dot_grn)

        self.top_text = QLabel("", self)
        self.top_text.setObjectName("TopText")
        self.top_text.setAlignment(Qt.AlignCenter)

        # right status pulse (separate)
        self.dot_net = PulseDot(QColor(0, 255, 240), self)
        self.status_text = QLabel("", self)
        self.status_text.setObjectName("TopText")

        right = QHBoxLayout()
        right.setSpacing(8)
        right.addWidget(self.dot_net)
        right.addWidget(self.status_text)

        topbar_l.addLayout(dots)
        topbar_l.addStretch(1)
        topbar_l.addWidget(self.top_text)
        topbar_l.addStretch(1)
        topbar_l.addLayout(right)

        # --- Header row (title + badges + lang buttons) ---
        header = QHBoxLayout()
        header.setSpacing(10)

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

        header.addWidget(self.title_label)
        header.addStretch(1)
        header.addWidget(self.badge_mode)
        header.addSpacing(6)
        header.addWidget(self.badge_lang)
        header.addWidget(self.ru_button)
        header.addWidget(self.en_button)

        self.hint_label = QLabel("", self)
        self.hint_label.setObjectName("Hint")

        self.ip_label = QLabel("—", self)
        self.ip_label.setObjectName("IP")
        self.ip_label.setAlignment(Qt.AlignCenter)

        self.meta_label = QLabel("", self)
        self.meta_label.setObjectName("Meta")
        self.meta_label.setAlignment(Qt.AlignCenter)

        # --- Controls row ---
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

        card_layout.addWidget(topbar)
        card_layout.addLayout(header)
        card_layout.addWidget(self.hint_label)
        card_layout.addSpacing(4)
        card_layout.addWidget(self.ip_label)
        card_layout.addWidget(self.meta_label)
        card_layout.addSpacing(6)
        card_layout.addLayout(controls)

        root.addStretch(1)
        root.addWidget(card)
        root.addStretch(1)

    def _tick_anim(self):
        self._anim_phase += 0.15
        # разные фазы, чтобы не мигали одинаково
        self.dot_red.set_phase(self._anim_phase + 0.0)
        self.dot_yel.set_phase(self._anim_phase + 1.2)
        self.dot_grn.set_phase(self._anim_phase + 2.4)
        self.dot_net.set_phase(self._anim_phase + 0.7)

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
        self.status_text.setText(self.tr("status"))
        self.top_text.setText("NEURAL NET / IP CORE v2.1")  # просто “футуристичная” строка

        self.generate_button.setText(self.tr("btn_generate"))
        self._reset_copy_button()
        self._render_meta()
        self._set_active_seg(self.current_version)

    def _render_meta(self):
        if self._last_total is None:
            self.meta_label.setText("")
            return
        if self.current_version == 4:
            self.meta_label.setText(self.tr("meta_v4").format(total=self._last_total, usable=self._last_usable))
        else:
            self.meta_label.setText(self.tr("meta_v6").format(total=self._last_total))

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

    # Горячие клавиши
    def keyPressEvent(self, e):
        k = e.key()
        if k == Qt.Key_Escape:
            self.close()
            return
        if k == Qt.Key_G:
            self.generate_again()
            return
        if k == Qt.Key_C:
            self.copy_ip()
            return
        if k == Qt.Key_1:
            self.generate_ip(4)
            return
        if k == Qt.Key_2:
            self.generate_ip(6)
            return
        if k == Qt.Key_R:
            self.set_language("ru")
            return
        if k == Qt.Key_E:
            self.set_language("en")
            return
        super().keyPressEvent(e)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
