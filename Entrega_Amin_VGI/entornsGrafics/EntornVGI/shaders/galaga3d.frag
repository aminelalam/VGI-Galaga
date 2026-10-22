#version 330 core
in vec3 worldPosition;
in vec3 worldNormal;
in vec4 vertexColor;
uniform vec3 eye;
uniform vec4 tint;
uniform float emission;
out vec4 outColor;
void main() {
    vec3 n = normalize(worldNormal);
    vec3 light = normalize(vec3(-0.45, 0.7, 1.1));
    vec3 viewDirection = normalize(eye - worldPosition);
    float diffuse = max(dot(n, light), 0.0);
    float specular = pow(max(dot(n, normalize(light + viewDirection)), 0.0), 32.0);
    vec3 base = vertexColor.rgb * tint.rgb;
    vec3 lit = base * (0.37 + 0.63 * diffuse) + vec3(0.16 * specular);
    outColor = vec4(mix(lit, base, clamp(emission, 0.0, 1.0)), vertexColor.a * tint.a);
}
