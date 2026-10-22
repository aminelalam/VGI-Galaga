#include "pch.h"
#include "Mesh3D.h"
#include <algorithm>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <type_traits>

namespace galaga {
namespace {
using V2 = glm::vec2;
using V3 = glm::vec3;
using Color = glm::vec4;
using Vertices = std::vector<MeshVertex>;
const Color white(.94f, .96f, 1.f, 1.f), blue(.13f, .37f, .96f, 1.f);
const Color red(.96f, .12f, .18f, 1.f), yellow(1.f, .79f, .12f, 1.f);
const Color green(.26f, .86f, .37f, 1.f), purple(.64f, .24f, .89f, 1.f);
const Color metal(.22f, .28f, .40f, 1.f), dark(.025f, .045f, .09f, 1.f);
const Color glass(.24f, .88f, 1.f, 1.f), flame(1.f, .46f, .12f, 1.f);

void triangle(Vertices& out, V3 a, V3 b, V3 c, Color color) {
    V3 n = glm::cross(b - a, c - a);
    const float length = glm::length(n);
    if (length < 1e-8f) return;
    n /= length;
    for (V3 p : {a, b, c}) out.push_back({p, n, V2(p.x + .5f, p.y + .5f), color});
}

void quad(Vertices& out, V3 a, V3 b, V3 c, V3 d, Color color) {
    triangle(out, a, b, c, color);
    triangle(out, a, c, d, color);
}

// A closed convex hull with a raised inset face, bevel and underside.
// All polygons below are convex; use separate pieces for concave silhouettes.
void hull(Vertices& out, std::vector<V2> polygon, float bottom, float top,
          Color color, float inset = .78f) {
    if (polygon.size() < 3) return;
    float area = 0;
    V2 center(0.f);
    for (std::size_t i = 0; i < polygon.size(); ++i) {
        const V2 a = polygon[i], b = polygon[(i + 1) % polygon.size()];
        area += a.x * b.y - b.x * a.y;
        center += a;
    }
    if (area < 0) std::reverse(polygon.begin(), polygon.end());
    center /= static_cast<float>(polygon.size());
    const float shoulder = bottom + (top - bottom) * .35f;
    const Color edge(color.r * .82f, color.g * .82f, color.b * .82f, color.a);
    for (std::size_t i = 0; i < polygon.size(); ++i) {
        const V2 a = polygon[i], b = polygon[(i + 1) % polygon.size()];
        const V2 ai = center + (a - center) * inset, bi = center + (b - center) * inset;
        triangle(out, V3(center, top), V3(ai, top), V3(bi, top), color);
        quad(out, V3(a, shoulder), V3(b, shoulder), V3(bi, top), V3(ai, top), color);
        quad(out, V3(a, bottom), V3(b, bottom), V3(b, shoulder), V3(a, shoulder), edge);
        triangle(out, V3(center, bottom), V3(b, bottom), V3(a, bottom), edge);
    }
}

void box(Vertices& out, V3 center, V3 half, Color color) {
    const V3 a = center - half, b = center + half;
    quad(out, {a.x,a.y,b.z}, {b.x,a.y,b.z}, {b.x,b.y,b.z}, {a.x,b.y,b.z}, color);
    quad(out, {b.x,a.y,a.z}, {a.x,a.y,a.z}, {a.x,b.y,a.z}, {b.x,b.y,a.z}, color);
    quad(out, {b.x,a.y,b.z}, {b.x,a.y,a.z}, {b.x,b.y,a.z}, {b.x,b.y,b.z}, color);
    quad(out, {a.x,a.y,a.z}, {a.x,a.y,b.z}, {a.x,b.y,b.z}, {a.x,b.y,a.z}, color);
    quad(out, {a.x,b.y,b.z}, {b.x,b.y,b.z}, {b.x,b.y,a.z}, {a.x,b.y,a.z}, color);
    quad(out, {a.x,a.y,a.z}, {b.x,a.y,a.z}, {b.x,a.y,b.z}, {a.x,a.y,b.z}, color);
}

// Six-sided motor, long axis Y. Flat-shaded faces show its real thickness.
void engine(Vertices& out, float x, float rear, float front, float radius, Color color) {
    const float tau = 6.28318530718f;
    for (int i = 0; i < 6; ++i) {
        const float a = tau * i / 6.f, b = tau * (i + 1) / 6.f;
        V3 ar(x + radius * std::cos(a), rear, radius * std::sin(a) - .04f);
        V3 br(x + radius * std::cos(b), rear, radius * std::sin(b) - .04f);
        V3 af(ar.x, front, ar.z), bf(br.x, front, br.z);
        quad(out, ar, af, bf, br, color);
        triangle(out, {x, front, -.04f}, bf, af, color);
        triangle(out, {x, rear, -.04f}, ar, br, flame);
    }
}

void cockpit(Vertices& out, float x, float y, float width, float length, float z) {
    hull(out, {{x-width,y-length}, {x+width,y-length}, {x+width*.65f,y+length},
               {x,y+length*1.22f}, {x-width*.65f,y+length}}, z, z + .065f, glass, .65f);
}

Vertices flecha() {
    Vertices out;
    for (float side : {-1.f, 1.f}) {
        hull(out, {{side*.09f,.34f}, {side*.58f,-.34f}, {side*.49f,-.46f},
                   {side*.08f,-.28f}}, -.075f, .075f, white);
        hull(out, {{side*.31f,-.12f}, {side*.49f,-.32f}, {side*.45f,-.37f},
                   {side*.27f,-.19f}}, .077f, .095f, red, .88f);
        engine(out, side * .29f, -.51f, -.29f, .074f, metal);
    }
    hull(out, {{0.f,.72f}, {-.135f,-.45f}, {.135f,-.45f}}, -.13f, .17f, blue, .76f);
    hull(out, {{0.f,.70f}, {-.035f,.43f}, {.035f,.43f}}, .06f, .19f, white);
    cockpit(out, 0, .16f, .065f, .16f, .18f);
    return out;
}

Vertices delta() {
    Vertices out;
    hull(out, {{0.f,.70f}, {-.59f,-.45f}, {.59f,-.45f}}, -.10f, .095f, red, .84f);
    for (float side : {-1.f, 1.f}) {
        hull(out, {{side*.22f,-.10f}, {side*.47f,-.36f}, {side*.20f,-.31f}}, .10f, .13f, white);
        engine(out, side * .23f, -.51f, -.33f, .07f, metal);
    }
    hull(out, {{0.f,.63f}, {-.10f,-.43f}, {.10f,-.43f}}, .05f, .19f, red, .75f);
    cockpit(out, 0.f, .10f, .06f, .17f, .19f);
    return out;
}

Vertices twinEngine() {
    Vertices out;
    box(out, {0.f,-.12f,-.08f}, {.39f,.065f,.06f}, metal);
    for (float side : {-1.f, 1.f}) {
        const float x = side * .40f;
        hull(out, {{x-.12f,-.48f}, {x+.12f,-.48f}, {x+.12f,.39f},
                   {x+.055f,.56f}, {x-.055f,.56f}, {x-.12f,.39f}}, -.12f, .14f, green);
        hull(out, {{x-.035f,-.34f}, {x+.035f,-.34f}, {x+.035f,.29f},
                   {x-.035f,.29f}}, .145f, .157f, white, .9f);
        engine(out, x, -.59f, -.42f, .085f, metal);
    }
    hull(out, {{-.15f,-.35f}, {.15f,-.35f}, {.14f,.40f}, {0.f,.58f}, {-.14f,.40f}},
         -.13f, .18f, white);
    hull(out, {{-.085f,-.34f}, {.085f,-.34f}, {.075f,.36f}, {0.f,.53f}, {-.075f,.36f}},
         .15f, .19f, green);
    cockpit(out, 0.f, .09f, .06f, .15f, .19f);
    return out;
}

void eyes(Vertices& out, float separation, float y, float z) {
    for (float side : {-1.f, 1.f}) {
        box(out, {side*separation,y,z}, {.046f,.052f,.017f}, dark);
        box(out, {side*separation,y-.015f,z+.02f}, {.018f,.023f,.01f}, white);
    }
}

Vertices bee() {
    Vertices out;
    for (float side : {-1.f, 1.f}) {
        hull(out, {{side*.10f,.20f}, {side*.43f,.37f}, {side*.54f,.12f},
                   {side*.30f,-.22f}, {side*.13f,-.15f}}, -.09f, .10f, blue);
        hull(out, {{side*.30f,.18f}, {side*.45f,.29f}, {side*.50f,.12f},
                   {side*.34f,-.02f}}, .10f, .135f, yellow);
        hull(out, {{side*.12f,-.17f}, {side*.27f,-.37f}, {side*.23f,-.43f},
                   {side*.08f,-.29f}}, -.02f, .085f, red);
    }
    hull(out, {{0.f,-.47f}, {.18f,-.27f}, {.13f,.31f}, {0.f,.43f},
               {-.13f,.31f}, {-.18f,-.27f}}, -.15f, .18f, yellow);
    box(out, {0.f,.12f,.185f}, {.105f,.045f,.017f}, blue);
    box(out, {0.f,.29f,.165f}, {.072f,.034f,.016f}, blue);
    eyes(out, .077f, -.23f, .195f);
    return out;
}

Vertices butterfly() {
    Vertices out;
    for (float side : {-1.f, 1.f}) {
        hull(out, {{side*.10f,.18f}, {side*.40f,.46f}, {side*.53f,.30f},
                   {side*.49f,-.17f}, {side*.17f,-.31f}}, -.10f, .12f, red);
        hull(out, {{side*.25f,.03f}, {side*.43f,.28f}, {side*.43f,-.08f},
                   {side*.29f,-.17f}}, .12f, .15f, white);
        hull(out, {{side*.08f,-.21f}, {side*.21f,-.45f}, {side*.14f,-.49f},
                   {side*.04f,-.29f}}, -.04f, .06f, blue);
    }
    hull(out, {{0.f,-.43f}, {.16f,-.23f}, {.10f,.32f}, {0.f,.43f},
               {-.10f,.32f}, {-.16f,-.23f}}, -.15f, .19f, white);
    hull(out, {{-.13f,-.17f}, {.13f,-.17f}, {.10f,.04f}, {-.10f,.04f}}, .19f, .205f, red);
    eyes(out, .067f, -.24f, .215f);
    return out;
}

Vertices boss() {
    Vertices out;
    for (float side : {-1.f, 1.f}) {
        hull(out, {{side*.12f,.15f}, {side*.42f,.43f}, {side*.56f,.28f},
                   {side*.52f,-.19f}, {side*.20f,-.35f}}, -.10f, .14f, purple);
        hull(out, {{side*.29f,-.13f}, {side*.48f,-.08f}, {side*.45f,.21f},
                   {side*.29f,.10f}}, .14f, .19f, green);
        hull(out, {{side*.09f,-.23f}, {side*.24f,-.46f}, {side*.14f,-.50f},
                   {side*.05f,-.31f}}, -.01f, .10f, yellow);
    }
    hull(out, {{-.19f,-.24f}, {0.f,-.45f}, {.19f,-.24f}, {.18f,.23f},
               {0.f,.43f}, {-.18f,.23f}}, -.16f, .22f, green);
    hull(out, {{0.f,.35f}, {-.10f,.07f}, {.10f,.07f}}, .22f, .24f, yellow);
    eyes(out, .085f, -.19f, .235f);
    return out;
}

Vertices projectile(bool hostile) {
    Vertices out;
    const Color color = hostile ? red : yellow;
    hull(out, {{0.f,.25f}, {-.045f,.14f}, {-.045f,-.21f}, {0.f,-.25f},
               {.045f,-.21f}, {.045f,.14f}}, -.04f, .04f, color, .7f);
    box(out, {0.f,0.f,.043f}, {.016f,.17f,.012f}, white);
    return out;
}
}

void Mesh3D::upload(const std::vector<MeshVertex>& vertices) {
    static_assert(std::is_standard_layout<MeshVertex>::value, "Vertex offsets must be stable");
    if (vertices.empty() || vertices.size() % 3 != 0 ||
        vertices.size() > static_cast<std::size_t>((std::numeric_limits<GLsizei>::max)()))
        throw std::runtime_error("Malla 3D sin triangulos validos.");
    for (const MeshVertex& v : vertices) {
        for (int k = 0; k < 3; ++k)
            if (!std::isfinite(v.position[k]) || !std::isfinite(v.normal[k]))
                throw std::runtime_error("La malla 3D contiene valores no finitos.");
        if (glm::dot(v.normal,v.normal) < .9f)
            throw std::runtime_error("La malla 3D contiene una normal degenerada.");
    }
    release();
    glGenVertexArrays(1, &vao);
    glGenBuffers(1, &vbo);
    glBindVertexArray(vao);
    glBindBuffer(GL_ARRAY_BUFFER, vbo);
    glBufferData(GL_ARRAY_BUFFER, static_cast<GLsizeiptr>(vertices.size() * sizeof(MeshVertex)),
                 vertices.data(), GL_STATIC_DRAW);
    glEnableVertexAttribArray(0);
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, sizeof(MeshVertex),
                          reinterpret_cast<void*>(offsetof(MeshVertex,position)));
    glEnableVertexAttribArray(1);
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, sizeof(MeshVertex),
                          reinterpret_cast<void*>(offsetof(MeshVertex,normal)));
    glEnableVertexAttribArray(2);
    glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, sizeof(MeshVertex),
                          reinterpret_cast<void*>(offsetof(MeshVertex,uv)));
    glEnableVertexAttribArray(3);
    glVertexAttribPointer(3, 4, GL_FLOAT, GL_FALSE, sizeof(MeshVertex),
                          reinterpret_cast<void*>(offsetof(MeshVertex,color)));
    glBindVertexArray(0);
    glBindBuffer(GL_ARRAY_BUFFER,0);
    if (!vao || !vbo || glGetError() != GL_NO_ERROR) {
        release();
        throw std::runtime_error("No se ha podido cargar una malla 3D en VAO/VBO.");
    }
    count = vertices.size();
}

