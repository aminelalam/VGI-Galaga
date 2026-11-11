#pragma once

#include <windows.h>
#include <mmsystem.h>
#include <array>
#include <cstdint>
#include <filesystem>
#include <vector>

namespace galaga {

enum class MusicScene { Silent, Menu, Combat };
enum class SoundEvent { Shot, Hit, Damage, Victory, Defeat, Transition, Count };

// Main-thread PCM mixer. Call tick from the window timer, including during menus.
class GameAudio {
public:
    GameAudio() = default;
    ~GameAudio();
    GameAudio(const GameAudio&) = delete;
    GameAudio& operator=(const GameAudio&) = delete;

    // Missing files or an unavailable audio device leave the game operational.
    bool initialize(const std::filesystem::path& folder) noexcept;
    void setScene(MusicScene scene);
    void play(SoundEvent event);
    void tick();
    void setMuted(bool value) { muted = value; }
    bool isMuted() const { return muted; }
    bool available() const { return device != nullptr; }
    void release() noexcept;

private:
    static constexpr unsigned SampleRate = 22050;
    static constexpr std::size_t SamplesPerBlock = 384;
    using Clip = std::vector<std::int16_t>;
    struct Block {
        std::array<std::int16_t, SamplesPerBlock> samples{};
        WAVEHDR header{};
    };
    struct Voice {
        std::size_t sound = 0;
        std::size_t position = 0;
        bool active = false;
    };

    HWAVEOUT device = nullptr;
    std::array<Block, 4> blocks{};
    std::array<Clip, 3> music;
    std::array<Clip, static_cast<std::size_t>(SoundEvent::Count)> sounds;
    std::array<Voice, 8> voices{};
    MusicScene currentScene = MusicScene::Silent;
    MusicScene desiredScene = MusicScene::Silent;
    std::size_t musicPosition = 0;
    std::size_t replacementVoice = 0;
    float musicGain = 0;
    bool muted = false;

    static Clip readWav(const std::filesystem::path& path);
    void mix(Block& block);
};

}
