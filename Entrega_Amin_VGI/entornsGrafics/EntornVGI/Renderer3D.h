#pragma once
#include "Mesh3D.h"
#include "Renderer2D.h"
#include <ostream>
namespace galaga {
class Renderer3D {
public:
    void initialize();
    void release();
    void draw(const Game3D&,int width,int height);
    bool modern() const { return program!=0; }
    bool verifyGpu(std::ostream&) const;
    bool verifyFraming(const Game3D&,std::ostream&);
    bool verifyLighting(std::ostream&);
    unsigned int uploadCount() const {return models.uploadCount();}
    unsigned int drawCount() const {return draws;}
    // Same geometry and shader, different camera: verifies real solid models.
    void modelGallery(int width,int height,float angle);
private:
    Renderer2D hud;
    ModelLibrary models;
    unsigned int program=0,draws=0;
    int modelLocation=-1,viewLocation=-1,projectionLocation=-1,normalLocation=-1,tintLocation=-1,eyeLocation=-1;
    int emissionLocation=-1,ambientLocation=-1,diffuseLocation=-1,specularLocation=-1,shininessLocation=-1;
    int lightPositionLocation=-1,lightDiffuseLocation=-1,lightSpecularLocation=-1,ambientLightLocation=-1;
    glm::mat4 view{1},projection{1};
    glm::vec3 eye{0,-4.5f,22};
    void begin3D();
    void camera(bool menu,float playerX=0);
    void instance(const Mesh3D&,const glm::mat4&,glm::vec4 tint=glm::vec4(1),float emission=0);
};
}
