# main.py (final, mit korrigierten Nachrichtenboxen)

import sys
from datetime import datetime
import pandas as pd
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QFrame, QDialog, QTextEdit,
    QMessageBox, QFileDialog, QGraphicsDropShadowEffect,
    QPlainTextEdit
)
from PySide6.QtGui import QColor, QPainter, QFont, QTextCursor, QTextFormat
from PySide6.QtCore import Qt, Signal, QRect, QSize

import qtawesome as qta
from ui import Ui_MainWindow


# Die Klassen für den Editor und den Dialog bleiben unverändert.
class LineNumberArea(QWidget):
    def __init__(self, editor): super().__init__(editor); self.codeEditor = editor

    def sizeHint(self): return QSize(self.codeEditor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event): self.codeEditor.lineNumberAreaPaintEvent(event)


class NumberedTextEdit(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent);
        self.lineNumberArea = LineNumberArea(self);
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth);
        self.updateRequest.connect(self.updateLineNumberArea);
        self.cursorPositionChanged.connect(self.highlightCurrentLine);
        self.updateLineNumberAreaWidth(0);
        self.highlightCurrentLine()

    def lineNumberAreaWidth(self):
        digits = 1;
        count = max(1, self.blockCount());
        while count >= 10: count /= 10; digits += 1
        return 10 + self.fontMetrics().horizontalAdvance('9') * digits

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())
        if rect.contains(self.viewport().rect()): self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        super().resizeEvent(event); cr = self.contentsRect(); self.lineNumberArea.setGeometry(
            QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def highlightCurrentLine(self):
        extraSelections = [];
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection();
            lineColor = QColor(Qt.yellow).lighter(160);
            selection.format.setBackground(lineColor);
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True);
            selection.cursor = self.textCursor();
            selection.cursor.clearSelection();
            extraSelections.append(selection)
        self.setExtraSelections(extraSelections)

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.lineNumberArea);
        painter.fillRect(event.rect(), QColor("#e0e0e0"));
        block = self.firstVisibleBlock();
        blockNumber = block.blockNumber();
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top();
        bottom = top + self.blockBoundingRect(block).height()
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1);
                painter.setPen(Qt.black);
                painter.drawText(0, int(top), self.lineNumberArea.width() - 5, self.fontMetrics().height(),
                                 Qt.AlignRight, number)
            block = block.next();
            top = bottom;
            bottom = top + self.blockBoundingRect(block).height();
            blockNumber += 1


class BestandInputDialog(QDialog):
    def __init__(self, required_lines: int, title: str, parent=None):
        super().__init__(parent);
        self.setWindowTitle(f"Bestand aufnehmen: {title}");
        self.setMinimumSize(400, 500);
        self.required_lines = required_lines;
        layout = QVBoxLayout(self);
        self.info_label = QLabel(
            f"Bitte fügen Sie {required_lines} Zeilen ein (eine ID pro Zeile).\nFür einen leeren Platz 'Keine Kuh' eingeben.");
        self.text_edit = NumberedTextEdit();
        self.text_edit.setPlaceholderText("Eine ID pro Zeile hier einfügen...");
        self.text_edit.textChanged.connect(self.check_line_count);
        self.status_label = QLabel(f"0 / {self.required_lines} Zeilen");
        layout.addWidget(self.info_label);
        layout.addWidget(self.text_edit);
        layout.addWidget(self.status_label);
        self.text_edit.setFocus()

    def check_line_count(self):
        content = self.text_edit.toPlainText();
        lines = [line for line in content.split('\n') if line.strip()];
        line_count = len(lines);
        self.status_label.setText(f"{line_count} / {self.required_lines} Zeilen")
        if line_count >= self.required_lines: final_content = "\n".join(
            lines[:self.required_lines]); self.text_edit.blockSignals(True); self.text_edit.setPlainText(
            final_content); self.text_edit.blockSignals(False); self.accept()

    def get_data(self) -> list[str] | None:
        if self.exec() == QDialog.Accepted: content = self.text_edit.toPlainText(); return [line.strip() for line in
                                                                                            content.split('\n')]
        return None


