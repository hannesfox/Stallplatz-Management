# ui.py (korrigiert)

import sys
from PySide6.QtCore import (
    QCoreApplication, QMetaObject, QRect,
    QSize, Qt
)
from PySide6.QtGui import (
    QAction, QFont, QIcon, QColor, QPalette
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFrame, QGridLayout, QScrollArea,
    QStackedWidget, QSpacerItem, QSizePolicy,
    QButtonGroup
)
import qtawesome as qta


class Ui_MainWindow(object):
    """
    Diese Klasse definiert die Benutzeroberfläche des Hauptfensters.
    Sie enthält keine Anwendungslogik.
    """

    def setupUi(self, MainWindow: QMainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1400, 900)
        MainWindow.setWindowTitle("Digitale Stalltafel")

        # Globale Schriftart und Styling
        font = QFont()
        font.setPointSize(10)
        MainWindow.setFont(font)
        MainWindow.setStyleSheet(self.get_stylesheet())

        # Zentrales Widget und Hauptlayout
        self.central_widget = QWidget(MainWindow)
        self.central_widget.setObjectName("CentralWidget")
        MainWindow.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(20, 10, 20, 20)
        self.main_layout.setSpacing(15)

        # 1. Kopfzeile erstellen und hinzufügen
        self.header_frame = self._create_header()
        self.main_layout.addWidget(self.header_frame)

        # 2. QStackedWidget für die verschiedenen Seiten
        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)

        # 3. Die drei Seiten erstellen und zum Stack hinzufügen
        self.page_einzelplaetze = self._create_einzelplaetze_page()
        self.page_gruppenboxen = self._create_gruppenboxen_page()
        self.page_setup = self._create_setup_page()

        self.stacked_widget.addWidget(self.page_einzelplaetze)
        self.stacked_widget.addWidget(self.page_gruppenboxen)
        self.stacked_widget.addWidget(self.page_setup)

    def _create_header(self) -> QWidget:
        """Erstellt die Kopfzeile mit Titel und Navigationsbuttons."""
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(0)

        title_label = QLabel("Digitale Stalltafel")
        title_label.setObjectName("TitleLabel")

        subtitle_label = QLabel("Hof Kienhuber")
        subtitle_label.setObjectName("SubtitleLabel")

        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)

        header_layout.addLayout(title_layout)
        header_layout.addStretch()

        # Button-Gruppe für exklusives Umschalten
        self.button_group = QButtonGroup()
        self.button_group.setExclusive(True)

        self.btn_einzelplaetze = QPushButton("Einzelplätze")
        self.btn_einzelplaetze.setObjectName("HeaderButton")
        self.btn_einzelplaetze.setCheckable(True)
        self.btn_einzelplaetze.setIcon(qta.icon('fa5s.user', color='white'))
        self.button_group.addButton(self.btn_einzelplaetze, 0)

        self.btn_gruppenboxen = QPushButton("Gruppenboxen")
        self.btn_gruppenboxen.setObjectName("HeaderButton")
        self.btn_gruppenboxen.setCheckable(True)
        self.btn_gruppenboxen.setIcon(qta.icon('fa5s.users', color='white'))
        self.button_group.addButton(self.btn_gruppenboxen, 1)

        self.btn_setup = QPushButton("Setup")
        self.btn_setup.setObjectName("HeaderButton")
        self.btn_setup.setCheckable(True)
        self.btn_setup.setIcon(qta.icon('fa5s.cog', color='white'))
        self.button_group.addButton(self.btn_setup, 2)

        header_layout.addWidget(self.btn_einzelplaetze)
        header_layout.addWidget(self.btn_gruppenboxen)
        header_layout.addWidget(self.btn_setup)

        return header_widget

    def _create_setup_page(self) -> QWidget:
        """Erstellt die Setup-Seite."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(10, 20, 10, 10)
        layout.setSpacing(30)

        # --- Card Einzelplätze ---
        card_einzel = QFrame()
        card_einzel.setObjectName("Card")
        card_einzel_layout = QVBoxLayout(card_einzel)
        card_einzel_layout.setSpacing(20)

        label_einzel = QLabel("Setup für Einzelplätze")
        label_einzel.setObjectName("CardTitle")

        btn_layout_einzel = QHBoxLayout()
        self.btn_bestand_einzel = QPushButton("Bestand aufnehmen")
        self.btn_bestand_einzel.setObjectName("PrimaryButton")
        self.btn_aktualisieren_einzel = QPushButton("Aktualisieren")
        self.btn_aktualisieren_einzel.setObjectName("SecondaryButton")
        btn_layout_einzel.addWidget(self.btn_bestand_einzel)
        btn_layout_einzel.addWidget(self.btn_aktualisieren_einzel)

        card_einzel_layout.addWidget(label_einzel)
        card_einzel_layout.addLayout(btn_layout_einzel)
        layout.addWidget(card_einzel)

        # --- Card Gruppenboxen ---
        card_gruppe = QFrame()
        card_gruppe.setObjectName("Card")
        card_gruppe_layout = QVBoxLayout(card_gruppe)
        card_gruppe_layout.setSpacing(20)

        label_gruppe = QLabel("Setup für Gruppenboxen")
        label_gruppe.setObjectName("CardTitle")

        btn_layout_gruppe = QHBoxLayout()
        self.btn_bestand_gruppe = QPushButton("Bestand aufnehmen")
        self.btn_bestand_gruppe.setObjectName("PrimaryButton")
        self.btn_aktualisieren_gruppe = QPushButton("Aktualisieren")
        self.btn_aktualisieren_gruppe.setObjectName("SecondaryButton")
        btn_layout_gruppe.addWidget(self.btn_bestand_gruppe)
        btn_layout_gruppe.addWidget(self.btn_aktualisieren_gruppe)

        card_gruppe_layout.addWidget(label_gruppe)
        card_gruppe_layout.addLayout(btn_layout_gruppe)
        layout.addWidget(card_gruppe)

        return page

    def _create_scroll_area_with_grid(self) -> tuple[QScrollArea, QGridLayout]:
        """Hilfsfunktion, um eine Scroll-Area mit einem Grid-Layout zu erstellen."""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setObjectName("ScrollArea")

        scroll_content = QWidget()
        grid_layout = QGridLayout(scroll_content)
        grid_layout.setSpacing(20)
        grid_layout.setContentsMargins(10, 10, 10, 10)

        scroll_area.setWidget(scroll_content)
        return scroll_area, grid_layout

    def _create_einzelplaetze_page(self) -> QWidget:
        """Erstellt die Seite für die Einzelplätze (Platzhalter)."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        scroll_area, grid_layout = self._create_scroll_area_with_grid()
        self.einzelplaetze_grid_layout = grid_layout
        layout.addWidget(scroll_area)

        return page

    def _create_gruppenboxen_page(self) -> QWidget:
        """Erstellt die Seite für die Gruppenboxen (Platzhalter)."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        scroll_area, grid_layout = self._create_scroll_area_with_grid()
        self.gruppenboxen_grid_layout = grid_layout
        layout.addWidget(scroll_area)

        return page



    def get_stylesheet(self) -> str:
        """Gibt den QSS-Stylesheet-String für die Anwendung zurück."""
        return """
            /* --- Globale Einstellungen --- */
            #MainWindow, #CentralWidget {
                background-color: #f0f2f5;
            }

            /* --- Labels --- */
            #TitleLabel {
                font-size: 28px;
                font-weight: bold;
                color: #2c3e50;
            }
            #SubtitleLabel {
                font-size: 14px;
                color: #7f8c8d;
            }
            #CardTitle {
                font-size: 18px;
                font-weight: bold;
                color: #34495e;
            }
            #PlatzFreiLabel {
                font-size: 16px;
                font-style: italic;
                color: #95a5a6;
            }

            /* --- Buttons in der Kopfzeile --- */
            QPushButton#HeaderButton {
                background-color: #34495e;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton#HeaderButton:hover {
                background-color: #4a6572;
            }
            QPushButton#HeaderButton:checked {
                background-color: #2c3e50;
                border-bottom: 3px solid #3498db;
            }

            /* --- Buttons auf der Setup-Seite --- */
            QPushButton#PrimaryButton, QPushButton#SecondaryButton {
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton#PrimaryButton {
                background-color: #2c3e50;
                color: white;
            }
            QPushButton#PrimaryButton:hover {
                background-color: #34495e;
            }
            QPushButton#SecondaryButton {
                background-color: white;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
            }
            QPushButton#SecondaryButton:hover {
                background-color: #ecf0f1;
            }

            /* --- KARTEN-DESIGN KORRIGIERT --- */
            QFrame#Card {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }

            /* --- Scroll-Area --- */
            QScrollArea#ScrollArea {
                border: none;
            }
        """