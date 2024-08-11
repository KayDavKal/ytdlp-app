from kivy.app import App
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.lang import Builder
from threading import Thread
import threading
import yt_dlp
import os

class YTDLPApp(App):
    def build(self):
        Window.set_icon('logo.png')
        root = Builder.load_file('ytdlp.kv')
        self.url_input = root.ids.url_input
        self.status_label = root.ids.status_label
        self.file_list = root.ids.file_list
        self.current_playing_label = root.ids.current_playing_label
        self.progress_bar = root.ids.progress_bar
        self.current_sound = None
        self.current_file_name = None
        self.current_file_index = -1

        root.ids.download_button.bind(on_press=self.start_download)
        root.ids.stop_button.bind(on_press=self.stop_audio)
        root.ids.next_button.bind(on_press=self.play_next)

        # Aktualisiere die Dateiliste beim Start
        self.update_file_list()

        return root
    
    def start_download(self, instance):
        url = self.url_input.text
        if url:
            self.status_label.text = 'Status: Herunterladen...'
            Thread(target=self.download_audio, args=(url,)).start()
    
    def update_status_label(self, status_text):
        self.status_label.text = status_text
    
    def download_audio(self, url):
        def download():
            try:
                options = {
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                    'outtmpl': './audio/%(title)s.%(ext)s',
                    'quiet': True,
                }
            
                with yt_dlp.YoutubeDL(options) as ydl:
                    ydl.download([url])
            
                # Update the status label after the download is complete
                Clock.schedule_once(lambda dt: self.update_status_label('Status: Download abgeschlossen!'))
                Clock.schedule_once(lambda dt: self.update_file_list(), 0)
            except Exception as e:
                import traceback
                error_message = f'Status: Fehler - {str(e)}'
                # Display error in the status label
                Clock.schedule_once(lambda dt: self.update_status_label(error_message))
                print(traceback.format_exc())
    
        # Run the download in a separate thread to avoid blocking the UI
        threading.Thread(target=download).start()
    
    def update_file_list(self, dt=None):
        self.file_list.clear_widgets()
        if not os.path.exists('./audio'):
            os.makedirs('./audio')
        
        self.files = os.listdir('./audio')
        self.files.sort()  # Sort files to ensure consistent ordering
        
        for file_name in self.files:
            file_path = os.path.join('./audio', file_name)
            # Button erstellen und `on_press` Event richtig konfigurieren
            button = Button(text=file_name, size_hint_y=None, height=40, background_color='#6EACDA')
            button.bind(on_press=self.create_play_function(file_path, file_name))
            self.file_list.add_widget(button)
    
    def create_play_function(self, file_path, file_name):
        def play_function(instance):
            self.play_file(file_path, file_name)
        return play_function
    
    def play_file(self, file_path, file_name):
        # Stop the currently playing sound if any
        if self.current_sound:
            self.current_sound.stop()
        
        # Load and play the new sound
        self.current_sound = SoundLoader.load(file_path)
        if self.current_sound:
            self.current_sound.play()
            # Update the label with the name of the currently playing file
            self.current_playing_label.text = f'Aktuell abgespielt: {file_name}'
            # Update the current file index
            self.current_file_name = file_name
            self.current_file_index = self.files.index(file_name)
            # Reset the progress bar
            self.progress_bar.value = 0
            self.progress_bar.max = self.current_sound.length * 1000  # In milliseconds
            Clock.schedule_interval(self.update_progress_bar, 0.1)
        else:
            print("Failed to load sound")
    
    def update_progress_bar(self, dt):
        if self.current_sound:
            # Update progress bar based on the elapsed time
            self.progress_bar.value = self.current_sound.get_pos()
            if self.progress_bar.value >= self.progress_bar.max:
                # Stop updating the progress bar if the sound is finished
                self.stop_audio(None)
    
    def stop_audio(self, instance):
        # Stop the currently playing sound
        if self.current_sound:
            self.current_sound.stop()
            self.current_sound = None
            # Clear the label text when stopping
            self.current_playing_label.text = 'Es wird gerade nichts abgespielt'
            self.progress_bar.value = 0
            Clock.unschedule(self.update_progress_bar)
            # Do not reset the current file index and name here
    
    def play_next(self, instance):
        if self.current_file_index != -1 and self.current_file_index + 1 < len(self.files):
            # Stop the current sound
            self.stop_audio(None)
            # Play the next file
            next_file_index = self.current_file_index + 1
            next_file_name = self.files[next_file_index]
            next_file_path = os.path.join('./audio', next_file_name)
            self.play_file(next_file_path, next_file_name)
        else:
            # No more files to play
            self.current_playing_label.text = 'Keine weiteren Dateien'

if __name__ == '__main__':
    YTDLPApp().run()
