from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QLineEdit, QComboBox, QCheckBox, QLabel, QDateEdit, QFormLayout, QSpinBox,
    QDialog, QApplication, QDialogButtonBox, QTextEdit, QHeaderView
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor
from PyQt5.QtGui import QIcon
from db import init_db, fetch_all, add_entry, update_menge, delete_entry
from settings import load_theme, save_theme
from datetime import datetime

UNIT_SCALE = {
    "g": 1,
    "kg": 1000,
    "ml": 1,
    "l": 1000,
    "Stk": 1,  # Stück bleibt unskaliert
    "Pkg": 1,  # Packung bleibt unskaliert
}

class AddDialog(QDialog):
    def __init__(self, parent=None, existing_data=None):
        super().__init__(parent)
        self.setWindowTitle("Lebensmittel bearbeiten" if existing_data else "Lebensmittel hinzufügen")
        self.build_ui()
        if existing_data:
            self.populate_fields(existing_data)

    def build_ui(self):
        layout = QVBoxLayout()

        self.name = QLineEdit()
        self.kategorie = QLineEdit()
        self.menge = QLineEdit()
        self.menge.setPlaceholderText("z. B. 1,5")
        self.einheit = QComboBox()
        self.einheit.addItems(["g", "kg", "ml", "l", "Stk", "Pkg"])
        self.lagerort = QLineEdit()
        self.geöffnet = QCheckBox("Geöffnet")
        self.mhd = QDateEdit()
        self.mhd.setCalendarPopup(True)
        self.mhd.setDate(QDate.currentDate())
        self.eingelagert = QDateEdit()
        self.eingelagert.setCalendarPopup(True)
        self.eingelagert.setDate(QDate.currentDate())
        self.bemerkungen = QTextEdit()

        layout.addWidget(QLabel("Name"))
        layout.addWidget(self.name)
        layout.addWidget(QLabel("Kategorie"))
        layout.addWidget(self.kategorie)
        layout.addWidget(QLabel("Menge"))
        layout.addWidget(self.menge)
        layout.addWidget(QLabel("Einheit"))
        layout.addWidget(self.einheit)
        layout.addWidget(QLabel("Lagerort"))
        layout.addWidget(self.lagerort)
        layout.addWidget(self.geöffnet)
        layout.addWidget(QLabel("MHD"))
        layout.addWidget(self.mhd)
        layout.addWidget(QLabel("Eingelagert am"))
        layout.addWidget(self.eingelagert)
        layout.addWidget(QLabel("Bemerkungen"))
        layout.addWidget(self.bemerkungen)

        btn_layout = QHBoxLayout()

        ok_btn = QPushButton()
        ok_icon = QIcon("icons/check.png")
        ok_btn.setIcon(ok_icon)
        ok_btn.setText("Hinzufügen" if self.windowTitle() == "Lebensmittel hinzufügen" else "Ändern")
        ok_btn.setStyleSheet("background-color: #f3f6f4; color: black; padding: 6px;")
        ok_btn.clicked.connect(self.accept)

        cancel_btn = QPushButton()
        cancel_icon = QIcon("icons/cancel.png")
        cancel_btn.setIcon(cancel_icon)
        cancel_btn.setText("Abbrechen")
        cancel_btn.setStyleSheet("background-color: #f3f6f4; color: black; padding: 6px;")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def populate_fields(self, data):
        id_, name, kat, menge, einheit, ort, geöffnet, mhd, eingelagert, bemerkung = data
        self.name.setText(name)
        self.kategorie.setText(kat)
        self.menge.setText(str(menge).replace(".", ","))
        self.einheit.setCurrentText(einheit)
        self.lagerort.setText(ort)
        self.geöffnet.setChecked(bool(geöffnet))
        if mhd:
            self.mhd.setDate(QDate.fromString(mhd, "yyyy-MM-dd"))
        self.eingelagert.setDate(QDate.fromString(eingelagert, "yyyy-MM-dd"))
        self.bemerkungen.setText(bemerkung)

    def get_data(self):
        mhd_str = self.mhd.date().toString("yyyy-MM-dd")
        if self.mhd.date() == QDate(2000, 1, 1):
            mhd_str = ""

        menge_text = self.menge.text().replace(",", ".")
        try:
            menge_float = float(menge_text)
        except ValueError:
            menge_float = 0.0

        return (
            self.name.text(),
            self.kategorie.text(),
            menge_float,
            self.einheit.currentText(),
            self.lagerort.text(),
            self.geöffnet.isChecked(),
            mhd_str,
            self.eingelagert.date().toString("yyyy-MM-dd"),
            self.bemerkungen.toPlainText()
        )

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lebensmittel-Datenbank")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        init_db()
        self.build_controls()
        self.build_table()
        self.apply_theme(load_theme())
        self.refresh_table()

    def build_controls(self):
        control_layout = QHBoxLayout()
        self.add_btn = QPushButton("➕ Lebensmittel hinzufügen")
        self.add_btn.clicked.connect(self.open_add_dialog)
        self.theme_toggle = QPushButton()
        self.theme_toggle.setCheckable(True)
        self.theme_toggle.clicked.connect(self.toggle_theme)
        control_layout.addWidget(self.add_btn)
        control_layout.addWidget(self.theme_toggle)
        self.layout.addLayout(control_layout)

    def build_table(self):
        self.table = QTableWidget()
        self.table.setColumnCount(14)
        self.table.setHorizontalHeaderLabels([
        "ID", "Name", "Kategorie", "Menge", "+ / –", "Einheit", "Lagerort", "Geöffnet",
        "MHD", "Eingelagert", "Bemerkungen", "Tage bis Ablauf", "📝", "🗑️"
        ])
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(10, QHeaderView.Stretch)  # Spalte 10 = Bemerkungen
        self.layout.addWidget(self.table)
        self.table.itemChanged.connect(self.handle_checkbox_change)
    
    def open_add_dialog(self):
        dialog = AddDialog(self)
        if dialog.exec_():
            data = dialog.get_data()
            add_entry(data)
            self.refresh_table()

    def open_edit_dialog(self, id_):
        import sqlite3
        conn = sqlite3.connect("lebensmittel.db")
        c = conn.cursor()
        c.execute("SELECT * FROM lebensmittel WHERE id = ?", (id_,))
        row = c.fetchone()
        conn.close()

        if row:
            dialog = AddDialog(self, existing_data=row)
            if dialog.exec_():
                updated = dialog.get_data()
                conn = sqlite3.connect("lebensmittel.db")
                c = conn.cursor()
                c.execute("""
                    UPDATE lebensmittel SET
                        name = ?, kategorie = ?, menge = ?, einheit = ?, lagerort = ?,
                        geöffnet = ?, mhd = ?, eingelagert = ?, bemerkungen = ?
                    WHERE id = ?
                """, (*updated, id_))
                conn.commit()
                conn.close()
                self.refresh_table()

    def refresh_table(self):
        self.table.setRowCount(0)
        for row in fetch_all():
            id_, name, kat, menge, einheit, ort, geöffnet, mhd, eingelagert, bemerkung = row
            tage = self.days_until(mhd)
            r = self.table.rowCount()
            self.table.insertRow(r)

            # ID, Name, Kategorie
            self.table.setItem(r, 0, QTableWidgetItem(str(id_)))
            self.table.setItem(r, 1, QTableWidgetItem(name))
            self.table.setItem(r, 2, QTableWidgetItem(kat))

            # Menge (numerisch sortierbar + Kommaanzeige ohne Sortierverlust)
            menge_item = QTableWidgetItem()
            if isinstance(menge, (int, float)):
                faktor = UNIT_SCALE.get(einheit, 1)
                skaliert = menge * faktor
                einheit = str(row[4]) # Spalte 4 = Einheit
                menge_item.setData(Qt.ItemDataRole.DisplayRole, skaliert)  # für Sortierung
                menge_item.setData(Qt.ItemDataRole.EditRole, skaliert)     # optional für Bearbeitung
                menge_item.setTextAlignment(Qt.AlignCenter)

                # Kommaanzeige nur visuell, ohne Sortierverlust
                menge_item.setData(Qt.ItemDataRole.UserRole, f"{menge:.2f}".replace(".", ","))
            else:
                menge_item.setData(Qt.ItemDataRole.DisplayRole, "")
            self.table.setItem(r, 3, menge_item)
            # Anzeige mit Komma statt Punkt
            menge_item.setText(menge_item.data(Qt.ItemDataRole.UserRole))

            # ➕➖ Icons nebeneinander in einer Spalte
            plus_btn = QPushButton()
            plus_btn.setIcon(QIcon("icons/plus.png"))
            plus_btn.setFixedSize(24, 24)
            plus_btn.setStyleSheet("border: none;")

            minus_btn = QPushButton()
            minus_btn.setIcon(QIcon("icons/minus.png"))
            minus_btn.setFixedSize(24, 24)
            minus_btn.setStyleSheet("border: none;")

            plus_btn.clicked.connect(lambda _, id=id_: self.change_menge(id, +1))
            minus_btn.clicked.connect(lambda _, id=id_: self.change_menge(id, -1))

            btn_layout = QHBoxLayout()
            btn_layout.setContentsMargins(0, 0, 0, 0)
            btn_layout.setSpacing(4)
            btn_layout.addWidget(minus_btn)
            btn_layout.addWidget(plus_btn)

            btn_widget = QWidget()
            btn_widget.setLayout(btn_layout)
            self.table.setCellWidget(r, 4, btn_widget)  # Spalte 4 = „+ / –“

            # Einheit, Lagerort
            self.table.setItem(r, 5, QTableWidgetItem(einheit))
            self.table.setItem(r, 6, QTableWidgetItem(ort))

            # Geöffnet als editierbare Checkbox
            check_item = QTableWidgetItem()
            check_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable | Qt.ItemIsEditable)
            check_item.setCheckState(Qt.Checked if geöffnet else Qt.Unchecked)
            self.table.setItem(r, 7, check_item)

            # MHD, Eingelagert
            self.table.setItem(r, 8, QTableWidgetItem(self.format_date(mhd)))
            self.table.setItem(r, 9, QTableWidgetItem(self.format_date(eingelagert)))

            # Bemerkungen
            self.table.setItem(r, 10, QTableWidgetItem(bemerkung))

            # Tage bis Ablauf
            tage_item = QTableWidgetItem()
            tage_item.setData(Qt.ItemDataRole.DisplayRole, tage if isinstance(tage, int) else "")
            tage_item.setTextAlignment(Qt.AlignCenter)
            
            if isinstance(tage, int):
                if tage < 3:
                    tage_item.setBackground(QColor("#e53935")) # Rot für ablaufend kritisch
                elif tage < 7:
                    tage_item.setBackground(QColor("#ff9800")) # Orange für ablaufend bald
            self.table.setItem(r, 11, tage_item)

            # Spalte 12: Ändern-Button

            edit_btn = QPushButton("📝")
            edit_btn.clicked.connect(lambda _, id=id_: self.open_edit_dialog(id))
            self.table.setCellWidget(r, 12, edit_btn)

            # Spalte 13: Löschen
            del_btn = QPushButton("🗑️")
            del_btn.clicked.connect(lambda _, id=id_: self.delete_entry(id))
            self.table.setCellWidget(r, 13, del_btn)

    def change_menge(self, id_, delta):
        update_menge(id_, delta)
        self.refresh_table()

    def handle_checkbox_change(self, item):
        if item.column() == 6:  # Geöffnet-Spalte
           
            id_item = self.table.item(item.row(), 0)
            if id_item:
                id_ = int(id_item.text())
                new_state = item.checkState() == Qt.Checked
                import sqlite3
                conn = sqlite3.connect("lebensmittel.db")
                c = conn.cursor()
                c.execute("UPDATE lebensmittel SET geöffnet = ? WHERE id = ?", (new_state, id_))
                conn.commit()
                conn.close()

    def delete_entry(self, id_):
        delete_entry(id_)
        self.refresh_table()

    def days_until(self, mhd_str):
        try:
            if not mhd_str:
                return ""
            mhd_date = datetime.strptime(mhd_str, "%Y-%m-%d")
            return (mhd_date - datetime.today()).days
        except:
            return ""

    def format_date(self, date_str):
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d.%m.%Y")
        except:
            return ""

    def apply_theme(self, theme):
        if theme == "dark":
            self.theme_toggle.setChecked(True)
            self.theme_toggle.setText("☀️ Light Mode aktivieren")
            QApplication.instance().setStyleSheet(self.dark_stylesheet())
        else:
            self.theme_toggle.setChecked(False)
            self.theme_toggle.setText("🌙 Dark Mode aktivieren")
            QApplication.instance().setStyleSheet(self.light_stylesheet())

    def toggle_theme(self):
        if self.theme_toggle.isChecked():
            self.theme_toggle.setText("☀️ Light Mode aktivieren")
            QApplication.instance().setStyleSheet(self.dark_stylesheet())
            save_theme("dark")
        else:
            self.theme_toggle.setText("🌙 Dark Mode aktivieren")
            QApplication.instance().setStyleSheet(self.light_stylesheet())
            save_theme("light")

    def dark_stylesheet(self):
        return """
        QWidget { background-color: #121212; color: #e0e0e0; font-size: 10pt; }
        QLineEdit, QComboBox, QSpinBox, QDateEdit, QTextEdit {
            background-color: #1e1e1e; border: 1px solid #333; color: #ffffff;
        }
        QPushButton { background-color: #2c2c2c; border: 1px solid #444; color: #ffffff; }
        QPushButton:hover { background-color: #3c3c3c; }
        QTableWidget { background-color: #1a1a1a; gridline-color: #333; color: #ffffff; }
        QHeaderView::section { background-color: #2a2a2a; color: #ffffff; }
        """

    def light_stylesheet(self):
        return """
        QWidget {
            background-color: #f0f0f0;
            color: #000000;
            font-size: 10pt;
        }
        QLineEdit, QComboBox, QSpinBox, QDateEdit, QTextEdit {
            background-color: #ffffff;
            border: 1px solid #ccc;
            color: #000000;
        }
        QPushButton {
            background-color: #e0e0e0;
            border: 1px solid #aaa;
            color: #000000;
        }
        QPushButton:hover {
            background-color: #d0d0d0;
        }
        QTableWidget {
            background-color: #ffffff;
            gridline-color: #ccc;
            color: #000000;
        }
        QHeaderView::section {
            background-color: #e0e0e0;
            color: #000000;
            padding: 4px;
            border: 1px solid #aaa;
        }
        QCheckBox {
            padding: 2px;
        }
        """



