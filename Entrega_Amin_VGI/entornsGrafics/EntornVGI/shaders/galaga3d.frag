#version 330 core
in vec3 worldPosition;
in vec3 worldNormal;
in vec4 vertexColor;
in vec2 surfaceMaterial;
in vec3 materialGlow;
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
uniform float environmentFill;
out vec4 outColor;
void main() {
    vec3 n = normalize(worldNormal);
    vec3 lightDirection = normalize(light.position.xyz - worldPosition * light.position.w);
    vec3 viewDirection = normalize(eye - worldPosition);
    vec3 base = vertexColor.rgb * tint.rgb;

    vec3 emissive = material.emission * base + materialGlow * tint.rgb;
    vec3 ambient = material.ambient * base * ambientLight;
    float cosine = max(dot(n, lightDirection), 0.0);
    vec3 diffuse = material.diffuse * base * light.diffuse * cosine;

    vec3 specular = vec3(0.0);
    if (cosine > 0.0) {
        vec3 reflected = reflect(-lightDirection, n);
        float highlight = pow(max(dot(reflected, viewDirection), 0.0), material.shininess * surfaceMaterial.y);
        specular = material.specular * base * light.specular * highlight * surfaceMaterial.x;
    }
    // A soft blue hemisphere and grazing reflection keep dark hulls legible.
    // This explicit secondary illumination is disabled by the GL-6 term tests.
    float sky = 0.5 + 0.5 * n.z;
    float rim = pow(1.0 - max(dot(n, viewDirection), 0.0), 3.0);
    vec3 fill = environmentFill * (base * mix(vec3(0.10,0.12,0.16),vec3(0.27,0.36,0.48),sky)
                 + vec3(0.12,0.17,0.23) * rim * clamp(surfaceMaterial.x * 0.16,0.0,1.0));
    outColor = vec4(clamp(emissive + ambient + diffuse + specular + fill, 0.0, 1.0),
                    vertexColor.a * tint.a);
}
