import os
from os.path import dirname, join


class MeshData(object):
    def __init__(self, **kwargs):
        self.name = kwargs.get("name")
        self.vertex_format = [
            ('v_pos', 3, 'float'),
            ('v_normal', 3, 'float'),
            ('v_tc0', 2, 'float'),
            ('v_ambient', 3, 'float'),
            ('v_diffuse', 3, 'float'),
            ('v_specular', 3, 'float'),
            ('v_specular_coeff', 1, 'float'),
            ('v_transparency', 1, 'float'),
            ]
        self.vertices = []
        self.indices = []
        # Default basic material of mesh object
        self.diffuse_color = (1.0, 1.0, 1.0)
        self.ambient_color = (1.0, 1.0, 1.0)
        self.specular_color = (1.0, 1.0, 1.0)
        self.specular_coefficent = 16.0
        self.transparency = 1.0
        self.texture = None

    def set_materials(self, mtl_dict):
        self.diffuse_color = mtl_dict.get('Kd', self.diffuse_color)
        self.diffuse_color = [float(v) for v in self.diffuse_color]
        self.ambient_color = mtl_dict.get('Ka', self.ambient_color)
        self.ambient_color = [float(v) for v in self.ambient_color]
        self.specular_color = mtl_dict.get('Ks', self.specular_color)
        self.specular_color = [float(v) for v in self.specular_color]
        self.specular_coefficent = float(
            mtl_dict.get('Ns', self.specular_coefficent))
        transparency = mtl_dict.get('d')
        if not transparency:
            transparency = 1.0 - float(mtl_dict.get('Tr', 0))
        self.transparency = float(transparency)
        self.texture = mtl_dict.get('map_Kd', self.texture)

    def calculate_normals(self):
        for i in range(len(self.indices) / (3)):
            fi = i * 3
            v1i = self.indices[fi]
            v2i = self.indices[fi + 1]
            v3i = self.indices[fi + 2]

            vs = self.vertices
            p1 = [vs[v1i + c] for c in range(3)]
            p2 = [vs[v2i + c] for c in range(3)]
            p3 = [vs[v3i + c] for c in range(3)]

            u, v = [0, 0, 0], [0, 0, 0]
            for j in range(3):
                v[j] = p2[j] - p1[j]
                u[j] = p3[j] - p1[j]

            n = [0, 0, 0]
            n[0] = u[1] * v[2] - u[2] * v[1]
            n[1] = u[2] * v[0] - u[0] * v[2]
            n[2] = u[0] * v[1] - u[1] * v[0]

            # for k in range(3):
            #     self.vertices[v1i + 3] = n[k]
            #     self.vertices[v2i + 3] = n[k]
            #     self.vertices[v3i + 3] = n[k]


class ObjFileLoader(object):
    """  """
    def finish_object(self):
        if self._current_object is None:
            return

        mesh = MeshData()
        idx = 0
        material = self.mtl.get(self.obj_material)
        if material:
            mesh.set_materials(material)
        for f in self.faces:
            verts = f[0]
            norms = f[1]
            tcs = f[2]
            for i in range(3):
                # get normal components
                n = (0.0, 0.0, 0.0)
                if norms[i] != -1:
                    n = self.normals[norms[i]-1]

                # get texture coordinate components
                t = (0.0, 0.0)
                if tcs[i] != -1:
                    t = self.texcoords[tcs[i]-1]

                # get vertex components
                v = self.vertices[verts[i]-1]

                data = [v[0], v[1], v[2], n[0], n[1], n[2], t[0], t[1]]
                mesh.vertices.extend(data)

                # add material info in the vertice
                mesh.vertices.extend(list(
                    mesh.ambient_color +
                    mesh.diffuse_color +
                    mesh.specular_color) +
                    [mesh.specular_coefficent, mesh.transparency]
                )

            tri = [idx, idx+1, idx+2]
            mesh.indices.extend(tri)
            idx += 3

        self.objects[self._current_object] = mesh
        # mesh.calculate_normals()
        self.faces = []

    def __init__(self, filename, swapyz=False, delimiter="# object"):
        """Loads a Wavefront OBJ file. """
        self.objects = {}
        self.vertices = []
        self.normals = []
        self.texcoords = []
        self.faces = []

        self._current_object = None

        self.obj_material = None

        print "filename %s" % filename
        for line in open(filename, "r"):
            if delimiter == "# object" and "# object" in line:
                if self._current_object:
                    self.finish_object()
                self._current_object = line.split()[2]
            if line.startswith('#'):
                continue
            if line.startswith('s'):
                continue
            values = line.split()
            if not values:
                continue
            if values[0] == 'o':
                self.finish_object()
                self._current_object = values[1]
            elif values[0] == 'mtllib':
                # load materials file here
                self.mtl = MTL(join(dirname(filename), (values[1])))
            elif values[0] in ('usemtl', 'usemat'):
                self.obj_material = values[1]
            if values[0] == 'v':
                v = map(float, values[1:4])
                if swapyz:
                    v = v[0], v[2], v[1]
                self.vertices.append(v)
            elif values[0] == 'vn':
                v = map(float, values[1:4])
                if swapyz:
                    v = v[0], v[2], v[1]
                self.normals.append(v)
            elif values[0] == 'vt':
                self.texcoords.append(map(float, values[1:3]))
            elif values[0] == 'f':
                face = []
                texcoords = []
                norms = []
                for v in values[1:]:
                    w = v.split('/')
                    face.append(int(w[0]))
                    if len(w) >= 2 and len(w[1]) > 0:
                        texcoords.append(int(w[1]))
                    else:
                        texcoords.append(-1)
                    if len(w) >= 3 and len(w[2]) > 0:
                        norms.append(int(w[2]))
                    else:
                        norms.append(-1)
                self.faces.append((face, norms, texcoords))
        self.finish_object()


class MTL(object):
    def __init__(self, filename):
        self.contents = {}
        if not os.path.exists(filename):
            return
        for line in open(filename, "r"):
            if line.startswith('#'):
                continue
            values = line.split()
            if not values:
                continue
            if values[0] == 'newmtl':
                mtl = self.contents[values[1]] = {}
            elif mtl is None:
                raise ValueError("mtl file doesn't start with newmtl stmt")
            if len(values[1:]) > 1:
                mtl[values[0]] = values[1:]
            else:
                mtl[values[0]] = values[1]

    def __getitem__(self, key):
        return self.contents[key]

    def get(self, key, default=None):
        return self.contents.get(key, default)
