import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QFileDialog, QListWidget, QLabel, QMessageBox, QHBoxLayout, QInputDialog, QLineEdit, QTextEdit
)
from PyQt5.QtCore import Qt

# ----------------- CONFIG -----------------
TESTS_DIR = os.path.join(os.getcwd(), "testy")
ANSWERS_DIR = os.path.join(os.getcwd(), "odpovede")
PROFILE_FILE = os.path.join(os.getcwd(), "vyhodnotenie.txt")  # Complex personality profile
ADMIN_PASSWORD = "admin123"  # Change for production!
# ------------------------------------------

def ensure_dirs():
    for d in [TESTS_DIR, ANSWERS_DIR]:
        if not os.path.exists(d):
            os.makedirs(d)

class AdminWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ADMIN - Správa testov")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.intro_label = QLabel("Nahrajte testy vo forme .txt súborov. Pridané testy sa zobrazia nižšie.")
        self.layout.addWidget(self.intro_label)

        self.add_test_button = QPushButton("Pridať test (vybrať .txt súbor)")
        self.add_test_button.clicked.connect(self.add_test)
        self.layout.addWidget(self.add_test_button)

        self.test_list = QListWidget()
        self.layout.addWidget(self.test_list)

        self.test_folder_button = QPushButton("Otvoriť zložku s testami")
        self.test_folder_button.clicked.connect(lambda: os.startfile(TESTS_DIR))
        self.layout.addWidget(self.test_folder_button)

        self.refresh_test_list()

    def add_test(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Vyberte test (.txt)", "", "Text Files (*.txt)")
        if file_path:
            try:
                base_name = os.path.basename(file_path)
                dest_path = os.path.join(TESTS_DIR, base_name)
                idx = 1
                while os.path.exists(dest_path):
                    name, ext = os.path.splitext(base_name)
                    dest_path = os.path.join(TESTS_DIR, f"{name}_{idx}{ext}")
                    idx += 1
                with open(file_path, "r", encoding="utf-8") as src, open(dest_path, "w", encoding="utf-8") as dst:
                    dst.write(src.read())
                self.refresh_test_list()
            except Exception as e:
                QMessageBox.warning(self, "Chyba", f"Nastala chyba pri nahrávaní testu:\n{e}")

    def refresh_test_list(self):
        self.test_list.clear()
        if os.path.exists(TESTS_DIR):
            for fname in sorted(os.listdir(TESTS_DIR)):
                if fname.endswith('.txt'):
                    self.test_list.addItem(fname)

class TestTakingWindow(QWidget):
    def __init__(self, username=None, parent=None):
        super().__init__(parent)
        self.username = username
        self.setWindowTitle("Používateľ - Výber a spustenie testu")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.intro_label = QLabel("Vyberte test na spustenie:")
        self.layout.addWidget(self.intro_label)

        self.test_list = QListWidget()
        self.layout.addWidget(self.test_list)
        self.test_list.itemDoubleClicked.connect(self.start_test)

        self.refresh_test_list()

        self.profile_button = QPushButton("Zobraziť komplexné vyhodnotenie")
        self.profile_button.clicked.connect(self.show_profile)
        self.layout.addWidget(self.profile_button)

    def refresh_test_list(self):
        self.test_list.clear()
        if os.path.exists(TESTS_DIR):
            for fname in sorted(os.listdir(TESTS_DIR)):
                if fname.endswith('.txt'):
                    self.test_list.addItem(fname)

    def start_test(self, item):
        test_file = os.path.join(TESTS_DIR, item.text())
        with open(test_file, "r", encoding="utf-8") as f:
            questions = [line.strip() for line in f if line.strip()]

        self.test_dialog = TestDialog(self.username, item.text(), questions, self)
        self.test_dialog.finished.connect(self.on_test_finished)
        self.test_dialog.show()

    def on_test_finished(self):
        # After test: run AI evaluation and update profile
        self.run_ai_evaluation()

    def run_ai_evaluation(self):
        # Find all user's answers and concatenate to result.txt
        user_answers_files = [os.path.join(ANSWERS_DIR, f) for f in os.listdir(ANSWERS_DIR)
                              if f.startswith(self.username + "_") and f.endswith('.txt')]
        with open("result.txt", "w", encoding="utf-8") as out:
            for fname in user_answers_files:
                out.write(f"=== {os.path.basename(fname)} ===\n")
                with open(fname, "r", encoding="utf-8") as inp:
                    out.write(inp.read() + "\n")
        # Run vyhodnotenie.py (if possible)
        if os.path.exists("vyhodnotenie.py"):
            os.system(f"{sys.executable} vyhodnotenie.py")
        # Inform user
        QMessageBox.information(self, "AI vyhodnotenie", "Vaše odpovede boli vyhodnotené a profil aktualizovaný.")

    def show_profile(self):
        if os.path.exists(PROFILE_FILE):
            with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                txt = f.read()
        else:
            txt = "Zatiaľ nebol vygenerovaný žiadny komplexný profil."
        dlg = QTextEdit()
        dlg.setReadOnly(True)
        dlg.setWindowTitle("Komplexné vyhodnotenie osobnosti")
        dlg.setText(txt)
        dlg.setMinimumSize(600, 400)
        dlg.show()
        # Prevent garbage collection
        self.profile_dlg = dlg

class TestDialog(QWidget):
    from PyQt5.QtCore import pyqtSignal
    finished = pyqtSignal()
    def __init__(self, username, test_name, questions, parent=None):
        super().__init__(parent)
        self.username = username
        self.test_name = test_name
        self.questions = questions
        self.answers = []
        self.cur = 0
        self.setWindowTitle(f"Test: {test_name}")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.question_label = QLabel()
        self.layout.addWidget(self.question_label)
        self.answer_edit = QTextEdit()
        self.layout.addWidget(self.answer_edit)
        self.next_button = QPushButton("Ďalej")
        self.next_button.clicked.connect(self.next_question)
        self.layout.addWidget(self.next_button)

        self.show_question()

    def show_question(self):
        if self.cur < len(self.questions):
            self.question_label.setText(self.questions[self.cur])
            self.answer_edit.setText("")
        else:
            self.save_answers()

    def next_question(self):
        self.answers.append(f"Otázka: {self.questions[self.cur]}\nOdpoveď: {self.answer_edit.toPlainText().strip()}\n")
        self.cur += 1
        if self.cur < len(self.questions):
            self.show_question()
        else:
            self.save_answers()

    def save_answers(self):
        fname = os.path.join(ANSWERS_DIR, f"{self.username}_{self.test_name}")
        with open(fname, "w", encoding="utf-8") as f:
            for a in self.answers:
                f.write(a + "\n")
        QMessageBox.information(self, "Hotovo", "Test dokončený. Odpovede boli uložené a odoslané na AI vyhodnotenie.")
        self.finished.emit()
        self.close()

class LoginWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Prihlásenie")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.admin_button = QPushButton("Prihlásiť sa ako ADMIN")
        self.admin_button.clicked.connect(self.admin_login)
        self.layout.addWidget(self.admin_button)

        self.user_button = QPushButton("Prihlásiť sa ako používateľ")
        self.user_button.clicked.connect(self.user_login)
        self.layout.addWidget(self.user_button)

    def admin_login(self):
        pwd, ok = QInputDialog.getText(self, "ADMIN prihlásenie", "Zadajte heslo:", QLineEdit.Password)
        if ok and pwd == ADMIN_PASSWORD:
            self.hide()
            self.admin_win = AdminWindow()
            self.admin_win.setWindowTitle("ADMIN - Správa testov")
            self.admin_win.show()
        elif ok:
            QMessageBox.warning(self, "Chyba", "Nesprávne heslo!")

    def user_login(self):
        username, ok = QInputDialog.getText(self, "Používateľ", "Zadajte svoje meno:")
        if ok and username.strip():
            self.hide()
            self.user_win = TestTakingWindow(username=username.strip())
            self.user_win.setWindowTitle(f"Používateľ: {username.strip()}")
            self.user_win.show()

if __name__ == "__main__":
    ensure_dirs()
    app = QApplication(sys.argv)
    login_win = LoginWindow()
    login_win.show()
    sys.exit(app.exec_())
