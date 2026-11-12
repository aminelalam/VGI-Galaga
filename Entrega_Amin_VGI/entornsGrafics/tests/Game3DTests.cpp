#include "../EntornVGI/Game3D.h"
#include <algorithm>
#include <cmath>
#include <iostream>
#include <stdexcept>

using namespace galaga;
namespace {
int checks = 0;
void check(bool condition, const char* name) {
    if (!condition) throw std::runtime_error(name);
    ++checks;
    std::cout << "PASS " << name << '\n';
}
void ticks(Game3D& game, int count, Input input = {}) {
    for (int i = 0; i < count; ++i) game.update(input);
}
Game3D fixture() {
    Game3D game;
    game.reset();
    game.enemies.resize(1);
    auto& enemy = game.enemies.front();
    enemy.id = 0;
    enemy.phase = EnemyPhase::Formation;
    enemy.slot = enemy.pos = enemy.previous = {0, 7};
    enemy.slotZ = enemy.z = enemy.previousZ = 0;
    enemy.timer = 0;
    return game;
}

// Infer the missing position from the observed wall, not the spawn sequence.
Vec2 openingAt(const Game3D& game, float wallY) {
    std::vector<float> xs, zs;
    for (const auto& obstacle : game.obstacles) {
        if (!obstacle.alive || std::abs(obstacle.pos.y - wallY) > .1f) continue;
        if (std::none_of(xs.begin(), xs.end(), [&](float x) { return std::abs(x - obstacle.pos.x) < .01f; })) xs.push_back(obstacle.pos.x);
        if (std::none_of(zs.begin(), zs.end(), [&](float z) { return std::abs(z - obstacle.z) < .01f; })) zs.push_back(obstacle.z);
    }
    Vec2 target{game.player.x, game.playerZ};
    float bestDistance = 1e9f;
    for (float z : zs) {
        for (float x : xs) {
            bool free = true;
            for (const auto& obstacle : game.obstacles) {
                if (!obstacle.alive || std::abs(obstacle.pos.y - wallY) > .1f) continue;
                const float dx = x - obstacle.pos.x, dz = z - obstacle.z;
                const float radius = obstacle.radius + Game3D::PlayerRadius + .15f;
                if (dx * dx + dz * dz < radius * radius) free = false;
            }
            const float dx = x - game.player.x, dz = z - game.playerZ;
            const float distance = dx * dx + dz * dz;
            if (free && distance < bestDistance) {
                bestDistance = distance;
                target = {x, z};
            }
        }
    }
    return target;
}

Input pilot(const Game3D& game) {
    float targetX = game.player.x, targetZ = game.playerZ;
    if (game.stage == Stage::Evasion) {
        float nearestY = 1e9f;
        for (const auto& obstacle : game.obstacles)
            if (obstacle.alive && obstacle.pos.y > game.player.y - obstacle.radius - Game3D::PlayerRadius)
                nearestY = std::min(nearestY, obstacle.pos.y);
        const Vec2 opening = openingAt(game, nearestY);
        targetX = opening.x;
        targetZ = opening.y;
    } else {
        float closest = 1e9f;
        for (const auto& enemy : game.enemies) {
            if (!enemy.alive || enemy.timer < 0 || enemy.phase == EnemyPhase::Entering || enemy.phase == EnemyPhase::Returning) continue;
            const float flight = std::max(0.f, (enemy.pos.y - game.player.y) / Game3D::PlayerShotSpeed);
            const float x = enemy.pos.x + enemy.velocityX * flight;
            const float z = enemy.z + enemy.velocityZ * flight;
            const float dx = x - game.player.x, dz = z - game.playerZ;
            float distance = dx * dx + dz * dz;
            if (enemy.phase == EnemyPhase::Diving) distance += 30;
            if (distance < closest) {
                closest = distance;
                targetX = std::clamp(x, -Game3D::PlayerLimitX, Game3D::PlayerLimitX);
                targetZ = std::clamp(z, Game3D::PlayerMinZ, Game3D::PlayerMaxZ);
            }
        }
        for (const auto& bullet : game.bullets) {
            if (bullet.ally || !bullet.alive || bullet.forwardSpeed() >= 0) continue;
            const float flight = (game.player.y - bullet.pos.y) / bullet.forwardSpeed();
            if (flight < 0 || flight > .75f) continue;
            const float x = bullet.pos.x + bullet.velocityX * flight;
            const float z = bullet.z + bullet.velocityZ * flight;
            const float dx = game.player.x - x, dz = game.playerZ - z;
            if (dx * dx + dz * dz < 1.1f) {
                targetZ = game.playerZ < .7f ? game.playerZ + 1.8f : game.playerZ - 1.8f;
                targetX = game.player.x < 0 ? game.player.x + 1.5f : game.player.x - 1.5f;
            }
        }
    }
    return {game.player.x > targetX + .07f, game.player.x < targetX - .07f,
            game.stage != Stage::Evasion, game.playerZ < targetZ - .07f,
            game.playerZ > targetZ + .07f, game.stage == Stage::Boss};
}

void checkEvasion(Game3D game) {
    std::vector<Obstacle> allRocks;
    int lastWallId = -1, openings = 0;
    Vec2 previousGap;
    float longestGapMove = 0;
    game.invulnerable = 0;
    const int lives = game.lives;
    for (int tick = 0; tick < 60 * 16 && game.stage == Stage::Evasion && game.phase == Phase::Playing; ++tick) {
        const int oldLives = game.lives;
        game.update(pilot(game));
        if (game.lives < oldLives) std::cerr << "Evasion damage at " << game.stageTime << " player " << game.player.x << ',' << game.playerZ << '\n';
        if (game.obstacles.empty() || game.obstacles.back().id <= lastWallId) continue;
        lastWallId = game.obstacles.back().id;
        const float wallY = game.obstacles.back().pos.y;
        const Vec2 gap = openingAt(game, wallY);
        check(gap.x >= -Game3D::PlayerLimitX && gap.x <= Game3D::PlayerLimitX &&
            gap.y >= Game3D::PlayerMinZ && gap.y <= Game3D::PlayerMaxZ,
            "asteroid opening remains inside the controllable flight area");
        if (openings > 0) longestGapMove = std::max(longestGapMove, std::hypot(gap.x - previousGap.x, gap.y - previousGap.y));
        previousGap = gap;
        ++openings;
        for (const auto& obstacle : game.obstacles)
            if (std::abs(obstacle.pos.y - wallY) < .1f) allRocks.push_back(obstacle);
    }
    check(openings >= 4 && longestGapMove < 6.f * 1.5f,
        "successive openings leave travel time after the preceding wall clears");
    check(game.stage == Stage::Combat && game.lives == lives,
        "observed openings can be flown with ordinary controls without damage or invulnerability");
    bool allThreatened = true;
    for (int column = 0; column <= 154; ++column) for (int row = 0; row <= 78; ++row) {
        const float x = -Game3D::PlayerLimitX + 2 * Game3D::PlayerLimitX * column / 154;
        const float z = Game3D::PlayerMinZ + (Game3D::PlayerMaxZ - Game3D::PlayerMinZ) * row / 78;
        allThreatened &= std::any_of(allRocks.begin(), allRocks.end(), [=](const Obstacle& obstacle) {
            return std::hypot(x - obstacle.pos.x, z - obstacle.z) < obstacle.radius + Game3D::PlayerRadius;
        });
    }
    check(allThreatened, "no permanent safe spot across 12245 sampled positions including flight boundaries");
}
}

