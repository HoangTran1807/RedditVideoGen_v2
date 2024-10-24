import os
from faster_whisper import WhisperModel
import edge_tts
import asyncio
from moviepy.editor import *
from moviepy.config import change_settings
import time
import random

class Word:
    def __init__(self, word, start, end):
        self.word = word
        self.start = start
        self.end = end

    def __str__(self):
        return f"Word({self.word}, {self.start}, {self.end})"

    def __repr__(self):
        return str(self)

change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"})

_video_path = "videoinput/video3.webm"
_voice = "en-GB-RyanNeural"
_vn_voice = "vi-VN-HoaiMyNeural"
_audio_path = "output_0.mp3"
_story_path = "story.txt"
_video_output_path = "video_output"
_Dictionary_path = "dictionarys"

def get_story(story_path):
    # Read story from file 
    #couter time
    start = time.time()
    with open(story_path, "r") as f:
        story = f.read()
    end = time.time()
    print("Story read in ", round(end - start, 2), " seconds")
    return story

def create_audio_from_text(text, voice, audio_path):
    start = time.time()
    comunicete = edge_tts.Communicate(text, voice)
    asyncio.run(comunicete.save(audio_path))
    end = time.time()
    print("Audio created in ", round(end - start, 2), " seconds")
    return audio_path

def _get_words_from_video(audio_path):
    start = time.time()
    model = WhisperModel("base", device="cpu", compute_type="float32")
    segments, _ = model.transcribe(audio_path, word_timestamps=True)
    words = []
    for segment in segments:
        for word in segment.words:
            new_word = Word(word.word, word.start, word.end)
            words.append(new_word)
    end = time.time()
    print("Words extracted in ", round(end - start, 2), " seconds")
    return words

def compress_words(words, dictionary_path):
    i = 0
    num_words = len(words)
    # tạo từ điển từ chứa các từ không trùng lặp
    dictionary = {}
    
    while i < num_words:
        word = words[i]
        if word.word not in dictionary:
            dictionary[word.word] = word
        if i < num_words - 1:
            next_word = words[i + 1]
            if next_word.word[0] == "-":
                # Hợp nhất các từ
                next_word.word = next_word.word[1:]
                word.end = next_word.end
                word.word += " " + next_word.word
                words.remove(next_word)
                num_words -= 1  # Cập nhật số lượng từ
            else:
                i += 1  # Chỉ tăng chỉ số nếu không xóa từ
        else:
            i += 1  # Đảm bảo thoát vòng lặp khi đến từ cuối cùng
    # ghi từ điển vào file dictionary.txt
    with open(dictionary_path, "w") as f:
        for word in dictionary.values():
            f.write(f"{word.word}\n")
    return words

def get_snippet_background(video_path, duration):
    # Load the video file
    clip = VideoFileClip(video_path)
    
    # Ensure the duration between start and end is valid
    if duration > clip.duration:
        raise ValueError("The _end time exceeds the video duration.")
    
    # Calculate random start position where a snippet can be safely cut
    max_start = clip.duration - duration
    if max_start <= 0:
        raise ValueError("Video is too short for the specified duration.")
    
    start = random.uniform(0, max_start)
    end = start + duration
    
    # Return the subclip from the randomly calculated start to end
    snippet = clip.subclip(start, end)
    return snippet


def _create_video(words, videopath, audiopath, output_path):
    start = time.time()
    text_clips = []
    total_duration = 0
    num_words = len(words)
    for i in range(num_words):
        word = words[i]
        start = word.start
        end = word.end
        if i < num_words - 1:
            next_word = words[i+1]
            wating_time = next_word.start - word.end
        else:
            wating_time = 0
            # Create a text clip
        duration = (end - start) + wating_time
        txt_clip = TextClip(word.word,
                            fontsize=100, 
                            color='white', 
                            stroke_color='black',
                            stroke_width=4,
                            font='Arial')
        txt_clip = txt_clip.set_duration(duration)
        txt_clip = txt_clip.set_position(("center","center"))
        txt_clip = txt_clip.set_start(start)
        text_clips.append(txt_clip)
        total_duration += duration
    audio = AudioFileClip(audiopath)
    final_clip = concatenate_videoclips(text_clips)
    clip = get_snippet_background(videopath, final_clip.duration)
    final_clip = CompositeVideoClip([clip, final_clip.set_position(("center","center"))])
    final_clip = final_clip.set_audio(audio)
    final_clip = final_clip.set_duration(audio.duration)
    final_clip = final_clip.set_start(0)
    final_clip.write_videofile(output_path, codec="libx264", fps=24)
    end = time.time()
    print("Video created in ", round(end - start, 2), " seconds")



def main(video_name):
    # Create audio from text
    _output_path = os.path.join(_video_output_path, video_name + ".mp4")
    text = get_story(_story_path)
    audio_path = create_audio_from_text(text, _voice, _audio_path)
    
    # Get words from video
    words = _get_words_from_video(audio_path)

    dictionary_path = os.path.join(_Dictionary_path, video_name + ".txt")
    words = compress_words(words, dictionary_path)
    # Create video
    _create_video(words, _video_path, audio_path, _output_path)



if __name__ == "__main__":
    # input parameters
    if len(sys.argv) != 2:
        print("Usage: python autoClip.py <output_path>")
        sys.exit(1)
    video_name = sys.argv[1]
    main(video_name)

