# main.py

import sys
import os
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd
from appdirs import user_data_dir

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QFrame, QDialog, QTextEdit,
    QMessageBox, QFileDialog, QGraphicsDropShadowEffect,
    QPlainTextEdit, QDialogButtonBox
)
from PySide6.QtPrintSupport import QPrinter, QPrintPreviewDialog
from PySide6.QtGui import QColor, QPainter, QTextFormat, QTextDocument, QPageLayout
from PySide6.QtCore import Qt, QRect, QSize, QSettings
import qtawesome as qta
from ui import Ui_MainWindow


# --- Globale Konfiguration & Pfade ---

def get_base_path() -> str:
    """
    Ermittelt den Basispfad für den Zugriff auf Ressourcendateien.
    Funktioniert sowohl im Entwicklungsmodus als auch in einer
    mit PyInstaller gebündelten Anwendung.
    """
    try:
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return base_path


ORG_NAME = "RinderApp"
APP_NAME = "Bestandsmanager"

# App-Datenordner (per appdirs) und State-Datei
DATA_DIR = user_data_dir(APP_NAME, ORG_NAME)
STATE_FILE = os.path.join(DATA_DIR, "state.json")

def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


# --- KONSTANTEN ---
NUM_EINZELPLAETZE = 14
NUM_GRUPPENBOXEN = 6
GRUPPENBOX_SLOTS = 3

REQUIRED_COLUMNS = {
    'Ohrmarke-Name',
    'Geburtsdatum',
    'Rasse(n)',
    'Geschlecht',
}