int main() {
    try {
        Game3D game;
        game.reset();
        check(game.wave == 1 && game.stage == Stage::Combat && game.remaining() == 12 && game.lives == 3, "fresh campaign starts with 12 enemies and three lives");
        ticks(game, 30, {false, true, false});
        check(std::abs(game.player.x - 3.f) < .001f, "lateral speed is six units per second");
        game.reset();
        ticks(game, 30, {false, false, false, true});
        check(std::abs(game.playerZ - 3.f) < .001f && game.player.y == -4, "vertical control changes world Z");
        game.reset();
        ticks(game, 30, {false, true, false, true});
        check(std::abs(std::sqrt(game.player.x * game.player.x + game.playerZ * game.playerZ) - 3.f) < .001f, "diagonal movement is normalized");
        ticks(game, 120, {false, true, false, true});
        check(game.player.x == Game3D::PlayerLimitX && game.playerZ == Game3D::PlayerMaxZ, "upper right movement limits");
        ticks(game, 240, {true, false, false, false, true});
        check(game.player.x == -Game3D::PlayerLimitX && game.playerZ == Game3D::PlayerMinZ, "lower left movement limits");
        game.reset();
        ticks(game, 60, {true, true, false, true, true});
        check(game.player.x == 0 && game.playerZ == 0, "opposite controls cancel on both axes");

        game.reset();
        game.invulnerable = 999;
        bool seen[5]{};
        float maximumStep = 0, minimumZ = 100, maximumZ = -100;
        for (int tick = 0; tick < 60 * 28; ++tick) {
            game.update({});
            for (const auto& enemy : game.enemies) {
                if (!enemy.alive || enemy.timer < 0) continue;
                seen[static_cast<int>(enemy.phase)] = true;
                const float dx = enemy.pos.x - enemy.previous.x;
                const float dy = enemy.pos.y - enemy.previous.y;
                const float dz = enemy.z - enemy.previousZ;
                maximumStep = std::max(maximumStep, std::sqrt(dx * dx + dy * dy + dz * dz));
                minimumZ = std::min(minimumZ, enemy.z);
                maximumZ = std::max(maximumZ, enemy.z);
            }
        }
        check(std::all_of(std::begin(seen), std::end(seen), [](bool value) { return value; }), "enemies enter form warn dive and return");
        check(maximumStep < .9f && maximumZ - minimumZ > 5.f, "enemy paths remain continuous in XYZ");

        game = fixture();
        game.playerZ = 2.f;
        game.update({false, false, true});
        check(game.bullets.front().velocityX == 0 && game.bullets.front().velocityZ == 0 && game.bullets.front().z == 2.f, "normal shots follow the player's actual height");
        ticks(game, 30);
        check(game.kills == 0, "aligned X at the wrong height does not kill");
        game = fixture();
        ticks(game, 35, {false, false, true});
        check(game.kills == 1 && game.stage == Stage::Evasion, "manual XYZ alignment hits and advances the stage");
        game = fixture();
        game.bullets = {{9000, true, true, {.84f, 7}, {.84f, 7}}};
        game.update({});
        check(game.kills == 1, "shots touching the visible wing width register a hit");
        game = fixture();
        game.bullets = {{9000, true, true, {1.05f, 7}, {1.05f, 7}}};
        game.update({});
        check(game.kills == 0, "shots visibly beyond the wing collider remain misses");
        check(Game3D::hitTime3D({0, -2}, {0, 2}, 2, 2, {0, 0}, {0, 0}, 0, 0, .46f) < 0, "projected overlap alone is not collision");
        check(Game3D::hitTime3D({0, 0}, {0, 0}, -2, 2, {0, 0}, {0, 0}, 0, 0, .46f) >= 0, "fast vertical paths use swept contact");

        game = fixture();
        game.selectWeapon(1);
        game.update({false, false, true});
        check(game.bullets.size() == 2 && std::abs(game.bullets[1].pos.x - game.bullets[0].pos.x - .56f) < .001f, "double shot uses two separate parallel barrels");
        check(game.bullets[0].velocityX == 0 && game.bullets[1].velocityX == 0, "parallel shots do not converge artificially");
        game = fixture();
        game.selectWeapon(2);
        game.update({false, false, true});
        check(game.bullets.size() == 3 && game.bullets[0].velocityX < 0 && game.bullets[1].velocityX == 0 && game.bullets[2].velocityX > 0, "triple shot produces a spatial fan");
        for (const auto& bullet : game.bullets) {
            const float speed = std::sqrt(bullet.velocityX * bullet.velocityX + bullet.velocityY * bullet.velocityY);
            check(std::abs(speed - Game3D::PlayerShotSpeed) < .001f, "fan projectiles have constant resultant speed");
        }
        game = fixture();
        game.player.x = .8f;
        game.selectWeapon(3);
        game.update({false, false, true});
        const auto missile = game.bullets.front();
        check(missile.kind == 3 && missile.damage == 4 && missile.velocityX < 0, "missile fixes a three-dimensional launch direction");
        game.player.x = -5;
        game.update({});
        check(game.bullets.front().velocityX == missile.velocityX, "missile trajectory stays fixed after launch");
        game = fixture();
        game.update({false, false, false, false, false, true});
        check(game.shots == 1 && game.specialCooldown == 4.f, "special missile starts its cooldown");
        ticks(game, 60, {false, false, false, false, false, true});
        check(game.shots == 1, "held special cannot bypass cooldown");

        game = fixture();
        game.bullets = {{100, true, true, {0, 6.9f}, {0, 6.9f}}, {101, true, true, {0, 6.9f}, {0, 6.9f}}};
        game.update({});
        check(game.kills == 1 && game.score == 100, "simultaneous lethal shots award one kill");
        game = fixture();
        game.enemies.resize(6, game.enemies.front());
        for (int index = 0; index < 6; ++index) game.enemies[index].id = index;
        const std::vector<Bullet> volley{
            {1000, true, true, {0, 7}, {0, 7}},
            {1001, true, true, {0, 7}, {0, 7}},
            {1002, true, true, {0, 7}, {0, 7}}
        };
        game.bullets = volley;
        game.update({});
        check(game.hitStreak == 3 && game.multiplier == 2 && game.score == 400, "third consecutive kill applies double points");
        game.bullets = volley;
        game.update({});
        check(game.hitStreak == 6 && game.multiplier == 3 && game.score == 1100, "sixth consecutive kill applies triple points once");
        game.bullets = {{1003, true, true, {0, 54}, {0, 54}, .001f}};
        game.update({});
        check(game.hitStreak == 0 && game.multiplier == 1 && game.score == 1100, "a missed shot resets the combo without removing earned points");

        // Reproduce a successful spread shot whose unused pellets leave the scene.
        for (int weapon : {1, 2}) {
            game = fixture();
            game.enemies.front().slot.y = game.enemies.front().pos.y = game.enemies.front().previous.y = 18.f;
            Enemy distant = game.enemies.front();
            distant.id = 1;
            distant.slot = distant.pos = distant.previous = {6, 30};
            distant.slotZ = distant.z = distant.previousZ = 4;
            game.enemies.push_back(distant);
            game.hitStreak = 2;
            game.selectWeapon(weapon);
            game.update({false, false, true});
            ticks(game, 115);
            check(game.kills == 1 && game.hitStreak == 3 && game.multiplier == 2,
                "a successful double or triple salvo keeps its combo after the other pellets miss");
            game.playerZ = game.previousPlayerZ = -3;
            game.update({false, false, true});
            ticks(game, 115);
            check(game.hitStreak == 0 && game.multiplier == 1,
                "an entirely missed later salvo still resets the combo");
        }
        game = fixture();
        game.bullets = {{100, true, true, {0, 7}, {0, 7}, 0}};
        game.update({});
        check(game.kills == 0, "expired projectiles cannot hit");
        game = fixture();
        game.enemies.front().hp = game.enemies.front().maxHp = 2;
        game.update({false, false, true});
        ticks(game, 25);
        check(game.hits == 1 && game.kills == 0 && game.enemies.front().hp == 1,
            "a nonlethal armored hit is reported to audio independently of kills");
        game.reset();
        game.invulnerable = 0;
        Bullet expiring;
        expiring.id = 9000;
        expiring.ally = false;
        expiring.pos = expiring.previous = {.59f, -4};
        expiring.radius = .17f;
        expiring.ttl = .001f;
        game.bullets = {expiring};
        game.update({false, true});
        check(game.lives == 3, "a projectile cannot collide with movement after its expiry inside a step");
        game.reset();
        game.invulnerable = 0;
        game.bullets = {{100, false, true, game.player, game.player}, {101, false, true, game.player, game.player}};
        game.update({});
        check(game.lives == 2 && game.respawn > 0, "simultaneous hostile hits cost one life");
        check(game.damageFlash > 0, "damage starts visible feedback even in cockpit view");
        game.pause();
        const float pausedFlash = game.damageFlash;
        ticks(game, 30);
        check(game.damageFlash == pausedFlash, "pause freezes damage feedback with gameplay");
        game.pause();
        ticks(game, 45);
        check(game.player.x == 0 && game.playerZ == 0 && game.invulnerable > 0, "respawn resets both axes with protection");
        check(game.damageFlash == 0, "damage flash clears before protected flight resumes");

        game.reset();
        for (auto& enemy : game.enemies) enemy.alive = false;
        game.update({});
        check(game.stage == Stage::Evasion && game.stageDuration == 12.f, "first combat leads to a timed cockpit evasion");
        checkEvasion(game);
        Game3D camper = game;
        camper.player.x = Game3D::PlayerLimitX;
        camper.previousPlayer = camper.player;
        while (camper.stage == Stage::Evasion && camper.phase == Phase::Playing) camper.update({});
        check(camper.lives < 3, "remaining still at the right boundary no longer bypasses evasion");
        ticks(game, 65);
        check(game.obstacles.size() == 14, "asteroid wall leaves one clear three-dimensional opening");
        const float obstacleY = game.obstacles.front().pos.y;
        game.update({});
        check(game.obstacles.front().pos.y < obstacleY && game.obstacles.front().z == game.obstacles.front().previousZ, "obstacles approach along real world depth");
        const float time = game.time, stageTime = game.stageTime;
        const auto obstacles = game.obstacles;
        game.pause();
        ticks(game, 120, {false, true, true, true});
        check(game.time == time && game.stageTime == stageTime && game.obstacles.front().pos.y == obstacles.front().pos.y, "pause freezes stage camera clock and hazards");
        game.pause();
        game.invulnerable = 999;
        while (game.stage == Stage::Evasion) game.update(pilot(game));
        check(game.wave == 2 && game.remaining() == 15 && game.obstacles.empty(), "second wave starts with clean transient state");
        for (auto& enemy : game.enemies) enemy.alive = false;
        game.update({});
        check(game.stage == Stage::Evasion && game.stageDuration == 15.f, "second evasion is a distinct timed phase");
        checkEvasion(game);
        while (game.stage == Stage::Evasion) game.update(pilot(game));
        check(game.wave == 3 && game.remaining() == 18, "third wave has eighteen enemies");
        for (auto& enemy : game.enemies) enemy.alive = false;
        game.update({});
        check(game.stage == Stage::Boss && game.bossHealth == 36 && game.remaining() == 1, "clearing three waves introduces the boss");
        Game3D acceleratingBoss = game;
        ticks(acceleratingBoss, 240);
        acceleratingBoss.bossHealth = acceleratingBoss.enemies.front().hp = acceleratingBoss.bossMaxHealth / 2;
        acceleratingBoss.update({});
        const Enemy& movingBoss = acceleratingBoss.enemies.front();
        const float bossDx = movingBoss.pos.x - movingBoss.previous.x;
        const float bossDy = movingBoss.pos.y - movingBoss.previous.y;
        const float bossDz = movingBoss.z - movingBoss.previousZ;
        check(std::sqrt(bossDx * bossDx + bossDy * bossDy + bossDz * bossDz) < .1f, "boss accelerates below half health without teleporting");
        auto& boss = game.enemies.front();
        boss.phase = EnemyPhase::Formation;
        boss.timer = 0;
        boss.pos = boss.previous = {0, 24};
        boss.z = boss.previousZ = 1.1f;
        Game3D aboveBoss = game;
        Bullet highShot;
        highShot.id = 8998;
        highShot.pos = highShot.previous = {0, 21};
        highShot.z = highShot.previousZ = boss.z + 2.5f;
        aboveBoss.bullets = {highShot};
        ticks(aboveBoss, 20);
        check(aboveBoss.bossHealth == aboveBoss.bossMaxHealth, "a shot 2.5 units above the boss passes without hitting empty space");
        Game3D wingBoss = game;
        Bullet wingShot;
        wingShot.id = 8999;
        wingShot.pos = wingShot.previous = {2.9f, 22};
        wingShot.z = wingShot.previousZ = boss.z;
        wingBoss.bullets = {wingShot};
        ticks(wingBoss, 12);
        check(wingBoss.bossHealth == wingBoss.bossMaxHealth - 1, "the boss ellipsoid still includes shots near the outer wing");
        Bullet shot;
        shot.id = 9000;
        shot.pos = shot.previous = {0, 24};
        shot.z = shot.previousZ = 1.1f;
        shot.damage = 4;
        game.bullets = {shot};
        game.update({});
        check(game.bossHealth == 32 && game.kills == 0 && game.enemies.front().hitFlash > 0, "boss takes damage over multiple hits with feedback");
        game.enemies.front().hp = game.bossHealth = 1;
        game.lives = 1;
        game.invulnerable = game.respawn = 0;
        shot.pos = shot.previous = game.enemies.front().pos;
        shot.z = shot.previousZ = game.enemies.front().z;
        Bullet hostile;
        hostile.id = 9001;
        hostile.ally = false;
        hostile.pos = hostile.previous = game.player;
        hostile.z = hostile.previousZ = game.playerZ;
        game.bullets = {shot, hostile};
        game.update({});
        check(game.phase == Phase::Defeat && game.bossHealth == 0, "defeat takes priority over the simultaneous final boss kill");

        game.reset();
        game.selectedShip = 2;
        game.selectWeapon(2);
        game.score = 400;
        game.reset();
        check(game.selectedShip == 2 && game.weapon == Weapon::Triple && game.bestScore >= 400 && game.score == 0, "restart preserves ship weapon and record");
        game.returnToMenu();
        game.selectShip(1);
        check(game.phase == Phase::Menu && game.selectedShip == 1 && game.obstacles.empty(), "menu returns to a clean selection state");

        game.reset();
        game.selectWeapon(2);
        float minHeight = game.playerZ, maxHeight = game.playerZ;
        bool stages[3]{};
        for (int tick = 0; tick < 60 * 300 && game.phase == Phase::Playing; ++tick) {
            stages[static_cast<int>(game.stage)] = true;
            if (game.stage == Stage::Boss) game.selectWeapon(1);
            game.update(pilot(game));
            minHeight = std::min(minHeight, game.playerZ);
            maxHeight = std::max(maxHeight, game.playerZ);
        }
        std::cout << "PILOT lives=" << game.lives << " kills=" << game.kills << " wave=" << game.wave << " stage=" << static_cast<int>(game.stage) << " seconds=" << game.time << '\n';
        check(game.phase == Phase::Victory && game.bossHealth == 0 && game.wave == 3, "pilot completes the entire campaign through ordinary inputs");
        check(stages[0] && stages[1] && stages[2] && maxHeight - minHeight > 5.f, "campaign exercises combat evasion boss and vertical control");
        game.reset();
        ticks(game, 60 * 90);
        check(game.phase == Phase::Defeat && game.lives == 0, "idle player loses naturally");
        std::cout << checks << " checks passed\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "FAIL " << error.what() << '\n';
        return 1;
    }
}
