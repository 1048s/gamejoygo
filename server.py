import socket
import threading
import json
import random
import time
import os
import msvcrt
import math

# --- 서버 설정 ---
HOST = '0.0.0.0'
import sys
if len(sys.argv) > 1:
    PORT = int(sys.argv[1])
else:
    PORT = 12345
# PORT = int(input("서버 포트를! 조일 번호 : "))

clients = []        # 접속한 모든 클라이언트
waiting_queue = []  # 매칭 대기 중인 클라이언트
games = {}          # socket -> GameSession
nicknames = {}      # socket -> nickname
clients_lock = threading.Lock()

class GameSession:
    def __init__(self, p1, p2, p1_nick, p2_nick, map_idx):
        self.p1 = p1
        self.p2 = p2
        self.p1_nick = p1_nick
        self.p2_nick = p2_nick
        self.map_idx = map_idx
        self.start_time = time.time()
        self.current_round = 1
        self.is_break_time = True # 게임 시작 직후 대기 시간
        self.round_start_time = time.time()
        self.round_duration = 45 # 라운드 진행 시간
        self.break_duration = 15 # 쉬는 시간
        self.is_running = True
        
        # 클라이언트에게 시작 신호 전송
        send_json(p1, {"type": "START", "map": map_idx, "opponent": p2_nick})
        send_json(p2, {"type": "START", "map": map_idx, "opponent": p1_nick})

    def update(self):
        if not self.is_running: return

        elapsed = time.time() - self.round_start_time
        
        # 상태 관리 (휴식 <-> 라운드)
        current_limit = self.break_duration if self.is_break_time else self.round_duration
        
        time_left = max(0, current_limit - elapsed)
        
        if time_left <= 0:
            if self.is_break_time:
                # 휴식 끝 -> 라운드 시작
                self.is_break_time = False
                self.round_start_time = time.time()
                # 라운드별 시간 조정 (main.py 로직 참고)
                spawn_interval_secs = max(0.4, 1.5 - self.current_round*0.05)
                enemies_count = math.floor(45 / spawn_interval_secs) if spawn_interval_secs > 0 else 50
                if self.current_round == 40: enemies_count = 10
                
                # 라운드 시작 알림 (필요하다면)
            else:
                # 라운드 끝 -> 휴식 시작
                self.is_break_time = True
                self.current_round += 1
                self.round_start_time = time.time()
                
        # 1초마다 시간 동기화 패킷 전송 (대략)
        if int(elapsed * 10) % 10 == 0:
            pkt = {
                "type": "TIME",
                "round": self.current_round,
                "is_break": self.is_break_time,
                "time_left": int(time_left),
                "total_time": current_limit
            }
            send_json(self.p1, pkt)
            send_json(self.p2, pkt)

    def close(self):
        self.is_running = False


def send_json(sock, data):
    """JSON 데이터를 개행 문자와 함께 전송"""
    try:
        msg = json.dumps(data) + "\n"
        sock.send(msg.encode('utf-8'))
    except:
        pass

def broadcast(data, sender=None):
    """모든 클라이언트에게 메시지 전송 (sender 제외)"""
    with clients_lock:
        for c in clients:
            if c != sender:
                send_json(c, data)

def handle_client(sock, addr):
    print(f"[+] 연결됨: {addr}")
    with clients_lock:
        clients.append(sock)
    
    try:
        buffer = ""
        while True:
            data = sock.recv(4096)
            if not data: break
            
            buffer += data.decode('utf-8')
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                if not line.strip(): continue
                try:
                    pkt = json.loads(line)
                    process_packet(sock, pkt)
                except json.JSONDecodeError:
                    print(f"[!] JSON 파싱 에러: {line}")
    except Exception as e:
        print(f"[-] 에러 ({addr}): {e}")
    finally:
        cleanup_client(sock)

def process_packet(sock, pkt):
    ptype = pkt.get("type")
    
    if ptype == "MATCH":
        with clients_lock:
            nicknames[sock] = pkt.get("nickname", "Unknown")
            if sock in waiting_queue or sock in games: return
            
            if len(waiting_queue) > 0:
                # 대기열에 있는 상대와 매칭
                opponent = waiting_queue.pop(0)
                if opponent == sock: # 혹시 모를 자기 자신 매칭 방지
                    waiting_queue.append(sock)
                    return

                # 게임 세션 생성
                map_idx = random.randint(0, 2)
                p1_nick = nicknames.get(sock, "Player")
                p2_nick = nicknames.get(opponent, "Player")
                
                print(f"[!] 게임 시작: {p1_nick} vs {p2_nick} (Map: {map_idx})")
                
                session = GameSession(sock, opponent, p1_nick, p2_nick, map_idx)
                games[sock] = session
                games[opponent] = session
            else:
                # 대기열 등록
                waiting_queue.append(sock)
                send_json(sock, {"type": "WAIT"})
                print(f"[*] 대기열 등록: {sock.getpeername()}")

    elif ptype == "CHAT":
        # 채팅은 전체 브로드캐스트 (로비/인게임 공용)
        broadcast({"type": "CHAT", "msg": pkt.get("msg")}, sock)

    elif ptype in ["SPAWN", "HP", "DIE"]:
        # 게임 상대방에게 패킷 전달
        session = games.get(sock)
        if session:
            opponent = session.p2 if session.p1 == sock else session.p1
            if ptype == "DIE":
                send_json(opponent, {"type": "WIN"})
                session.close()
            else:
                send_json(opponent, pkt)

def cleanup_client(sock):
    with clients_lock:
        if sock in clients: clients.remove(sock)
        if sock in waiting_queue: waiting_queue.remove(sock)
        if sock in nicknames: del nicknames[sock]
        
        if sock in games:
            session = games[sock]
            if session.is_running:
                opponent = session.p2 if session.p1 == sock else session.p1
                send_json(opponent, {"type": "WIN", "reason": "disconnect"})
                session.close()
            
            # 양쪽 모두의 레퍼런스 제거
            if session.p1 in games: del games[session.p1]
            if session.p2 in games: del games[session.p2]
            
    try:
        sock.close()
    except: pass
    print("[-] 클라이언트 퇴장")

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind((HOST, PORT))
        server.listen()
        print(f"[*] 서버 시작됨 ({PORT}). 종료하려면 Esc를 누르세요.")
        
        # 클라이언트 수락 스레드
        def accept_clients():
            while True:
                try:
                    client_sock, addr = server.accept()
                    threading.Thread(target=handle_client, args=(client_sock, addr), daemon=True).start()
                except:
                    break
        
        threading.Thread(target=accept_clients, daemon=True).start()

        import math

        # 메인 루프 (게임 로직 업데이트 및 종료 체크)
        while True:
            # 1. 종료 키 체크 (Windows 전용)
            if msvcrt.kbhit():
                if ord(msvcrt.getch()) == 27: # ESC
                    print("\n[!] 서버 종료 요청됨.")
                    break
            
            # 2. 게임 세션 업데이트
            active_sessions = set(games.values())
            for session in active_sessions:
                session.update()
                
            time.sleep(0.1)

    except Exception as e:
        print(f"[!] 서버 실행 실패: {e}")
    finally:
        server.close()
        os._exit(0)

if __name__ == "__main__":
    start_server()