# --- HAUPTKLASSE ---

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__();
        self.ui = Ui_MainWindow();
        self.ui.setupUi(self);
        self.einzelplaetze_raw_ids = [];
        self.gruppenboxen_raw_ids = [];
        self.einzelplaetze_processed_data = [];
        self.gruppenboxen_processed_data = [];
        self.connect_signals();
        self.populate_einzelplaetze();
        self.populate_gruppenboxen();
        self.ui.stacked_widget.setCurrentIndex(2);
        self.ui.btn_setup.setChecked(True)

    def connect_signals(self):
        self.ui.button_group.buttonClicked.connect(self.switch_page);
        self.ui.btn_bestand_einzel.clicked.connect(self.aufnahme_einzelplaetze_ids);
        self.ui.btn_bestand_gruppe.clicked.connect(self.aufnahme_gruppenboxen_ids);
        self.ui.btn_aktualisieren_einzel.clicked.connect(self.update_einzelplaetze_ui);
        self.ui.btn_aktualisieren_gruppe.clicked.connect(self.update_gruppenboxen_ui)

    def switch_page(self, button):
        self.ui.stacked_widget.setCurrentIndex(self.ui.button_group.id(button))

    # --- KORRIGIERTE NACHRICHTENBOXEN ---
    def aufnahme_einzelplaetze_ids(self):
        dialog = BestandInputDialog(12, "Einzelplätze", self)
        ids = dialog.get_data()
        if ids:
            self.einzelplaetze_raw_ids = ids
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Erfolg")
            msg.setText(f"Alle {len(ids)} Tier-IDs für Einzelplätze übernommen.\nBitte klicken Sie nun auf 'Aktualisieren'.")
            msg.setStyleSheet("QLabel { color: wight; }")  # Sicherstellt, dass Text lesbar ist
            msg.exec()

    def aufnahme_gruppenboxen_ids(self):
        dialog = BestandInputDialog(18, "Gruppenboxen", self)
        ids = dialog.get_data()
        if ids:
            self.gruppenboxen_raw_ids = ids
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Erfolg")
            msg.setText(f"Alle {len(ids)} Tier-IDs für Gruppenboxen übernommen.\nBitte klicken Sie nun auf 'Aktualisieren'.")
            msg.setStyleSheet("QLabel { color: wight; }")  # Verhindert unsichtbaren Text bei Dark Theme
            msg.exec()

    def update_einzelplaetze_ui(self):
        if not self.einzelplaetze_raw_ids: QMessageBox.warning(self, "Hinweis",
                                                               "Bitte zuerst den Bestand für Einzelplätze aufnehmen."); return
        csv_path = self.get_csv_path()
        if not csv_path: return
        df = self.load_csv_data(csv_path)
        if df is None: return
        self.einzelplaetze_processed_data = self.process_tier_ids(self.einzelplaetze_raw_ids, df)
        self.populate_einzelplaetze()
        QMessageBox.about(self, "Abschluss", "Einzelplatz-Ansicht wurde aktualisiert.")
        self.ui.stacked_widget.setCurrentIndex(0);
        self.ui.btn_einzelplaetze.setChecked(True)

    def update_gruppenboxen_ui(self):
        if not self.gruppenboxen_raw_ids: QMessageBox.warning(self, "Hinweis",
                                                              "Bitte zuerst den Bestand für Gruppenboxen aufnehmen."); return
        csv_path = self.get_csv_path()
        if not csv_path: return
        df = self.load_csv_data(csv_path)
        if df is None: return
        self.gruppenboxen_processed_data = self.process_tier_ids(self.gruppenboxen_raw_ids, df)
        self.populate_gruppenboxen()
        QMessageBox.about(self, "Abschluss", "Gruppenboxen-Ansicht wurde aktualisiert.")
        self.ui.stacked_widget.setCurrentIndex(1);
        self.ui.btn_gruppenboxen.setChecked(True)

    def get_csv_path(self) -> str | None:
        file_path, _ = QFileDialog.getOpenFileName(self, "CSV-Datei auswählen", "", "CSV-Dateien (*.csv)");
        return file_path

    def load_csv_data(self, file_path: str) -> pd.DataFrame | None:
        try:
            df = pd.read_csv(file_path, delimiter=';', dtype=str, quotechar='"', skipinitialspace=True)
            df.columns = [col.strip() for col in df.columns]
            return df
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Laden der CSV-Datei:\n{e}");
            return None

    def process_tier_ids(self, ids: list[str], df: pd.DataFrame) -> list[dict | None]:
        processed_data = [];
        for tier_id in ids:
            if not tier_id or tier_id.lower() == 'keine kuh': processed_data.append(None); continue
            cleaned_tier_id = tier_id.strip().lstrip('0');
            full_id_to_search = f"AT{cleaned_tier_id}"
            match = df[df['Ohrmarke-Name'] == full_id_to_search]
            if not match.empty:
                tier_info = match.iloc[0];
                geb_dat_str = tier_info.get('Geburtsdatum')
                data_dict = {'id': tier_info.get('Ohrmarke-Name'), 'geburtsdatum': geb_dat_str,
                             'alter': self._calculate_age(geb_dat_str), 'gewicht': 'N/A',
                             'rasse': tier_info.get('Rasse(n)', 'N/A'),
                             'geschlecht': tier_info.get('Geschlecht', 'N/A')}
                processed_data.append(data_dict)
            else:
                processed_data.append(None)
        return processed_data

    def _calculate_age(self, birthdate_str: str) -> str:
        if not isinstance(birthdate_str, str): return "N/A"
        try:
            birthdate = datetime.strptime(birthdate_str, "%d.%m.%Y");
            today = datetime.now()
            total_months = (today.year - birthdate.year) * 12 + (today.month - birthdate.month)
            if today.day < birthdate.day: total_months -= 1
            years = total_months // 12;
            months = total_months % 12
            year_str = f"{years} Jahr" if years == 1 else f"{years} Jahre"
            month_str = f"{months} Monat" if months == 1 else f"{months} Monate"
            if years > 0 and months > 0:
                return f"{year_str}, {month_str}"
            elif years > 0:
                return year_str
            else:
                return month_str
        except (ValueError, TypeError):
            return "N/A"

    def _clear_grid_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0);
            widget = item.widget()
            if widget is not None: widget.deleteLater()

    def populate_einzelplaetze(self):
        self._clear_grid_layout(self.ui.einzelplaetze_grid_layout);
        num_plaetze = 14;
        cols = 7
        for i in range(num_plaetze):
            tier_info = self.einzelplaetze_processed_data[i] if i < len(self.einzelplaetze_processed_data) else None
            row, col = divmod(i, cols);
            card = self.create_einzelplatz_card(i + 1, tier_info);
            self.ui.einzelplaetze_grid_layout.addWidget(card, row, col)

    def populate_gruppenboxen(self):
        self._clear_grid_layout(self.ui.gruppenboxen_grid_layout);
        num_boxes = 6;
        box_slots = 3;
        cols = 3
        for i in range(num_boxes):
            start_index = i * box_slots;
            end_index = start_index + box_slots
            tiere_in_box = [self.gruppenboxen_processed_data[j] for j in range(start_index, end_index) if
                            j < len(self.gruppenboxen_processed_data) and self.gruppenboxen_processed_data[j]]
            box_data = {'box_nr': i + 1, 'max_plaetze': box_slots, 'tiere': tiere_in_box};
            row, col = divmod(i, cols);
            card = self.create_gruppenbox_card(box_data);
            self.ui.gruppenboxen_grid_layout.addWidget(card, row, col)

    def _create_info_row(self, icon_name: str, label: str, value: str) -> QWidget:
        row_widget = QWidget();
        row_layout = QHBoxLayout(row_widget);
        row_layout.setContentsMargins(0, 0, 0, 0);
        row_layout.setSpacing(10);
        icon_label = QLabel();
        icon_label.setPixmap(qta.icon(icon_name, color='#7f8c8d').pixmap(16, 16));
        icon_label.setFixedWidth(20);
        text_label = QLabel(f"{label}");
        text_label.setFixedWidth(80);
        value_label = QLabel(f"<b>{value}</b>");
        row_layout.addWidget(icon_label);
        row_layout.addWidget(text_label);
        row_layout.addWidget(value_label);
        row_layout.addStretch();
        return row_widget

    def _apply_shadow(self, widget: QWidget):
        shadow = QGraphicsDropShadowEffect(self);
        shadow.setBlurRadius(25);
        shadow.setColor(QColor(0, 0, 0, 35));
        shadow.setOffset(0, 3);
        widget.setGraphicsEffect(shadow)

    def create_einzelplatz_card(self, platz_nr: int, tier_info: dict | None) -> QFrame:
        card = QFrame();
        card.setObjectName("Card");
        card.setMinimumSize(250, 220);
        self._apply_shadow(card);
        layout = QVBoxLayout(card);
        layout.setContentsMargins(15, 10, 15, 15);
        layout.setSpacing(10);
        header_layout = QHBoxLayout();
        title = QLabel(f"<b>Platz {platz_nr}</b>");
        title.setStyleSheet("font-size: 14px;");
        status_icon = QLabel()
        if tier_info:
            icon = qta.icon('fa5s.check-circle', color='#27ae60')
        else:
            icon = qta.icon('fa5s.minus-circle', color='#e74c3c')
        status_icon.setPixmap(icon.pixmap(24, 24));
        header_layout.addWidget(title);
        header_layout.addStretch();
        header_layout.addWidget(status_icon);
        layout.addLayout(header_layout)
        if tier_info:
            layout.addWidget(self._create_info_row('fa5s.tag', '# Tier-ID', tier_info.get('id', 'N/A')))
            layout.addWidget(
                self._create_info_row('fa5s.calendar-day', '# Geboren', tier_info.get('geburtsdatum', 'N/A')))
            layout.addWidget(self._create_info_row('fa5s.birthday-cake', '# Alter', tier_info.get('alter', 'N/A')))
            layout.addWidget(self._create_info_row('fa5s.dna', '# Rasse', tier_info.get('rasse', 'N/A')))
            layout.addWidget(
                self._create_info_row('fa5s.venus-mars', '# Geschlecht', tier_info.get('geschlecht', 'N/A')))
            layout.addStretch()
        else:
            frei_label = QLabel("<i>Platz ist frei</i>");
            frei_label.setObjectName("PlatzFreiLabel");
            frei_label.setAlignment(Qt.AlignmentFlag.AlignCenter);
            layout.addStretch();
            layout.addWidget(frei_label);
            layout.addStretch()
        return card

    def create_gruppenbox_card(self, box_data: dict) -> QFrame:
        card = QFrame();
        card.setObjectName("Card");
        card.setMinimumWidth(400);
        self._apply_shadow(card);
        layout = QVBoxLayout(card);
        layout.setContentsMargins(15, 10, 15, 15);
        header_layout = QHBoxLayout();
        title = QLabel(f"<b>Box {box_data['box_nr']}</b>");
        title.setStyleSheet("font-size: 14px;");
        belegt = len(box_data['tiere']);
        max_p = box_data['max_plaetze'];
        status_label = QLabel(f"<b>{belegt} / {max_p}</b> Belegt");
        status_label.setStyleSheet("color: #7f8c8d;");
        header_layout.addWidget(title);
        header_layout.addStretch();
        header_layout.addWidget(status_label);
        layout.addLayout(header_layout);
        line = QFrame();
        line.setFrameShape(QFrame.Shape.HLine);
        line.setFrameShadow(QFrame.Shadow.Sunken);
        line.setStyleSheet("color: #ecf0f1;");
        layout.addWidget(line)
        for tier in box_data['tiere']:
            tier_layout = QVBoxLayout();
            tier_layout.setSpacing(5)
            tier_layout.addWidget(self._create_info_row('fa5s.tag', '# Tier-ID', tier.get('id', 'N/A')))
            tier_layout.addWidget(
                self._create_info_row('fa5s.calendar-day', '# Geboren', tier.get('geburtsdatum', 'N/A')))
            tier_layout.addWidget(self._create_info_row('fa5s.birthday-cake', '# Alter', tier.get('alter', 'N/A')))
            tier_layout.addWidget(self._create_info_row('fa5s.dna', '# Rasse', tier.get('rasse', 'N/A')))
            layout.addLayout(tier_layout);
            layout.addSpacing(15)
        freie_plaetze = max_p - belegt
        for i in range(freie_plaetze): frei_label = QLabel(
            f"<i>Platz {belegt + i + 1} ist frei</i>"); frei_label.setStyleSheet(
            "color: #95a5a6; padding-top: 10px; padding-bottom: 10px;"); layout.addWidget(frei_label)
        layout.addStretch();
        return card


if __name__ == '__main__':
    app = QApplication(sys.argv);
    window = MainWindow();
    window.show();
    sys.exit(app.exec())