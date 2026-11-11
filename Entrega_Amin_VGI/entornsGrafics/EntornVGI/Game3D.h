#pragma once
#include <vector>

namespace galaga {
inline constexpr float EnemyHitRadius = .76f;
struct Vec2 { float x = 0, y = 0; };
enum class Phase { Menu, Playing, Paused, Victory, Defeat };
enum class Stage { Combat, Evasion, Boss };
enum class Weapon { Single, Double, Triple, Missile };
enum class EnemyPhase { Entering, Formation, Warning, Diving, Returning };
struct Input {
    bool left = false, right = false, fire = false;
    bool up = false, down = false, special = false;
};
struct Enemy {
    int id = 0, type = 0;
    bool alive = true, shot = false;
    EnemyPhase phase = EnemyPhase::Entering;
    Vec2 pos, previous, slot, start;
    float timer = 0, targetX = 0;
    float z = 0, previousZ = 0;
    float slotZ = 0, startZ = 0, targetZ = 0;
    float velocityX = 0, velocityY = 0, velocityZ = 0;
    float radius = EnemyHitRadius, hitFlash = 0;
    int hp = 1, maxHp = 1;
};
struct Bullet {
    int id = 0;
    bool ally = true, alive = true;
    Vec2 pos, previous;
    float ttl = 3.5f;
    float z = 0, previousZ = 0, velocityZ = 0;
    float velocityX = 0, velocityY = 0;
    int kind = 0, damage = 1;
    float radius = .12f;
    float forwardSpeed() const;
};
struct Spark {
    Vec2 pos;
    float age = 0;
    bool player = false;
    float z = 0, duration = .55f, size = .75f;
};
struct Obstacle {
    int id = 0;
    bool alive = true;
    Vec2 pos, previous;
    float z = 0, previousZ = 0;
    float radius = 1.f, velocityY = -11.f;
};

// Fixed-step simulation in world XYZ coordinates, independent of MFC and OpenGL.
class Game3D {
public:
    static constexpr float Step = 1.f / 60.f;
    static constexpr float EnemyScale = 1.45f;
    static constexpr float BossScale = 2.3f;
    // Boss collider semiaxes: world X (wings), Y (depth), Z (height).
    static constexpr float BossHitRadius = 3.f;
    static constexpr float BossHitDepth = 2.3f;
    static constexpr float BossHitHeight = 1.5f;
    static constexpr float EnemyHitRadius = galaga::EnemyHitRadius;
    static constexpr float AimTolerance = 1.4f;
    static constexpr float PlayerShotSpeed = 36.f;
    static constexpr float EnemyShotSpeed = 8.f;
    static constexpr float PlayerRadius = .38f;
    static constexpr float PlayerLimitX = 7.68f;
    static constexpr float PlayerMinZ = -3.2f;
    static constexpr float PlayerMaxZ = 4.6f;
    Phase phase = Phase::Menu;
    Stage stage = Stage::Combat;
    Weapon weapon = Weapon::Single;
    Vec2 player{0, -4}, previousPlayer{0, -4};
    float playerZ = 0, previousPlayerZ = 0;
    int lives = 3, score = 0, shots = 0, kills = 0;
    int selectedShip = 0, bestScore = 0, hitStreak = 0, multiplier = 1;
    int wave = 1, bossHealth = 0, bossMaxHealth = 36;
    float time = 0, stageTime = 0, stageDuration = 0;
    float invulnerable = 1.5f, respawn = 0, specialCooldown = 0;
    std::vector<Enemy> enemies;
    std::vector<Bullet> bullets;
    std::vector<Spark> sparks;
    std::vector<Obstacle> obstacles;
    void reset();
    void returnToMenu();
    void selectShip(int ship);
    void selectWeapon(int index);
    void pause();
    void update(const Input& input, float dt = Step);
    int remaining() const;
    const Enemy* aimTarget() const;
    static float hitTime(Vec2 a0, Vec2 a1, Vec2 b0, Vec2 b1, float radius);
    static float hitTime3D(Vec2 a0, Vec2 a1, float za0, float za1,
        Vec2 b0, Vec2 b1, float zb0, float zb1, float radius);
private:
    float fireClock = 0, enemyFireClock = 3.f, diveClock = 5.f, obstacleClock = 1.f;
    float bossOrbit = 0;
    int nextId = 100, nextAttacker = 0, obstacleBurst = 0;
    void startWave();
    void startEvasion();
    void startBoss();
    void movePlayer(const Input& input, float dt);
    void firePlayer(Weapon mode);
    void fireEnemy(const Enemy& enemy, float offsetX = 0, float offsetZ = 0);
    void moveEnemies(float dt);
    void moveObstacles(float dt);
    void resolveContacts(float dt);
    void damage();
    void clearCombo();
    void addEffect(Vec2 pos, float z, bool playerHit, float size);
};
}
