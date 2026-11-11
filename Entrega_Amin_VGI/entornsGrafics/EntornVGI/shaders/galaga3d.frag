#version 330 core
in vec3 worldPosition;
in vec3 worldNormal;
in vec4 vertexColor;
in vec2 surfaceMaterial;
uniform vec3 eye;
uniform vec4 tint;

// GL-6, pp. 18, 38 and 49-52. Lighting is evaluated in world coordinates.
struct Light {
    vec4 position; // w=0 for the directional light used by this scene.
    vec3 diffuse;
    vec3 specular;
};
struct Material {
    vec3 emission;
    vec3 ambient;
    vec3 diffuse;
    vec3 specular;
    float shininess;
};
uniform Light light;
uniform Material material;
uniform vec3 ambientLight;
out vec4 outColor;
void main() {
    vec3 n = normalize(worldNormal);
    vec3 lightDirection = normalize(light.position.xyz - worldPosition * light.position.w);
    vec3 viewDirection = normalize(eye - worldPosition);
    vec3 base = vertexColor.rgb * tint.rgb;

    vec3 emissive = material.emission * base;
    vec3 ambient = material.ambient * base * ambientLight;
    float cosine = max(dot(n, lightDirection), 0.0);
    vec3 diffuse = material.diffuse * base * light.diffuse * cosine;

    vec3 specular = vec3(0.0);
    if (cosine > 0.0) {
        vec3 reflected = reflect(-lightDirection, n);
        float highlight = pow(max(dot(reflected, viewDirection), 0.0), material.shininess * surfaceMaterial.y);
        specular = material.specular * base * light.specular * highlight * surfaceMaterial.x;
    }
    outColor = vec4(clamp(emissive + ambient + diffuse + specular, 0.0, 1.0),
                    vertexColor.a * tint.a);
}
