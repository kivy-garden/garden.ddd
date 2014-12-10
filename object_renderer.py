from kivy.uix.widget import Widget
from kivy.resources import resource_find
try:
    from assimpobjloader import AssimpObjLoader as ObjFileLoader
except Exception as e:
    print("Error trying to import assimp: %s, using simple objloader" %
          e.message)
    from objloader import ObjFileLoader

from kivy.uix.image import Image
from kivy.graphics.fbo import Fbo
from kivy.graphics import (
    Callback, PushMatrix, PopMatrix, Rotate, Translate, Scale,
    Rectangle, Color, Mesh, UpdateNormalMatrix, Canvas)
from kivy.graphics.transformation import Matrix
from kivy.graphics.opengl import (
    glEnable, glDisable, GL_DEPTH_TEST)
from kivy.properties import (
    StringProperty, ListProperty, ObjectProperty, NumericProperty,
    BooleanProperty, DictProperty)
from os.path import join, dirname


class ObjectRenderer(Widget):
    scene = StringProperty('')
    obj_id = StringProperty('')
    obj_translation = ListProperty([0, 0, 0])
    obj_rotation = ListProperty([0, 0, 0])
    obj_scale = NumericProperty(1)
    obj_texture = StringProperty('')
    texture = ObjectProperty(None, allownone=True)
    cam_translation = ListProperty([0, 0, 0])
    cam_rotation = ListProperty([0, 0, 0])
    display_all = BooleanProperty(False)
    light_sources = DictProperty()
    ambiant = NumericProperty(.5)
    diffuse = NumericProperty(.5)
    specular = NumericProperty(.5)
    mode = StringProperty('triangles')

    def __init__(self, **kwargs):
        self.canvas = Canvas()
        with self.canvas:
            self.fbo = Fbo(size=self.size,
                           with_depthbuffer=True,
                           compute_normal_mat=True,
                           clear_color=(0., 0., 0., 0.))

            self.viewport = Rectangle(size=self.size, pos=self.pos)

        self.fbo.shader.source = resource_find(
            join(dirname(__file__), 'simple.glsl'))
        super(ObjectRenderer, self).__init__(**kwargs)

    def on_obj_rotation(self, *args):
        self.obj_rot_x.angle = self.obj_rotation[0]
        self.obj_rot_y.angle = self.obj_rotation[1]
        self.obj_rot_z.angle = self.obj_rotation[2]

    def on_cam_rotation(self, *args):
        self.cam_rot_x.angle = self.cam_rotation[0]
        self.cam_rot_y.angle = self.cam_rotation[1]
        self.cam_rot_z.angle = self.cam_rotation[2]

    def on_obj_translation(self, *args):
        self.obj_translate.xyz = self.cam_translation

    def on_cam_translation(self, *args):
        self.cam_translate.xyz = self.cam_translation

    def on_obj_scale(self, *args):
        self.scale.xyz = [self.obj_scale, ] * 3

    def on_display_all(self, *args):
        self.setup_canvas()

    def on_light_sources(self, *args):
        self.fbo['light_sources'] = [
            ls[:] for ls in self.light_sources.values()]
        self.fbo['nb_lights'] = len(self.light_sources)

    def on_ambiant(self, *args):
        self.fbo['ambiant'] = self.ambiant

    def on_diffuse(self, *args):
        self.fbo['diffuse'] = self.diffuse

    def on_specular(self, *args):
        self.fbo['specular'] = self.specular

    def on_mode(self, *args):
        self.setup_canvas()

    def setup_canvas(self, *args):
        if not (self.scene and self.obj_id or self.display_all):
            return

        print 'setting up the scene'
        with self.fbo:
            self.fbo['ambiant'] = self.ambiant
            self.fbo['diffuse'] = self.diffuse
            self.fbo['specular'] = self.specular
            self.cb = Callback(self.setup_gl_context)
            PushMatrix()
            self.setup_scene()
            PopMatrix()
            self.cb = Callback(self.reset_gl_context)

    def on_scene(self, instance, value):
        print "loading scene %s" % value
        self._scene = ObjFileLoader(resource_find(value))
        self.setup_canvas()

    def on_obj_id(self, *args):
        self.setup_canvas()

    def on_size(self, instance, value):
        self.fbo.size = value
        self.viewport.texture = self.fbo.texture
        self.viewport.size = value
        self.update_glsl()

    def on_pos(self, instance, value):
        self.viewport.pos = value

    def on_texture(self, instance, value):
        self.viewport.texture = value

    def setup_gl_context(self, *args):
        glEnable(GL_DEPTH_TEST)
        self.fbo.clear_buffer()

    def reset_gl_context(self, *args):
        glDisable(GL_DEPTH_TEST)

    def update_glsl(self, *args):
        asp = self.width / float(self.height)
        proj = Matrix().view_clip(-asp, asp, -1, 1, 1, 100, 1)
        self.fbo['projection_mat'] = proj

    def setup_scene(self):
        Color(1, 1, 1, 0)

        PushMatrix()
        self.cam_translate = Translate(self.cam_translation)
        # Rotate(0, 1, 0, 0)
        self.cam_rot_x = Rotate(self.cam_rotation[0], 1, 0, 0)
        self.cam_rot_y = Rotate(self.cam_rotation[1], 0, 1, 0)
        self.cam_rot_z = Rotate(self.cam_rotation[2], 0, 0, 1)
        self.scale = Scale(self.obj_scale)
        UpdateNormalMatrix()
        if self.display_all:
            for i in self._scene.objects:
                self.draw_object(i)
        else:
            self.draw_object(self.obj_id)
        PopMatrix()

    def draw_object(self, obj_id):
        m = self._scene.objects[obj_id]
        self.obj_rot_x = Rotate(self.obj_rotation[0], 1, 0, 0)
        self.obj_rot_y = Rotate(self.obj_rotation[1], 0, 1, 0)
        self.obj_rot_z = Rotate(self.obj_rotation[2], 0, 0, 1)
        self.obj_translate = Translate(xyz=self.obj_translation)

        if len(m.indices) > 2 ** 16:
            print '%s too big! %s indices' % (obj_id, len(m.indices))

        if m.texture:
            print "loading texture %s " % m.texture
            img = Image(source=resource_find(
                join(dirname(self.scene), m.texture)))
            texture = img.texture
            if texture:
                texture.wrap = 'repeat'
        else:
            texture = None

        vertex_lenght = sum(x[1] for x in m.vertex_format)
        if len(m.vertices) % vertex_lenght:
            print(
                (
                    'warning: vertices lenght (%s)'
                    'is not a multiple of vertex_format lenght(%s)'
                )
                % (len(m.vertices), vertex_lenght))
        Mesh(
            vertices=m.vertices,
            indices=m.indices,
            fmt=m.vertex_format,
            texture=texture,
            mode=self.mode)
