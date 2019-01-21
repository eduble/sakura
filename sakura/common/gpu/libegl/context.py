#!/usr/bin/env python
import OpenGL.EGL as egl
from ctypes import pointer
from sakura.common.gpu.libegl import devices, egl_convert_to_int_array
from sakura.common.tools import TransactionMixin

class EGLContext(TransactionMixin):
    CURRENT = None
    @property
    def is_current(self):
        return EGLContext.CURRENT == self
    def initialize(self, width, height):
        for device in devices.probe():
            if not self.initialize_on_device(device, width, height):
                continue
            return True
        return False
    def initialize_on_device(self, device, width, height):
        print("selected: " + device.name)
        # step 1
        if device.initialize():
            self.add_rollback_cb(lambda: device.release())
        else:
            self.rollback(); return False
        # step 2
        egl_dpy = device.get_egl_display()
        if egl_dpy != egl.EGL_NO_DISPLAY:
            self.add_rollback_cb(lambda: egl.eglTerminate(egl_dpy))
            self.egl_dpy = egl_dpy
        else:
            self.rollback(); return False
        # step 3
        major, minor = egl.EGLint(), egl.EGLint()
        if not egl.eglInitialize(egl_dpy, pointer(major), pointer(minor)):
            self.rollback(); return False
        print("EGL version %d.%d" % (major.value, minor.value))
        # step 4
        egl_config = self.get_config(egl_dpy, device.compatible_surface_type())
        if egl_config is None:
            self.rollback(); return False
        # step 5
        egl_surface = device.create_surface(egl_dpy, egl_config)
        if egl_surface.initialize(width, height):
            self.add_rollback_cb(lambda: egl_surface.release())
            self.egl_surface = egl_surface
        else:
            self.rollback(); return False
        # step 6
        egl_context = self.get_context(egl_dpy, egl_config)
        if egl_context is not None:
            self.add_rollback_cb(lambda: egl.eglDestroyContext(egl_dpy, egl_context))
            self.egl_context = egl_context
        else:
            self.rollback(); return False
        # device seems to be working
        return True
    def get_config(self, egl_dpy, surface_type):
        egl_config_attribs = {
            egl.EGL_RED_SIZE:           8,
            egl.EGL_GREEN_SIZE:         8,
            egl.EGL_BLUE_SIZE:          8,
            egl.EGL_ALPHA_SIZE:         8,
            egl.EGL_DEPTH_SIZE:         egl.EGL_DONT_CARE,
            egl.EGL_STENCIL_SIZE:       egl.EGL_DONT_CARE,
            egl.EGL_RENDERABLE_TYPE:    egl.EGL_OPENGL_BIT,
            egl.EGL_SURFACE_TYPE:       surface_type,
        }
        egl_config_attribs = egl_convert_to_int_array(egl_config_attribs)
        egl_config = egl.EGLConfig()
        num_configs = egl.EGLint()
        if not egl.eglChooseConfig(egl_dpy, egl_config_attribs,
                        pointer(egl_config), 1, pointer(num_configs)):
            return None
        if num_configs.value == 0:
            return None
        return egl_config
    def get_context(self, egl_dpy, egl_config):
        if not egl.eglBindAPI(egl.EGL_OPENGL_API):
            return None
        egl_context = egl.eglCreateContext(egl_dpy, egl_config, egl.EGL_NO_CONTEXT, None)
        if egl_context == egl.EGL_NO_CONTEXT:
            return None
        return egl_context
    def release(self):
        if self.is_current:
            self.make_surface_not_current()
            EGLContext.CURRENT = None
        self.rollback()
    def resize(self, width, height):
        if self.is_current:
            self.make_surface_not_current()
        self.egl_surface.resize(width, height)
        if self.is_current:
            self.make_surface_current()
    def make_current(self):
        if self.is_current:
            return True     # nothing to do
        if EGLContext.CURRENT is not None:
            EGLContext.CURRENT.make_surface_not_current()
        res = self.make_surface_current()
        EGLContext.CURRENT = self
        return res
    def make_surface_current(self):
        return self.egl_surface.make_current(self.egl_context)
    def make_surface_not_current(self):
        egl.eglMakeCurrent(self.egl_dpy, egl.EGL_NO_SURFACE, egl.EGL_NO_SURFACE, egl.EGL_NO_CONTEXT)