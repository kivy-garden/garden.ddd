from object_renderer import ObjectRenderer

from kivy.core.window import Window  # noqa
from kivy.lang import Builder
from kivy.properties import NumericProperty, BooleanProperty
from kivy.clock import Clock
from kivy.animation import Animation
from math import cos, sin, pi


def dist(p1, p2):
    return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** .5


class MultitouchCamera(object):
    def __init__(self, **kwargs):
        super(MultitouchCamera, self).__init__(**kwargs)
        self.touches = []
        self.touches_center = []
        self.touches_dist = 0
        Clock.schedule_interval(self.update_cam, 0)

    def on_touch_down(self, touch):
        if super(MultitouchCamera, self).on_touch_move(touch):
            return True

        if self.collide_point(*touch.pos):
            self.touches.append(touch)
            touch.grab(self)
            if len(self.touches) > 1:
                self.touches_center = self.get_center()
                self.touches_dist = self.get_dist(self.touches_center)

    def update_cam(self, dt):
        if not self.touches:
            return

        elif len(self.touches) == 1:
            self.cam_translation[0] += self.touches[0].dx / 100.
            self.cam_translation[1] += self.touches[0].dy / 100.

        else:
            c = self.get_center()
            d = self.get_dist(c)

            self.cam_rotation[1] += (c[0] - self.touches_center[0]) / 5.
            self.cam_rotation[0] -= (c[1] - self.touches_center[1]) / 5.
            self.cam_translation[2] += min(.5, max(-.5, (d - self.touches_dist) / 10.))

            self.touches_center = c
            self.touches_dist = d
        return True

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            self.touches.remove(touch)
            self.touches_center = self.get_center()
            self.touches_dist = self.get_dist(self.touches_center)
        else:
            return super(MultitouchCamera, self).on_touch_move(touch)

    def get_center(self):
        return (
            sum(t.x for t in self.touches) / float(len(self.touches)),
            sum(t.y for t in self.touches) / float(len(self.touches))
        ) if self.touches else self.center

    def get_dist(self, center):
        return (sum(
            dist(t.pos, center)
            for t in self.touches
        ) / float(len(self.touches))) if self.touches else 0


class MultitouchCenteredCamera(MultitouchCamera):
    def setup_scene(self):
        super(MultitouchCenteredCamera, self).setup_scene()
        self.cam_rot_x.origin = (0, 0, 0)
        self.cam_rot_x.origin = (0, 0, 0)
        self.cam_rot_x.origin = (0, 0, 0)

    def update_cam(self, dt):
        if not self.touches:
            return

        elif len(self.touches) == 1:
            self.cam_rotation[1] += self.touches[0].dx / 5.
            self.cam_rotation[0] -= self.touches[0].dy / 5.

        else:
            c = self.get_center()
            d = self.get_dist(c)

            self.obj_scale += (d - self.touches_dist) / 100.
            self.touches_center = c
            self.touches_dist = d
        return True


class BaseView(ObjectRenderer):
    time = NumericProperty(0)
    light_radius = NumericProperty(20)
    move_light = BooleanProperty(True)

    def reset(self, *args):
        Animation(
            cam_rotation=(20, 0, 0),
            cam_translation=(0, -3, -8),
            t='in_out_quad',
            d=2).start(self)

    def update_lights(self, dt):
        if not self.move_light:
            return
        self.time += dt
        self.time %= 2 * pi
        for i in range(self.nb_lights):
            a = self.time + i * 2 * pi / self.nb_lights
            self.light_sources[i] = [
                cos(a) * self.light_radius, 5, sin(a) * self.light_radius, 1.0]

        for k in self.light_sources.keys():
            if k >= self.nb_lights:
                del(self.light_sources[k])

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            Clock.unschedule(self.reset)
        return super(View, self).on_touch_down(touch)

    def on_touch_up(self, touch):
        if len(self.touches) == 1 and touch in self.touches:
            Clock.unschedule(self.reset)
            Clock.schedule_once(self.reset, 3)

        return super(View, self).on_touch_up(touch)


class View(MultitouchCamera, BaseView):
    pass


class CenteredView(MultitouchCenteredCamera, BaseView):
    min_scale = NumericProperty(0)
    max_scale = NumericProperty(100)

    def on_obj_scale(self, *args):
        self.obj_scale = max(
            self.min_scale, min(
                self.max_scale,
                self.obj_scale))
        super(CenteredView, self).on_obj_scale(*args)


KV = '''
#:import listdir os.listdir

FloatLayout:
    View:
        canvas.before:
            Color:
                rgba: .6, .6, .6, 1
            Rectangle:
                pos: self.pos
                size: self.size

        id: rendering
        scene: 'data/3d/%s' % scene.text
        obj_scale: scale.value if scale.value > 0 else 1
        display_all: True
        ambiant: ambiant.value
        diffuse: diffuse.value
        specular: specular.value
        on_parent: self.reset()
        mode: modechoice.text
        light_radius: light_radius.value
        nb_lights: int(nb_lights.value)
        move_light: move_light.active

    GridLayout:
        size_hint: 1, None
        rows: 2
        Slider:
            min: 0
            max: 10
            id: scale
            step: .1
            value: rendering.obj_scale

        Spinner:
            id: scene
            text: 'colorplane.obj'
            values:
                sorted([x for x in listdir('data/3d/')
                if x.lower().endswith(('.3ds', '.obj'))])

        Slider:
            min: 0
            max: 50
            step: 1
            value: 10
            id: light_radius

        Slider:
            min: 0
            max: 50
            step: 1
            value: 4
            id: nb_lights

        Spinner:
            text: rendering.mode
            values: 'triangles', 'points', 'lines'
            id: modechoice

        Slider:
            id: ambiant
            min: 0
            max: 1
            value: .01
            step: .01

        Slider:
            id: diffuse
            min: 0
            max: 1
            value: 1
            step: .01

        Slider:
            id: specular
            min: 0
            max: 1
            value: 1
            step: .01

        CheckBox:
            id: move_light
            active: True

        Label:
            size_hint_y: .1
            text: 'scale %s' % scale.value

        Label:
            size_hint_y: .1
            text: 'scene'

        Label:
            size_hint_y: .1
            text: 'light_radius %s' % light_radius.value
        Label:
            size_hint_y: .1
            text: 'nb_lights %s' % nb_lights.value

        Label:
            text: 'mode'
        Label:
            size_hint_y: .1
            text: 'ambiant %s' % ambiant.value
        Label:
            size_hint_y: .1
            text: 'diffuse %s' % diffuse.value
        Label:
            size_hint_y: .1
            text: 'specular %s' % specular.value

        Label:
            text: 'move lights'
'''


if __name__ == '__main__':
    from kivy.app import App

    class App3D(App):
        def build(self):
            root = Builder.load_string(KV)
            Clock.schedule_interval(root.ids.rendering.update_lights, 0)
            return root

    App3D().run()
