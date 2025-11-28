import socket
import math
import pickle
from threading import Thread
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QLineEdit, QPushButton, QLabel, QMessageBox,
                             QListWidget, QListWidgetItem, QGridLayout, QFrame)
from PyQt6.QtGui import QPainter, QColor, QMouseEvent, QKeySequence, QShortcut
from PyQt6.QtCore import Qt, QPointF

class Communication(QObject):
    game_update_signal = pyqtSignal(dict)
    connection_lost_signal = pyqtSignal()

class SocketCommunication(Thread):
    def __init__(self, sock: socket.socket, comm: Communication):
        super().__init__(daemon=True)
        self.comm = comm
        self.sock = sock
        self.running = True
        self.start()

    def run(self):
        while self.running:
            try:
                data = self.sock.recv(4096)
                if not data:
                    break

                message = pickle.loads(data)
                self.comm.game_update_signal.emit(message)

            except Exception as e:
                print(f"Ошибка подключения: {e}")
                break

        self.comm.connection_lost_signal.emit()

    def send_message(self, message):
        try:
            self.sock.send(pickle.dumps(message))
        except Exception as e:
            print(f"Ошибка отправки: {e}")

    def stop(self):
        self.running = False

class Star:
    def __init__(self, star_data):
        self.star_id = star_data['star_id']
        self.x = star_data['x']
        self.y = star_data['y']
        self.radius = star_data['radius']
        self.speed_x = star_data['speed_x']
        self.speed_y = star_data['speed_y']
        self.active = star_data['active']
        self.color = QColor(255, 215, 0)

def draw_star(painter, x, y, radius, color):
    points = []
    for i in range(10):
        angle_deg = i * 36
        r = radius if i % 2 == 0 else radius / 2
        angle_rad = math.radians(angle_deg - 90)
        px = x + r * math.cos(angle_rad)
        py = y + r * math.sin(angle_rad)
        points.append(QPointF(px, py))
    painter.setBrush(color)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawPolygon(points)

class GameField(QFrame):
    def __init__(self, sock_comm):
        super().__init__()
        self.sock_comm = sock_comm
        self.stars = []
        self.setFixedSize(760, 330)
        self.setStyleSheet("QFrame {border: 2px solid #FFB6C1; border-radius: 10px; background-color: #FFF0F5}")

    def update_stars(self, stars):
        self.stars = stars
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing) # сглаживание

        for star in self.stars:
            if star.active:
                draw_star(painter, star.x, star.y, star.radius, star.color)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            x, y = event.pos().x(), event.pos().y()  # координаты клика мышью

            if 0 <= x <= self.width() and 0 <= y <= self.height():
                message = {'type': 'click', 'data': {'x': x, 'y': y} }
                self.sock_comm.send_message(message)

