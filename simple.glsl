/* simple.glsl

simple diffuse lighting based on laberts cosine law; see e.g.:
    http://en.wikipedia.org/wiki/Lambertian_reflectance
    http://en.wikipedia.org/wiki/Lambert%27s_cosine_law
*/
---VERTEX SHADER-------------------------------------------------------
#ifdef GL_ES
    precision highp float;
#endif

attribute vec3 v_pos;
attribute vec3 v_normal;
attribute vec2 v_tc0;
attribute vec3 v_ambient;
attribute vec3 v_diffuse;
attribute vec3 v_specular;
attribute float v_specular_coeff;
attribute float v_transparency;

varying vec2 uv_vec;

uniform mat4 modelview_mat;
uniform mat4 projection_mat;

varying vec4 normal_vec;
varying vec4 vertex_pos;

varying vec3 v_a;
varying vec3 v_d;
varying vec3 v_s;
varying float v_sc;
varying float v_alpha;

void main (void) {
    //compute vertex position in eye_sapce and normalize normal vector
    vec4 pos = modelview_mat * vec4(v_pos, 1.0);
    vertex_pos = pos;
    normal_vec = vec4(v_normal,0.0);
    gl_Position = projection_mat * pos;
    uv_vec = v_tc0;
    v_a = v_ambient;
    v_d = v_diffuse;
    v_s = v_specular;
    v_sc = v_specular_coeff;
    v_alpha = v_transparency;
}


---FRAGMENT SHADER-----------------------------------------------------
#ifdef GL_ES
    precision highp float;
#endif

varying vec4 normal_vec;
varying vec4 vertex_pos;
varying vec3 v_a;
varying vec3 v_d;
varying vec3 v_s;
varying float v_sc;
varying float v_alpha;

uniform mat4 normal_mat;
uniform vec4 light_sources[16];
uniform int nb_lights;
uniform mat4 modelview_mat;
varying vec2 uv_vec;

uniform float ambiant;
uniform float diffuse;
uniform float specular;

uniform sampler2D tex;

vec3 get_light(vec4 light, vec4 v_normal){
    vec4 v_light = normalize(light - vertex_pos);
    vec3 theta = v_d * clamp(dot(v_normal, v_light), 0.0, 1.0) * diffuse;

    // specular
    vec3 sp = specular * v_s * pow(max(dot(normal_vec, normalize(vertex_pos - v_light)), 0.0), v_sc);

    return v_a + (theta + sp) / log(distance(vertex_pos, v_light));
}

void main (void){
    //correct normal, and compute light vector (assume light at the eye)
    vec4 v_normal = normalize(normal_mat * normal_vec);

    //reflectance based on lamberts law of cosine
    vec3 light = vec3(0.0, 0.0, 0.0);
    for (int i = 0; i < nb_lights; i++){
        light += get_light(modelview_mat * light_sources[i], v_normal);
    }

    vec4 color = texture2D(tex, vec2(uv_vec.x, 1.0 - uv_vec.y)) * vec4(light, v_alpha);
    gl_FragColor = color;
}
