from pyassimp import load, postprocess


class AssimpObjLoader(object):
    def __init__(self, source):
        # super(AssimpObjLoader, **kwargs)
        # source = kwargs.get('source', '')
        if not source:
            print "no source given!"
            return

        self.scene = scene = load(
            source, 0
            | postprocess.aiProcess_Triangulate
            | postprocess.aiProcess_SplitLargeMeshes
            | postprocess.aiProcess_GenNormals
            )

        self.objects = {}
        for i, mesh in enumerate(scene.meshes):
            self.objects[i] = AssimpMesh(scene, mesh)


class AssimpMesh(object):
    def __init__(self, scene, mesh):
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
        self.texture = mesh.material.properties.get(('file', 1L))

        ambiant = [0.0, 0.0, 0.0]
        diffuse = [1.0, 1.0, 1.0]
        specular = [1.0, 1.0, 1.0]

        for i, v in enumerate(mesh.vertices):
            data = (
                list(v) + list(mesh.normals[i]) +
                list(mesh.texturecoords[0][i][:2]
                     if len(mesh.texturecoords) else [0, 0]) +
                mesh.material.properties.get(('ambiant', 0L), ambiant) +
                mesh.material.properties.get(('diffuse', 0L), diffuse) +
                mesh.material.properties.get(('specular', 0L), specular) + [
                    mesh.material.properties.get(('refracti', 0L), 1),
                    mesh.material.properties.get(('opacity', 0L), 1)
                ]
            )

            self.vertices.extend(data)

        for f in mesh.faces:
            self.indices.extend(f)
