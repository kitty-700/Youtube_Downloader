import sys

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5 import uic
from pytube import YouTube
import ffmpeg
import subprocess

import re

import os
import sys
form_class = uic.loadUiType('main.ui')[0]
file_size = 0

class MainScreen(QMainWindow, form_class): # main_screen
    def __init__(self):
        super().__init__()
        self.setupUi(self) # uic 로부터 상속받은 화면 초기화
        self.setWindowTitle('Youtube Downloader')
        # menu = MenuInit(self)

        self.btn_download : QPushButton

        self.le_yt_link     : QLineEdit
        self.le_title       : QLineEdit
        self.le_author      : QLineEdit
        self.le_date        : QLineEdit
        self.le_res         : QLineEdit
        self.le_file_size   : QLineEdit

        self.qpb_download    : QProgressBar

        def clear():
            self.le_title.setText("")
            self.le_author.setText("")
            self.le_date.setText("")
            self.le_res.setText("")
            self.le_file_size.setText("")

        def download():
            clear()
            self.btn_download.setEnabled(False)
            self.downloader = Downloader(url=self.le_yt_link.text())
            self.downloader.downloading.connect(self.downloading)
            self.downloader.checks .connect(self.checks)
            self.downloader.start()

        def open_folder():
            os.startfile(".")

        self.btn_download.clicked.connect(download)
        self.btn_open_folder.clicked.connect(open_folder)
        self.show()

    @pyqtSlot(int)
    def downloading(self, num:int):
        self.qpb_download    : QProgressBar
        self.qpb_download.setValue(num)
        if num >= 100:
            self.btn_download.setEnabled(True)

    @pyqtSlot(tuple)
    def checks(self, tuple:tuple):
        self.le_title.      setText(tuple[0])
        self.le_author.     setText(tuple[1])
        self.le_date.       setText(tuple[2])
        self.le_res.        setText(tuple[3])
        GB_convert = int(tuple[4]) / 1024 / 1024 / 1024
        self.le_file_size.  setText("%.2f GB" % GB_convert)

class Downloader(QThread):
    downloading = pyqtSignal(int)    # 사용자 정의 시그널
    checks      = pyqtSignal(tuple)    # 사용자 정의 시그널

    def progress_Check(self, chunk, file_handle, remaining):
        file_downloaded = file_size - remaining
        percentage = file_downloaded / file_size * 100
        print(percentage)
        self.downloading.emit(int(percentage))  # 방출

    def __init__(self, url:str):
        super().__init__()
        self.num = 0             # 초깃값 설정
        self.url = url

    def run(self):
        print("Download Start")
        DOWNLOAD_FOLDER = "."

        file_name = ""
        audio_file_name = "temp_audio.mp4"
        video_file_name = "temp_video.mp4"

        def audio_download(audio_file_name):
            for i in range(1):
                # STEP 1
                print("Audio 스트림 생성")
                try:
                    yta = YouTube(self.url, on_progress_callback=self.progress_Check)
                    streama = yta.streams.filter(adaptive=True, file_extension='mp4', only_audio=True).order_by('abr').desc().first()
                    print(streama)
                except Exception as ex:
                    print("Audio 스트림 생성 실패 [%s]" % (str(ex)))
                    break
                # STEP 2
                try:
                    global file_size
                    file_size = streama.filesize # 굳이 위젯에 emit() 안 뿌려주더라도, 이 부분이 없으면 [division by zero] 에러 발생
                except Exception as ex:
                    print("Audio error[%s]" % (str(ex)))
                    break
                # STEP 3
                print("Audio 다운로드 실행")
                try:
                    streama.download(DOWNLOAD_FOLDER, filename=audio_file_name)
                except Exception as ex:
                    print("Audio 다운로드 실행 실패 [%s]" % (str(ex)))
                    break

        def video_download(video_file_name):
            # 비디오 다운로드
            for i in range(1):
                # STEP 1
                print("Video 스트림 생성")
                try:
                    yt = YouTube(self.url, on_progress_callback=self.progress_Check)
                    stream = yt.streams.filter(adaptive=True, only_video=True).order_by('resolution').desc().first()
                    print(stream)
                except Exception as ex:
                    print("Video 스트림 생성 실패 [%s]" % (str(ex)))
                    break
                # STEP 2
                print("메타 데이터 출력")
                try:
                    global file_size
                    file_size = stream.filesize
                    self.checks.emit((yt.title, yt.author, str(yt.publish_date), "%s/%s" % (str(stream.resolution), str(stream.fps)),  str(file_size)))
                except Exception as ex:
                    print("메타 데이터 출력 실패 [%s]" % (str(ex)))
                    break
                # STEP 3
                print("Video 다운로드 실행")
                try:
                    stream.download(DOWNLOAD_FOLDER, filename=video_file_name)
                except Exception as ex:
                    print("Video 다운로드 실행 실패 [%s]" % (str(ex)))
                    break
                return yt.title

        def combine(video_file_name, audio_file_name):
            try:
                workdir = os.path.dirname(os.path.realpath(__file__))
                print(workdir)
                print(workdir + f'\\{video_file_name}')
                print(workdir + f'\\{audio_file_name}')
                result = subprocess.Popen(
                    [
                        'ffmpeg',
                        '-y',
                        '-i',
                        workdir + f'\\{video_file_name}',
                        '-i',
                        workdir + f'\\{audio_file_name}',
                        workdir + '\\' + file_name.replace('\\', '-') + '.mp4'
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                out, err = result.communicate()
                exitcode = result.returncode
                if exitcode != 0:
                    print(exitcode, out.decode('utf8'), err.decode('utf8'))
                else:
                    print('Completed')
            except Exception as ex:
                print(ex)

        audio_download(audio_file_name)
        video_download(video_file_name)

        self.downloading.emit(90)
        combine(video_file_name, audio_file_name)
        self.downloading.emit(100)

# print("제목 : ", yt.title)
# print("길이 : ", yt.length)
# print("게시자 : ", yt.author)
# print("게시날짜 : ", yt.publish_date)
# print("조회수 : ", yt.views)
# print("키워드 : ", yt.keywords)
# print("설명 : ", yt.description)
# print("썸네일 : ", yt.thumbnail_url)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainScreen()
    sys.exit(app.exec_())

#