void Mesh3D::draw() const {
    if (!valid()) return;
    glBindVertexArray(vao);
    glDrawArrays(GL_TRIANGLES, 0, static_cast<GLsizei>(count));
}

bool Mesh3D::verifyGpu() const {
    if (!valid() || !glIsVertexArray || !glIsBuffer ||
        glIsVertexArray(vao) != GL_TRUE || glIsBuffer(vbo) != GL_TRUE) return false;

    GLint previousVao = 0, previousBuffer = 0;
    glGetIntegerv(GL_VERTEX_ARRAY_BINDING, &previousVao);
    glGetIntegerv(GL_ARRAY_BUFFER_BINDING, &previousBuffer);
    glBindVertexArray(vao);
    glBindBuffer(GL_ARRAY_BUFFER, vbo);

    GLint bytes = 0, usage = 0;
    glGetBufferParameteriv(GL_ARRAY_BUFFER, GL_BUFFER_SIZE, &bytes);
    glGetBufferParameteriv(GL_ARRAY_BUFFER, GL_BUFFER_USAGE, &usage);
    bool correct = bytes > 0 && static_cast<std::size_t>(bytes) == count * sizeof(MeshVertex)
                   && usage == GL_STATIC_DRAW;
    const GLint sizes[] = {3, 3, 2, 4};
    const std::size_t offsets[] = {offsetof(MeshVertex, position), offsetof(MeshVertex, normal),
                                  offsetof(MeshVertex, uv), offsetof(MeshVertex, color)};
    for (GLuint index = 0; index < 4; ++index) {
        GLint enabled = 0, size = 0, type = 0, binding = 0, stride = 0, normalized = 0;
        void* offset = nullptr;
        glGetVertexAttribiv(index, GL_VERTEX_ATTRIB_ARRAY_ENABLED, &enabled);
        glGetVertexAttribiv(index, GL_VERTEX_ATTRIB_ARRAY_SIZE, &size);
        glGetVertexAttribiv(index, GL_VERTEX_ATTRIB_ARRAY_TYPE, &type);
        glGetVertexAttribiv(index, GL_VERTEX_ATTRIB_ARRAY_BUFFER_BINDING, &binding);
        glGetVertexAttribiv(index, GL_VERTEX_ATTRIB_ARRAY_STRIDE, &stride);
        glGetVertexAttribiv(index, GL_VERTEX_ATTRIB_ARRAY_NORMALIZED, &normalized);
        glGetVertexAttribPointerv(index, GL_VERTEX_ATTRIB_ARRAY_POINTER, &offset);
        if (enabled != GL_TRUE || size != sizes[index] || type != GL_FLOAT ||
            static_cast<GLuint>(binding) != vbo || stride != sizeof(MeshVertex) ||
            normalized != GL_FALSE || reinterpret_cast<std::size_t>(offset) != offsets[index])
            correct = false;
    }

    glBindVertexArray(static_cast<GLuint>(previousVao));
    glBindBuffer(GL_ARRAY_BUFFER, static_cast<GLuint>(previousBuffer));
    const GLenum error = glGetError();
    return correct && error == GL_NO_ERROR;
}

