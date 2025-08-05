# main.py (korrigiert)

import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QFrame, QSpacerItem, QSizePolicy,
    QGraphicsDropShadowEffect
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt
import qtawesome as qta

from ui import Ui_MainWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.button_group.buttonClicked.connect(self.switch_page)
        self.ui.stacked_widget.setCurrentIndex(0)
        self.ui.btn_einzelplaetze.setChecked(True)

        self.populate_einzelplaetze()
        self.populate_gruppenboxen()

    def switch_page(self, button):
        index = self.ui.button_group.id(button)
        self.ui.stacked_widget.setCurrentIndex(index)

    def _apply_shadow(self, widget: QWidget):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 35))
        shadow.setOffset(0, 3)
        widget.setGraphicsEffect(shadow)

    def _create_info_row(self, icon_name: str, label: str, value: str) -> QWidget:
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(10)
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon(icon_name, color='#7f8c8d').pixmap(16, 16))
        icon_label.setFixedWidth(20)
        text_label = QLabel(f"{label}")
        text_label.setFixedWidth(70)
        value_label = QLabel(f"<b>{value}</b>")
        row_layout.addWidget(icon_label)
        row_layout.addWidget(text_label)
        row_layout.addWidget(value_label)
        row_layout.addStretch()
        return row_widget

    def populate_einzelplaetze(self):
        data = [
            (1, {'id': 'DE089012345678', 'alter': '5 Jahre', 'gewicht': '650 kg', 'datum': '15.5.2024'}), (2, None),
            (3, {'id': 'AT4568292983', 'alter': '3 Jahre', 'gewicht': '580 kg', 'datum': '20.11.2023'}), (4, {'id': 'CH012023456789', 'alter': '7 Jahre', 'gewicht': '710 kg', 'datum': '5.1.2024'}), (5, None),
            (6, {'id': 'DE0895544322', 'alter': '4 Jahre', 'gewicht': '620 kg', 'datum': '1.7.2024'}), (7, {'id': 'DE0890802345', 'alter': '6 Jahre', 'gewicht': '685 kg', 'datum': '30.8.2022'}), (8, None),
            (9, {'id': 'AT9988776655', 'alter': '2 Jahre', 'gewicht': '490 kg', 'datum': '18.6.2024'}), (10, {'id': 'DE0802111223S', 'alter': '8 Jahre', 'gewicht': '750 kg', 'datum': '24.12.2021'}),
            (11, {'id': 'DE0853511122', 'alter': '5 Jahre', 'gewicht': '660 kg', 'datum': '28.2.2024'}), (12, None), (13, None),
            (14, {'id': 'DE8987654321', 'alter': '3 Jahre', 'gewicht': '595 kg', 'datum': '15.7.2024'}),
        ]
        cols = 7
        for i, (platz_nr, tier_info) in enumerate(data):
            row, col = divmod(i, cols)
            card = self.create_einzelplatz_card(platz_nr, tier_info)
            self.ui.einzelplaetze_grid_layout.addWidget(card, row, col)

    def create_einzelplatz_card(self, platz_nr: int, tier_info: dict | None) -> QFrame:
        card = QFrame()
        # KORREKTUR HIER:
        card.setObjectName("Card")
        card.setMinimumSize(250, 220)
        self._apply_shadow(card)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 10, 15, 15)
        layout.setSpacing(10)
        header_layout = QHBoxLayout()
        title = QLabel(f"<b>Platz {platz_nr}</b>")
        title.setStyleSheet("font-size: 14px;")
        status_icon = QLabel()
        if tier_info:
            icon = qta.icon('fa5s.check-circle', color='#27ae60')
        else:
            icon = qta.icon('fa5s.minus-circle', color='#e74c3c')
        status_icon.setPixmap(icon.pixmap(24, 24))
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(status_icon)
        layout.addLayout(header_layout)
        if tier_info:
            layout.addWidget(self._create_info_row('fa5s.tag', '# Tier-ID', tier_info['id']))
            layout.addWidget(self._create_info_row('fa5s.birthday-cake', '# Alter', tier_info['alter']))
            layout.addWidget(self._create_info_row('fa5s.weight-hanging', '# Gewicht', tier_info['gewicht']))
            layout.addWidget(self._create_info_row('fa5s.calendar-alt', '# Eingelagert', tier_info['datum']))
            layout.addStretch()
        else:
            frei_label = QLabel("<i>Platz ist frei</i>")
            frei_label.setObjectName("PlatzFreiLabel")
            frei_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addStretch()
            layout.addWidget(frei_label)
            layout.addStretch()
        return card

    def populate_gruppenboxen(self):
        data = [
            {'box_nr': 1, 'max_plaetze': 3, 'tiere': [{'id': 'DE82123235667', 'alter': '2 Jahre', 'gewicht': '450 kg', 'datum': '10.7.2024'}, {'id': 'DE82123235668', 'alter': '2 Jahre', 'gewicht': '460 kg', 'datum': '10.7.2024'}]},
            {'box_nr': 2, 'max_plaetze': 3, 'tiere': [{'id': 'AT1234567890', 'alter': '3 Jahre', 'gewicht': '510 kg', 'datum': '1.6.2024'}, {'id': 'AT1234567891', 'alter': '3 Jahre', 'gewicht': '505 kg', 'datum': '1.6.2024'}, {'id': 'AT1234567892', 'alter': '3 Jahre', 'gewicht': '520 kg', 'datum': '1.6.2024'}]},
            {'box_nr': 3, 'max_plaetze': 3, 'tiere': []},
            {'box_nr': 4, 'max_plaetze': 3, 'tiere': [{'id': 'DE81777888999', 'alter': '1 Jahre', 'gewicht': '380 kg', 'datum': '20.7.2024'}]},
            {'box_nr': 5, 'max_plaetze': 3, 'tiere': [{'id': 'CH9876543210', 'alter': '4 Jahre', 'gewicht': '600 kg', 'datum': '15.3.2024'}, {'id': 'CH9876543211', 'alter': '4 Jahre', 'gewicht': '615 kg', 'datum': '15.3.2024'}]},
            {'box_nr': 6, 'max_plaetze': 3, 'tiere': []},
        ]
        cols = 3
        for i, box_data in enumerate(data):
            row, col = divmod(i, cols)
            card = self.create_gruppenbox_card(box_data)
            self.ui.gruppenboxen_grid_layout.addWidget(card, row, col)

    def create_gruppenbox_card(self, box_data: dict) -> QFrame:
        card = QFrame()
        # KORREKTUR HIER:
        card.setObjectName("Card")
        card.setMinimumWidth(400)
        self._apply_shadow(card)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 10, 15, 15)
        header_layout = QHBoxLayout()
        title = QLabel(f"<b>Box {box_data['box_nr']}</b>")
        title.setStyleSheet("font-size: 14px;")
        belegt = len(box_data['tiere'])
        max_p = box_data['max_plaetze']
        status_label = QLabel(f"<b>{belegt} / {max_p}</b> Belegt")
        status_label.setStyleSheet("color: #7f8c8d;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(status_label)
        layout.addLayout(header_layout)
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("color: #ecf0f1;")
        layout.addWidget(line)
        for tier in box_data['tiere']:
            tier_layout = QVBoxLayout()
            tier_layout.setSpacing(5)
            tier_layout.addWidget(self._create_info_row('fa5s.tag', '# Tier-ID', tier['id']))
            tier_layout.addWidget(self._create_info_row('fa5s.birthday-cake', '# Alter', tier['alter']))
            tier_layout.addWidget(self._create_info_row('fa5s.weight-hanging', '# Gewicht', tier['gewicht']))
            tier_layout.addWidget(self._create_info_row('fa5s.calendar-alt', '# Eingelagert', tier['datum']))
            layout.addLayout(tier_layout)
            layout.addSpacing(15)
        freie_plaetze = max_p - belegt
        for i in range(freie_plaetze):
            frei_label = QLabel(f"<i>Platz {belegt + i + 1} ist frei</i>")
            frei_label.setStyleSheet("color: #95a5a6; padding-top: 10px; padding-bottom: 10px;")
            layout.addWidget(frei_label)
        layout.addStretch()
        return card

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())