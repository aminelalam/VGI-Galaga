#include "GameAudio.h"
#include <algorithm>
#include <cmath>
#include <cstring>
#include <fstream>

#pragma comment(lib, "winmm.lib")

namespace galaga {
namespace {
std::uint32_t little32(const unsigned char* bytes) {
    return std::uint32_t(bytes[0]) | (std::uint32_t(bytes[1]) << 8) |
           (std::uint32_t(bytes[2]) << 16) | (std::uint32_t(bytes[3]) << 24);
}

std::uint16_t little16(const unsigned char* bytes) {
    return std::uint16_t(bytes[0]) | (std::uint16_t(bytes[1]) << 8);
}
}

GameAudio::~GameAudio() {
    release();
}

GameAudio::Clip GameAudio::readWav(const std::filesystem::path& path) {
    std::ifstream file(path, std::ios::binary);
    unsigned char header[12]{};
    if (!file.read(reinterpret_cast<char*>(header), sizeof(header)) ||
        std::memcmp(header, "RIFF", 4) || std::memcmp(header + 8, "WAVE", 4))
        return {};

    bool formatValid = false;
    Clip samples;
    unsigned char chunk[8]{};
    while (file.read(reinterpret_cast<char*>(chunk), sizeof(chunk))) {
        const std::uint32_t size = little32(chunk + 4);
        // The supplied tracks are shorter than one minute. Bound corrupt files.
        if (size > SampleRate * 2 * 60) return {};
        if (std::memcmp(chunk, "fmt ", 4) == 0) {
            unsigned char format[16]{};
            if (size < sizeof(format) || !file.read(reinterpret_cast<char*>(format), sizeof(format)))
                return {};
            formatValid = little16(format) == WAVE_FORMAT_PCM && little16(format + 2) == 1 &&
                          little32(format + 4) == SampleRate && little32(format + 8) == SampleRate * 2 &&
                          little16(format + 12) == 2 && little16(format + 14) == 16;
            file.seekg(size - sizeof(format), std::ios::cur);
        } else if (std::memcmp(chunk, "data", 4) == 0) {
            if (size % sizeof(std::int16_t) != 0) return {};
            samples.resize(size / sizeof(std::int16_t));
            if (!file.read(reinterpret_cast<char*>(samples.data()), size)) return {};
        } else {
            file.seekg(size, std::ios::cur);
        }
        if (size & 1) file.seekg(1, std::ios::cur);
        if (!file) return {};
    }
    return formatValid ? samples : Clip{};
}

bool GameAudio::initialize(const std::filesystem::path& folder) noexcept {
    release();
    try {
        music[static_cast<std::size_t>(MusicScene::Menu)] = readWav(folder / L"menu.wav");
        music[static_cast<std::size_t>(MusicScene::Combat)] = readWav(folder / L"combat.wav");
        const wchar_t* files[] = {L"shot.wav", L"hit.wav", L"damage.wav",
                                  L"victory.wav", L"defeat.wav", L"transition.wav"};
        bool hasAudio = !music[1].empty() || !music[2].empty();
        for (std::size_t index = 0; index < sounds.size(); ++index) {
            sounds[index] = readWav(folder / files[index]);
            hasAudio |= !sounds[index].empty();
        }
        if (!hasAudio) return false;

        WAVEFORMATEX format{};
        format.wFormatTag = WAVE_FORMAT_PCM;
        format.nChannels = 1;
        format.nSamplesPerSec = SampleRate;
        format.nAvgBytesPerSec = SampleRate * 2;
        format.nBlockAlign = 2;
        format.wBitsPerSample = 16;
        if (waveOutOpen(&device, WAVE_MAPPER, &format, 0, 0, CALLBACK_NULL) != MMSYSERR_NOERROR) {
            release();
            return false;
        }
        for (auto& block : blocks) {
            block.header.lpData = reinterpret_cast<LPSTR>(block.samples.data());
            block.header.dwBufferLength = static_cast<DWORD>(block.samples.size() * sizeof(std::int16_t));
            if (waveOutPrepareHeader(device, &block.header, sizeof(WAVEHDR)) != MMSYSERR_NOERROR ||
                waveOutWrite(device, &block.header, sizeof(WAVEHDR)) != MMSYSERR_NOERROR) {
                release();
                return false;
            }
        }
        return true;
    } catch (...) {
        release();
        return false;
    }
}

void GameAudio::setScene(MusicScene scene) {
    if (static_cast<std::size_t>(scene) < music.size()) desiredScene = scene;
}

void GameAudio::play(SoundEvent event) {
    const auto sound = static_cast<std::size_t>(event);
    if (!device || muted || sound >= sounds.size() || sounds[sound].empty()) return;
    auto voice = std::find_if(voices.begin(), voices.end(), [](const Voice& item) { return !item.active; });
    if (voice == voices.end()) {
        voice = voices.begin() + replacementVoice;
        replacementVoice = (replacementVoice + 1) % voices.size();
    }
    *voice = Voice{sound, 0, true};
}

void GameAudio::mix(Block& block) {
    constexpr float fadeStep = .30f / (SampleRate * .08f);
    for (auto& sample : block.samples) {
        const float targetGain = currentScene == desiredScene && currentScene != MusicScene::Silent ? .30f : 0.f;
        musicGain += std::clamp(targetGain - musicGain, -fadeStep, fadeStep);
        if (musicGain == 0 && currentScene != desiredScene) {
            currentScene = desiredScene;
            musicPosition = 0;
        }
        const auto& track = music[static_cast<std::size_t>(currentScene)];
        float mixed = 0;
        if (!track.empty()) {
            mixed = track[musicPosition] * musicGain;
            musicPosition = (musicPosition + 1) % track.size();
        }
        for (auto& voice : voices) {
            if (!voice.active) continue;
            const auto& clip = sounds[voice.sound];
            mixed += clip[voice.position++] * .65f;
            if (voice.position == clip.size()) voice.active = false;
        }
        // Soft limiting keeps coincident hits from clipping the PCM output.
        sample = muted ? 0 : static_cast<std::int16_t>(30000.f * std::tanh(mixed / 32768.f));
    }
}

void GameAudio::tick() {
    if (!device) return;
    for (auto& block : blocks) {
        if (!(block.header.dwFlags & WHDR_DONE)) continue;
        mix(block);
        if (waveOutWrite(device, &block.header, sizeof(WAVEHDR)) != MMSYSERR_NOERROR) {
            release();
            return;
        }
    }
}

void GameAudio::release() noexcept {
    if (device) {
        waveOutReset(device);
        for (auto& block : blocks)
            if (block.header.dwFlags & WHDR_PREPARED)
                waveOutUnprepareHeader(device, &block.header, sizeof(WAVEHDR));
        waveOutClose(device);
    }
    device = nullptr;
    blocks = {};
    voices = {};
    for (auto& track : music) track.clear();
    for (auto& sound : sounds) sound.clear();
    currentScene = desiredScene = MusicScene::Silent;
    musicPosition = replacementVoice = 0;
    musicGain = 0;
}

}
