# ********coding      :   utf-8
# ********create at   :   2025/4
# ********create by   :   wml
# ********Description :   Audio detection

import collections
import contextlib
import wave
import webrtcvad


class audio_frame(object):
    def __init__(self, bytes, timestamp, duration):
        self.bytes = bytes
        self.timestamp = timestamp
        self.duration = duration


class AudioDetection():
    def __init__(self, aggressiveness=2, frame_duration_ms=30, padding_duration_ms=300):
        self.aggressiveness = aggressiveness
        self.frame_duration_ms = frame_duration_ms
        self.padding_duration_ms = padding_duration_ms
        self.vad = webrtcvad.Vad(self.aggressiveness)

    def read_wave(self, path):
        with contextlib.closing(wave.open(path, 'rb')) as wf:
            num_channels = wf.getnchannels()
            assert num_channels == 1
            sample_width = wf.getsampwidth()
            assert sample_width == 2
            sample_rate = wf.getframerate()
            assert sample_rate in (8000, 16000, 32000, 48000)
            pcm_data = wf.readframes(wf.getnframes())
            return pcm_data, sample_rate

    def write_wave(self, path, audio, sample_rate):
        with contextlib.closing(wave.open(path, 'wb')) as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio)

    def frame_generator(self, audio, sample_rate):
        n = int(sample_rate * (self.frame_duration_ms / 1000.0) * 2)
        offset = 0
        timestamp = 0.0
        duration = (float(n) / sample_rate) / 2.0
        while offset + n < len(audio):
            yield audio_frame(audio[offset:offset + n], timestamp, duration)
            timestamp += duration
            offset += n

    def vad_collector(self, sample_rate, frames):
        num_padding_frames = int(self.padding_duration_ms / self.frame_duration_ms)
        ring_buffer = collections.deque(maxlen=num_padding_frames)
        triggered = False
        voiced_frames = []
        for frame in frames:
            is_speech = self.vad.is_speech(frame.bytes, sample_rate)
            if not triggered:
                ring_buffer.append((frame, is_speech))
                num_voiced = len([f for f, speech in ring_buffer if speech])
                if num_voiced > 0.9 * ring_buffer.maxlen:
                    triggered = True
                    for f, s in ring_buffer:
                        voiced_frames.append(f)
                    ring_buffer.clear()
            else:
                voiced_frames.append(frame)
                ring_buffer.append((frame, is_speech))
                num_unvoiced = len([f for f, speech in ring_buffer if not speech])
                if num_unvoiced > 0.9 * ring_buffer.maxlen:
                    triggered = False
                    yield b''.join([f.bytes for f in voiced_frames])
                    ring_buffer.clear()
                    voiced_frames = []
        if voiced_frames:
            yield b''.join([f.bytes for f in voiced_frames])

    def detect(self, audio_path, output_dir):
        audio, sample_rate = self.read_wave(audio_path)
        frames = self.frame_generator(audio, sample_rate)
        segments = self.vad_collector(sample_rate, frames)
        for i, segment in enumerate(segments):
            path = f"{output_dir}/chunk-{i:02d}.wav"
            print(f'Writing {path}')
            self.write_wave(path, segment, sample_rate)


def main() :
    audio_path = 'C:\\Users\\L\\Desktop\\表情\\audio\\what_you_sad.wav'  # 音频输入路径
    output_dir = 'C:\\Users\\L\\Desktop\\表情\\audio'  # 音频输出路径
    detector = AudioDetection()
    detector.detect(audio_path, output_dir)


if __name__ == "__main__":
    main()