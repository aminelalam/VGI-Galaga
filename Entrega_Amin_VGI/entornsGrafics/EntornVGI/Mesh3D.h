#pragma once
#include <glm/glm.hpp>
#include <cstddef>
#include <filesystem>
#include <vector>

namespace galaga {

// Interleaved position, normal, UV, colour and per-material Phong coefficients.
struct MeshVertex {
    glm::vec3 position;
    glm::vec3 normal;
    glm::vec2 uv;
    glm::vec4 color;
    glm::vec2 surface{1.f, 1.f}; // Specular gain and shininess relative to the GL-6 material.
    glm::vec3 emission{0.f}; // MTL Ke: small engine cores and physical instruments.
};

class Mesh3D {
public:
    Mesh3D() = default;
    Mesh3D(const Mesh3D&) = delete;
    Mesh3D& operator=(const Mesh3D&) = delete;
    void upload(const std::vector<MeshVertex>& vertices);
    void loadObj(const std::filesystem::path& path);
    void draw() const;
    // Inspects actual GPU storage and all six VAO attributes; restores bindings.
    bool verifyGpu() const;
    // Call while the owning OpenGL context is current.
    void release();
    std::size_t vertexCount() const { return count; }
    bool valid() const { return vao != 0 && vbo != 0 && ebo != 0 && count != 0; }
    glm::vec3 minimum() const { return lower; }
    glm::vec3 maximum() const { return upper; }
private:
    unsigned int vao = 0, vbo = 0, ebo = 0;
    std::size_t count = 0, storedVertices = 0;
    glm::vec3 lower{0}, upper{0};
};

class ModelLibrary {
public:
    static constexpr unsigned int MeshCount = 17;
    Mesh3D ships[3];       // Flecha, Delta, Doble Motor; noses point to +Y.
    Mesh3D enemies[3];     // Abeja, Escarabajo, Jefe; heads point to -Y.
    Mesh3D distantEnemies[2]; // Closed lower-detail versions for small distant targets.
    Mesh3D scenery;
    Mesh3D asteroid, cockpit, stars;
    Mesh3D shot, enemyShot, particle;
    Mesh3D missile, exhaust;
    void initialize(const std::filesystem::path& folder);
    void release();
    bool verifyGpu() const;
    unsigned int uploadCount() const { return uploads; }
    std::size_t vertexCount() const;
private:
    unsigned int uploads = 0;
};

}
