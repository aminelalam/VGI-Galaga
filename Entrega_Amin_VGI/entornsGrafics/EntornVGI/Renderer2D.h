#pragma once
#include "Game3D.h"
#include <filesystem>
#include <string>
#include <vector>
namespace galaga {
// Screen-space HUD; all ships and projectiles are solid meshes in Renderer3D.
class Renderer2D {
public:
    void initialize();
    void release();
    void background(const Game3D&,int width,int height);
    void overlay(const Game3D&,int width,int height);
    static std::filesystem::path executableDirectory();
private:
    struct Vertex {float x,y,u,v,r,g,b,a;};
    struct Color {float r,g,b,a=1;};
    struct Batch {unsigned int texture;int first,count;};
    unsigned int program=0,vao=0,vbo=0,white=0,font=0;
    std::vector<Vertex> vertices;
    std::vector<Batch> batches;
    int pendingStart=0;
    void begin(int width,int height);
    void finish();
    void flush(unsigned int texture=0);
    void quad(float x,float y,float w,float h,Color,float u1=0,float v1=0,float u2=1,float v2=1);
    void border(float x,float y,float w,float h,Color);
    void text(const std::string&,float x,float y,int height,Color,bool center=false);
};
}