# --- WIEDERVERWENDBARE KLASSEN ---

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.codeEditor = editor

    def sizeHint(self):
        return QSize(self.codeEditor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.codeEditor.lineNumberAreaPaintEvent(event)


class NumberedTextEdit(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lineNumberArea = LineNumberArea(self)
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        self.updateLineNumberAreaWidth(0)
        self.highlightCurrentLine()

    def lineNumberAreaWidth(self):
        digits = 1
        count = max(1, self.blockCount())
        while count >= 10:
            count //= 10  # int division to avoid float
            digits += 1
        return 10 + self.fontMetrics().horizontalAdvance('9') * digits

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def highlightCurrentLine(self):
        extraSelections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            lineColor = QColor(Qt.yellow).lighter(160)
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)
        self.setExtraSelections(extraSelections)

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), QColor("#e0e0e0"))
        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                painter.setPen(Qt.black)
                painter.drawText(0, int(top), self.lineNumberArea.width() - 5, self.fontMetrics().height(),
                                 Qt.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            blockNumber += 1


class BestandInputDialog(QDialog):
    def __init__(self, required_lines: int, title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Bestand aufnehmen: {title}")
        self.setMinimumSize(420, 520)
        self.required_lines = required_lines
        self.final_data: list[str] | None = None

        layout = QVBoxLayout(self)

        self.info_label = QLabel(
            f"Bitte fügen Sie genau {required_lines} Zeilen ein (eine ID pro Zeile).\n"
            f"Für einen leeren Platz 'Keine Kuh' eingeben."
        )
        self.text_edit = NumberedTextEdit()
        self.text_edit.setPlaceholderText("Eine ID pro Zeile hier einfügen...")
        self.text_edit.textChanged.connect(self.check_line_count)

        self.status_label = QLabel(f"0 / {self.required_lines} Zeilen")
        self.status_label.setStyleSheet("color: #7f8c8d;")

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self)
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
        self.button_box.accepted.connect(self.on_accept)
        self.button_box.rejected.connect(self.reject)

        layout.addWidget(self.info_label)
        layout.addWidget(self.text_edit)
        layout.addWidget(self.status_label)
        layout.addWidget(self.button_box)

        self.text_edit.setFocus()

    def _collect_lines(self) -> list[str]:
        content = self.text_edit.toPlainText()
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        return lines

    def check_line_count(self):
        lines = self._collect_lines()
        count = len(lines)
        extra_hint = ""
        if count > self.required_lines:
            extra_hint = " (es werden die ersten Zeilen verwendet)"
            self.status_label.setStyleSheet("color: #e67e22;")  # orange Hinweis
        elif count == self.required_lines:
            self.status_label.setStyleSheet("color: #2ecc71;")  # grün OK
        else:
            self.status_label.setStyleSheet("color: #7f8c8d;")
        self.status_label.setText(f"{count} / {self.required_lines} Zeilen{extra_hint}")
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(count >= self.required_lines)

    def on_accept(self):
        lines = self._collect_lines()
        if len(lines) < self.required_lines:
            QMessageBox.warning(self, "Unvollständig", f"Bitte genau {self.required_lines} Zeilen eingeben.")
            return
        # Nur die ersten N Zeilen verwenden
        self.final_data = lines[:self.required_lines]
        self.accept()

    def get_data(self) -> list[str] | None:
        if self.exec() == QDialog.Accepted:
            return self.final_data
        return None


# --- HAUPTKLASSE ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # feste Fenstergröße
        self.resize(1950, 950)

        self.einzelplaetze_raw_ids: list[str] = []
        self.gruppenboxen_raw_ids: list[str] = []
        self.einzelplaetze_processed_data: list[dict | None] = []
        self.gruppenboxen_processed_data: list[dict | None] = []
        self._csv_index: dict[str, pd.Series] = {}

        self.settings = QSettings(ORG_NAME, APP_NAME)

        ensure_data_dir()
        self.load_state()

        self.connect_signals()
        self.populate_einzelplaetze()
        self.populate_gruppenboxen()
        self.ui.stacked_widget.setCurrentIndex(0)
        self.ui.btn_setup.setChecked(True)

    def connect_signals(self):
        self.ui.button_group.buttonClicked.connect(self.switch_page)
        self.ui.btn_bestand_einzel.clicked.connect(self.aufnahme_einzelplaetze_ids)
        self.ui.btn_bestand_gruppe.clicked.connect(self.aufnahme_gruppenboxen_ids)
        self.ui.btn_aktualisieren_einzel.clicked.connect(self.update_einzelplaetze_ui)
        self.ui.btn_aktualisieren_gruppe.clicked.connect(self.update_gruppenboxen_ui)
        self.ui.schlachtalter_combo.currentIndexChanged.connect(self.on_schlachtalter_changed)
        self.ui.btn_drucken_einzel.clicked.connect(self.handle_print_einzelplaetze)
        self.ui.btn_drucken_gruppe.clicked.connect(self.handle_print_gruppenboxen)

    def switch_page(self, button):
        self.ui.stacked_widget.setCurrentIndex(self.ui.button_group.id(button))

    # --- Drucken ---
    def handle_print_einzelplaetze(self):
        if not self.einzelplaetze_processed_data:
            QMessageBox.information(self, "Hinweis", "Keine Daten zum Drucken vorhanden.")
            return
        html_content = self.generate_print_html_einzelplaetze()
        self.print_html(html_content, orientation=QPageLayout.Orientation.Landscape)

    def handle_print_gruppenboxen(self):
        if not self.gruppenboxen_processed_data:
            QMessageBox.information(self, "Hinweis", "Keine Daten zum Drucken vorhanden.")
            return
        html_content = self.generate_print_html_gruppenboxen()
        self.print_html(html_content, orientation=QPageLayout.Orientation.Landscape)

    def generate_print_html_einzelplaetze(self) -> str:
        header = "<h1>Einzelplätze Übersicht</h1>"
        table_start = (
            "<table border='1' cellspacing='0' cellpadding='5' width='100%'>"
            "<tr><th>Platz</th><th>Tier-ID</th><th>Geboren</th><th>Alter</th><th>Schlachtung</th><th>Rasse</th></tr>"
        )
        rows = []
        for i in range(NUM_EINZELPLAETZE):
            platz_nr = i + 1
            tier = self.einzelplaetze_processed_data[i] if i < len(self.einzelplaetze_processed_data) else None
            if tier is None:
                rows.append(f"<tr><td>{platz_nr}</td><td colspan='5'><i>Platz ist frei</i></td></tr>")
            elif tier.get('status') == 'not_found':
                rows.append(
                    f"<tr><td>{platz_nr}</td><td colspan='5' style='color:#c0392b;'>"
                    f"<b>ID nicht gefunden:</b> {tier.get('id','')}</td></tr>"
                )
            else:
                rows.append(
                    f"<tr>"
                    f"<td>{platz_nr}</td>"
                    f"<td>{tier.get('id', '')}</td>"
                    f"<td>{tier.get('geburtsdatum', '')}</td>"
                    f"<td>{tier.get('alter', '')}</td>"
                    f"<td>{tier.get('schlachtdatum', '')}</td>"
                    f"<td>{tier.get('rasse', '')}</td>"
                    f"</tr>"
                )
        table_end = "</table>"
        return (
            "<html><head>"
            "<style>"
            "body { font-family: sans-serif; }"
            "table { border-collapse: collapse; }"
            "th, td { text-align: left; }"
            "</style>"
            "</head><body>"
            f"{header}{table_start}{''.join(rows)}{table_end}"
            "</body></html>"
        )

    def generate_print_html_gruppenboxen(self) -> str:
        header = "<h1>Gruppenboxen Übersicht</h1>"
        html_parts = [
            "<html><head><style>"
            "body { font-family: sans-serif; }"
            "table { border-collapse: collapse; }"
            "th, td { text-align: left; }"
            "h2 { margin-top: 20px; }"
            "</style></head><body>",
            header
        ]
        for i in range(NUM_GRUPPENBOXEN):
            box_nr = i + 1
            html_parts.append(f"<h2>Box {box_nr}</h2>")
            html_parts.append(
                "<table border='1' cellspacing='0' cellpadding='5' width='100%'>"
                "<tr><th>Tier-ID</th><th>Geboren</th><th>Alter</th><th>Schlachtung</th><th>Rasse</th></tr>"
            )
            start_index = i * GRUPPENBOX_SLOTS
            end_index = start_index + GRUPPENBOX_SLOTS
            for j in range(start_index, end_index):
                if j >= len(self.gruppenboxen_processed_data):
                    html_parts.append("<tr><td colspan='5'><i>Platz ist frei</i></td></tr>")
                    continue
                tier = self.gruppenboxen_processed_data[j]
                if tier is None:
                    html_parts.append("<tr><td colspan='5'><i>Platz ist frei</i></td></tr>")
                elif tier.get('status') == 'not_found':
                    html_parts.append(
                        "<tr><td colspan='5' style='color:#c0392b;'>"
                        f"<b>ID nicht gefunden:</b> {tier.get('id','')}"
                        "</td></tr>"
                    )
                else:
                    html_parts.append(
                        f"<tr>"
                        f"<td>{tier.get('id', '')}</td>"
                        f"<td>{tier.get('geburtsdatum', '')}</td>"
                        f"<td>{tier.get('alter', '')}</td>"
                        f"<td>{tier.get('schlachtdatum', '')}</td>"
                        f"<td>{tier.get('rasse', '')}</td>"
                        f"</tr>"
                    )
            html_parts.append("</table>")
        html_parts.append("</body></html>")
        return "".join(html_parts)

    def print_html(self, html_content: str, orientation=QPageLayout.Orientation.Portrait):
        printer = QPrinter(QPrinter.HighResolution)

        # Qt6-sicheres Setzen der Ausrichtung über QPageLayout
        layout = printer.pageLayout()
        layout.setOrientation(orientation)
        printer.setPageLayout(layout)

        preview_dialog = QPrintPreviewDialog(printer, self)

        def paint_html_on_printer(p: QPrinter):
            doc = QTextDocument()
            doc.setHtml(html_content)
            doc.print_(p)

        preview_dialog.paintRequested.connect(paint_html_on_printer)
        preview_dialog.exec()

    # --- Datenaufnahme/Update ---
    def aufnahme_einzelplaetze_ids(self):
        dialog = BestandInputDialog(NUM_EINZELPLAETZE, "Einzelplätze", self)
        ids = dialog.get_data()
        if ids:
            self.einzelplaetze_raw_ids = ids

    def aufnahme_gruppenboxen_ids(self):
        dialog = BestandInputDialog(NUM_GRUPPENBOXEN * GRUPPENBOX_SLOTS, "Gruppenboxen", self)
        ids = dialog.get_data()
        if ids:
            self.gruppenboxen_raw_ids = ids

    def update_einzelplaetze_ui(self):
        if not self.einzelplaetze_raw_ids:
            QMessageBox.information(self, "Hinweis", "Bitte zuerst IDs für Einzelplätze eingeben.")
            return
        csv_path = self.get_csv_path()
        if not csv_path:
            return
        df = self.load_csv_data(csv_path)
        if df is None:
            return
        self._csv_index = self.build_index(df)
        self.einzelplaetze_processed_data = self.process_tier_ids(self.einzelplaetze_raw_ids, self._csv_index)
        self.populate_einzelplaetze()
        self.save_state()
        self.ui.stacked_widget.setCurrentIndex(0)
        self.ui.btn_einzelplaetze.setChecked(True)

    def update_gruppenboxen_ui(self):
        if not self.gruppenboxen_raw_ids:
            QMessageBox.information(self, "Hinweis", "Bitte zuerst IDs für Gruppenboxen eingeben.")
            return
        csv_path = self.get_csv_path()
        if not csv_path:
            return
        df = self.load_csv_data(csv_path)
        if df is None:
            return
        self._csv_index = self.build_index(df)
        self.gruppenboxen_processed_data = self.process_tier_ids(self.gruppenboxen_raw_ids, self._csv_index)
        self.populate_gruppenboxen()
        self.save_state()
        self.ui.stacked_widget.setCurrentIndex(1)
        self.ui.btn_gruppenboxen.setChecked(True)

    def on_schlachtalter_changed(self):
        changed = False
        if self.einzelplaetze_processed_data:
            self.reprocess_data(self.einzelplaetze_processed_data)
            self.populate_einzelplaetze()
            changed = True
        if self.gruppenboxen_processed_data:
            self.reprocess_data(self.gruppenboxen_processed_data)
            self.populate_gruppenboxen()
            changed = True
        if changed:
            self.save_state()

    # --- CSV/ID Verarbeitung ---
    def get_csv_path(self) -> str | None:
        start_dir = self.settings.value("last_csv_dir", "")
        file_path, _ = QFileDialog.getOpenFileName(self, "CSV-Datei auswählen", start_dir, "CSV-Dateien (*.csv)")
        if file_path:
            self.settings.setValue("last_csv_dir", os.path.dirname(file_path))
        return file_path

    def load_csv_data(self, file_path: str) -> pd.DataFrame | None:
        try:
            df = pd.read_csv(file_path, delimiter=';', dtype=str, quotechar='"',
                             skipinitialspace=True, encoding='utf-8-sig')
            df.columns = [col.strip() for col in df.columns]
            missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
            if missing:
                QMessageBox.critical(
                    self, "CSV-Fehler",
                    "In der CSV fehlen Spalten:\n- " + "\n- ".join(missing)
                )
                return None
            return df
        except Exception as e:
            QMessageBox.critical(self, "CSV-Fehler", f"Konnte CSV-Datei nicht laden:\n{e}")
            return None

    @staticmethod
    def normalize_ear_tag(s: str) -> str:
        if not isinstance(s, str):
            return ""
        s = s.strip().upper().replace(" ", "")
        if s.startswith("AT"):
            s = s[2:]
        s = s.lstrip("0")
        key = f"AT{s}"
        return key if key != "AT" else ""

    def build_index(self, df: pd.DataFrame) -> dict[str, pd.Series]:
        col = 'Ohrmarke-Name'
        index: dict[str, pd.Series] = {}
        for _, row in df.iterrows():
            key = self.normalize_ear_tag(str(row.get(col, "")))
            if key:
                index[key] = row
        return index

    def process_tier_ids(self, ids: list[str], index: dict[str, pd.Series]) -> list[dict | None]:
        processed_data: list[dict | None] = []
        for original_id in ids:
            if not original_id or original_id.strip().lower() in {"keine kuh", "leer", "frei"}:
                processed_data.append(None)
                continue
            key = self.normalize_ear_tag(original_id)
            row = index.get(key)
            if row is None:
                processed_data.append({'id': original_id, 'status': 'not_found'})
                continue

            geb_dat_str = (row.get('Geburtsdatum') or "").strip()
            rasse = (row.get('Rasse(n)') or "N/A").strip()
            geschlecht = (row.get('Geschlecht') or "N/A").strip()
            full_id = (row.get('Ohrmarke-Name') or key)

            data_dict = {
                'id': full_id,
                'geburtsdatum': geb_dat_str,
                'alter': self._calculate_age(geb_dat_str),
                'schlachtdatum': self._calculate_slaughter_date(geb_dat_str),
                'rasse': rasse,
                'geschlecht': geschlecht,
                'status': 'ok',
            }
            processed_data.append(data_dict)
        return processed_data

    def reprocess_data(self, data_list: list[dict | None]):
        for item in data_list:
            if item and item.get('status') == 'ok' and 'geburtsdatum' in item:
                geb = item['geburtsdatum']
                item['schlachtdatum'] = self._calculate_slaughter_date(geb)
                item['alter'] = self._calculate_age(geb)

    @staticmethod
    def _parse_date(date_str: str) -> datetime | None:
        if not isinstance(date_str, str) or not date_str.strip():
            return None
        for fmt in ("%d.%m.%Y", "%d.%m.%y", "%Y-%m-%d"):
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        return None

    def _calculate_age(self, birthdate_str: str) -> str:
        birthdate = self._parse_date(birthdate_str)
        if not birthdate:
            return "N/A"
        today = datetime.now()
        total_months = (today.year - birthdate.year) * 12 + (today.month - birthdate.month)
        if today.day < birthdate.day:
            total_months -= 1
        years = total_months // 12
        months = total_months % 12
        year_str = f"{years} Jahr" if years == 1 else f"{years} Jahre"
        month_str = f"{months} Monat" if months == 1 else f"{months} Monate"
        if years > 0 and months > 0:
            return f"{year_str}, {month_str}"
        elif years > 0:
            return year_str
        else:
            return month_str

    def _calculate_slaughter_date(self, birthdate_str: str) -> str:
        birthdate = self._parse_date(birthdate_str)
        if not birthdate:
            return "N/A"
        months_to_add = self.ui.schlachtalter_combo.currentData()
        try:
            months_to_add = int(months_to_add) if months_to_add is not None else 0
        except (ValueError, TypeError):
            months_to_add = 0
        slaughter_date = birthdate + relativedelta(months=months_to_add)
        return slaughter_date.strftime("%d.%m.%Y")

    # --- State speichern/laden ---
    def save_state(self):
        try:
            state = {
                "einzelplaetze": {
                    "raw_ids": self.einzelplaetze_raw_ids,
                    "processed": self.einzelplaetze_processed_data,
                },
                "gruppenboxen": {
                    "raw_ids": self.gruppenboxen_raw_ids,
                    "processed": self.gruppenboxen_processed_data,
                },
            }
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.warning(self, "Speichern fehlgeschlagen", f"Zustand konnte nicht gespeichert werden:\n{e}")

    def load_state(self):
        if not os.path.isfile(STATE_FILE):
            return
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
            ep = state.get("einzelplaetze", {})
            gp = state.get("gruppenboxen", {})

            self.einzelplaetze_raw_ids = ep.get("raw_ids", []) or []
            self.einzelplaetze_processed_data = ep.get("processed", []) or []

            self.gruppenboxen_raw_ids = gp.get("raw_ids", []) or []
            self.gruppenboxen_processed_data = gp.get("processed", []) or []

            # abgeleitete Felder aktualisieren (Alter/Schlachtung)
            if self.einzelplaetze_processed_data:
                self.reprocess_data(self.einzelplaetze_processed_data)
            if self.gruppenboxen_processed_data:
                self.reprocess_data(self.gruppenboxen_processed_data)
        except Exception as e:
            QMessageBox.warning(self, "Zustand laden", f"Gespeicherter Zustand konnte nicht geladen werden:\n{e}")

    def closeEvent(self, event):
        try:
            self.save_state()
        finally:
            super().closeEvent(event)

    # --- UI-Aufbau ---
    def _clear_grid_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            child_layout = item.layout()
            if child_layout is not None:
                self._clear_grid_layout(child_layout)

    def populate_einzelplaetze(self):
        self._clear_grid_layout(self.ui.einzelplaetze_grid_layout)
        cols = 7
        for i in range(NUM_EINZELPLAETZE):
            tier_info = self.einzelplaetze_processed_data[i] if i < len(self.einzelplaetze_processed_data) else None
            row, col = divmod(i, cols)
            card = self.create_einzelplatz_card(i + 1, tier_info)
            self.ui.einzelplaetze_grid_layout.addWidget(card, row, col)

    def populate_gruppenboxen(self):
        self._clear_grid_layout(self.ui.gruppenboxen_grid_layout)
        cols = 3
        for i in range(NUM_GRUPPENBOXEN):
            start_index = i * GRUPPENBOX_SLOTS
            end_index = start_index + GRUPPENBOX_SLOTS
            tiere_in_box: list[dict | None] = []
            for j in range(start_index, end_index):
                if j < len(self.gruppenboxen_processed_data):
                    tiere_in_box.append(self.gruppenboxen_processed_data[j])
                else:
                    tiere_in_box.append(None)
            box_data = {'box_nr': i + 1, 'max_plaetze': GRUPPENBOX_SLOTS, 'tiere': tiere_in_box}
            row, col = divmod(i, cols)
            card = self.create_gruppenbox_card(box_data)
            self.ui.gruppenboxen_grid_layout.addWidget(card, row, col)

    def _create_info_row(self, icon_name: str, label: str, value: str) -> QWidget:
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(10)
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon(icon_name, color='#7f8c8d').pixmap(16, 16))
        icon_label.setFixedWidth(20)
        text_label = QLabel(f"{label}")
        text_label.setFixedWidth(80)
        value_label = QLabel(f"<b>{value}</b>")
        row_layout.addWidget(icon_label)
        row_layout.addWidget(text_label)
        row_layout.addWidget(value_label)
        row_layout.addStretch()
        return row_widget

    def _apply_shadow(self, widget: QWidget):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 35))
        shadow.setOffset(0, 3)
        widget.setGraphicsEffect(shadow)

    def create_einzelplatz_card(self, platz_nr: int, tier_info: dict | None) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        card.setMinimumSize(250, 240)
        self._apply_shadow(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 10, 15, 15)
        layout.setSpacing(10)

        header_layout = QHBoxLayout()
        title = QLabel(f"<b>Platz {platz_nr}</b>")
        title.setStyleSheet("font-size: 14px;")
        status_icon = QLabel()

        if tier_info is None:
            icon = qta.icon('fa5s.minus-circle', color='#bdc3c7')
        elif tier_info.get('status') == 'not_found':
            icon = qta.icon('fa5s.exclamation-triangle', color='#e74c3c')
        else:
            icon = qta.icon('fa5s.check-circle', color='#27ae60')

        status_icon.setPixmap(icon.pixmap(24, 24))
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(status_icon)
        layout.addLayout(header_layout)

        if tier_info is None:
            frei_label = QLabel("<i>Platz ist frei</i>")
            frei_label.setObjectName("PlatzFreiLabel")
            frei_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addStretch()
            layout.addWidget(frei_label)
            layout.addStretch()
        elif tier_info.get('status') == 'not_found':
            not_found_label = QLabel(f"<span style='color:#c0392b;'><b>ID nicht gefunden:</b> {tier_info.get('id','')}</span>")
            not_found_label.setWordWrap(True)
            layout.addStretch()
            layout.addWidget(not_found_label)
            layout.addStretch()
        else:
            layout.addWidget(self._create_info_row('fa5s.tag', '# Tier-ID', tier_info.get('id', 'N/A')))
            layout.addWidget(self._create_info_row('fa5s.calendar-day', '# Geboren', tier_info.get('geburtsdatum', 'N/A')))
            layout.addWidget(self._create_info_row('fa5s.birthday-cake', '# Alter', tier_info.get('alter', 'N/A')))
            layout.addWidget(self._create_info_row('fa5s.gavel', '# Schlachtung', tier_info.get('schlachtdatum', 'N/A')))
            layout.addWidget(self._create_info_row('fa5s.dna', '# Rasse', tier_info.get('rasse', 'N/A')))
            layout.addWidget(self._create_info_row('fa5s.venus-mars', '# Geschlecht', tier_info.get('geschlecht', 'N/A')))
            layout.addStretch()

        return card

    def create_gruppenbox_card(self, box_data: dict) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        card.setMinimumWidth(400)
        self._apply_shadow(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 10, 15, 15)

        header_layout = QHBoxLayout()
        title = QLabel(f"<b>Box {box_data['box_nr']}</b>")
        title.setStyleSheet("font-size: 14px;")

        belegt = sum(1 for t in box_data['tiere'] if t is not None)
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

        # Einträge
        for idx, tier in enumerate(box_data['tiere'], start=1):
            if tier is None:
                frei_label = QLabel(f"<i>Platz {idx} ist frei</i>")
                frei_label.setStyleSheet("color: #95a5a6; padding-top: 6px; padding-bottom: 6px;")
                layout.addWidget(frei_label)
                continue

            if tier.get('status') == 'not_found':
                nf_label = QLabel(f"<span style='color:#c0392b;'><b>ID nicht gefunden:</b> {tier.get('id','')}</span>")
                nf_label.setWordWrap(True)
                layout.addWidget(nf_label)
                layout.addSpacing(8)
                continue

            tier_layout = QVBoxLayout()
            tier_layout.setSpacing(5)
            tier_layout.addWidget(self._create_info_row('fa5s.tag', '# Tier-ID', tier.get('id', 'N/A')))
            tier_layout.addWidget(self._create_info_row('fa5s.calendar-day', '# Geboren', tier.get('geburtsdatum', 'N/A')))
            tier_layout.addWidget(self._create_info_row('fa5s.birthday-cake', '# Alter', tier.get('alter', 'N/A')))
            tier_layout.addWidget(self._create_info_row('fa5s.gavel', '# Schlachtung', tier.get('schlachtdatum', 'N/A')))
            tier_layout.addWidget(self._create_info_row('fa5s.dna', '# Rasse', tier.get('rasse', 'N/A')))
            layout.addLayout(tier_layout)
            layout.addSpacing(10)

        layout.addStretch()
        return card


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())