void Mesh3D::release() {
    if (vao) glDeleteVertexArrays(1, &vao);
    if (vbo) glDeleteBuffers(1, &vbo);
    vao = vbo = 0;
    count = 0;
}

void ModelLibrary::initialize() {
    if (uploads == 9) return;
    release();
    try {
        auto upload = [this](Mesh3D& mesh, const Vertices& vertices) {
            mesh.upload(vertices);
            ++uploads;
        };
        upload(ships[0],flecha());
        upload(ships[1],delta());
        upload(ships[2],twinEngine());
        upload(enemies[0],bee());
        upload(enemies[1],butterfly());
        upload(enemies[2],boss());
        upload(shot,projectile(false));
        upload(enemyShot,projectile(true));
        Vertices cube;
        box(cube,V3(0.f),V3(.5f),white);
        upload(particle,cube);
    } catch (...) {
        release();
        throw;
    }
}

void ModelLibrary::release() {
    for (auto& mesh : ships) mesh.release();
    for (auto& mesh : enemies) mesh.release();
    shot.release();
    enemyShot.release();
    particle.release();
    uploads = 0;
}

bool ModelLibrary::verifyGpu() const {
    bool correct = uploads == 9;
    // Check every mesh even if an earlier one fails, including its GL errors.
    for (const auto& mesh : ships) if (!mesh.verifyGpu()) correct = false;
    for (const auto& mesh : enemies) if (!mesh.verifyGpu()) correct = false;
    if (!shot.verifyGpu()) correct = false;
    if (!enemyShot.verifyGpu()) correct = false;
    if (!particle.verifyGpu()) correct = false;
    const GLenum error = glGetError();
    return correct && error == GL_NO_ERROR;
}

std::size_t ModelLibrary::vertexCount() const {
    std::size_t total = shot.vertexCount() + enemyShot.vertexCount() + particle.vertexCount();
    for (const auto& mesh : ships) total += mesh.vertexCount();
    for (const auto& mesh : enemies) total += mesh.vertexCount();
    return total;
}
}