class GameWidget(QWidget):
    def __init__(self, username, sock_comm: SocketCommunication):
        super().__init__()
        self.username = username
        self.sock_comm = sock_comm
        self.stars = []
        self.players = []
        self.score = 0

        self.setWindowTitle(f"STAR CLICKER - {username}")
        self.setFixedSize(800, 600)

        self.init_ui()
        self.setup_connections()

    def init_ui(self):
        grid_layout = QGridLayout()

        # панель информации
        info_layout = QHBoxLayout()
        self.setStyleSheet("QWidget {font-weight: bold; color: #FFB6C1}")
        self.score_label = QLabel(f"Ваш счет: 0")
        self.players_label = QLabel("Игроки онлайн: 0")

        info_layout.addWidget(self.score_label)
        info_layout.addWidget(self.players_label)
        info_layout.addStretch()

        # кнопки действий
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Сохранить игру")
        self.disconnect_btn = QPushButton("Отключиться")

        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.disconnect_btn)
        button_layout.addStretch()

        # игровое поле
        self.game_field = GameField(self.sock_comm)

        # рейтинг игроков
        self.leaderboard = QListWidget()
        self.leaderboard.setStyleSheet("QWidget {border: 2px solid #FFB6C1; border-radius: 10px}")

        grid_layout.addLayout(info_layout, 0, 0, 1, 2)
        grid_layout.addLayout(button_layout, 1, 0, 1, 2)
        grid_layout.addWidget(QLabel("Кликайте на звезды!"), 2, 0, 1, 2)
        grid_layout.addWidget(self.game_field, 3, 0, 1, 2)
        grid_layout.addWidget(QLabel("Рейтинг игроков:"), 4, 0, 1, 2)
        grid_layout.addWidget(self.leaderboard, 5, 0, 1, 2)

        self.setLayout(grid_layout)

    def setup_connections(self):
        self.save_btn.clicked.connect(self.save_game)
        self.disconnect_btn.clicked.connect(self.disconnect)

    def update_game_state(self, game_state):
        server_stars = game_state.get('stars', [])
        self.stars = [Star(star_data) for star_data in server_stars]

        self.game_field.update_stars(self.stars)
        self.players = game_state.get('players', [])

        for player in self.players:
            if player['username'] == self.username:
                self.score = player['score']
                break

        self.score_label.setText(f"Ваш счет: {self.score}")
        self.players_label.setText(f"Игроки онлайн: {len(self.players)}")

        self.update_leaderboard()

    def update_leaderboard(self):
        self.leaderboard.clear()

        sorted_players = sorted(self.players, key=lambda x: x['score'], reverse=True)

        max_score = 0
        if sorted_players:
            max_score = sorted_players[0]['score']

        for i, player in enumerate(sorted_players):
            item_text = f"{i + 1}. {player['username']}: {player['score']} очков"

            if player['score'] > 0 and player['score'] == max_score:
                item_text += " 👑"

            if player['username'] == self.username:
                item_text += " (Вы)"

            item = QListWidgetItem(item_text)
            self.leaderboard.addItem(item)

    def save_game(self):
        message = {'type': 'save', 'data': None}
        self.sock_comm.send_message(message)

    def disconnect(self):
        message = {'type': 'disconnect', 'data': None}
        self.sock_comm.send_message(message)
        self.close()

    def closeEvent(self, event):
        self.sock_comm.stop()
        event.accept()

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.game_widget = None
        self.sock_comm = None

        self.init_ui()
        self.setStyleSheet("QWidget {font-weight: bold; color: #FFB6C1}")
        self.setWindowTitle("STAR CLICKER - Подключение")
        self.show()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.address_field = QLineEdit()
        self.address_field.setText("127.0.0.1")
        self.address_field.setPlaceholderText("Адрес сервера")

        self.port_field = QLineEdit()
        self.port_field.setText("10000")
        self.port_field.setPlaceholderText("Порт")

        self.username_field = QLineEdit()
        self.username_field.setPlaceholderText("Имя игрока")

        self.connect_btn = QPushButton("Подключиться")
        self.connect_btn.clicked.connect(self.connect_to_server)

        self.enter_shortcut = QShortcut(QKeySequence("Return"), self)
        self.enter_shortcut.activated.connect(self.connect_to_server)

        layout.addWidget(QLabel("Адрес сервера:"))
        layout.addWidget(self.address_field)
        layout.addWidget(QLabel("Порт:"))
        layout.addWidget(self.port_field)
        layout.addWidget(QLabel("Имя игрока:"))
        layout.addWidget(self.username_field)
        layout.addWidget(self.connect_btn)

        self.setLayout(layout)

    def connect_to_server(self):
        address = self.address_field.text().strip()
        port = self.port_field.text().strip()
        username = self.username_field.text().strip()

        if not all([address, port, username]):
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            return

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((address, int(port)))

            comm = Communication()
            self.sock_comm = SocketCommunication(sock, comm)

            register_msg = {'type': 'register', 'data': username}
            self.sock_comm.send_message(register_msg)

            comm.game_update_signal.connect(self.handle_game_update)
            comm.connection_lost_signal.connect(self.handle_connection_lost)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось подключиться: {e}")

    @pyqtSlot(dict)
    def handle_game_update(self, message):
        msg_type = message.get('type')

        if msg_type == 'register_success':
            data = message.get('data', {})
            username = data.get('username')

            self.game_widget = GameWidget(username, self.sock_comm)
            self.game_widget.show()
            self.hide()

        elif msg_type == 'game_state':
            if self.game_widget:
                self.game_widget.update_game_state(message.get('data', {}))

        elif msg_type == 'click_success':
            data = message.get('data', {})
            print(f"Получено очков: {data.get('points_earned', 0)}")

        elif msg_type == 'save_success':
            QMessageBox.information(self.game_widget if self.game_widget else self,
                                    "Сохранение", message.get('data', 'Игра сохранена'))

        elif msg_type == 'error':
            QMessageBox.warning(self, "Ошибка", message.get('data', 'Неизвестная ошибка'))

    @pyqtSlot()
    def handle_connection_lost(self):
        QMessageBox.warning(self, "Соединение", "Соединение с сервером потеряно")
        if self.game_widget:
            self.game_widget.close()
        self.show()


if __name__ == '__main__':
    app = QApplication([])
    window = LoginWindow()
    app.exec()