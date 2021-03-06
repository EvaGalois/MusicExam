import numpy as np
import scipy.sparse
import scipy.signal
import scipy.fftpack

import sys
import os
import time
import random
import configparser
from PyQt5.Qt import *
from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtMultimedia import *

import librosa
import librosa.display

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt

import traceback

class QTitleLabel(QLabel):
    """
    新建标题栏标签类
    """
    def __init__(self, *args):
        super(QTitleLabel, self).__init__(*args)
        self.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.setFixedHeight(30)

class musicPlayer(QtWidgets.QMainWindow):
    CQT = ''

    def __init__(self, *args, **kwargs):
        super(musicPlayer, self).__init__(*args, **kwargs)
        self.setObjectName("mainwindow")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setWindowOpacity(0.8)
        self.setMouseTracking(True)
        self.setupUI()

    def setupUI(self):
        self.resize(800, 800)
        self._padding = 0
        self.setWindowTitle('音乐音频处理')
        self.setWindowIcon(QtGui.QIcon('web.png'))
        self.setMinimumSize(800, 1200)
        # self.setFixedSize(self.width(), self.height())
        # self.setStyleSheet('.QWidget { background: black; border-radius: 5;}')
        self.setStyleSheet('#mainwindow {background: black; border-radius: 5;}')
        # self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.initTitleLabel()
        self.player = QMediaPlayer()
        self.player.setVolume(20.0)
        self.songs_list = []
        self.song_formats = ['mp3', 'm4a', 'flac', 'wav', 'ogg']
        self.cur_path = os.path.abspath(os.path.dirname(__file__))
        self.cur_path = self.cur_path + '/testmusic'
        self.cur_playing_song = ''
        self.is_switching = False
        self.is_pause = True
        self.settingfilename = 'setting.ini'

        self.center()
        self.widgets()
        self.layouts()
        self.menubar()
        self.Event()
        self.initDrag()

    def center(self):
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def initDrag(self):
        # 设置鼠标跟踪判断扳机默认值
        # pass
        self._move_drag = False
        self._corner_drag = False
        self._bottom_drag = False
        self._right_drag = False

    def initTitleLabel(self):
        # 安放标题栏标签
        self._TitleLabel = QTitleLabel(self)
        self._TitleLabel.setMouseTracking(True) # 设置标题栏标签鼠标跟踪（如不设，则标题栏内在widget上层，无法实现跟踪）
        self._TitleLabel.setIndent(10) # 设置标题栏文本缩进
        self._TitleLabel.move(0, 0) # 标题栏安放到左上角

    def widgets(self):
        self.close_btn = QPushButton(self)              # 创建一个按钮
        self.close_btn.setCheckable(True)
        # self.close_btn.setText('X')                     # 按钮显示显示文本
        # self.close_btn.resize(20, 20)
        self.close_btn.setMaximumSize(12, 12)
        self.close_btn.setStyleSheet("background-color: rgb(255, 12, 12); border-radius: 6;")
        self.close_btn.move(12, 10)

        self.max_btn = QPushButton(self)
        # self.max_btn.setText('口')
        # self.max_btn.resize(20, 20)
        self.max_btn.setMaximumSize(12, 12)
        self.max_btn.setStyleSheet("background-color: rgb(28, 255, 3); border-radius: 6;")
        self.max_btn.move(24, 10)

        self.min_btn = QPushButton(self)
        # self.min_btn.setText('一')
        # self.min_btn.resize(20, 20)
        self.min_btn.setMaximumSize(12, 12)
        self.min_btn.setStyleSheet("background-color: rgb(255, 243, 75); border-radius: 6;")
        self.min_btn.move(36, 10)

        self.titlelabel = QLabel('音乐音频处理')
        self.titlelabel.setStyle(QStyleFactory.create('Fusion'))
        self.titlelabel.setFont(QtGui.QFont("Arial", 16))
        self.setCentralWidget(self.titlelabel)

        self.placeholder = QLabel()
        autoplaceholder = int(self.geometry().x() / 2)
        self.placeholder.setMaximumSize(autoplaceholder-200, 20)


        # --播放时间
        self.label1 = QLabel('00:00')
        self.label1.setStyle(QStyleFactory.create('Fusion'))
        self.label2 = QLabel('00:00')
        self.label2.setStyle(QStyleFactory.create('Fusion'))
        self.label1.setFont(QtGui.QFont("Arial", 18))
        self.label2.setFont(QtGui.QFont("Arial", 18))

        # --滑动条
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setStyleSheet('background-color: rgba(0,0,0,0)')

        # --播放按钮
        self.play_button = QPushButton('播放', self)
        self.play_button.setStyle(QStyleFactory.create('Fusion'))

        # --静音按钮
        self.mute_button = QPushButton('静音', self)
        self.mute_button.setStyle(QStyleFactory.create('Fusion'))

        self.choose_button = QPushButton('选择', self)
        self.choose_button.setStyle(QStyleFactory.create('Fusion'))

        # --上一首按钮
        self.preview_button = QPushButton('上一首', self)
        self.preview_button.setStyle(QStyleFactory.create('Fusion'))

        # --下一首按钮
        self.next_button = QPushButton('下一首', self)
        self.next_button.setStyle(QStyleFactory.create('Fusion'))

        # --打开文件夹按钮
        self.open_button = QPushButton('打开文件夹', self)
        self.open_button.setStyle(QStyleFactory.create('Fusion'))

        # --显示音乐列表
        self.qlist = QListWidget()
        self.qlist.setStyle(QStyleFactory.create('Fusion'))
        self.qlist.setHorizontalScrollBarPolicy(1)
        self.qlist.setFont(QtGui.QFont("Arial", 18))
        self.qlist.setMinimumSize(200, 200)

        # --如果有初始化setting, 导入setting
        self.loadSetting()

        # --播放模式
        self.cmb = QComboBox()
        self.cmb.setStyle(QStyleFactory.create('Fusion'))
        self.cmb.setStyleSheet('color: white;')
        self.cmb.addItem('顺序播放')
        self.cmb.addItem('单曲循环')
        self.cmb.addItem('随机播放')

        # --计时器
        self.timer = QTimer(self)
        self.timer.start(1000)
        self.timer.timeout.connect(self.playByMode)

        plt.style.use('dark_background')
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumSize(200, 200)

    def Event(self):
        self.close_btn.clicked.connect(lambda:self.close())              # 关闭按钮被点击，调用关闭函数
        self.max_btn.clicked.connect(self.max_normal)           #最大化按钮被点击，调用最大化_恢复函数
        self.min_btn.clicked.connect(self.showMinimized)        # 最小化按钮被点击，调用最小化函数

        self.slider.sliderMoved[int].connect(
            lambda: self.player.setPosition(self.slider.value()))

        self.play_button.clicked.connect(self.playMusic)

        self.mute_button.clicked.connect(self.Mute)
        # self.mute_button.setEnabled(False)

        self.choose_button.clicked.connect(lambda:self.onclick())

        self.preview_button.clicked.connect(self.previewMusic)

        self.next_button.clicked.connect(self.nextMusic)

        self.qlist.itemDoubleClicked.connect(self.doubleClicked)

        self.open_button.clicked.connect(self.openDir)

        self.qlist.activated.connect(self.waveplotclean)
        self.qlist.activated.connect(self.waveplot)

    def layouts(self):

        self.titlebar = QtWidgets.QWidget()
        self.TBox = QtWidgets.QHBoxLayout()
        # TBox.addWidget(cmmbar)
        self.TBox.addWidget(self.close_btn)
        self.TBox.addWidget(self.min_btn)
        self.TBox.addWidget(self.max_btn)
        self.TBox.addWidget(self.placeholder)
        # self.TBox.addWidget(self.titlelabel, Qt.AlignRight)
        self.TBox.addWidget(self.titlelabel)
        self.TBox.setContentsMargins(2, 0, 2, 0)
        self.titlebar.setLayout(self.TBox)

        self.bottom_widget = QtWidgets.QWidget()
        self.r_Hbox = QtWidgets.QHBoxLayout()
        self.r_Hbox.addWidget(self.label1)
        self.r_Hbox.addWidget(self.label2)
        self.r_Hbox.addWidget(self.preview_button)
        self.r_Hbox.addWidget(self.next_button)
        self.r_Hbox.addWidget(self.cmb)
        self.r_Hbox.addWidget(self.open_button)
        self.r_Hbox.addWidget(self.mute_button)
        self.r_Hbox.addWidget(self.play_button)
        self.r_Hbox.addWidget(self.choose_button)
        self.r_Hbox.setContentsMargins(5, 5, 5, 5)
        self.bottom_widget.setLayout(self.r_Hbox)

        self.top_widget = QtWidgets.QWidget()
        self.l_Vbox = QtWidgets.QVBoxLayout()
        self.l_Vbox.addWidget(self.qlist)
        self.l_Vbox.addWidget(self.canvas)
        self.l_Vbox.addWidget(self.slider)
        self.l_Vbox.setContentsMargins(0, 0, 0, 0)
        self.top_widget.setLayout(self.l_Vbox)

        self.widget = QtWidgets.QWidget()
        self.Box = QtWidgets.QVBoxLayout()
        self.Box.addWidget(self.titlebar)
        self.Box.addWidget(self.top_widget)
        self.Box.addWidget(self.bottom_widget)
        self.widget.setLayout(self.Box)

        self.setCentralWidget(self.widget)

    def menubar(self):
        self.menubar = self.menuBar()

    # 窗体大小改变事件
    def resizeEvent(self, QResizeEvent):
        # 自定义窗口调整大小事件
        self._TitleLabel.setFixedWidth(self.width()) # 将标题标签始终设为窗口宽度
        # 分别移动三个按钮到正确的位置
        try:
            self._CloseButton.move(self.width() - self._CloseButton.width(), 0)
        except:
            pass
        try:
            self._MinimumButton.move(self.width() - (self._CloseButton.width() + 1) * 3 + 1, 0)
        except:
            pass
        try:
            self._MaximumButton.move(self.width() - (self._CloseButton.width() + 1) * 2 + 1, 0)
        except:
            pass
        # 重新调整边界范围以备实现鼠标拖放缩放窗口大小，采用三个列表生成式生成三个列表
        self._right_rect = [QPoint(x, y) for x in range(self.width() - self._padding, self.width() + 1)
        for y in range(1, self.height() - self._padding)]
        self._bottom_rect = [QPoint(x, y) for x in range(1, self.width() - self._padding)
        for y in range(self.height() - self._padding, self.height() + 1)]
        self._corner_rect = [QPoint(x, y) for x in range(self.width() - self._padding, self.width() + 1)
        for y in range(self.height() - self._padding, self.height() + 1)]
        # autoplaceholder = int(self.geometry().x() / 2)
        # self.placeholder.setMaximumSize(autoplaceholder-200, 20)

    #5. 判断最大化，还是窗口化
    def max_normal(self):
        if self.isMaximized():
            self.showNormal()                  #窗口化显示
            self.max_btn.setText('口')
        else:
            self.showMaximized()               #最大化显示
            self.max_btn.setText('o')

    # 1.鼠标点击事件
    def mousePressEvent(self, event):
        # 重写鼠标点击的事件
        if (event.button() == Qt.LeftButton) and (event.pos() in self._corner_rect):
            # 鼠标左键点击右下角边界区域
            self._corner_drag = True
            event.accept()
        elif (event.button() == Qt.LeftButton) and (event.pos() in self._right_rect):
            # 鼠标左键点击右侧边界区域
            self._right_drag = True
            event.accept()
        elif (event.button() == Qt.LeftButton) and (event.pos() in self._bottom_rect):
            # 鼠标左键点击下侧边界区域
            self._bottom_drag = True
            event.accept()
        elif (event.button() == Qt.LeftButton) and (event.y() < self._TitleLabel.height()):
            # 鼠标左键点击标题栏区域
            self._move_drag = True
            self.move_DragPosition = event.globalPos() - self.pos()
            event.accept()

    # 2.鼠标移动事件
    # def mouseMoveEvent(self, evt):
    #     # 计算鼠标移动的x，y位移
    #     move_x = evt.globalX() - self.mouse_x
    #     move_y = evt.globalY() - self.mouse_y

    #     # 计算窗体更新后的坐标：更新后的坐标 = 原本的坐标 + 鼠标的位移
    #     dest_x = self.origin_x + move_x
    #     dest_y = self.origin_y + move_y

    #     # 移动窗体
    #     self.move(dest_x,dest_y)

    def mouseMoveEvent(self, QMouseEvent):
        try:
            # 判断鼠标位置切换鼠标手势
            if QMouseEvent.pos() in self._corner_rect:
                self.setCursor(Qt.SizeFDiagCursor)
            elif QMouseEvent.pos() in self._bottom_rect:
                self.setCursor(Qt.SizeVerCursor)
            elif QMouseEvent.pos() in self._right_rect:
                self.setCursor(Qt.SizeHorCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
            # 当鼠标左键点击不放及满足点击区域的要求后，分别实现不同的窗口调整
            # 没有定义左方和上方相关的5个方向，主要是因为实现起来不难，但是效果很差，拖放的时候窗口闪烁，再研究研究是否有更好的实现
            if Qt.LeftButton and self._right_drag:
                # 右侧调整窗口宽度
                self.resize(QMouseEvent.pos().x(), self.height())
                QMouseEvent.accept()
            elif Qt.LeftButton and self._bottom_drag:
                # 下侧调整窗口高度
                self.resize(self.width(), QMouseEvent.pos().y())
                QMouseEvent.accept()
            elif Qt.LeftButton and self._corner_drag:
                # 右下角同时调整高度和宽度
                self.resize(QMouseEvent.pos().x(), QMouseEvent.pos().y())
                QMouseEvent.accept()
            elif Qt.LeftButton and self._move_drag:
                # 标题栏拖放窗口位置
                self.move(QMouseEvent.globalPos() - self.move_DragPosition)
                QMouseEvent.accept()
        except Exception:
            # print(e)
            # traceback.print_exc()
            pass

    def mouseReleaseEvent(self, QMouseEvent):
        # 鼠标释放后，各扳机复位
        self._move_drag = False
        self._corner_drag = False
        self._bottom_drag = False
        self._right_drag = False


    def openDir(self):
        self.cur_path = QFileDialog.getExistingDirectory(self, "选取文件夹", self.cur_path)
        if self.cur_path:
            self.showMusicList()
            self.cur_playing_song = ''
            self.setCurPlaying()
            self.label1.setText('00:00')
            self.label2.setText('00:00')
            self.slider.setSliderPosition(0)
            self.is_pause = True
            self.play_button.setText('播放')

    def loadSetting(self):
        try:
            if os.path.isfile(self.settingfilename):
                config = configparser.ConfigParser()
                config.read(self.settingfilename)
                self.cur_path = config.get('MusicPlayer', 'PATH')
                self.showMusicList()
        except Exception:
            # print(e)
            traceback.print_exc()
            pass
        # pass

    def updateSetting(self):
        config = configparser.ConfigParser()
        config.read(self.settingfilename)
        if not os.path.isfile(self.settingfilename):
            config.add_section('MusicPlayer')
        config.set('MusicPlayer', 'PATH', self.cur_path)
        config.write(open(self.settingfilename, 'w'))

    def showMusicList(self):
        self.qlist.clear()
        self.updateSetting()
        for song in os.listdir(self.cur_path):
            if song.split('.')[-1] in self.song_formats:
                self.songs_list.append([song, os.path.join(self.cur_path, song).replace('\\', '/')])
                self.qlist.addItem(song)
        self.qlist.setCurrentRow(0)
        if self.songs_list:
            self.cur_playing_song = self.songs_list[self.qlist.currentRow()][-1]

    def doubleClicked(self):
        self.slider.setValue(0)
        self.is_switching = True
        self.setCurPlaying()
        self.playMusic()
        self.is_switching = False

    def setCurPlaying(self):
        self.cur_playing_song = self.songs_list[self.qlist.currentRow()][-1]
        self.connect = QMediaContent(QtCore.QUrl.fromLocalFile(self.cur_playing_song))
        self.player.setMedia(self.connect)

    def Tips(self, message):
        QMessageBox.about(self, "提示", message)

    '''根据播放模式播放音乐'''
    def playByMode(self):
        if (not self.is_pause) and (not self.is_switching):
            self.slider.setMinimum(0)
            self.slider.setMaximum(self.player.duration())
            self.slider.setValue(self.slider.value() + 1000)
        self.label1.setText(time.strftime('%M:%S', time.localtime(self.player.position()/1000)))
        self.label2.setText(time.strftime('%M:%S', time.localtime(self.player.duration()/1000)))
        # 顺序播放
        if (self.cmb.currentIndex() == 0) and (not self.is_pause) and (not self.is_switching):
            if self.qlist.count() == 0:
                return
            if self.player.position() == self.player.duration():
                self.nextMusic()
        # 单曲循环
        elif (self.cmb.currentIndex() == 1) and (not self.is_pause) and (not self.is_switching):
            if self.qlist.count() == 0:
                return
            if self.player.position() == self.player.duration():
                self.is_switching = True
                self.setCurPlaying()
                self.slider.setValue(0)
                self.playMusic()
                self.is_switching = False
        # 随机播放
        elif (self.cmb.currentIndex() == 2) and (not self.is_pause) and (not self.is_switching):
            if self.qlist.count() == 0:
                return
            if self.player.position() == self.player.duration():
                self.is_switching = True
                self.qlist.setCurrentRow(random.randint(0, self.qlist.count()-1))
                self.setCurPlaying()
                self.slider.setValue(0)
                self.playMusic()
                self.is_switching = False

    def playMusic(self):
        if self.qlist.count() == 0:
            self.Tips('当前路径内无可播放的音乐文件')
            return
        if not self.player.isAudioAvailable():
            self.setCurPlaying()
        if self.is_pause or self.is_switching:
            self.player.play()
            self.is_pause = False
            self.play_button.setText('暂停')
        elif (not self.is_pause) and (not self.is_switching):
            self.player.pause()
            self.is_pause = True
            self.play_button.setText('播放')

    def Mute(self):
        if self.qlist.count() == 0:
            self.Tips('当前路径内无可播放的音乐文件')
            return
        if not self.player.isAudioAvailable():
            self.setCurPlaying()

        if self.player.volume() == 0:
            self.player.setVolume(20.0)
        elif self.player.volume() > 0:
            self.player.setVolume(0)


    def previewMusic(self):
        self.slider.setValue(0)
        if self.qlist.count() == 0:
            self.Tips('当前路径内无可播放的音乐文件')
            return
        pre_row = self.qlist.currentRow()-1 if self.qlist.currentRow() != 0 else self.qlist.count() - 1
        self.qlist.setCurrentRow(pre_row)
        self.is_switching = True
        self.setCurPlaying()
        self.playMusic()
        self.is_switching = False

    def nextMusic(self):
        self.slider.setValue(0)
        if self.qlist.count() == 0:
            self.Tips('当前路径内无可播放的音乐文件')
            return
        next_row = self.qlist.currentRow()+1 if self.qlist.currentRow() != self.qlist.count()-1 else 0
        self.qlist.setCurrentRow(next_row)
        self.is_switching = True
        self.setCurPlaying()
        self.playMusic()
        self.is_switching = False

    def waveplot(self):
        self.axset()
        self.audio_signal, self.sample_rate = librosa.load(self.cur_playing_song, offset=40)
        self.re_sample = 100
        self.re_audio = librosa.resample(self.audio_signal, self.sample_rate, self.re_sample)
        plt.subplot(5,1,1)
        librosa.display.waveplot(self.re_audio, self.re_sample, linewidth=.1, max_sr=10, color='#8ef')
        plt.title('signal')
        plt.xlabel('Time')
        plt.ylabel('Amplitude')

        self.axset()

        plt.subplot(5,1,2)
        self.chromaCqt()
        global CQT
        librosa.display.specshow(CQT, x_axis='time', y_axis='cqt_note')
        # plt.colorbar(format='%+2.0f dB')
        plt.title('Constant-Q power spectrogram (note)')
        plt.ylabel('dB')
        plt.set_cmap('bone')

        self.axset()


        plt.subplot(5,1,3)

        librosa.display.specshow(self.chroma_cqt, y_axis='chroma', x_axis='time')
        plt.title('chroma_cqt')
        # plt.colorbar()
        plt.tight_layout()

        self.axset()

        plt.subplot(5,1,4)
        plt.bar(np.arange(len(self.chroma_cqt_bar_normalized)), self.chroma_cqt_bar_normalized, color='#234', alpha=1)
        plt.xticks(range(12), ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'])
        plt.xlabel('Pitch class')
        plt.yticks(np.arange(11)/10)
        plt.ylabel('Relative energy')
        plt.title('PCP feature vector extracted')

        self.axset()

        plt.subplot(5,1,5)
        S = librosa.feature.melspectrogram(y=self.audio_signal, sr=self.sample_rate, n_mels=12, fmax=8000)
        mfccs = librosa.feature.mfcc(S=librosa.power_to_db(S))
        librosa.display.specshow(mfccs, x_axis='time', y_axis='mel')
        plt.title('MFCC')
        plt.tight_layout()

        self.axset()


        self.canvas.draw()

    def waveplotclean(self):
        plt.cla()

    def axset(self):
        plt.rc('font', size=5)
        plt.xticks(size = 4)
        plt.yticks(size = 4)

        ax = plt.gca()
        ax.spines['top'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['right'].set_visible(False)

    def chromaCqt(self):
        global CQT

        CQT = librosa.amplitude_to_db(np.abs(librosa.cqt(self.audio_signal, self.sample_rate)), ref=np.max)

        self.chroma_cqt = librosa.feature.chroma_cqt(y=self.audio_signal, sr=self.sample_rate, C=None, hop_length=512, fmin=None, #~=32.7 'C1' \
            norm=np.inf, threshold=0.0, tuning=None, n_chroma=12, n_octaves=7,
            window=scipy.signal.windows.hamming(1),
            bins_per_octave=None,
            cqt_mode='full')

        # print(self.chroma_cqt.shape)

        self.chroma_cqt_bar = self.chroma_cqt.mean(axis=1)
        self.chroma_cqt_bar_normalized = self.chroma_cqt_bar * (1 / max(self.chroma_cqt_bar))

    def onclick(self):
        self.newWindow = MyWindow2()
        self.newWindow.show()



class MyWindow2(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.resize(800, 600)
        self.setFixedSize(self.width(), self.height())
        # self.setWindowFlags(QtCore.Qt.WindowMinimizeButtonHint)
        self.setStyleSheet('background: black; border-radius: 5;')

        self.setWindowTitle('音乐分析数据对比')
        self.setWindowIcon(QIcon('web.png'))
        self.center()
        self.widget()
        self.layouts()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def widget(self):
        self.open_button = QPushButton('打开文件夹', self)
        self.open_button.setStyle(QStyleFactory.create('Fusion'))


    def layouts(self):

        values = musicPlayer()
        print(values.CQT)





if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = musicPlayer()
    gui.show()
    sys.exit(app.exec_())