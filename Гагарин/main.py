from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel, QLineEdit, QStackedWidget, QMessageBox, QComboBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
import sys
import psycopg2
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Константы
BG_COLOR = "#DECFB4"
BUTTON_COLOR = "#67BA80"
BUTTON_TEXT_COLOR = "#FFFFFF"
FONT_COLOR = "#000000"
HEADER_FONT_SIZE = 32
TITLE_FONT_SIZE = 24
FORM_TITLE_FONT_SIZE = 18
BUTTON_PADDING = 10

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Мастер Пол")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet(f"background-color: {BG_COLOR};")

        # Установка иконки приложения
        self.set_icon("icon.ico")

        # Database connection
        self.connection = self.connect_to_db()

        # Main layout
        self.main_layout = QVBoxLayout()
        self.central_widget = QWidget()
        self.central_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.central_widget)

        self.create_header()
        self.create_stacked_widget()
        self.create_navigation_buttons()

    def set_icon(self, icon_path):
        try:
            self.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить иконку: {e}")

    def create_header(self):
        header_layout = QHBoxLayout()

        logo_label = QLabel()
        logo_pixmap = QPixmap("logo.png")
        logo_label.setPixmap(logo_pixmap.scaledToWidth(70, Qt.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignLeft)
        header_layout.addWidget(logo_label)

        title = QLabel("Партнеры")
        title.setStyleSheet(f"font-size: {HEADER_FONT_SIZE}px; font-weight: bold; color: {FONT_COLOR};")
        title.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title)

        self.main_layout.addLayout(header_layout)

    def create_stacked_widget(self):
        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)

        self.create_partners_page()
        self.create_history_page()
        self.create_partner_form_page()

    def create_navigation_buttons(self):
        button_layout = QVBoxLayout()  # Вертикальное расположение кнопок

        self.partners_button = self.create_button("Партнеры", lambda: self.stacked_widget.setCurrentIndex(0))
        button_layout.addWidget(self.partners_button)

        self.history_button = self.create_button("История", lambda: self.stacked_widget.setCurrentIndex(1))
        button_layout.addWidget(self.history_button)

        # Добавление в основное пространство
        self.main_layout.addLayout(button_layout)

    def create_button(self, text, on_click):
        button = QPushButton(text)
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {BUTTON_COLOR};
                color: {BUTTON_TEXT_COLOR};
                font-weight: bold;
                padding: {BUTTON_PADDING}px;
                font-size: 16px;
                border-radius: 5px;
                transition: background-color 0.3s ease;
                margin-bottom: 10px;  /* Добавим отступы между кнопками */
            }}
            QPushButton:hover {{
                background-color: #4C9E6F;
            }}
            QPushButton:pressed {{
                background-color: #3D7F56;
            }}
        """)
        button.clicked.connect(on_click)
        return button

    def create_partners_page(self):
        partners_page = QWidget()
        partners_layout = QVBoxLayout()
        partners_page.setLayout(partners_layout)

        self.partners_table = self.create_table(["Наименование", "Тип", "Директор", "Номер телефона", "Рейтинг", "Скидка"])
        partners_layout.addWidget(self.partners_table)

        # Перемещаем кнопки в нижнюю часть
        button_layout = QHBoxLayout()

        add_button = self.create_button("Добавить партнера", lambda: self.open_partner_form("Добавление партнера"))
        button_layout.addWidget(add_button)

        edit_button = self.create_button("Редактировать партнера", self.open_edit_partner_form)
        button_layout.addWidget(edit_button)

        partners_layout.addLayout(button_layout)  # Добавляем кнопки в нижнюю часть

        self.load_partners_data()
        self.stacked_widget.addWidget(partners_page)

    def create_table(self, headers):
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setStyleSheet("background-color: #FFFFFF; color: #000000;")
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        return table

    def create_partner_form_page(self):
        self.partner_form_page = QWidget()
        form_layout = QVBoxLayout()
        self.partner_form_page.setLayout(form_layout)

        self.form_title = QLabel()
        self.form_title.setStyleSheet(f"font-size: {FORM_TITLE_FONT_SIZE}px; font-weight: bold; color: {FONT_COLOR};")
        form_layout.addWidget(self.form_title)

        self.form_inputs = {}
        fields = ["Наименование", "Директор", "Телефон", "Рейтинг", "Скидка"]
        for field in fields:
            self.add_form_input(form_layout, field)

        self.type_dropdown = QComboBox()
        self.type_dropdown.setStyleSheet("background-color: #F4E8D3; color: #000000;")
        self.load_company_types()
        form_layout.addWidget(QLabel("Тип"))
        form_layout.addWidget(self.type_dropdown)

        submit_button = self.create_button("Сохранить", self.save_partner)
        form_layout.addWidget(submit_button)

        back_button = self.create_button("Назад", lambda: self.stacked_widget.setCurrentIndex(0))
        form_layout.addWidget(back_button)

        self.stacked_widget.addWidget(self.partner_form_page)

    def add_form_input(self, layout, field):
        label = QLabel(field)
        label.setStyleSheet(f"color: {FONT_COLOR};")
        input_field = QLineEdit()
        input_field.setStyleSheet("background-color: #F4E8D3; color: #000000; padding: 5px;")
        self.form_inputs[field] = input_field
        layout.addWidget(label)
        layout.addWidget(input_field)

    def create_history_page(self):
        if not self.connection:
            print("No connection to the database.")
            return

        history_page = QWidget()
        history_layout = QVBoxLayout()
        history_page.setLayout(history_layout)

        title = QLabel("История")
        title.setStyleSheet(f"font-size: {TITLE_FONT_SIZE}px; font-weight: bold; color: {FONT_COLOR};")
        history_layout.addWidget(title)

        self.history_table = self.create_table(["Продукция", "Количество продукта", "Наименование партнера", "Дата продажи"])
        history_layout.addWidget(self.history_table)

        report_button = self.create_button("Создать отчет", self.create_pdf_report)
        history_layout.addWidget(report_button)

        self.load_history_data()
        self.stacked_widget.addWidget(history_page)

    def create_pdf_report(self):
        pdf_file_path = "partner_product_report.pdf"
        pdf_file = canvas.Canvas(pdf_file_path)
        pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
        pdf_file.setFont("DejaVuSans", 12)

        # Заголовок отчета
        pdf_file.drawString(100, 800, "Отчет по продукции партнеров")
        pdf_file.drawString(100, 780, "-----------------------------------")

        # Получение данных из PartnerProduct
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT p.description, pp.quantity, pr.company_name, pp.date_of_sale
            FROM PartnerProduct pp
            LEFT JOIN Products p ON pp.id_product = p.id
            LEFT JOIN Partners pr ON pp.id_partener = pr.id;
        """)
        rows = cursor.fetchall()

        # Заполнение PDF данными
        y_position = 750  # Начальная позиция по оси Y для текста
        for row in rows:
            if y_position < 50:  # Если достигли нижней границы страницы
                pdf_file.showPage()  # Создаем новую страницу
                pdf_file.setFont("DejaVuSans", 12)  # Устанавливаем шрифт для новой страницы
                y_position = 800  # Сбрасываем позицию Y

            pdf_file.drawString(100, y_position, f"Продукция: {row[0]}, Количество: {row[1]}, Партнер: {row[2]}, Дата: {row[3]}")
            y_position -= 20  # Смещение вниз для следующей строки

        pdf_file.save()  # Сохраняем PDF файл
        QMessageBox.information(self, "Успех", f"Отчет успешно создан: {pdf_file_path}")

    def open_partner_form(self, title_text, partner_data=None):
        self.form_title.setText(title_text)
        for i, (field, input_field) in enumerate(self.form_inputs.items()):
            input_field.setText(partner_data[i] if partner_data else "")

        self.stacked_widget.setCurrentWidget(self.partner_form_page)

    def save_partner(self):
        name = self.form_inputs["Наименование"].text()
        director = self.form_inputs["Директор"].text()
        phone = self.form_inputs["Телефон"].text()
        rating_str = self.form_inputs["Рейтинг"].text()
        discount_str = self.form_inputs["Скидка"].text()

        try:
            rating = float(rating_str)
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Рейтинг должен быть числом.")
            return

        type_id = self.type_dropdown.currentData()

        if not name or not director or not phone or not rating or not type_id:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, заполните все поля.")
            return

        # Расчет скидки на основе общего количества продаж
        total_sales = self.get_total_sales(name)  # Получаем общее количество продаж для партнера
        discount = self.calculate_discount(total_sales)

        cursor = self.connection.cursor()

        if hasattr(self, 'edited_partner_id'):
            query = """
                UPDATE Partners
                SET company_name = %s, type_partner = %s, director_full_name = %s, phone = %s, rating = %s, discount = %s
                WHERE id = %s;
            """
            cursor.execute(query, (name, type_id, director, phone, rating, discount, self.edited_partner_id))
            del self.edited_partner_id
        else:
            query = """
                INSERT INTO Partners (company_name, type_partner, director_full_name, phone, rating, discount)
                VALUES (%s, %s, %s, %s, %s, %s);
            """
            cursor.execute(query, (name, type_id, director, phone, rating, discount))

        self.connection.commit()
        cursor.close()

        QMessageBox.information(self, "Успех", "Партнер успешно сохранен.")
        self.load_partners_data()

    def load_company_types(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT id, name FROM TypeCompany")
        types = cursor.fetchall()
        for type_id, type_name in types:
            self.type_dropdown.addItem(type_name, type_id)
        cursor.close()

    def connect_to_db(self):
        try:
            connection = psycopg2.connect(
                dbname="postgres",
                user="postgres",
                password="",
                host="localhost",
                port="5432"
            )
            print("Connected to the database.")
            return connection
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Database Error", f"Could not connect to the database.\nError: {e}")
            return None

    def load_partners_data(self):
        if self.connection:
            cursor = self.connection.cursor()

            query = """
                SELECT p.company_name, pt.name AS type, p.director_full_name, p.phone, p.rating, p.discount
                FROM Partners p
                LEFT JOIN TypeCompany pt ON p.type_partner = pt.id;
            """
            cursor.execute(query)
            rows = cursor.fetchall()

            self.partners_table.setRowCount(len(rows))

            for row_num, row_data in enumerate(rows):
                # Меняем местами "Наименование" и "Тип"
                self.partners_table.setItem(row_num, 0, QTableWidgetItem(str(row_data[1]) if row_data[1] is not None else ''))  # Тип
                self.partners_table.setItem(row_num, 1, QTableWidgetItem(str(row_data[0]) if row_data[0] is not None else ''))  # Наименование
                for col_num in range(2, len(row_data)):
                    self.partners_table.setItem(row_num, col_num, QTableWidgetItem(str(row_data[col_num]) if row_data[col_num] is not None else ''))

            cursor.close()

    def open_edit_partner_form(self):
        selected_row = self.partners_table.currentRow()

        if selected_row == -1:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, выберите партнера для редактирования.")
            return

        name = self.partners_table.item(selected_row, 1).text() if self.partners_table.item(selected_row, 1) else ""
        type_name = self.partners_table.item(selected_row, 0).text() if self.partners_table.item(selected_row, 0) else ""
        director = self.partners_table.item(selected_row, 2).text() if self.partners_table.item(selected_row, 2) else ""
        phone = self.partners_table.item(selected_row, 3).text() if self.partners_table.item(selected_row, 3) else ""
        rating = self.partners_table.item(selected_row, 4).text() if self.partners_table.item(selected_row, 4) else ""

        cursor = self.connection.cursor()
        cursor.execute("SELECT id FROM TypeCompany WHERE name = %s", (type_name,))
        type_id = cursor.fetchone()[0]
        cursor.close()

        self.open_partner_form("Редактирование партнера", [name, director, phone, rating, ""])

        index = self.type_dropdown.findData(type_id)
        if index != -1:
            self.type_dropdown.setCurrentIndex(index)

        self.edited_partner_id = self.get_partner_id(name, director)

    def get_partner_id(self, name, director):
        cursor = self.connection.cursor()
        cursor.execute("SELECT id FROM Partners WHERE company_name = %s AND director_full_name = %s", (name, director))
        partner_id = cursor.fetchone()[0]
        cursor.close()
        return partner_id

    def get_total_sales(self, partner_name):
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT SUM(pp.quantity)
            FROM PartnerProduct pp
            LEFT JOIN Partners p ON pp.id_partener = p.id
            WHERE p.company_name = %s;
        """, (partner_name,))
        total_sales = cursor.fetchone()[0] or 0  # Если нет продаж, устанавливаем 0
        cursor.close()
        return total_sales

    def calculate_discount(self, total_sales):
        if total_sales < 10000:
            return 0
        elif 10000 <= total_sales < 50000:
            return 5
        elif 50000 <= total_sales < 300000:
            return 10
        else:  # total_sales >= 300000
            return 15

    def load_history_data(self):
        if self.connection:
            cursor = self.connection.cursor()

            query = """
                SELECT 
                    p.description AS "Продукция", 
                    pp.quantity AS "Количество", 
                    pr.company_name AS "Наименование партнера", 
                    pp.date_of_sale AS "Дата продажи"
                FROM 
                    PartnerProduct pp
                LEFT JOIN Products p ON pp.id_product = p.id
                LEFT JOIN Partners pr ON pp.id_partener = pr.id
                ORDER BY 
                    pp.date_of_sale DESC;
            """

            cursor.execute(query)
            rows = cursor.fetchall()

            self.history_table.setRowCount(len(rows))

            for row_num, row_data in enumerate(rows):
                for col_num, data in enumerate(row_data):
                    self.history_table.setItem(row_num, col_num, QTableWidgetItem(str(data) if data is not None else ''))

            cursor.close()

app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
