import numpy as np
import scipy.sparse
import scipy.signal
import scipy.fftpack

import sys
import os
import time
import math
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
import matplotlib.gridspec as mg

import traceback

class musicPlayer(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(musicPlayer, self).__init__(*args, **kwargs)
        self.setObjectName("mainwindow")

        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | QtCore.Qt.WindowMaximizeButtonHint | QtCore.Qt.WindowMinimizeButtonHint | QtCore.Qt.WindowCloseButtonHint)
        # self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setWindowOpacity(0.8)
        # self.setMouseTracking(True)
        self.setupUI()

    def setupUI(self):
        # self.resize(800, 800)
        self._padding = 0
        self.setWindowTitle('音乐音频处理')
        self.setWindowIcon(QtGui.QIcon('web.png'))
        self.setMinimumSize(1000, 1400)
        # self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.player = QMediaPlayer()
        self.player.setVolume(20.0)
        self.songs_list = []
        self.songs_list2 = self.songs_list
        self.song_formats = ['mp3', 'm4a', 'flac', 'wav', 'ogg']
        self.cur_path = os.path.abspath(os.path.dirname(__file__))
        self.cur_path = self.cur_path + '/testmusic'
        self.cur_path2 = self.cur_path
        self.cur_playing_song = ''
        self.cur_playing_song2 = ''
        self.is_switching = False
        self.is_pause = True
        self.settingfilename = 'setting.ini'

        self.center()
        self.widgets()
        self.layouts()
        self.menubar()
        self.Event()

    def center(self):
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    # 移动窗口 #
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.m_flag = True
            self.m_Position = event.globalPos() - self.pos()  # 获取鼠标相对窗口的位置
            event.accept()
            self.setCursor(QCursor(Qt.OpenHandCursor))  # 更改鼠标图标

    def mouseMoveEvent(self, QMouseEvent):
        if Qt.LeftButton and self.m_flag:
            self.move(QMouseEvent.globalPos() - self.m_Position)  # 更改窗口位置
            QMouseEvent.accept()

    def mouseReleaseEvent(self, QMouseEvent):
        self.m_flag = False
        self.setCursor(QCursor(Qt.ArrowCursor))
    # 移动窗口 #

    @pyqtSlot()
    def on_pushButton_max_clicked(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
            # self.setWindowState(Qt.WindowMaximized)

    @pyqtSlot()
    def on_pushButton_min_clicked(self):
        # self.showMinimized()
        # self.setWindowState(Qt.WindowMinimized)
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMinimized()
            self.showNormal()

    @pyqtSlot()
    def on_pushButton_close_clicked(self):
        self.close()


    def widgets(self):
        self.close_btn = QPushButton(self)
        # self.close_btn.raise_()
        # self.close_btn.setCheckable(True)
        # self.close_btn.setText('X')
        # self.close_btn.resize(20, 20)
        self.close_btn.setStyle(QStyleFactory.create('Fusion'))
        self.close_btn.setMaximumSize(12, 12)
        self.close_btn.setObjectName('close')
        # self.close_btn.setStyleSheet("#close {background-color: rgb(255, 12, 12); border-radius: 6; margin: 0}")
        # self.close_btn.move(12, 10)

        self.max_btn = QPushButton(self)
        self.max_btn.setStyle(QStyleFactory.create('Fusion'))
        # self.max_btn.setText('口')
        # self.max_btn.resize(20, 20)
        self.max_btn.setMaximumSize(12, 12)
        self.max_btn.setObjectName('max')
        # self.max_btn.move(24, 10)

        self.min_btn = QPushButton(self)
        self.min_btn.setStyle(QStyleFactory.create('Fusion'))
        # self.min_btn.setText('一')
        # self.min_btn.resize(20, 20)
        self.min_btn.setMaximumSize(12, 12)
        self.min_btn.setObjectName('min')
        # self.min_btn.move(36, 10)

        self.titlelabel = QLabel('Music Analysis')
        self.titlelabel.setStyle(QStyleFactory.create('Fusion'))
        self.titlelabel.setFont(QtGui.QFont("Arial", 14))
        self.titlelabel.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
        self.setCentralWidget(self.titlelabel)

        # self.placeholder = QLabel()
        # autoplaceholder = int(self.geometry().x() / 2)
        # self.placeholder.setMaximumSize(autoplaceholder-180, 20)


        # --播放时间
        self.label1 = QLabel('00:00')
        self.label1.setStyle(QStyleFactory.create('Fusion'))
        self.label2 = QLabel('00:00')
        self.label2.setStyle(QStyleFactory.create('Fusion'))
        self.label1.setFont(QtGui.QFont("Arial", 14))
        self.label2.setFont(QtGui.QFont("Arial", 14))

        self.label3 = QLabel('MPCP')
        self.label3.setStyle(QStyleFactory.create('Fusion'))
        self.label3.setFont(QtGui.QFont("Arial", 14))

        self.label4 = QLabel('正在计算')
        self.label4.setStyle(QStyleFactory.create('Fusion'))
        self.label4.setFont(QtGui.QFont("Arial", 14))

        # --滑动条
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setStyleSheet('background-color: rgba(0,0,0,0)')
        self.slider.setStyle(QStyleFactory.create('Fusion'))
        self.slider.setObjectName('slider')

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
        self.qlist.setObjectName('qlist')
        self.qlist.setHorizontalScrollBarPolicy(1)
        self.qlist.setFont(QtGui.QFont("Arial", 18))
        self.qlist.setMinimumSize(200, 200)

        self.qlist2 = QListWidget()
        self.qlist2.setStyle(QStyleFactory.create('Fusion'))
        self.qlist2.setObjectName('qlist2')
        self.qlist2.setHorizontalScrollBarPolicy(1)
        self.qlist2.setFont(QtGui.QFont("Arial", 18))
        self.qlist2.setMinimumSize(200, 200)


        # --如果有初始化setting, 导入setting
        self.loadSetting()

        # --播放模式
        self.cmb = QComboBox()
        self.cmb.setStyle(QStyleFactory.create('Fusion'))
        self.cmb.setObjectName('cmb')
        self.cmb.setStyleSheet('color: white;')
        self.cmb.addItem('顺序播放')
        self.cmb.addItem('单曲循环')
        self.cmb.addItem('随机播放')

        # --计时器
        self.timer = QTimer(self)
        self.timer.start(1000)
        self.timer.timeout.connect(self.playByMode)

        plt.style.use('dark_background')
        self.figure = plt.figure('Object_1')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumSize(200, 200)

    def Event(self):
        self.close_btn.clicked.connect(self.waveplotclean)
        self.close_btn.clicked.connect(self.on_pushButton_close_clicked)
        self.min_btn.clicked.connect(self.on_pushButton_min_clicked)
        self.max_btn.clicked.connect(self.on_pushButton_max_clicked)

        self.slider.sliderMoved[int].connect(
            lambda: self.player.setPosition(self.slider.value()))

        self.play_button.clicked.connect(self.playMusic)

        self.mute_button.clicked.connect(self.Mute)
        # self.mute_button.setEnabled(False)

        self.preview_button.clicked.connect(self.previewMusic)

        self.next_button.clicked.connect(self.nextMusic)

        self.qlist.itemDoubleClicked.connect(self.doubleClicked)
        self.qlist2.itemClicked.connect(self.comparison)

        self.open_button.clicked.connect(self.openDir)

        self.qlist.activated.connect(self.waveplotclean)
        self.qlist.activated.connect(lambda:self.waveplot(classnum=2))

        self.choose_button.clicked.connect(self.comparChoose)
        self.choose_button.clicked.connect(self.waveplotclean)
        self.choose_button.setEnabled(False)

    def layouts(self):

        self.titlebar = QtWidgets.QWidget()
        self.titlebar.setObjectName('titlebar')
        # self.setStyleSheet("#titlebar {border-radius: 6; padding: 0; background: red}")
        # self.titlebar.setFixedHeight(40)
        # self.titlebar.setStyleSheet('background: blue;')
        # print(self.titlebar.getContentsMargins())
        # print(self.titlebar.contentsRect())
        self.TBox = QtWidgets.QHBoxLayout()

        self.TBox.addWidget(self.close_btn)
        self.TBox.addWidget(self.min_btn)
        self.TBox.addWidget(self.max_btn)
        # self.TBox.addWidget(self.placeholder)
        # self.TBox.addWidget(self.titlelabel, Qt.AlignRight)
        self.TBox.addWidget(self.titlelabel)
        # print(self.TBox.getContentsMargins())
        self.titlebar.setLayout(self.TBox)
        # print(self.close_btn.contentsRect())

        self.listbar = QtWidgets.QWidget()
        self.listbar.setObjectName('listbar')
        self.listbox = QtWidgets.QHBoxLayout()
        self.listbox.addWidget(self.qlist)
        self.listbox.addWidget(self.qlist2)
        self.listbar.setLayout(self.listbox)

        self.bottom_widget = QtWidgets.QWidget()
        self.r_Hbox = QtWidgets.QHBoxLayout()
        self.r_Hbox.addWidget(self.label1)
        self.r_Hbox.addWidget(self.label2)
        self.r_Hbox.addWidget(self.label3)
        self.r_Hbox.addWidget(self.label4)
        self.r_Hbox.addWidget(self.preview_button)
        self.r_Hbox.addWidget(self.next_button)
        self.r_Hbox.addWidget(self.cmb)
        self.r_Hbox.addWidget(self.open_button)
        self.r_Hbox.addWidget(self.mute_button)
        self.r_Hbox.addWidget(self.play_button)
        self.r_Hbox.addWidget(self.choose_button)
        # print(self.r_Hbox.getContentsMargins())
        self.bottom_widget.setLayout(self.r_Hbox)

        self.top_widget = QtWidgets.QWidget()
        self.l_Vbox = QtWidgets.QVBoxLayout()
        self.l_Vbox.addWidget(self.listbar)
        self.l_Vbox.addWidget(self.canvas)
        self.l_Vbox.addWidget(self.slider)
        # print(self.l_Vbox.getContentsMargins())
        self.top_widget.setLayout(self.l_Vbox)

        self.widget = QtWidgets.QWidget()
        self.widget.setObjectName('widget')
        self.Box = QtWidgets.QVBoxLayout()
        self.Box.addWidget(self.titlebar)
        self.Box.addWidget(self.top_widget)
        self.Box.addWidget(self.bottom_widget)
        self.widget.setLayout(self.Box)
        self.Box.setContentsMargins(0, 0, 0, 0)
        # print(self.Box.getContentsMargins())
        self.setStyleSheet('''
            #mainwindow {background: black; border-radius: 6;}
            #widget {background: black; border-radius: 5; border: 1 solid rgba(90,120,150,.4);}
            #close {background: rgb(255, 12, 12); border-radius: 6;}
            #close:hover {background: rgb(255, 60, 60)}
            #max {background-color: rgb(28, 255, 3); border-radius: 6;}
            #max:hover {background-color: rgb(128, 255, 30);}
            #min {background-color: rgb(255, 243, 75); border-radius: 6;}
            #min:hover {background-color: rgb(255, 243, 175);}
            #titlebar {border-radius: 6; padding: 0;}
            #qlist {background: black; color: darkgray;}
            #qlist * {background: black; border-radius: 4;}
            #qlist::Item:hover {background: #568; color: orange; border-radius: 10;}
            #qlist::item:selected{background: #268; color: yellow; border-radius: 10;}

            #qlist2 {background: black; color: darkgray;}
            #qlist2 * {background: black; border-radius: 4;}
            #qlist2::Item:hover {background: #568; color: orange; border-radius: 10;}
            #qlist2::item:selected{background: #268; color: yellow; border-radius: 10;}

            #slider::handle:horizontal {background: #68c; border-radius: 7; border: 2 solid orange;}
            #slider::sub-page:horizontal {background: #28c;}
            #cmb {background-color: black; border: None;}
            #cmb * {background-color: black; border: 1 solid rgba(90,120,150,.4);}
            QPushButton {border-radius: 6; height: 30; border-radius: 15}
            QPushButton:hover {background: rgba(90,160,210,.6);}
            QPushButton:pressed {background: orange; color: black;}
            ''')
        self.setCentralWidget(self.widget)

    def menubar(self):
        self.menubar = self.menuBar()

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

        self.cur_path2 = self.cur_path

    def loadSetting(self):
        try:
            if os.path.isfile(self.settingfilename):
                config = configparser.ConfigParser()
                config.read(self.settingfilename)
                self.cur_path = config.get('MusicPlayer', 'PATH')
                self.cur_path2 = self.cur_path
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

        ## list2
        self.qlist2.clear()
        self.updateSetting()
        count = 0
        for song in os.listdir(self.cur_path2):
            if song.split('.')[-1] in self.song_formats:
                self.songs_list2.append([song, os.path.join(self.cur_path2, song).replace('\\', '/')])
                self.qlist2.addItem(song)
                count += 1
                # print(song, count)
        self.qlist2.setCurrentRow(0)
        if self.songs_list2:
            self.cur_playing_song2 = self.songs_list2[self.qlist2.currentRow()][-1]

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

    def comparison(self):
        self.cur_playing_song2 = self.songs_list2[self.qlist2.currentRow()][-1]
        # print(QtCore.QUrl.fromLocalFile(self.cur_playing_song2))
        self.choose_button.setEnabled(True)

    def comparChoose(self):
        # self.compar_signal, self.sr_compar = librosa.load(self.cur_playing_song2, offset=40)
        self.compar_signal, self.sr_compar = librosa.load(self.cur_playing_song2)
        self.rsr_compar = 100
        self.re_compar = librosa.resample(self.compar_signal, self.sr_compar, self.rsr_compar)
        self.plotshow()
        self.calculus()

    # def __getattribute__(self, name):
    #     try:
    #         r = object.__getattribute__(self, name)
    #     except:
    #         r = None
    #     return r

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
            self.mute_button.setText('静音')
        elif self.player.volume() > 0:
            self.player.setVolume(0)
            self.mute_button.setText('取消静音')


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

    def waveplot(self, classnum=2):
        # a = [1, 2, 3, 4, 5, 6]
        # b = [1, 3, 5, 7, 9, 11]
        # if classnum == 1:
        #     n = a
        #     m = 1
        # elif classnum == 2:
        #     n = b
        #     m = 2
        # else:
        #     n = a
        #     m = 1

        self.axset()
        self.gs = mg.GridSpec(6, 2)
        # self.audio_signal, self.sample_rate = librosa.load(self.cur_playing_song, offset=40)
        self.audio_signal, self.sample_rate = librosa.load(self.cur_playing_song)
        self.re_sample = 100
        self.re_audio = librosa.resample(self.audio_signal, self.sample_rate, self.re_sample)
        plt.subplot(self.gs[0,:classnum])
        librosa.display.waveplot(self.re_audio, self.re_sample, linewidth=.1, max_sr=10, color='#8ef')
        plt.title('signal')
        plt.xlabel('Time')
        plt.ylabel('Amplitude')

        self.axset()

        plt.subplot(self.gs[1,:classnum])
        self.chromaCqt()
        librosa.display.specshow(10*self.CQT, x_axis='time', y_axis='cqt_note')
        # plt.colorbar(format='%+2.0f dB')
        plt.title('Constant-Q power spectrogram (note)')
        plt.ylabel('dB')
        plt.set_cmap('bone')

        self.axset()


        plt.subplot(self.gs[2,:classnum])

        librosa.display.specshow(self.chroma_cqt ** 3, y_axis='chroma', x_axis='time')
        plt.title('chroma_cqt')
        # plt.colorbar()
        plt.tight_layout()

        self.axset()

        plt.subplot(self.gs[3,:classnum])
        plt.bar(np.arange(len(self.chroma_cqt_bar_normalized)), self.chroma_cqt_bar_normalized, color='#6ac', alpha=1)
        plt.xticks(range(12), ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'])
        plt.xlabel('Pitch class')
        plt.yticks(np.arange(11)/10)
        plt.ylabel('Relative energy')
        plt.title('PCP feature vector extracted')

        self.axset()

        plt.subplot(self.gs[4,:classnum])
        S = librosa.feature.melspectrogram(y=self.audio_signal, sr=self.sample_rate, n_mels=12, fmax=8000)
        self.mfccs = librosa.feature.mfcc(S=librosa.power_to_db(S))
        librosa.display.specshow(12 * self.mfccs ** 1.2, x_axis='time', y_axis='mel')
        plt.title('MFCC')
        plt.tight_layout()

        self.axset()


        self.canvas.draw()

    def waveplotclean(self):
        # plt.cla()
        plt.clf()
        # plt.close()

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
        self.CQT = librosa.amplitude_to_db(np.abs(librosa.cqt(self.audio_signal, self.sample_rate)), ref=np.max)

        self.chroma_cqt = librosa.feature.chroma_cqt(y=self.audio_signal, sr=self.sample_rate, C=None, hop_length=512, fmin=None, #~=32.7 'C1' \
            norm=np.inf, threshold=0.0, tuning=None, n_chroma=12, n_octaves=7,
            window=scipy.signal.windows.hamming(1),
            bins_per_octave=None,
            cqt_mode='full')

        # print(self.chroma_cqt.shape)

        self.chroma_cqt_bar = self.chroma_cqt.mean(axis=1) ** 3
        self.chroma_cqt_bar_normalized = self.chroma_cqt_bar * (1 / max(self.chroma_cqt_bar))


    def plotshow(self):
        plt.clf()
        self.axset()
        self.waveplot(classnum=1)

        plt.subplot(self.gs[0,1:])
        librosa.display.waveplot(self.re_compar, self.rsr_compar, linewidth=.1, max_sr=10, color='orange')
        plt.title('signal')
        plt.xlabel('Time')
        plt.ylabel('Amplitude')

        self.axset()

        plt.subplot(self.gs[1,1:])
        self.chromaCqt2()
        librosa.display.specshow(10*self.CQT2, x_axis='time', y_axis='cqt_note')
        # plt.colorbar(format='%+2.0f dB')
        plt.title('Constant-Q power spectrogram (note)')
        plt.ylabel('dB')
        plt.set_cmap('bone')

        self.axset()

        plt.subplot(self.gs[2,1:])

        librosa.display.specshow(self.chroma_cqt2 ** 3, y_axis='chroma', x_axis='time')
        plt.title('chroma_cqt')
        # plt.colorbar()
        plt.tight_layout()

        self.axset()

        plt.subplot(self.gs[3,1:])
        plt.bar(np.arange(len(self.chroma_cqt_bar_normalized2)), self.chroma_cqt_bar_normalized2, color='orange', alpha=1)
        plt.xticks(range(12), ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'])
        plt.xlabel('Pitch class')
        plt.yticks(np.arange(11)/10)
        plt.ylabel('Relative energy')
        plt.title('PCP feature vector extracted')

        self.axset()

        plt.subplot(self.gs[4,1:])
        S2 = librosa.feature.melspectrogram(y=self.compar_signal, sr=self.sr_compar, n_mels=12, fmax=8000)
        self.mfccs2 = librosa.feature.mfcc(S=librosa.power_to_db(S2))
        librosa.display.specshow(12 * self.mfccs2 ** 1.2, x_axis='time', y_axis='mel')
        plt.title('MFCC')
        plt.tight_layout()

        self.axset()

        self.canvas.draw()

    def chromaCqt2(self):
        self.CQT2 = librosa.amplitude_to_db(np.abs(librosa.cqt(self.compar_signal, self.sr_compar)), ref=np.max)

        self.chroma_cqt2 = librosa.feature.chroma_cqt(y=self.compar_signal, sr=self.sr_compar, C=None, hop_length=512, fmin=None, #~=32.7 'C1' \
            norm=np.inf, threshold=0.0, tuning=None, n_chroma=12, n_octaves=7,
            window=scipy.signal.windows.hamming(1),
            bins_per_octave=None,
            cqt_mode='full')

        # print(self.chroma_cqt.shape)

        self.chroma_cqt_bar2 = self.chroma_cqt2.mean(axis=1) ** 3
        self.chroma_cqt_bar_normalized2 = self.chroma_cqt_bar2 * (1 / max(self.chroma_cqt_bar2))

    def calculus(self):
        # print(self.chroma_cqt.shape)
        # print(self.mfccs2.shape)
        # print(self.mfccs.shape)
        # print(self.mfccs2.shape)
        MPCP1 = np.concatenate([self.mfccs, self.chroma_cqt], axis=0)
        MPCP2 = np.concatenate([self.mfccs2, self.chroma_cqt2], axis=0)
        print(MPCP1.shape)
        print(MPCP2.shape)
        if MPCP1.shape[1] > MPCP2.shape[1]:
            Z = np.zeros((24, MPCP1.shape[1] - MPCP2.shape[1]))
            newMPCP = np.column_stack((MPCP2, Z))
            # print('第一种情况', MPCP1.shape, newMPCP.shape)
            self.MPCP_1 = MPCP1
            self.MPCP_2 = newMPCP
        elif MPCP1.shape[1] < MPCP2.shape[1]:
            Z = np.zeros((24, MPCP2.shape[1] - MPCP1.shape[1]))
            newMPCP = np.column_stack((MPCP1, Z))
            # print('第二种情况', newMPCP.shape, MPCP2.shape)
            self.MPCP_1 = newMPCP
            self.MPCP_2 = MPCP2
        else:
            self.MPCP_1 = MPCP1
            self.MPCP_2 = MPCP2

        self.cosineSimilarityVector = np.zeros((self.MPCP_1.shape[0],))
        for i in range(0, self.MPCP_1.shape[0]):
            sumcount = 0
            Xsum = 0
            Ysum = 0
            for j in range(0, self.MPCP_1.shape[1]):
                sumij = self.MPCP_1[i][j] * self.MPCP_2[i][j]
                sumcount = sumcount + sumij

                XsumCount = self.MPCP_1[i][j] ** 2
                Xsum = Xsum + XsumCount
                YsumCount = self.MPCP_2[i][j] ** 2
                Ysum = Ysum + YsumCount


            self.cosineSimilarityVector[i] = sumcount / (math.sqrt(Xsum) * math.sqrt(Ysum))

        self.totalMean = np.mean(self.cosineSimilarityVector)
        self.PCPFeatureMean = np.mean(self.cosineSimilarityVector[:12])
        self.MFCCFeatureMean = np.mean(self.cosineSimilarityVector[12:])

        print('特征相似度向量：', self.cosineSimilarityVector)
        print('特征相似度向量 Shape：', self.cosineSimilarityVector.shape)
        print('总相似度 (MPCP)：', self.totalMean,
            'PCP 特征相似度', self.PCPFeatureMean,
            'MFCC 特征相似度', self.MFCCFeatureMean)


        self.label3.setText('MPCP: %f-' % (self.totalMean,))
        self.label3.setObjectName('MPCP')
        self.label4.setObjectName('Result')
        if self.totalMean >= 0.6:
            self.label4.setText('鉴定结果: 翻唱作品')
            self.setStyleSheet('''
                #mainwindow {background: black; border-radius: 6;}
                #widget {background: black; border-radius: 5; border: 1 solid rgba(90,120,150,.4);}
                #close {background: rgb(255, 12, 12); border-radius: 6;}
                #close:hover {background: rgb(255, 60, 60)}
                #max {background-color: rgb(28, 255, 3); border-radius: 6;}
                #max:hover {background-color: rgb(128, 255, 30);}
                #min {background-color: rgb(255, 243, 75); border-radius: 6;}
                #min:hover {background-color: rgb(255, 243, 175);}
                #titlebar {border-radius: 6; padding: 0;}
                #qlist {background: black; color: darkgray;}
                #qlist * {background: black; border-radius: 4;}
                #qlist::Item:hover {background: #568; color: orange; border-radius: 10;}
                #qlist::item:selected{background: #268; color: yellow; border-radius: 10;}

                #qlist2 {background: black; color: darkgray;}
                #qlist2 * {background: black; border-radius: 4;}
                #qlist2::Item:hover {background: #568; color: orange; border-radius: 10;}
                #qlist2::item:selected{background: #268; color: yellow; border-radius: 10;}

                #slider::handle:horizontal {background: #68c; border-radius: 7; border: 2 solid orange;}
                #slider::sub-page:horizontal {background: #28c;}
                #cmb {background-color: black; border: None;}
                #cmb * {background-color: black; border: 1 solid rgba(90,120,150,.4);}
                QPushButton {border-radius: 6; height: 30; border-radius: 15}
                QPushButton:hover {background: rgba(90,160,210,.6);}
                QPushButton:pressed {background: orange; color: black;}
                #MPCP {color: green;}
                #Result {color: green}
                ''')
        else:
            self.label4.setText('鉴定结果: 不相关作品')
            self.setStyleSheet('''
                #mainwindow {background: black; border-radius: 6;}
                #widget {background: black; border-radius: 5; border: 1 solid rgba(90,120,150,.4);}
                #close {background: rgb(255, 12, 12); border-radius: 6;}
                #close:hover {background: rgb(255, 60, 60)}
                #max {background-color: rgb(28, 255, 3); border-radius: 6;}
                #max:hover {background-color: rgb(128, 255, 30);}
                #min {background-color: rgb(255, 243, 75); border-radius: 6;}
                #min:hover {background-color: rgb(255, 243, 175);}
                #titlebar {border-radius: 6; padding: 0;}
                #qlist {background: black; color: darkgray;}
                #qlist * {background: black; border-radius: 4;}
                #qlist::Item:hover {background: #568; color: orange; border-radius: 10;}
                #qlist::item:selected{background: #268; color: yellow; border-radius: 10;}

                #qlist2 {background: black; color: darkgray;}
                #qlist2 * {background: black; border-radius: 4;}
                #qlist2::Item:hover {background: #568; color: orange; border-radius: 10;}
                #qlist2::item:selected{background: #268; color: yellow; border-radius: 10;}

                #slider::handle:horizontal {background: #68c; border-radius: 7; border: 2 solid orange;}
                #slider::sub-page:horizontal {background: #28c;}
                #cmb {background-color: black; border: None;}
                #cmb * {background-color: black; border: 1 solid rgba(90,120,150,.4);}
                QPushButton {border-radius: 6; height: 30; border-radius: 15}
                QPushButton:hover {background: rgba(90,160,210,.6);}
                QPushButton:pressed {background: orange; color: black;}
                #MPCP {color: red;}
                #Result {color: red}
                ''')

        self.axset()
        x = np.arange(0, self.cosineSimilarityVector.shape[0])
        plt.subplot(self.gs[5,:])
        plt.plot(x, self.cosineSimilarityVector, color='orange', marker='o', markersize=4, alpha=0.5)
        plt.fill_between(x, self.cosineSimilarityVector, 0, where=self.cosineSimilarityVector >= 0.5, facecolor='green', interpolate=True, alpha=0.7)
        plt.fill_between(x, self.cosineSimilarityVector, 0, where=self.cosineSimilarityVector < 0.5, facecolor='red', interpolate=True, alpha=0.7)

        plt.xlim([0, 12])
        plt.ylim([-0.3, 1.2])

        # plt.xticks(range(24), ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B', 'Freq1', 'Freq2', 'Freq3', 'Freq4', 'Freq5', 'Freq6', 'Freq7', 'Freq8', 'Freq9', 'Freq10', 'Freq11', 'Freq12'])
        plt.xticks(range(12), ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'])
        plt.xlabel('Feature class')
        plt.yticks(np.arange(11)/10)
        plt.ylabel('Similarity')

        plt.title('FeatureSimilarityVector')
        plt.tight_layout()

        self.axset()

        self.canvas.draw()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = musicPlayer()
    gui.show()
    sys.exit(app.exec_())