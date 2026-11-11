#include "pch.h"
#include "Mesh3D.h"
#include <algorithm>
#include <cmath>
#include <fstream>
#include <limits>
#include <locale>
#include <map>
#include <sstream>
#include <stdexcept>
#include <type_traits>

namespace galaga {
namespace {
using V2 = glm::vec2;
using V3 = glm::vec3;
using Color = glm::vec4;
using Vertices = std::vector<MeshVertex>;
const Color white(.94f, .96f, 1.f, 1.f);

std::map<std::string, Color> readMaterials(const std::filesystem::path& path) {
    std::ifstream file(path);
    if (!file) throw std::runtime_error("Falta el material " + path.filename().string());
    std::map<std::string, Color> colors;
    std::string line, name;
    while (std::getline(file, line)) {
        std::istringstream row(line);
        row.imbue(std::locale::classic());
        std::string tag;
        row >> tag;
        if (tag == "newmtl") {
            std::getline(row >> std::ws, name);
            if (name.empty()) throw std::runtime_error("Material sin nombre en " + path.filename().string());
            colors[name] = white;
        } else if (tag == "Kd") {
            Color color(1.f);
            if (name.empty() || !(row >> color.r >> color.g >> color.b))
                throw std::runtime_error("Color Kd invalido en " + path.filename().string());
            for (int channel = 0; channel < 3; ++channel)
                if (!std::isfinite(color[channel]) || color[channel] < 0 || color[channel] > 1)
                    throw std::runtime_error("Color Kd fuera de rango en " + path.filename().string());
            colors[name] = color;
        }
    }
    return colors;
}

// OBJ indices are one-based; negative indices refer to the last defined entries.
std::size_t objIndex(int index, std::size_t count) {
    const auto resolved = index > 0 ? static_cast<long long>(index) - 1
                                  : static_cast<long long>(count) + index;
    if (index == 0 || resolved < 0 || static_cast<std::size_t>(resolved) >= count)
        throw std::runtime_error("Indice OBJ fuera de rango.");
    return static_cast<std::size_t>(resolved);
}

Vertices readObj(const std::filesystem::path& path) {
    std::ifstream file(path);
    if (!file) throw std::runtime_error("Falta la malla " + path.filename().string());
    std::vector<V3> positions, normals;
    std::vector<V2> coordinates;
    std::map<std::string, Color> materials;
    Color color = white;
    Vertices vertices;
    std::string line;
    std::size_t lineNumber = 0;
    try {
        while (std::getline(file, line)) {
            ++lineNumber;
            std::istringstream row(line);
            row.imbue(std::locale::classic());
            std::string tag;
            row >> tag;
            if (tag == "v" || tag == "vn") {
                V3 value;
                if (!(row >> value.x >> value.y >> value.z))
                    throw std::runtime_error("Se necesitan tres coordenadas.");
                if (tag == "vn") {
                    const float length = glm::length(value);
                    if (!std::isfinite(length) || length < 1e-8f)
                        throw std::runtime_error("Normal OBJ degenerada.");
                    normals.push_back(value / length);
                } else {
                    positions.push_back(value);
                }
            } else if (tag == "vt") {
                V2 uv;
                if (!(row >> uv.x >> uv.y)) throw std::runtime_error("UV incompletas.");
                coordinates.push_back(uv);
            } else if (tag == "mtllib") {
                std::string name;
                std::getline(row >> std::ws, name);
                const std::filesystem::path materialFile(name);
                if (name.empty() || materialFile.has_parent_path())
                    throw std::runtime_error("El MTL debe estar junto al OBJ.");
                const auto loaded = readMaterials(path.parent_path() / materialFile);
                materials.insert(loaded.begin(), loaded.end());
            } else if (tag == "usemtl") {
                std::string name;
                std::getline(row >> std::ws, name);
                const auto found = materials.find(name);
                if (found == materials.end()) throw std::runtime_error("Material desconocido " + name);
                color = found->second;
            } else if (tag == "f") {
                for (int corner = 0; corner < 3; ++corner) {
                    std::string faceVertex;
                    if (!(row >> faceVertex)) throw std::runtime_error("Cara OBJ incompleta.");
                    std::istringstream indices(faceVertex);
                    int position = 0, uv = 0, normal = 0;
                    char firstSlash = 0, secondSlash = 0;
                    if (!(indices >> position >> firstSlash >> uv >> secondSlash >> normal) ||
                        firstSlash != '/' || secondSlash != '/' || indices.peek() != EOF)
                        throw std::runtime_error("Exporta cada vertice como posicion/UV/normal.");
                    vertices.push_back({positions.at(objIndex(position, positions.size())),
                                        normals.at(objIndex(normal, normals.size())),
                                        coordinates.at(objIndex(uv, coordinates.size())), color});
                }
                std::string extra;
                if (row >> extra && extra.front() != '#')
                    throw std::runtime_error("Triangula las caras antes de exportar el OBJ.");
            }
        }
    } catch (const std::exception& error) {
        throw std::runtime_error(path.filename().string() + " linea " + std::to_string(lineNumber) + ": " + error.what());
    }
    return vertices;
}

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

Vertices projectile(bool hostile) {
    Vertices out;
    const Color color = hostile ? Color(1.f,.22f,.08f,1.f) : Color(.25f,.85f,1.f,1.f);
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
        for (int k = 0; k < 2; ++k)
            if (!std::isfinite(v.uv[k])) throw std::runtime_error("La malla tiene UV no finitas.");
        for (int k = 0; k < 4; ++k)
            if (!std::isfinite(v.color[k])) throw std::runtime_error("La malla tiene un color no finito.");
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
    lower = upper = vertices.front().position;
    for (const auto& vertex : vertices) {
        lower = glm::min(lower, vertex.position);
        upper = glm::max(upper, vertex.position);
    }
}

void Mesh3D::loadObj(const std::filesystem::path& path) {
    upload(readObj(path));
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
    lower = upper = V3(0.f);
}

void ModelLibrary::initialize(const std::filesystem::path& folder) {
    if (uploads == 10) return;
    release();
    try {
        auto upload = [this](Mesh3D& mesh, const Vertices& vertices) {
            mesh.upload(vertices);
            ++uploads;
        };
        auto load = [this, &folder](Mesh3D& mesh, const wchar_t* filename) {
            mesh.loadObj(folder / filename);
            ++uploads;
        };
        load(ships[0],L"nave_flecha.obj");
        load(ships[1],L"nave_delta.obj");
        load(ships[2],L"nave_doble_motor.obj");
        load(enemies[0],L"enemigo_abeja.obj");
        load(enemies[1],L"enemigo_escarabajo.obj");
        load(enemies[2],L"jefe_acorazado.obj");
        load(scenery,L"escenario_orbital.obj");
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
    scenery.release();
    shot.release();
    enemyShot.release();
    particle.release();
    uploads = 0;
}

bool ModelLibrary::verifyGpu() const {
    bool correct = uploads == 10;
    // Check every mesh even if an earlier one fails, including its GL errors.
    for (const auto& mesh : ships) if (!mesh.verifyGpu()) correct = false;
    for (const auto& mesh : enemies) if (!mesh.verifyGpu()) correct = false;
    if (!scenery.verifyGpu()) correct = false;
    if (!shot.verifyGpu()) correct = false;
    if (!enemyShot.verifyGpu()) correct = false;
    if (!particle.verifyGpu()) correct = false;
    const GLenum error = glGetError();
    return correct && error == GL_NO_ERROR;
}

std::size_t ModelLibrary::vertexCount() const {
    std::size_t total = shot.vertexCount() + enemyShot.vertexCount() + particle.vertexCount() + scenery.vertexCount();
    for (const auto& mesh : ships) total += mesh.vertexCount();
    for (const auto& mesh : enemies) total += mesh.vertexCount();
    return total;
}
}
