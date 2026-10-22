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
    unsigned int uploadCount() const {return models.uploadCount();}
    unsigned int drawCount() const {return draws;}
    // Same geometry and shader, different camera: verifies real solid models.
    void modelGallery(int width,int height,float angle);
private:
    Renderer2D hud;
    ModelLibrary models;
    unsigned int program=0,draws=0;
    int modelLocation=-1,viewLocation=-1,projectionLocation=-1,normalLocation=-1,tintLocation=-1,eyeLocation=-1,emissionLocation=-1;
    glm::mat4 view{1},projection{1};
    glm::vec3 eye{0,-4.5f,22};
    void begin3D();
    void camera(bool menu);
    void instance(const Mesh3D&,const glm::mat4&,glm::vec4 tint=glm::vec4(1),float emission=0);
};
}
