from OpenGL.GL import *
from OpenGL.GLU import *

import pygame
from pygame import *

import sys
import ctypes

pygame.init()
clock = pygame.time.Clock()

class Window:
    initialized = False
    toInit = []
    def __init__(self, size, flags = 0):
        self.flags = flags
        self.resize(size)

        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)

        gluPerspective(90, (self.width/self.height),0,2)
        glTranslatef(0,0,-1)

        Window.initialized = True
        for f in Window.toInit:
            f()

    def resize(self, size):
        pygame.display.set_mode(size, OPENGL | DOUBLEBUF | self.flags)
        self.width = size[0]
        self.height = size[1]
        self.size = size

    def update(self, fps):
        pygame.display.flip()
        clock.tick(fps)

class Texture:
    def __init__(self, arg):
        if not Window.initialized:
            Window.toInit.append(lambda: self.__init__(arg))
            return
        if type(arg) == str:
            image = pygame.image.load(arg).convert()
        elif type(arg) == tuple:
            self.width, self.height = arg
        elif type(arg) == pygame.Surface:
            image = arg
        
        self.id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.id)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP);

        if type(arg) in (str, pygame.Surface):
            data = pygame.image.tostring(image, "RGBA")
            self.width, self.height = image.get_size()
        else:
            data = b"\0\0\0\xff"*(self.width*self.height)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.width, self.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)

    def __del__(self):
        if sys.meta_path:
            glDeleteTextures(1, [int(self.id)])

    def reload(self, arg):
        if type(arg) == str:
            image = pygame.image.load(arg).convert()
        elif type(arg) == pygame.Surface:
            image = arg

        glBindTexture(GL_TEXTURE_2D, self.id)

        data = pygame.image.tostring(image, "RGBA")
        self.width, self.height = image.get_size()
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.width, self.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)

    def select(self, uniformLocation):
        glActiveTexture(GL_TEXTURE0 + self.id)
        glBindTexture(GL_TEXTURE_2D, self.id)
        glUniform1i(uniformLocation, self.id)

shaderMarkers = {
    "--VERTEX--" : GL_VERTEX_SHADER,
    "--GEOMETRY--" : GL_GEOMETRY_SHADER,
    "--FRAGMENT--" : GL_FRAGMENT_SHADER
}

attributeTypes = {
    GL_FLOAT.numerator : (GL_FLOAT, 1),
    GL_FLOAT_VEC2.numerator : (GL_FLOAT, 2),
    GL_FLOAT_VEC3.numerator : (GL_FLOAT, 3),
    GL_FLOAT_VEC4.numerator : (GL_FLOAT, 4),
    GL_INT.numerator : (GL_INT, 1),
    GL_INT_VEC2.numerator : (GL_INT, 2),
    GL_INT_VEC3.numerator : (GL_INT, 3),
    GL_INT_VEC4.numerator : (GL_INT, 4),
}

class Shader:
    def __init__(self, path, mode):
        if not Window.initialized:
            Window.toInit.append(lambda: self.__init__(path, mode))
            return
        self.mode = mode
        self.id = glCreateProgram()
        file = open(path, "r")
        lines = file.readlines()
        file.close()
        shaderTypes = []
        shaderSources = []
        for line in lines:
            if line[:-1] in shaderMarkers:
                shaderTypes.append(shaderMarkers[line[:-1]])
                shaderSources.append("")
            else:
                shaderSources[-1] += line + "\n"

        shaderIds = []
        for i in range(len(shaderTypes)):
            id = glCreateShader(shaderTypes[i])
            glShaderSource(id, shaderSources[i])
            glCompileShader(id)

            success = glGetShaderiv(id, GL_COMPILE_STATUS)
            if not success:
                print(glGetShaderInfoLog(id).decode())
            
            shaderIds.append(id)
            glAttachShader(self.id, id)

        glLinkProgram(self.id)

        for id in shaderIds:
            glDetachShader(self.id, id)
            glDeleteShader(id)

        success = glGetProgramiv(self.id, GL_LINK_STATUS)
        if not success:
            print(glGetProgramInfoLog(self.id))

        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        attribCount = glGetProgramiv(self.id, GL_ACTIVE_ATTRIBUTES)
        attribInfo = []
        loc = 0
        for i in range(attribCount):
            name, size, typeNumerator = glGetActiveAttrib(self.id, i)
            attribType, count = attributeTypes[typeNumerator]
            attribInfo.append((size*count, attribType, loc))
            loc += size*count*4
        self.vertexSize = loc

        for i in range(attribCount):
            info = attribInfo[i]
            glVertexAttribPointer(i, *info[:2], False, self.vertexSize, ctypes.c_void_p(int(info[2])))
            glEnableVertexAttribArray(i)

        uniformCount = glGetProgramiv(self.id, GL_ACTIVE_UNIFORMS)
        self.uniformTypes = {}
        for i in range(uniformCount):
            name, size, typeNumerator = glGetActiveUniform(self.id, i, 255)
            if type(name) == np.ndarray:
                name = bytes(name[:np.where(name == 0)[0][0]])
            self.uniformTypes[name.decode()] = typeNumerator

    def use(self):
        glUseProgram(self.id)
        glBindVertexArray(self.vao)

uniformFuncs = {
    GL_FLOAT.numerator : glUniform1f,
    GL_FLOAT_VEC2.numerator : glUniform2f,
    GL_FLOAT_VEC3.numerator : glUniform3f,
    GL_FLOAT_VEC4.numerator : glUniform4f,
    GL_INT.numerator : glUniform1i,
    GL_INT_VEC2.numerator : glUniform2i,
    GL_INT_VEC3.numerator : glUniform3i,
    GL_INT_VEC4.numerator : glUniform4i
}

class Mesh:
    def __init__(self, shader, data = None, uniformData = None, textures = None):
        self.shader = shader
        self.data = data or []
        self.uniformData = uniformData or {}
        self.textures = textures or {}

    def render(self):
        self.shader.use()
        for name in self.uniformData:
            assert name in self.shader.uniformTypes, "Error: Uniform \"" + name + "\" not in shader"
            location = glGetUniformLocation(self.shader.id, name)
            uniformFuncs[self.shader.uniformTypes[name]](location, *self.uniformData[name])
        for name in self.textures:
            assert name in self.shader.uniformTypes, "Error: Uniform \"" + name + "\" not in shader"
            location = glGetUniformLocation(self.shader.id, name)
            self.textures[name].select(location)

        byteSize = len(self.data)*4
        glBufferData(GL_ARRAY_BUFFER, byteSize, (GLfloat*len(self.data))(*self.data), GL_STATIC_DRAW)
        count = 1 if self.shader.vertexSize == 0 else byteSize//self.shader.vertexSize
        glDrawArrays(self.shader.mode, 0, count)
