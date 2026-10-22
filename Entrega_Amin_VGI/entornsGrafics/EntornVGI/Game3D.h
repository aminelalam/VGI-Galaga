#pragma once
#include <vector>

namespace galaga {
struct Vec2 { float x = 0, y = 0; };
enum class Phase { Menu, Playing, Paused, Victory, Defeat };
enum class EnemyPhase { Entering, Formation, Warning, Diving, Returning };
struct Input { bool left = false, right = false, fire = false; };
struct Enemy {
    int id = 0, type = 0;
    bool alive = true, shot = false;
    EnemyPhase phase = EnemyPhase::Entering;
    Vec2 pos, previous, slot, start;
    float timer = 0, targetX = 0;
    float z = 0, previousZ = 0;
};
struct Bullet {
    int id = 0;
    bool ally = true, alive = true;
    Vec2 pos, previous;
    float ttl = 3.5f;
    float z = 0, previousZ = 0, velocityZ = 0;
};
struct Spark { Vec2 pos; float age = 0; bool player = false; float z = 0; };

// Pure simulation: no MFC, GL, system clock or file dependencies.
class Game3D {
public:
    static constexpr float Step = 1.0f / 60.0f;
    Phase phase = Phase::Menu;
    Vec2 player{0, -4}, previousPlayer{0, -4};
    int lives = 3, score = 0, shots = 0, kills = 0;
    int selectedShip = 0, bestScore = 0, hitStreak = 0, multiplier = 1;
    float time = 0, invulnerable = 1.5f, respawn = 0;
    std::vector<Enemy> enemies;
    std::vector<Bullet> bullets;
    std::vector<Spark> sparks;
    void reset();
    void returnToMenu();
    void selectShip(int ship);
    void pause();
    void update(const Input& input, float dt = Step);
    int remaining() const;
    static float hitTime(Vec2 a0, Vec2 a1, Vec2 b0, Vec2 b1, float radius);
    static float hitTime3D(Vec2 a0, Vec2 a1, float za0, float za1,
        Vec2 b0, Vec2 b1, float zb0, float zb1, float radius);
private:
    float fireClock = 0, attackClock = 2.4f;
    int nextId = 100, nextAttacker = 0;
    void damage();
    void clearCombo();
};
}
