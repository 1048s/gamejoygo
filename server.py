import socket
import threading
import json
import random
import time

# --- 서버 설정 ---
HOST = '0.0.0.0'
PORT = 12345

clients = []        # 접속한 모든 클라이언트
waiting_queue = []  # 매칭 대기 중인 클라이언트
games = {}          # 현재 진행 중인 게임 (socket -> opponent_socket)
nicknames = {}      # socket -> nickname
clients_lock = threading.Lock()

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
                games[sock] = opponent
                games[opponent] = sock
                
                # 맵 랜덤 선택 후 게임 시작 신호 전송
                map_idx = random.randint(0, 2) # 0~2번 맵 중 하나
                p1_nick = nicknames.get(sock, "Player")
                p2_nick = nicknames.get(opponent, "Player")
                
                print(f"[!] 게임 시작: {p1_nick} vs {p2_nick} (Map: {map_idx})")
                
                send_json(sock, {"type": "START", "map": map_idx, "opponent": p2_nick})
                send_json(opponent, {"type": "START", "map": map_idx, "opponent": p1_nick})
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
        with clients_lock:
            opponent = games.get(sock)
            if opponent:
                if ptype == "DIE":
                    send_json(opponent, {"type": "WIN"})
                    # 게임 종료 처리 (메모리 정리는 cleanup이나 별도 로직에서)
                else:
                    send_json(opponent, pkt)

def cleanup_client(sock):
    with clients_lock:
        if sock in clients: clients.remove(sock)
        if sock in waiting_queue: waiting_queue.remove(sock)
        if sock in nicknames: del nicknames[sock]
        
        # 게임 중이었다면 상대방에게 승리 판정 전송
        if sock in games:
            opponent = games[sock]
            send_json(opponent, {"type": "WIN", "reason": "disconnect"})
            del games[sock]
            if opponent in games: del games[opponent]
            
    sock.close()
    print("[-] 클라이언트 퇴장")

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind((HOST, PORT))
        server.listen()
        print(f"[*] 서버 시작됨 ({PORT})")
        
        while True:
            client_sock, addr = server.accept()
            threading.Thread(target=handle_client, args=(client_sock, addr), daemon=True).start()
            
    except Exception as e:
        print(f"[!] 서버 실행 실패: {e}")

if __name__ == "__main__":
    start_server()
