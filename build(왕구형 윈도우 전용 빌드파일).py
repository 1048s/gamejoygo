import PyInstaller.__main__
import os
import shutil

# 빌드 설정
APP_NAME = "KaneDefense"
MAIN_SCRIPT = "main.py"  # 사용자님의 메인 코드 파일명에 맞게 수정하세요.
ICON_PATH = "icon.ico" # 아이콘으로 쓸 이미지 (있다면 지정)

def build_game():
    print(f"--- {APP_NAME} 빌드를 시작합니다 (세계 최고의 개발자 모드) ---")

    # 기존 빌드 폴더 삭제 (깨끗한 빌드 보장)
    for folder in ['build', 'dist']:
        if os.path.exists(folder):
            shutil.rmtree(folder)

    # PyInstaller 옵션 설정
    opts = [
        MAIN_SCRIPT,                # 실행할 메인 스크립트
        '--onefile',                # 파일 하나로 합치기
        '--noconsole',              # 실행 시 검은색 콘솔창 띄우지 않기
        f'--name={APP_NAME}',       # 생성될 파일 이름
        
        # 리소스 폴더 추가 (image 폴더와 sound 폴더를 포함)
        '--add-data=image;image',   
        '--add-data=sound;sound',
        
        # 필요한 라이브러리 강제 포함 (필요 시)
        '--clean',
    ]

    # 아이콘 파일이 실제로 존재하면 추가
    if os.path.exists(ICON_PATH):
        # .ico 파일이 아니라면 PyInstaller가 변환을 시도하거나 오류가 날 수 있음
        # 안전하게 아이콘 옵션은 주석 처리하거나 .ico 파일을 준비하는 것이 좋습니다.
        opts.append(f'--icon={ICON_PATH}')
        pass

    # 빌드 실행
    PyInstaller.__main__.run(opts)

    print(f"\n--- 빌드 완료! dist 폴더 내의 {APP_NAME}.exe를 확인하세요. ---")

if __name__ == "__main__":
    build_game()