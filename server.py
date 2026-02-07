import socket
import threading

# --- 서버 설정 ---
HOST = '0.0.0.0'  # 모든 IP에서의 접속 허용
PORT = 12345      # 원하는 포트로 변경 가능 (기본: 20318)

clients = []  # 접속한 클라이언트 소켓 리스트

def broadcast(message, sender_socket=None):
    """메시지를 모든 클라이언트에게 전송합니다 (보낸 사람 제외 가능)."""
    for client in clients:
        if client != sender_socket:
            try:
                client.send(message)
            except:
                # 전송 실패 시 (연결 끊김 등) 리스트에서 제거
                if client in clients:
                    clients.remove(client)

def handle_client(client_socket, addr):
    """각 클라이언트의 메시지 수신을 담당하는 함수"""
    print(f"[+] 새 연결: {addr}")
    
    # 입장 알림
    broadcast(f"[시스템] 누군가 입장했습니다.".encode('utf-8'), client_socket)

    while True:
        try:
            data = client_socket.recv(1024)
            if not data:
                break
            
            # 받은 메시지를 그대로 다른 사람들에게 전송 (에코/브로드캐스트)
            broadcast(data, client_socket)
            
        except Exception as e:
            print(f"[-] 연결 끊김: {addr} ({e})")
            break

    # 퇴장 처리
    if client_socket in clients:
        clients.remove(client_socket)
    client_socket.close()
    broadcast(f"[시스템] 누군가 퇴장했습니다.".encode('utf-8'))

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server.bind((HOST, PORT))
        server.listen()
        print(f"[*] 서버가 {PORT} 포트에서 시작되었습니다.")
        print(f"[*] 접속 대기 중...")

        while True:
            client_sock, addr = server.accept()
            clients.append(client_sock)
            
            # 각 클라이언트마다 별도의 스레드 생성
            thread = threading.Thread(target=handle_client, args=(client_sock, addr), daemon=True)
            thread.start()
            print(f"[*] 현재 접속자 수: {len(clients)}")
    except Exception as e:
        print(f"[!] 서버 시작 실패: {e}")

if __name__ == "__main__":
    start_server()