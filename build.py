import PyInstaller.__main__
import platform
import os
import subprocess
import shutil
import tempfile
import version

def build():
    # 운영체제 확인 (Windows는 ';', Mac/Linux는 ':')
    system_platform = platform.system()
    sep = ';' if system_platform == 'Windows' else ':'
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    print(f"Building {version.VERSION} for {system_platform}...")

    # 임시 작업 디렉토리 생성 (캐시 파일 저장용)
    build_cache_dir = tempfile.mkdtemp(prefix="KaneDefense_Build_")
    print(f"Using temporary build directory: {build_cache_dir}")

    # PyInstaller 옵션 설정
    options = [
        'start.py',                         # 메인 진입점 파일
        '--name=KaneDefense',               # 생성될 실행 파일 이름
        '--onedir',                         # 폴더 형태로 생성 (빌드 속도 빠름)
        '--noconsole',                      # 콘솔 창 숨김 (GUI 프로그램)
        '--clean',                          # 빌드 캐시 정리
        f'--workpath={build_cache_dir}',      # 빌드 작업 경로를 캐시 폴더로 지정
        f'--specpath={build_cache_dir}',      # .spec 파일을 캐시 폴더로 지정
    ]

    # 리소스 데이터 포함 (소스경로:대상경로) - 폴더가 존재할 때만 추가
    for folder in ['image', 'sound', 'font']:
        src_path = os.path.join(project_root, folder)
        if os.path.exists(src_path):
            options.append(f'--add-data={src_path}{sep}{folder}')
        else:
            print(f"Warning: Resource folder '{folder}' not found. Skipping.")

    # PyInstaller 실행
    PyInstaller.__main__.run(options)

    # 결과 폴더 생성 및 파일 이동 (dist -> result)
    result_path = os.path.abspath("result")
    if not os.path.exists(result_path):
        os.makedirs(result_path)

    dist_path = os.path.abspath("dist")
    if os.path.exists(dist_path):
        for filename in os.listdir(dist_path):
            src = os.path.join(dist_path, filename)
            dst = os.path.join(result_path, filename)
            if os.path.exists(dst): # 기존 파일이 있으면 삭제
                if os.path.isdir(dst): shutil.rmtree(dst)
                else: os.remove(dst)
            shutil.move(src, dst)
        shutil.rmtree(dist_path) # dist 폴더 삭제
        print(f"Moved build artifacts to '{result_path}'")

    # 빌드 캐시 디렉토리 삭제
    # 임시 빌드 디렉토리 정리
    if os.path.exists(build_cache_dir):
        print(f"Cleaning up temporary directory: {build_cache_dir}")
        shutil.rmtree(build_cache_dir)
        print("Cleaned up temporary build files.")

    # 결과 폴더 열기
    if os.path.exists(result_path):
        print(f"Opening result folder: {result_path}")
        if system_platform == 'Windows':
            os.startfile(result_path)
        elif system_platform == 'Darwin': # macOS
            subprocess.call(["open", result_path])
        else: # Linux
            subprocess.call(["xdg-open", result_path])

if __name__ == "__main__":
    build()