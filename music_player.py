import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSlider, QListWidget, QListWidgetItem,
    QFileDialog, QMessageBox, QFrame, QSplitter, QComboBox
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QMediaPlaylist
from PyQt5.QtGui import QFont
from mutagen import File as MutagenFile


class MusicPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎵 音乐播放器")
        self.setGeometry(100, 100, 900, 700)
        self.setMinimumSize(800, 600)

        self.playlist_files = []
        self.current_index = -1
        self.is_playing = False
        self.is_paused = False

        self.available_speeds = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0]

        self.init_media_player()
        self.init_ui()

    def init_media_player(self):
        self.media_player = QMediaPlayer()
        self.media_playlist = QMediaPlaylist()
        self.media_player.setPlaylist(self.media_playlist)

        self.media_player.setVolume(50)

        self.media_player.positionChanged.connect(self.update_position)
        self.media_player.durationChanged.connect(self.update_duration)
        self.media_player.stateChanged.connect(self.on_state_changed)
        self.media_player.mediaStatusChanged.connect(self.on_media_status_changed)
        self.media_playlist.currentIndexChanged.connect(self.on_current_index_changed)

        self.slider_being_dragged = False

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)

        header_label = QLabel("🎵 音乐播放器")
        header_label.setFont(QFont("Microsoft YaHei", 24, QFont.Bold))
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet("color: #2c3e50;")
        main_layout.addWidget(header_label)

        song_info_layout = QHBoxLayout()
        song_info_layout.setSpacing(20)

        self.song_title_label = QLabel("未选择歌曲")
        self.song_title_label.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        self.song_title_label.setAlignment(Qt.AlignCenter)
        self.song_title_label.setStyleSheet(
            "color: #34495e; padding: 10px; background-color: #ecf0f1; border-radius: 10px;"
        )

        self.song_artist_label = QLabel("艺术家: -")
        self.song_artist_label.setFont(QFont("Microsoft YaHei", 11))
        self.song_artist_label.setStyleSheet("color: #7f8c8d;")

        self.song_album_label = QLabel("专辑: -")
        self.song_album_label.setFont(QFont("Microsoft YaHei", 11))
        self.song_album_label.setStyleSheet("color: #7f8c8d;")

        song_info_left = QVBoxLayout()
        song_info_left.addWidget(self.song_title_label)

        song_info_right = QVBoxLayout()
        song_info_right.addWidget(self.song_artist_label)
        song_info_right.addWidget(self.song_album_label)

        song_info_layout.addLayout(song_info_left, 2)
        song_info_layout.addLayout(song_info_right, 1)

        main_layout.addLayout(song_info_layout)

        progress_layout = QVBoxLayout()

        progress_label_layout = QHBoxLayout()
        self.current_time_label = QLabel("00:00")
        self.current_time_label.setFont(QFont("Microsoft YaHei", 10))
        self.current_time_label.setStyleSheet("color: #7f8c8d;")

        self.total_time_label = QLabel("00:00")
        self.total_time_label.setFont(QFont("Microsoft YaHei", 10))
        self.total_time_label.setStyleSheet("color: #7f8c8d;")

        progress_label_layout.addWidget(self.current_time_label)
        progress_label_layout.addStretch()
        progress_label_layout.addWidget(self.total_time_label)

        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setMinimum(0)
        self.progress_slider.setMaximum(1000)
        self.progress_slider.setValue(0)
        self.progress_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #bdc3c7;
                height: 8px;
                background: #ecf0f1;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #3498db;
                border: 2px solid #2980b9;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::sub-page:horizontal {
                background: #3498db;
                border-radius: 4px;
            }
        """)
        self.progress_slider.sliderPressed.connect(self.slider_pressed)
        self.progress_slider.sliderReleased.connect(self.slider_released)

        progress_layout.addLayout(progress_label_layout)
        progress_layout.addWidget(self.progress_slider)

        main_layout.addLayout(progress_layout)

        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(15)

        self.prev_button = QPushButton("⏮ 上一首")
        self.prev_button.setFont(QFont("Microsoft YaHei", 11))
        self.prev_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 12px 25px;
                border-radius: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        self.prev_button.clicked.connect(self.play_previous)

        self.play_button = QPushButton("▶ 播放")
        self.play_button.setFont(QFont("Microsoft YaHei", 12))
        self.play_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 15px 35px;
                border-radius: 25px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.play_button.clicked.connect(self.toggle_play_pause)

        self.next_button = QPushButton("下一首 ⏭")
        self.next_button.setFont(QFont("Microsoft YaHei", 11))
        self.next_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 12px 25px;
                border-radius: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        self.next_button.clicked.connect(self.play_next)

        self.stop_button = QPushButton("⏹ 停止")
        self.stop_button.setFont(QFont("Microsoft YaHei", 11))
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 12px 25px;
                border-radius: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.stop_button.clicked.connect(self.stop_playback)

        controls_layout.addWidget(self.prev_button)
        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.next_button)
        controls_layout.addWidget(self.stop_button)

        main_layout.addLayout(controls_layout)

        speed_volume_layout = QHBoxLayout()
        speed_volume_layout.setSpacing(30)

        speed_layout = QVBoxLayout()
        speed_label = QLabel("播放速度:")
        speed_label.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
        speed_label.setStyleSheet("color: #2c3e50;")

        speed_controls_layout = QHBoxLayout()

        self.speed_combo = QComboBox()
        for speed in self.available_speeds:
            self.speed_combo.addItem(f"{speed}x")
        self.speed_combo.setCurrentText("1.0x")
        self.speed_combo.setFont(QFont("Microsoft YaHei", 11))
        self.speed_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 15px;
                border: 2px solid #3498db;
                border-radius: 10px;
                background-color: white;
                color: #2c3e50;
                font-weight: bold;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 10px;
            }
        """)
        self.speed_combo.currentTextChanged.connect(self.change_playback_speed)

        self.decrease_speed_button = QPushButton("◀ 减速")
        self.decrease_speed_button.setFont(QFont("Microsoft YaHei", 10))
        self.decrease_speed_button.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                padding: 8px 18px;
                border-radius: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        self.decrease_speed_button.clicked.connect(self.decrease_speed)

        self.increase_speed_button = QPushButton("加速 ▶")
        self.increase_speed_button.setFont(QFont("Microsoft YaHei", 10))
        self.increase_speed_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 8px 18px;
                border-radius: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        self.increase_speed_button.clicked.connect(self.increase_speed)

        speed_controls_layout.addWidget(self.decrease_speed_button)
        speed_controls_layout.addWidget(self.speed_combo)
        speed_controls_layout.addWidget(self.increase_speed_button)

        speed_layout.addWidget(speed_label)
        speed_layout.addLayout(speed_controls_layout)

        volume_layout = QVBoxLayout()
        volume_label = QLabel("音量:")
        volume_label.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
        volume_label.setStyleSheet("color: #2c3e50;")

        volume_controls_layout = QHBoxLayout()

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(50)
        self.volume_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #bdc3c7;
                height: 8px;
                background: #ecf0f1;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #9b59b6;
                border: 2px solid #8e44ad;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::sub-page:horizontal {
                background: #9b59b6;
                border-radius: 4px;
            }
        """)
        self.volume_slider.valueChanged.connect(self.change_volume)

        self.volume_label = QLabel("50%")
        self.volume_label.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
        self.volume_label.setStyleSheet("color: #9b59b6; min-width: 50px;")

        volume_controls_layout.addWidget(self.volume_slider)
        volume_controls_layout.addWidget(self.volume_label)

        volume_layout.addWidget(volume_label)
        volume_layout.addLayout(volume_controls_layout)

        speed_volume_layout.addLayout(speed_layout)
        speed_volume_layout.addLayout(volume_layout)

        main_layout.addLayout(speed_volume_layout)

        file_buttons_layout = QHBoxLayout()
        file_buttons_layout.setSpacing(15)

        self.add_files_button = QPushButton("📁 添加音乐文件")
        self.add_files_button.setFont(QFont("Microsoft YaHei", 12))
        self.add_files_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 12px 30px;
                border-radius: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.add_files_button.clicked.connect(self.add_files)

        self.add_folder_button = QPushButton("📂 添加整个文件夹")
        self.add_folder_button.setFont(QFont("Microsoft YaHei", 12))
        self.add_folder_button.setStyleSheet("""
            QPushButton {
                background-color: #1abc9c;
                color: white;
                border: none;
                padding: 12px 30px;
                border-radius: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #16a085;
            }
        """)
        self.add_folder_button.clicked.connect(self.add_folder)

        self.clear_playlist_button = QPushButton("🗑️ 清空播放列表")
        self.clear_playlist_button.setFont(QFont("Microsoft YaHei", 12))
        self.clear_playlist_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 12px 30px;
                border-radius: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.clear_playlist_button.clicked.connect(self.clear_playlist)

        file_buttons_layout.addWidget(self.add_files_button)
        file_buttons_layout.addWidget(self.add_folder_button)
        file_buttons_layout.addWidget(self.clear_playlist_button)

        main_layout.addLayout(file_buttons_layout)

        playlist_label = QLabel("🎶 播放列表")
        playlist_label.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        playlist_label.setStyleSheet("color: #2c3e50;")
        main_layout.addWidget(playlist_label)

        self.playlist_widget = QListWidget()
        self.playlist_widget.setFont(QFont("Microsoft YaHei", 11))
        self.playlist_widget.setSelectionMode(QListWidget.ExtendedSelection)
        self.playlist_widget.setStyleSheet("""
            QListWidget {
                border: 2px solid #3498db;
                border-radius: 15px;
                background-color: white;
                padding: 10px;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #ecf0f1;
                border-radius: 8px;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QListWidget::item:hover:!selected {
                background-color: #ecf0f1;
            }
        """)
        self.playlist_widget.itemDoubleClicked.connect(self.play_selected)

        main_layout.addWidget(self.playlist_widget)

        self.status_label = QLabel("就绪 - 请添加音乐文件开始播放")
        self.status_label.setFont(QFont("Microsoft YaHei", 10))
        self.status_label.setStyleSheet("color: #7f8c8d; padding: 10px;")
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            QWidget {
                font-family: 'Microsoft YaHei', sans-serif;
            }
        """)

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择音乐文件",
            "",
            "音频文件 (*.mp3 *.wav *.flac *.aac *.ogg *.m4a);;所有文件 (*.*)"
        )

        if files:
            added_count = 0
            for file in files:
                if file not in self.playlist_files:
                    self.playlist_files.append(file)
                    self.media_playlist.addMedia(QMediaContent(QUrl.fromLocalFile(file)))

                    filename = os.path.basename(file)
                    item = QListWidgetItem(filename)
                    item.setData(Qt.UserRole, file)
                    self.playlist_widget.addItem(item)
                    added_count += 1

            self.status_label.setText(f"已添加 {added_count} 个文件，共 {len(self.playlist_files)} 首歌曲")

            if self.current_index == -1 and self.playlist_files:
                self.current_index = 0
                self.load_song(self.playlist_files[0])

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "选择音乐文件夹",
            ""
        )

        if folder:
            audio_extensions = ('.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a')
            files_added = 0

            for root, dirs, files in os.walk(folder):
                for file in files:
                    if file.lower().endswith(audio_extensions):
                        full_path = os.path.join(root, file)
                        if full_path not in self.playlist_files:
                            self.playlist_files.append(full_path)
                            self.media_playlist.addMedia(QMediaContent(QUrl.fromLocalFile(full_path)))

                            filename = os.path.basename(full_path)
                            item = QListWidgetItem(filename)
                            item.setData(Qt.UserRole, full_path)
                            self.playlist_widget.addItem(item)
                            files_added += 1

            self.status_label.setText(f"已从文件夹添加 {files_added} 个文件，共 {len(self.playlist_files)} 首歌曲")

            if self.current_index == -1 and self.playlist_files:
                self.current_index = 0
                self.load_song(self.playlist_files[0])

    def clear_playlist(self):
        if not self.playlist_files:
            return

        reply = QMessageBox.question(
            self,
            "确认清空",
            "确定要清空播放列表吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.stop_playback()
            self.playlist_files.clear()
            self.media_playlist.clear()
            self.playlist_widget.clear()
            self.current_index = -1
            self.song_title_label.setText("未选择歌曲")
            self.song_artist_label.setText("艺术家: -")
            self.song_album_label.setText("专辑: -")
            self.status_label.setText("播放列表已清空")

    def load_song(self, file_path):
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "错误", f"文件不存在: {file_path}")
            return

        try:
            self.update_song_info(file_path)

            for i in range(self.playlist_widget.count()):
                item = self.playlist_widget.item(i)
                if item.data(Qt.UserRole) == file_path:
                    self.playlist_widget.setCurrentItem(item)
                    item.setSelected(True)
                    break

            self.status_label.setText(f"已加载: {os.path.basename(file_path)}")

        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法加载歌曲: {str(e)}")

    def update_song_info(self, file_path):
        try:
            audio = MutagenFile(file_path)
            filename = os.path.basename(file_path)

            title = filename
            artist = "-"
            album = "-"

            if audio:
                if hasattr(audio, 'tags') and audio.tags:
                    tags = audio.tags

                    if 'TIT2' in tags:
                        title = str(tags['TIT2'])
                    if 'TPE1' in tags:
                        artist = str(tags['TPE1'])
                    if 'TALB' in tags:
                        album = str(tags['TALB'])

                elif hasattr(audio, 'items'):
                    for key, value in audio.items():
                        if key == 'title':
                            title = str(value)
                        elif key == 'artist':
                            artist = str(value)
                        elif key == 'album':
                            album = str(value)

            self.song_title_label.setText(f"🎵 {title}")
            self.song_artist_label.setText(f"艺术家: {artist}")
            self.song_album_label.setText(f"专辑: {album}")

        except Exception as e:
            filename = os.path.basename(file_path)
            self.song_title_label.setText(f"🎵 {filename}")
            self.song_artist_label.setText("艺术家: -")
            self.song_album_label.setText("专辑: -")

    def toggle_play_pause(self):
        if not self.playlist_files:
            QMessageBox.information(self, "提示", "请先添加音乐文件！")
            return

        if self.current_index == -1:
            self.current_index = 0
            self.media_playlist.setCurrentIndex(0)
            self.load_song(self.playlist_files[0])

        if self.is_playing:
            self.media_player.pause()
            self.is_playing = False
            self.is_paused = True
            self.play_button.setText("▶ 继续")
            self.status_label.setText("已暂停")
        else:
            if self.is_paused:
                self.media_player.play()
                self.is_playing = True
                self.is_paused = False
                self.play_button.setText("⏸ 暂停")
                self.status_label.setText("正在播放")
            else:
                self.start_playback()

    def start_playback(self):
        if self.current_index >= 0 and self.current_index < len(self.playlist_files):
            self.media_playlist.setCurrentIndex(self.current_index)
            self.load_song(self.playlist_files[self.current_index])
            self.media_player.play()
            self.is_playing = True
            self.is_paused = False
            self.play_button.setText("⏸ 暂停")
            self.status_label.setText(f"正在播放: {os.path.basename(self.playlist_files[self.current_index])}")

    def play_previous(self):
        if not self.playlist_files:
            return

        if self.current_index > 0:
            self.current_index -= 1
        else:
            self.current_index = len(self.playlist_files) - 1

        self.start_playback()

    def play_next(self):
        if not self.playlist_files:
            return

        if self.current_index < len(self.playlist_files) - 1:
            self.current_index += 1
        else:
            self.current_index = 0

        self.start_playback()

    def stop_playback(self):
        self.media_player.stop()
        self.is_playing = False
        self.is_paused = False
        self.play_button.setText("▶ 播放")
        self.progress_slider.setValue(0)
        self.current_time_label.setText("00:00")
        self.status_label.setText("已停止")

    def play_selected(self, item):
        file_path = item.data(Qt.UserRole)
        if file_path in self.playlist_files:
            self.current_index = self.playlist_files.index(file_path)
            self.start_playback()

    def change_volume(self, value):
        self.media_player.setVolume(value)
        self.volume_label.setText(f"{value}%")

    def change_playback_speed(self, text):
        speed = float(text.replace('x', ''))
        self.media_player.setPlaybackRate(speed)

    def increase_speed(self):
        current_text = self.speed_combo.currentText()
        current_speed = float(current_text.replace('x', ''))

        for i, speed in enumerate(self.available_speeds):
            if speed > current_speed:
                self.speed_combo.setCurrentIndex(i)
                break

    def decrease_speed(self):
        current_text = self.speed_combo.currentText()
        current_speed = float(current_text.replace('x', ''))

        for i in range(len(self.available_speeds) - 1, -1, -1):
            if self.available_speeds[i] < current_speed:
                self.speed_combo.setCurrentIndex(i)
                break

    def update_position(self, position):
        if not self.slider_being_dragged:
            duration = self.media_player.duration()
            if duration > 0:
                progress = (position / duration) * 1000
                self.progress_slider.setValue(int(progress))

        self.current_time_label.setText(self.format_time(position))

    def update_duration(self, duration):
        self.total_time_label.setText(self.format_time(duration))

    def slider_pressed(self):
        self.slider_being_dragged = True

    def slider_released(self):
        self.slider_being_dragged = False
        self.set_position_from_slider()

    def set_position_from_slider(self):
        slider_value = self.progress_slider.value()
        duration = self.media_player.duration()
        if duration > 0:
            position = (slider_value / 1000) * duration
            self.media_player.setPosition(int(position))

    def format_time(self, milliseconds):
        if milliseconds < 0:
            return "00:00"

        seconds = int(milliseconds / 1000)
        minutes = seconds // 60
        seconds = seconds % 60

        return f"{minutes:02d}:{seconds:02d}"

    def on_state_changed(self, state):
        if state == QMediaPlayer.PlayingState:
            self.is_playing = True
            self.is_paused = False
            self.play_button.setText("⏸ 暂停")
        elif state == QMediaPlayer.PausedState:
            self.is_playing = False
            self.is_paused = True
            self.play_button.setText("▶ 继续")
        elif state == QMediaPlayer.StoppedState:
            self.is_playing = False
            self.is_paused = False
            self.play_button.setText("▶ 播放")

    def on_media_status_changed(self, status):
        if status == QMediaPlayer.LoadedMedia:
            self.status_label.setText("媒体已加载")
        elif status == QMediaPlayer.BufferedMedia:
            pass
        elif status == QMediaPlayer.EndOfMedia:
            self.is_playing = False
            self.is_paused = False
            self.play_button.setText("▶ 播放")
            self.status_label.setText("播放完成")
            self.progress_slider.setValue(0)
            self.current_time_label.setText("00:00")

            if self.current_index < len(self.playlist_files) - 1:
                self.play_next()
        elif status == QMediaPlayer.InvalidMedia:
            self.status_label.setText("无效的媒体文件")
        elif status == QMediaPlayer.NoMedia:
            self.status_label.setText("没有媒体")

    def on_current_index_changed(self, index):
        if index >= 0 and index < len(self.playlist_files):
            self.current_index = index
            self.load_song(self.playlist_files[index])

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            self.toggle_play_pause()
            event.accept()
        elif event.key() == Qt.Key_Left:
            self.play_previous()
            event.accept()
        elif event.key() == Qt.Key_Right:
            self.play_next()
            event.accept()
        elif event.key() == Qt.Key_Up:
            current_volume = self.volume_slider.value()
            self.volume_slider.setValue(min(current_volume + 5, 100))
            event.accept()
        elif event.key() == Qt.Key_Down:
            current_volume = self.volume_slider.value()
            self.volume_slider.setValue(max(current_volume - 5, 0))
            event.accept()
        else:
            super().keyPressEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    player = MusicPlayer()
    player.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
