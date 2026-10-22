#version 330 core
// Same locations as the course GL-3 examples and MeshVertex's interleaved VBO.
layout(location=0) in vec3 position;
layout(location=1) in vec3 normal;
layout(location=2) in vec2 uv;
layout(location=3) in vec4 color;
uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
uniform mat3 normalMatrix;
out vec3 worldPosition;
out vec3 worldNormal;
out vec4 vertexColor;
void main() {
    vec4 world = model * vec4(position, 1.0);
    worldPosition = world.xyz;
    worldNormal = normalMatrix * normal;
    vertexColor = color;
    gl_Position = projection * view * world;
}
