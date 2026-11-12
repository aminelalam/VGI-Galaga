#include "Game3D.h"
#include <algorithm>
#include <cmath>

namespace galaga {
namespace {
struct Point3 { float x, y, z; };

Point3 formationPosition(const Enemy& enemy, float time) {
    return {enemy.slot.x + std::sin(time * .7f + enemy.id) * .25f,
            enemy.slot.y + std::sin(time * .5f + enemy.id) * .6f,
            enemy.slotZ + std::sin(time * .7f + enemy.id * .3f) * .2f};
}

Point3 bezier(Point3 start, Point3 first, Point3 second, Point3 end, float t) {
    t = std::clamp(t, 0.f, 1.f);
    const float s = 1.f - t;
    const float a = s * s * s, b = 3.f * s * s * t;
    const float c = 3.f * s * t * t, d = t * t * t;
    return {a * start.x + b * first.x + c * second.x + d * end.x,
            a * start.y + b * first.y + c * second.y + d * end.y,
            a * start.z + b * first.z + c * second.z + d * end.z};
}

void place(Enemy& enemy, Point3 point) {
    enemy.pos = {point.x, point.y};
    enemy.z = point.z;
}

void beginPath(Enemy& enemy, EnemyPhase phase) {
    enemy.phase = phase;
    enemy.timer = 0;
    enemy.start = enemy.pos;
    enemy.startZ = enemy.z;
    enemy.shot = false;
}

float weaponCadence(Weapon weapon) {
    switch (weapon) {
    case Weapon::Double: return .24f;
    case Weapon::Triple: return .32f;
    case Weapon::Missile: return .85f;
    default: return .18f;
    }
}

bool retired(const Bullet& bullet) {
    return !bullet.alive || bullet.ttl <= 0 || bullet.pos.y > 55.f || bullet.pos.y < -5.3f ||
        std::abs(bullet.pos.x) > 18.f || bullet.z < -12.f || bullet.z > 14.f;
}

float enemyHitTime(Vec2 start, Vec2 end, float startZ, float endZ,
    const Enemy& enemy, Vec2 enemyEnd, float enemyEndZ, float otherRadius) {
    if (enemy.type != 2) {
        return Game3D::hitTime3D(start, end, startZ, endZ,
            enemy.previous, enemyEnd, enemy.previousZ, enemyEndZ, enemy.radius + otherRadius);
    }

    // Scale relative movement into a unit sphere. Expanding each semiaxis
    // includes the projectile/player radius without giving the wide wings
    // an equally tall, invisible collision volume.
    const Point3 axes{Game3D::BossHitRadius + otherRadius,
        Game3D::BossHitDepth + otherRadius, Game3D::BossHitHeight + otherRadius};
    const Vec2 relativeStart{(start.x - enemy.previous.x) / axes.x,
        (start.y - enemy.previous.y) / axes.y};
    const Vec2 relativeEnd{(end.x - enemyEnd.x) / axes.x,
        (end.y - enemyEnd.y) / axes.y};
    const float relativeStartZ = (startZ - enemy.previousZ) / axes.z;
    const float relativeEndZ = (endZ - enemyEndZ) / axes.z;
    return Game3D::hitTime3D(relativeStart, relativeEnd, relativeStartZ, relativeEndZ,
        {}, {}, 0, 0, 1.f);
}
}

float Bullet::forwardSpeed() const {
    return velocityY != 0 ? velocityY : (ally ? Game3D::PlayerShotSpeed : -Game3D::EnemyShotSpeed);
}

const Enemy* Game3D::aimTarget() const {
    const Enemy* target = nullptr;
    float bestDistance = 1e9f;
    for (const auto& enemy : enemies) {
        if (!enemy.alive || enemy.timer < 0 || enemy.pos.y <= player.y + 1.f) continue;
        const float dx = enemy.pos.x - player.x, dz = enemy.z - playerZ;
        const float error = std::sqrt(dx * dx + dz * dz);
        if (error > AimTolerance + enemy.radius) continue;
        const float distance = error + (enemy.pos.y - player.y) * .015f;
        if (distance < bestDistance) {
            target = &enemy;
            bestDistance = distance;
        }
    }
    return target;
}

void Game3D::reset() {
    const int ship = selectedShip, record = std::max(bestScore, score);
    const Weapon selectedWeapon = weapon;
    *this = Game3D{};
    selectedShip = std::clamp(ship, 0, 2);
    bestScore = record;
    weapon = selectedWeapon;
    phase = Phase::Playing;
    startWave();
}

void Game3D::returnToMenu() {
    const int ship = selectedShip, record = std::max(bestScore, score);
    const Weapon selectedWeapon = weapon;
    *this = Game3D{};
    selectedShip = std::clamp(ship, 0, 2);
    bestScore = record;
    weapon = selectedWeapon;
}

void Game3D::selectShip(int ship) {
    if (phase == Phase::Menu && ship >= 0 && ship < 3) selectedShip = ship;
}

void Game3D::selectWeapon(int index) {
    if (index >= 0 && index < 4) weapon = static_cast<Weapon>(index);
}

void Game3D::pause() {
    if (phase == Phase::Playing) phase = Phase::Paused;
    else if (phase == Phase::Paused) phase = Phase::Playing;
}

int Game3D::remaining() const {
    return static_cast<int>(std::count_if(enemies.begin(), enemies.end(), [](const Enemy& e) { return e.alive; }));
}

void Game3D::startWave() {
    stage = Stage::Combat;
    stageTime = 0;
    stageDuration = 0;
    enemies.clear();
    bullets.clear();
    obstacles.clear();
    nextAttacker = 0;
    enemyFireClock = 3.8f;
    diveClock = 5.f;
    const int columns = wave + 3;
    for (int row = 0; row < 3; ++row) {
        for (int column = 0; column < columns; ++column) {
            Enemy enemy;
            enemy.id = nextId++;
            enemy.type = row == 2 ? 1 : 0;
            enemy.hp = enemy.maxHp = wave == 3 && enemy.type == 1 ? 2 : 1;
            enemy.slot = {(column - (columns - 1) * .5f) * 2.5f, 15.f + row * 5.f};
            enemy.slotZ = -1.8f + row * 2.7f;
            const float side = column % 2 == 0 ? -1.f : 1.f;
            enemy.start = {side * (11.f + row), 35.f + row * 4.f};
            enemy.startZ = column % 2 == 0 ? 6.5f : -4.5f;
            enemy.pos = enemy.previous = enemy.start;
            enemy.z = enemy.previousZ = enemy.startZ;
            enemy.timer = -(row * columns + column) * .075f;
            enemies.push_back(enemy);
        }
    }
}

void Game3D::startEvasion() {
    stage = Stage::Evasion;
    stageTime = 0;
    stageDuration = wave == 1 ? 12.f : 15.f;
    enemies.clear();
    bullets.clear();
    obstacles.clear();
    obstacleClock = 1.f;
    obstacleBurst = 0;
    invulnerable = std::max(invulnerable, 1.5f);
}

void Game3D::startBoss() {
    stage = Stage::Boss;
    stageTime = 0;
    stageDuration = 0;
    enemies.clear();
    bullets.clear();
    obstacles.clear();
    enemyFireClock = 3.5f;
    bossOrbit = 0;
    bossHealth = bossMaxHealth;
    Enemy boss;
    boss.id = nextId++;
    boss.type = 2;
    boss.hp = boss.maxHp = bossMaxHealth;
    boss.radius = BossHitRadius;
    boss.slot = {0, 24};
    boss.slotZ = 1.1f;
    boss.start = {0, 48};
    boss.startZ = 6.f;
    boss.pos = boss.previous = boss.start;
    boss.z = boss.previousZ = boss.startZ;
    enemies.push_back(boss);
}

float Game3D::hitTime(Vec2 a0, Vec2 a1, Vec2 b0, Vec2 b1, float radius) {
    return hitTime3D(a0, a1, 0, 0, b0, b1, 0, 0, radius);
}

float Game3D::hitTime3D(Vec2 a0, Vec2 a1, float za0, float za1,
    Vec2 b0, Vec2 b1, float zb0, float zb1, float radius) {
    const float x = a0.x - b0.x, y = a0.y - b0.y, z = za0 - zb0;
    const float vx = a1.x - a0.x - b1.x + b0.x;
    const float vy = a1.y - a0.y - b1.y + b0.y;
    const float vz = za1 - za0 - zb1 + zb0;
    const float c = x * x + y * y + z * z - radius * radius;
    const float a = vx * vx + vy * vy + vz * vz;
    if (c <= 0) return 0;
    if (a < 1e-10f) return -1;
    const float b = 2.f * (x * vx + y * vy + z * vz);
    const float discriminant = b * b - 4.f * a * c;
    if (discriminant < 0) return -1;
    const float t = (-b - std::sqrt(discriminant)) / (2.f * a);
    return t >= 0 && t <= 1 ? t : -1;
}

void Game3D::addEffect(Vec2 pos, float z, bool playerHit, float size) {
    sparks.push_back({pos, 0, playerHit, z, .55f, size});
}

void Game3D::clearCombo() {
    hitStreak = 0;
    multiplier = 1;
}

void Game3D::damage() {
    if (invulnerable > 0 || respawn > 0 || lives <= 0) return;
    --lives;
    damageFlash = .35f;
    clearCombo();
    addEffect(player, playerZ, true, 1.2f);
    respawn = .7f;
    invulnerable = 1.8f;
}

void Game3D::firePlayer(Weapon mode) {
    const int count = mode == Weapon::Double ? 2 : mode == Weapon::Triple ? 3 : 1;
    for (int index = 0; index < count; ++index) {
        const float spread = index - (count - 1) * .5f;
        Bullet shot;
        shot.id = nextId++;
        shot.salvo = shots + 1;
        shot.pos = {player.x + (mode == Weapon::Double ? spread * .56f : 0), player.y + .9f};
        shot.previous = shot.pos;
        shot.z = shot.previousZ = playerZ;
        shot.kind = static_cast<int>(mode);
        shot.velocityX = mode == Weapon::Triple ? spread * 2.8f : 0;
        shot.velocityY = std::sqrt(PlayerShotSpeed * PlayerShotSpeed - shot.velocityX * shot.velocityX);
        if (mode == Weapon::Missile) {
            shot.damage = 4;
            shot.radius = .24f;
            shot.velocityY = 23.f;
            if (const Enemy* target = aimTarget()) {
                const float dx = target->pos.x - shot.pos.x;
                const float dy = target->pos.y - shot.pos.y;
                const float dz = target->z - shot.z;
                const float travel = std::sqrt(dx * dx + dy * dy + dz * dz) / 23.f;
                shot.velocityX = dx / travel;
                shot.velocityY = dy / travel;
                shot.velocityZ = dz / travel;
            }
        }
        bullets.push_back(shot);
    }
    ++shots;
}

void Game3D::movePlayer(const Input& input, float dt) {
    previousPlayer = player;
    previousPlayerZ = playerZ;
    fireClock = std::max(0.f, fireClock - dt);
    specialCooldown = std::max(0.f, specialCooldown - dt);
    if (respawn > 0) {
        respawn = std::max(0.f, respawn - dt);
        if (respawn == 0) {
            player = previousPlayer = {0, -4};
            playerZ = previousPlayerZ = 0;
        }
        return;
    }
    invulnerable = std::max(0.f, invulnerable - dt);
    float dx = float(input.right) - float(input.left);
    float dz = float(input.up) - float(input.down);
    const float length = std::sqrt(dx * dx + dz * dz);
    if (length > 1.f) {
        dx /= length;
        dz /= length;
    }
    player.x = std::clamp(player.x + dx * 6.f * dt, -PlayerLimitX, PlayerLimitX);
    playerZ = std::clamp(playerZ + dz * 6.f * dt, PlayerMinZ, PlayerMaxZ);
    if (stage == Stage::Evasion) return;
    const auto active = std::count_if(bullets.begin(), bullets.end(), [](const Bullet& bullet) { return bullet.alive && bullet.ally; });
    if (active >= 48) return;
    if (input.fire && fireClock == 0) {
        firePlayer(weapon);
        fireClock = weaponCadence(weapon);
    }
    if (input.special && specialCooldown == 0) {
        firePlayer(Weapon::Missile);
        specialCooldown = 4.f;
    }
}

void Game3D::fireEnemy(const Enemy& enemy, float offsetX, float offsetZ) {
    if (enemy.pos.y <= player.y + 2.f) return;
    const float dx = player.x + offsetX - enemy.pos.x;
    const float dy = player.y - enemy.pos.y;
    const float dz = playerZ + offsetZ - enemy.z;
    const float travel = std::sqrt(dx * dx + dy * dy + dz * dz) / EnemyShotSpeed;
    Bullet shot;
    shot.id = nextId++;
    shot.ally = false;
    shot.pos = shot.previous = enemy.pos;
    shot.z = shot.previousZ = enemy.z;
    shot.velocityX = dx / travel;
    shot.velocityY = dy / travel;
    shot.velocityZ = dz / travel;
    shot.radius = .17f;
    shot.ttl = travel + .5f;
    bullets.push_back(shot);
}

void Game3D::moveEnemies(float dt) {
    for (auto& enemy : enemies) {
        enemy.previous = enemy.pos;
        enemy.previousZ = enemy.z;
        enemy.velocityX = enemy.velocityY = enemy.velocityZ = 0;
        if (!enemy.alive) continue;
        enemy.timer += dt;
        enemy.hitFlash = std::max(0.f, enemy.hitFlash - dt);
        if (enemy.timer < 0) continue;
        const Point3 start{enemy.start.x, enemy.start.y, enemy.startZ};
        const Point3 slot{enemy.slot.x, enemy.slot.y, enemy.slotZ};
        const Point3 formation = enemy.type == 2 ? slot : formationPosition(enemy, stageTime);
        const float side = enemy.id % 2 == 0 ? -1.f : 1.f;
        if (enemy.phase == EnemyPhase::Entering) {
            place(enemy, bezier(start, {start.x * .9f, 22, start.z},
                {slot.x - side * 2.f, slot.y + 5.f, slot.z + 2.f}, formation, enemy.timer / 2.4f));
            if (enemy.timer >= 2.4f) beginPath(enemy, EnemyPhase::Formation);
        } else if (enemy.type == 2) {
            const float speed = bossHealth <= bossMaxHealth / 2 ? .6f : .4f;
            // Integrating the phase avoids a position jump when the boss accelerates.
            bossOrbit += speed * dt;
            enemy.pos = {std::sin(bossOrbit) * 4.8f, 24.f + std::sin(enemy.timer * .3f) * 2.f};
            enemy.z = 1.1f + std::sin(enemy.timer * .55f) * 2.1f;
            enemy.phase = enemyFireClock < .65f ? EnemyPhase::Warning : EnemyPhase::Formation;
        } else if (enemy.phase == EnemyPhase::Formation || enemy.phase == EnemyPhase::Warning) {
            place(enemy, formation);
            if (enemy.phase == EnemyPhase::Warning && enemy.timer >= .8f) {
                beginPath(enemy, EnemyPhase::Diving);
                enemy.targetX = player.x;
                enemy.targetZ = playerZ;
            }
        } else if (enemy.phase == EnemyPhase::Diving) {
            const Point3 end{std::clamp(enemy.targetX + side * 3.f, -10.f, 10.f), -7.f, enemy.targetZ - .7f};
            place(enemy, bezier(start, {start.x + side * 4.f, start.y - 3.f, start.z + 2.7f},
                {enemy.targetX, 0, enemy.targetZ}, end, enemy.timer / 3.2f));
            if (!enemy.shot && enemy.timer > 1.f) {
                fireEnemy(enemy);
                enemy.shot = true;
            }
            if (enemy.timer >= 3.2f) beginPath(enemy, EnemyPhase::Returning);
        } else if (enemy.phase == EnemyPhase::Returning) {
            place(enemy, bezier(start, {side * 12.f, -6.f, start.z + 4.f},
                {side * 10.f, slot.y + 8.f, slot.z + 3.f}, formation, enemy.timer / 2.6f));
            if (enemy.timer >= 2.6f) beginPath(enemy, EnemyPhase::Formation);
        }
        enemy.velocityX = (enemy.pos.x - enemy.previous.x) / dt;
        enemy.velocityY = (enemy.pos.y - enemy.previous.y) / dt;
        enemy.velocityZ = (enemy.z - enemy.previousZ) / dt;
    }
    enemyFireClock -= dt;
    if (enemyFireClock <= 0) {
        for (std::size_t offset = 0; offset < enemies.size(); ++offset) {
            const std::size_t index = (nextAttacker + offset) % enemies.size();
            const auto& enemy = enemies[index];
            if (!enemy.alive || enemy.timer < 0 || enemy.phase == EnemyPhase::Entering) continue;
            if (enemy.type == 2) {
                const int spread = bossHealth <= bossMaxHealth / 2 ? 2 : 1;
                for (int shot = -spread; shot <= spread; ++shot)
                    fireEnemy(enemy, shot * 1.2f, shot % 2 == 0 ? 0.f : .7f);
            } else {
                fireEnemy(enemy);
            }
            nextAttacker = static_cast<int>((index + 1) % enemies.size());
            break;
        }
        enemyFireClock = stage == Stage::Boss ? 1.9f : 2.6f - wave * .3f;
    }
    if (stage != Stage::Combat) return;
    diveClock -= dt;
    if (diveClock > 0) return;
    const auto active = std::count_if(enemies.begin(), enemies.end(), [](const Enemy& enemy) {
        return enemy.alive && (enemy.phase == EnemyPhase::Warning || enemy.phase == EnemyPhase::Diving || enemy.phase == EnemyPhase::Returning);
    });
    if (active < 2) {
        for (std::size_t offset = 0; offset < enemies.size(); ++offset) {
            auto& enemy = enemies[(nextAttacker + offset) % enemies.size()];
            if (!enemy.alive || enemy.phase != EnemyPhase::Formation) continue;
            beginPath(enemy, EnemyPhase::Warning);
            break;
        }
    }
    diveClock = 3.6f - wave * .4f;
}

void Game3D::moveObstacles(float dt) {
    obstacleClock -= dt;
    if (obstacleClock <= 0 && stageTime < stageDuration - 4.4f) {
        // Shift successive groups in both axes: the old fixed grid left safe
        // places between rocks and along the boundaries for the entire phase.
        // The broad opening stays inside the flight limits and bounces gently.
        const float offsetsX[]{-.95f, .95f, .95f, -.95f};
        const float offsetsZ[]{-.825f, -.825f, .825f, .825f};
        const float offsetX = offsetsX[obstacleBurst % 4];
        const float offsetZ = offsetsZ[obstacleBurst % 4];
        const int columnPhase = obstacleBurst % 4;
        const int rowPhase = (obstacleBurst / 2 + wave - 1) % 4;
        const int gapColumn = 1 + (columnPhase <= 2 ? columnPhase : 4 - columnPhase);
        const int gapRow = rowPhase <= 2 ? rowPhase : 4 - rowPhase;
        for (int row = 0; row < 3; ++row) {
            for (int column = 0; column < 5; ++column) {
                if (column == gapColumn && row == gapRow) continue;
                Obstacle obstacle;
                obstacle.id = nextId++;
                obstacle.pos = obstacle.previous = {(column - 2) * 3.f + offsetX, 40.f};
                obstacle.z = obstacle.previousZ = -2.35f + row * 3.f + offsetZ;
                obstacles.push_back(obstacle);
            }
        }
        ++obstacleBurst;
        obstacleClock = 1.8f;
    }
    for (auto& obstacle : obstacles) {
        obstacle.previous = obstacle.pos;
        obstacle.previousZ = obstacle.z;
        obstacle.pos.y += obstacle.velocityY * dt;
    }
}

void Game3D::resolveContacts(float dt) {
    enum class Kind { ShotEnemy, ShotPlayer, EnemyPlayer, ObstaclePlayer };
    struct Contact { float time; Kind kind; int first, second, id; };
    std::vector<Contact> contacts;
    for (int index = 0; index < static_cast<int>(bullets.size()); ++index) {
        const auto& bullet = bullets[index];
        if (!bullet.alive) continue;
        // Expiring shots only see the part of the target's path during their lifetime.
        const float activeFraction = std::clamp(1.f + std::min(0.f, bullet.ttl) / dt, 0.f, 1.f);
        if (bullet.ally) {
            for (int other = 0; other < static_cast<int>(enemies.size()); ++other) {
                const auto& enemy = enemies[other];
                if (!enemy.alive || enemy.timer < 0) continue;
                const Vec2 end{enemy.previous.x + (enemy.pos.x - enemy.previous.x) * activeFraction,
                    enemy.previous.y + (enemy.pos.y - enemy.previous.y) * activeFraction};
                const float endZ = enemy.previousZ + (enemy.z - enemy.previousZ) * activeFraction;
                const float hit = enemyHitTime(bullet.previous, bullet.pos, bullet.previousZ, bullet.z,
                    enemy, end, endZ, bullet.radius);
                if (hit >= 0) contacts.push_back({hit * activeFraction, Kind::ShotEnemy, index, other, enemy.id});
            }
        } else if (respawn == 0) {
            const Vec2 end{previousPlayer.x + (player.x - previousPlayer.x) * activeFraction,
                previousPlayer.y + (player.y - previousPlayer.y) * activeFraction};
            const float endZ = previousPlayerZ + (playerZ - previousPlayerZ) * activeFraction;
            const float hit = hitTime3D(bullet.previous, bullet.pos, bullet.previousZ, bullet.z,
                previousPlayer, end, previousPlayerZ, endZ, PlayerRadius + bullet.radius);
            if (hit >= 0) contacts.push_back({hit * activeFraction, Kind::ShotPlayer, index, -1, bullet.id});
        }
    }
    if (respawn == 0) {
        for (int index = 0; index < static_cast<int>(enemies.size()); ++index) {
            const auto& enemy = enemies[index];
            if (!enemy.alive || enemy.timer < 0) continue;
            const float hit = enemyHitTime(previousPlayer, player, previousPlayerZ, playerZ,
                enemy, enemy.pos, enemy.z, PlayerRadius);
            if (hit >= 0) contacts.push_back({hit, Kind::EnemyPlayer, index, -1, enemy.id});
        }
        for (int index = 0; index < static_cast<int>(obstacles.size()); ++index) {
            const auto& obstacle = obstacles[index];
            if (!obstacle.alive) continue;
            const float hit = hitTime3D(obstacle.previous, obstacle.pos, obstacle.previousZ, obstacle.z,
                previousPlayer, player, previousPlayerZ, playerZ, obstacle.radius + PlayerRadius);
            if (hit >= 0) contacts.push_back({hit, Kind::ObstaclePlayer, index, -1, obstacle.id});
        }
    }
    std::sort(contacts.begin(), contacts.end(), [](const Contact& first, const Contact& second) {
        if (first.time != second.time) return first.time < second.time;
        if (first.id != second.id) return first.id < second.id;
        if (first.kind != second.kind) return first.kind < second.kind;
        return first.first < second.first;
    });
    for (const auto& contact : contacts) {
        if (contact.kind == Kind::ShotEnemy) {
            auto& bullet = bullets[contact.first];
            auto& enemy = enemies[contact.second];
            if (!bullet.alive || !enemy.alive) continue;
            bullet.alive = false;
            ++hits;
            // A double/triple trigger is one attempt. Its unused pellets must
            // not cancel the reward earned by a pellet that actually hit.
            if (bullet.salvo > 0) for (auto& sibling : bullets)
                if (sibling.ally && sibling.salvo == bullet.salvo) sibling.salvoHit = true;
            enemy.hp = std::max(0, enemy.hp - bullet.damage);
            enemy.hitFlash = .12f;
            addEffect(bullet.pos, bullet.z, false, enemy.hp == 0 ? .9f : .35f);
            if (enemy.type == 2) bossHealth = enemy.hp;
            if (enemy.hp != 0) continue;
            enemy.alive = false;
            ++kills;
            ++hitStreak;
            multiplier = std::min(3, 1 + hitStreak / 3);
            int points = enemy.type == 2 ? 2000 : enemy.type == 1 ? 150 : 100;
            if (enemy.phase == EnemyPhase::Diving) points = points * 3 / 2;
            score += points * multiplier;
            bestScore = std::max(bestScore, score);
        } else if (contact.kind == Kind::ShotPlayer) {
            auto& bullet = bullets[contact.first];
            if (!bullet.alive) continue;
            bullet.alive = false;
            damage();
        } else if (contact.kind == Kind::EnemyPlayer) {
            auto& enemy = enemies[contact.first];
            if (!enemy.alive) continue;
            damage();
            if (enemy.type != 2) {
                enemy.alive = false;
                ++kills;
                addEffect(enemy.pos, enemy.z, false, .9f);
            }
        } else {
            auto& obstacle = obstacles[contact.first];
            if (!obstacle.alive) continue;
            obstacle.alive = false;
            damage();
            addEffect(obstacle.pos, obstacle.z, false, 1.4f);
        }
    }
}

void Game3D::update(const Input& input, float dt) {
    if (phase != Phase::Playing || !std::isfinite(dt) || dt <= 0) return;
    time += dt;
    stageTime += dt;
    damageFlash = std::max(0.f, damageFlash - dt);
    for (auto& effect : sparks) effect.age += dt;
    sparks.erase(std::remove_if(sparks.begin(), sparks.end(), [](const Spark& effect) {
        return effect.age >= effect.duration;
    }), sparks.end());
    movePlayer(input, dt);
    if (stage == Stage::Evasion) moveObstacles(dt);
    else moveEnemies(dt);
    for (auto& bullet : bullets) {
        if (!bullet.alive || bullet.ttl <= 0) {
            bullet.alive = false;
            continue;
        }
        bullet.previous = bullet.pos;
        bullet.previousZ = bullet.z;
        const float activeTime = std::min(dt, bullet.ttl);
        bullet.pos.x += bullet.velocityX * activeTime;
        bullet.pos.y += bullet.forwardSpeed() * activeTime;
        bullet.z += bullet.velocityZ * activeTime;
        bullet.ttl -= dt;
    }
    resolveContacts(dt);
    for (const auto& bullet : bullets) {
        if (!bullet.ally || !bullet.alive || !retired(bullet) || bullet.salvoHit) continue;
        const bool pending = bullet.salvo > 0 && std::any_of(bullets.begin(), bullets.end(), [&](const Bullet& sibling) {
            return sibling.ally && sibling.salvo == bullet.salvo && !retired(sibling);
        });
        if (!pending) clearCombo();
    }
    bullets.erase(std::remove_if(bullets.begin(), bullets.end(), retired), bullets.end());
    obstacles.erase(std::remove_if(obstacles.begin(), obstacles.end(), [](const Obstacle& obstacle) {
        return !obstacle.alive || obstacle.pos.y < -6.f;
    }), obstacles.end());
    // Defeat has priority even when a final hit or stage timer expires in this step.
    if (lives == 0) {
        phase = Phase::Defeat;
    } else if (stage == Stage::Evasion && stageTime >= stageDuration) {
        ++wave;
        startWave();
    } else if (stage != Stage::Evasion && remaining() == 0) {
        if (stage == Stage::Boss) phase = Phase::Victory;
        else if (wave < 3) startEvasion();
        else startBoss();
    }
    if (phase != Phase::Playing) bullets.clear();
}
}
