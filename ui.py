# ui.py

import sys
import os
from PySide6.QtCore import (
    QCoreApplication, QMetaObject, QRect,
    QSize, Qt
)
from PySide6.QtGui import (
    QAction, QFont, QIcon, QColor, QPalette, QPixmap,
    QPainter, QPainterPath
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFrame, QGridLayout, QScrollArea,
    QStackedWidget, QSpacerItem, QSizePolicy,
    QButtonGroup, QComboBox
)
import qtawesome as qta


def get_base_path() -> str:
    """
    Gibt den korrekten Basispfad zurück, egal ob als Skript oder PyInstaller-Bundle ausgeführt.
    """
    try:
        # PyInstaller erstellt einen temporären Ordner und speichert den Pfad in _MEIPASS
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    except AttributeError:
        # Wenn nicht gebündelt, den Pfad des Skripts verwenden
        base_path = os.path.dirname(os.path.abspath(__file__))
    return base_path


class Ui_MainWindow(object):
    """
    Diese Klasse definiert die Benutzeroberfläche des Hauptfensters.
    Sie enthält keine Anwendungslogik.
    """

    def create_rounded_pixmap(self, source_pixmap: QPixmap, radius: int) -> QPixmap:
        """
        Erstellt aus einem Quell-Pixmap ein neues Pixmap mit abgerundeten Ecken.
        """
        if source_pixmap.isNull():
            return QPixmap()

        rounded = QPixmap(source_pixmap.size())
        rounded.fill(Qt.GlobalColor.transparent)

        painter = QPainter(rounded)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        path = QPainterPath()
        path.addRoundedRect(rounded.rect(), radius, radius)

        painter.setClipPath(path)
        painter.drawPixmap(0, 0, source_pixmap)
        painter.end()

        return rounded

    def setupUi(self, MainWindow: QMainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1400, 900)
        MainWindow.setWindowTitle("Digitale Stalltafel")

        font = QFont()
        font.setPointSize(10)
        MainWindow.setFont(font)
        MainWindow.setStyleSheet(self.get_stylesheet())

        self.central_widget = QWidget(MainWindow)
        self.central_widget.setObjectName("CentralWidget")
        MainWindow.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(20, 10, 20, 20)
        self.main_layout.setSpacing(15)

        self.header_frame = self._create_header()
        self.main_layout.addWidget(self.header_frame)

        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)

        self.page_einzelplaetze = self._create_einzelplaetze_page()
        self.page_gruppenboxen = self._create_gruppenboxen_page()
        self.page_setup = self._create_setup_page()

        self.stacked_widget.addWidget(self.page_einzelplaetze)
        self.stacked_widget.addWidget(self.page_gruppenboxen)
        self.stacked_widget.addWidget(self.page_setup)

    def _create_header(self) -> QWidget:
        """Erstellt die Kopfzeile mit Logo, Titel und Navigationsbuttons."""
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(15)

        # --- Logo hinzufügen (mit absolutem Pfad für PyInstaller) ---
        logo_label = QLabel()
        logo_size = 100

        # 1. Den korrekten Basispfad ermitteln (funktioniert im Skript & in der App)
        base_path = get_base_path()
        logo_path = os.path.join(base_path, "assets", "logo.png")

        # 2. Originales, quadratisches Bild vom absoluten Pfad laden
        source_pixmap = QPixmap(logo_path)

        # Optional: Prüfen, ob das Laden fehlgeschlagen ist
        if source_pixmap.isNull():
            print(f"WARNUNG: Logodatei konnte nicht geladen werden von: {logo_path}")

        # 3. Unsere Funktion aufrufen, um eine runde Version zu erstellen
        rounded_pixmap = self.create_rounded_pixmap(source_pixmap, 60)

        # 4. Das abgerundete Bild auf die Zielgröße skalieren
        scaled_pixmap = rounded_pixmap.scaled(
            logo_size, logo_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )

        # 5. Das finale Bild im Label setzen
        logo_label.setPixmap(scaled_pixmap)
        logo_label.setFixedSize(logo_size, logo_size)

        header_layout.addWidget(logo_label)
        # --- Ende Logo-Änderung ---

        title_layout = QVBoxLayout()
        title_layout.setSpacing(0)

        title_label = QLabel("Digitale Stalltafel")
        title_label.setObjectName("TitleLabel")

        subtitle_label = QLabel("Hof Krenhuber")
        subtitle_label.setObjectName("SubtitleLabel")

        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)

        header_layout.addLayout(title_layout)
        header_layout.addStretch()

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

        card_schlachtdatum = QFrame()
        card_schlachtdatum.setObjectName("Card")
        card_schlachtdatum_layout = QVBoxLayout(card_schlachtdatum)
        card_schlachtdatum_layout.setSpacing(15)
        label_schlachtdatum_title = QLabel("Schlachtdatum berechnen")
        label_schlachtdatum_title.setObjectName("CardTitle")
        schlachtdatum_control_layout = QHBoxLayout()
        label_schlachtdatum = QLabel("Schlachtalter in Monaten:")
        self.schlachtalter_combo = QComboBox()
        for i in range(1, 25):
            self.schlachtalter_combo.addItem(f"{i} Monate", userData=i)
        self.schlachtalter_combo.setFixedWidth(150)
        schlachtdatum_control_layout.addWidget(label_schlachtdatum)
        schlachtdatum_control_layout.addStretch()
        schlachtdatum_control_layout.addWidget(self.schlachtalter_combo)
        card_schlachtdatum_layout.addWidget(label_schlachtdatum_title)
        card_schlachtdatum_layout.addLayout(schlachtdatum_control_layout)
        layout.addWidget(card_schlachtdatum)

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
        self.btn_drucken_einzel = QPushButton("Drucken")
        self.btn_drucken_einzel.setObjectName("SecondaryButton")
        self.btn_drucken_einzel.setIcon(qta.icon('fa5s.print', color='#2c3e50'))
        btn_layout_einzel.addWidget(self.btn_bestand_einzel)
        btn_layout_einzel.addWidget(self.btn_aktualisieren_einzel)
        btn_layout_einzel.addWidget(self.btn_drucken_einzel)

        card_einzel_layout.addWidget(label_einzel)
        card_einzel_layout.addLayout(btn_layout_einzel)
        layout.addWidget(card_einzel)

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
        self.btn_drucken_gruppe = QPushButton("Drucken")
        self.btn_drucken_gruppe.setObjectName("SecondaryButton")
        self.btn_drucken_gruppe.setIcon(qta.icon('fa5s.print', color='#2c3e50'))
        btn_layout_gruppe.addWidget(self.btn_bestand_gruppe)
        btn_layout_gruppe.addWidget(self.btn_aktualisieren_gruppe)
        btn_layout_gruppe.addWidget(self.btn_drucken_gruppe)

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
        """Erstellt die Seite für die Einzelplätze."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        scroll_area, grid_layout = self._create_scroll_area_with_grid()
        self.einzelplaetze_grid_layout = grid_layout
        layout.addWidget(scroll_area)

        return page

    def _create_gruppenboxen_page(self) -> QWidget:
        """Erstellt die Seite für die Gruppenboxen."""
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

            /* --- GLOBALE KORREKTUR FÜR macOS & Schriften --- */
            QLabel {
                color: #333333; /* Setzt eine dunkle Standard-Textfarbe für alle Labels */
                background-color: transparent; /* Verhindert unerwünschte Hintergrundfarben auf Labels */
            }

            /* --- Spezifische Label-Stile (überschreiben die globale Regel) --- */
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

            /* --- Karten-Design --- */
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