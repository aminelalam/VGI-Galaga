#pragma once
#include <glm/glm.hpp>
#include <cstddef>
#include <vector>

namespace galaga {

// The shader uses this same interleaved layout: position, normal, UV, colour.
struct MeshVertex {
    glm::vec3 position;
    glm::vec3 normal;
    glm::vec2 uv;
    glm::vec4 color;
};

class Mesh3D {
public:
    Mesh3D() = default;
    Mesh3D(const Mesh3D&) = delete;
    Mesh3D& operator=(const Mesh3D&) = delete;
    void upload(const std::vector<MeshVertex>& vertices);
    void draw() const;
    // Inspects actual GPU storage and all four VAO attributes; restores bindings.
    bool verifyGpu() const;
    // Call while the owning OpenGL context is current.
    void release();
    std::size_t vertexCount() const { return count; }
    bool valid() const { return vao != 0 && vbo != 0 && count != 0; }
private:
    unsigned int vao = 0, vbo = 0;
    std::size_t count = 0;
};

class ModelLibrary {
public:
    Mesh3D ships[3];       // Flecha, Delta, Doble Motor; noses point to +Y.
    Mesh3D enemies[3];     // Abeja, Mariposa, Jefe; heads point to -Y.
    Mesh3D shot, enemyShot, particle;
    void initialize();
    void release();
    bool verifyGpu() const;
    unsigned int uploadCount() const { return uploads; }
    std::size_t vertexCount() const;
private:
    unsigned int uploads = 0;
};

}
