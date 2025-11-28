import socket
import pickle
import time
import threading
from datetime import datetime
import json
import random

class Player:
    def __init__(self, username, conn, address):
        self.username = username
        self.conn = conn
        self.address = address
        self.score = 0
        self.connected_at = datetime.now()

    def to_dict(self):
        return {'username': self.username, 'score': self.score}

class Star:
    def __init__(self, star_id, x, y, radius=30):
        self.star_id = star_id
        self.x = x
        self.y = y
        self.radius = radius
        self.speed_x = random.choice([-4, -3, -2, 2, 3, 4])
        self.speed_y = random.choice([-4, -3, -2, 2, 3, 4])
        self.active = True
        self.created_at = datetime.now()

    def to_dict(self):
        return {
            'star_id': self.star_id,
            'x': self.x,
            'y': self.y,
            'radius': self.radius,
            'speed_x': self.speed_x,
            'speed_y': self.speed_y,
            'active': self.active
        }

class ClickerGameServer:
    def __init__(self, host='127.0.0.1', port=10000):
        self.host = host
        self.port = port
        self.players = {}
        self.stars = {}
        self.lock = threading.Lock()
        self.running = True
        self.next_star_id = 1
        self.game_history = []
        self.field_width = 760
        self.field_height = 330
    def generate_star(self):
        star_id = self.next_star_id
        self.next_star_id += 1

        radius = random.randint(25, 45)
        x = random.randint(radius, self.field_width - radius)
        y = random.randint(radius, self.field_height - radius)

        star = Star(star_id, x, y, radius)
        self.stars[star_id] = star
        return star

    def update_stars(self):
        for star in self.stars.values():
            if not star.active:
                continue

            star.x += star.speed_x
            star.y += star.speed_y

            # отскок от границ
            if star.x - star.radius <= 0 or star.x + star.radius >= self.field_width:
                star.speed_x *= -1
            if star.y - star.radius <= 0 or star.y + star.radius >= self.field_height:
                star.speed_y *= -1

            # ограничение в пределах игрового поля
            star.x = max(star.radius, min(star.x, self.field_width - star.radius))
            star.y = max(star.radius, min(star.y, self.field_height - star.radius))

    def broadcast_game_state(self):
        with self.lock:
            game_state = {'type': 'game_state', 'data':
                {'players': [player.to_dict() for player in self.players.values()],
                    'stars': [star.to_dict() for star in self.stars.values() if star.active],
                    'timestamp': datetime.now().isoformat()} }

            disconnected_players = []
            for username, player in self.players.items():
                try:
                    player.conn.send(pickle.dumps(game_state))
                except:
                    disconnected_players.append(username)

            for username in disconnected_players:
                self.handle_disconnect(username)

    def handle_click(self, username, click_data):
        with self.lock:
            if username not in self.players:
                return

            player = self.players[username]
            x = click_data.get('x')
            y = click_data.get('y')

            star_clicked = None
            for star in self.stars.values():
                if not star.active:
                    continue

                # если расстояние от точки клика до центра звезды меньше
                # или равно радиусу звезды - клик попал в звезду
                distance = ((x - star.x) ** 2 + (y - star.y) ** 2) ** 0.5
                if distance <= star.radius:
                    star_clicked = star
                    break

            if star_clicked:
                star_clicked.active = False
                player.score += 1

                self.game_history.append({
                    'username': username,
                    'action': 'click',
                    'star_id': star_clicked.star_id,
                    'points': 1,
                    'timestamp': datetime.now().isoformat()
                })

                try:
                    response = {
                        'type': 'click_success',
                        'data': {
                            'star_id': star_clicked.star_id,
                            'points_earned': 1
                        }
                    }
                    player.conn.send(pickle.dumps(response))
                except:
                    self.handle_disconnect(username)

    def handle_register(self, username, conn, address):
        with self.lock:
            if username in self.players:
                response = {'type': 'error', 'data': 'Данное имя уже занято'}
                conn.send(pickle.dumps(response))
                return False

            player = Player(username, conn, address)
            self.players[username] = player

            self.game_history.append({
                'username': username,
                'action': 'connect',
                'timestamp': datetime.now().isoformat()
            })

            response = {'type': 'register_success', 'data': {'username': username}}
            conn.send(pickle.dumps(response))

            print(f"Player {username} registered from {address}")
            return True
    def handle_save(self, username):
        with self.lock:
            filename = f"game_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            try:
                with open(filename, 'w') as f:
                    json.dump(self.game_history, f, indent=2)

                response = {'type': 'save_success', 'data': f'Игра была сохранена в {filename}'}
                for player in self.players.values():
                    try:
                        player.conn.send(pickle.dumps(response))
                    except:
                        pass

                print(f"Game history saved to {filename}")
                return True
            except Exception as e:
                print(f"Error saving game: {e}")
                return False

    def handle_disconnect(self, username):
        with self.lock:
            if username in self.players:
                player = self.players[username]

                self.game_history.append({
                    'username': username,
                    'action': 'disconnect',
                    'score': player.score,
                    'timestamp': datetime.now().isoformat()
                })

                try:
                    player.conn.close()
                except:
                    pass

                del self.players[username]
                print(f"Player {username} disconnected")

    def handle_client(self, conn, address):
        username = None

        try:
            while self.running:
                data = conn.recv(4096)
                if not data:
                    break

                try:
                    message = pickle.loads(data)
                    msg_type = message.get('type')
                    msg_data = message.get('data')

                    if msg_type == 'register':
                        if self.handle_register(msg_data, conn, address):
                            username = msg_data
                            self.broadcast_game_state()

                    elif msg_type == 'click' and username:
                        self.handle_click(username, msg_data)
                        self.broadcast_game_state()

                    elif msg_type == 'save' and username:
                        self.handle_save(username)

                    elif msg_type == 'disconnect' and username:
                        break

                except pickle.UnpicklingError:
                    print(f"Invalid data from {address}")
                    break

        except Exception as e:
            print(f"Error handling client {address}: {e}")

        finally:
            if username:
                self.handle_disconnect(username)
            conn.close()

    def start_game_loop(self):
        while self.running:
            time.sleep(0.016)  # ~60 FPS

            with self.lock:
                self.update_stars()

                active_stars = sum(1 for star in self.stars.values() if star.active)
                if active_stars < 10 and random.random() < 0.05:
                    self.generate_star()

                current_time = datetime.now()
                stars_to_remove = []
                for star_id, star in self.stars.items():
                    if not star.active and (current_time - star.created_at).total_seconds() > 10:
                        stars_to_remove.append(star_id)

                for star_id in stars_to_remove:
                    del self.stars[star_id]

            self.broadcast_game_state()

    def start(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen()

        print(f"Clicker Game Server started on {self.host}:{self.port}")

        game_thread = threading.Thread(target=self.start_game_loop, daemon=True)
        game_thread.start()

        try:
            while self.running:
                conn, address = server_socket.accept()
                print(f"New connection from {address}")

                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(conn, address),
                    daemon=True
                )
                client_thread.start()

        except KeyboardInterrupt:
            print("Shutting down server...")
            self.running = False
        finally:
            server_socket.close()

if __name__ == '__main__':
    server = ClickerGameServer()
    server.start()