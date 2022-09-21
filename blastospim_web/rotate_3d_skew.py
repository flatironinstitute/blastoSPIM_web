
import numpy as np
import math
from H5Gizmos import Stack, Slider, Image
from . import scraper

def shearKJ(array, radians):
    (I, J, K) = array.shape
    result = array.copy()
    result[:] = 0
    Jmid = J / 2
    shifter = np.tan(radians)
    for j in range(J):
        shift = int((j - Jmid) * shifter)
        dst_mn = max(0, - shift)
        dst_mx = min(K, K - shift)
        src_mn = max(0, shift)
        src_mx = min(K, K + shift)
        try:
            result[:, j, dst_mn:dst_mx] = array[:, j, src_mn:src_mx]
        except Exception as e:
            print("shearKJ exception dst", dst_mn, dst_mx, "src", src_mn, src_mx)
            raise
    return result

def swapABC(array, A=0, B=1, C=2):
    result = array
    order = [A, B, C]
    assert set(order) == set([0,1,2]), "Bad indices: " + repr(order)
    for (p0,p1) in [(0,1), (1,2), (0,1)]:
        order0 = order[p0]
        order1 = order[p1]
        if order0 > order1:
            result = np.swapaxes(result, p0, p1)
            order[p0] = order1
            order[p1] = order0
    assert order[0] < order[1] < order[2], repr(order)
    return result

def invertABC(A=0, B=1, C=2):
    map = {A:0, B:1, C:2}
    return [map[i] for i in range(3)]

def shearABC(array, radians, A=0, B=1, C=2):
    swap = swapABC(array, A, B, C)
    shear = shearKJ(swap, radians)
    [iA, iB, iC] = invertABC(A, B, C)
    back = swapABC(shear, iA, iB, iC)
    return back

def rot90JK(array):
    T = np.swapaxes(array, 1, 2)
    return T[:, ::-1, :]

def rot90ABC(array, A=0, B=1, C=2):
    swap = swapABC(array, A, B, C)
    rot = rot90JK(array)
    [iA, iB, iC] = invertABC(A, B, C)
    back = swapABC(rot, iA, iB, iC)
    return back

# based on https://www.ocf.berkeley.edu/~fricke/projects/israel/paeth/rotation_by_shearing.html

pi4 = np.pi / 4.0
pi2 = np.pi / 2.0
pi34 = np.pi * 3.0 / 4.0

def rotateKJ45(array, theta):
    #global sA, sB, sC  # DEBUG ONLY
    assert theta >= -pi4 and theta <= pi4, "bad theta" + repr([pi4, theta])
    alpha = - np.tan(0.5 * theta)
    beta = np.sin(theta)
    sA = shearKJ(array, alpha)
    sB = shearABC(sA, beta, 0, 2, 1)
    sC = shearKJ(sB, alpha)
    return sC

def rotateKJ(array, theta):
    assert -np.pi - 1 <= theta <= np.pi + 1, "bad theta: " + repr(theta)
    # note: rotations are fast because they only make views of the array (?)
    buffer = array
    theta0 = theta
    if theta > pi4:
        if theta < pi34:
            # 90 degree rotation
            buffer = rot90JK(array)
            theta0 = theta - pi2
        else:
            # 180 degrees
            buffer = rot90JK(rot90JK(array))
            theta0 = theta - np.pi
    elif theta < -pi4:
        if theta > -pi34:
            # 270 degrees
            buffer = rot90JK(rot90JK(rot90JK(array)))
            theta0 = theta + pi2
        else:
            # 180 degrees
            buffer = rot90JK(rot90JK(array))
            theta0 = np.pi + theta
    return rotateKJ45(buffer, theta0)

def rotateABC(array, radians, A=0, B=1, C=2):
    swap = swapABC(array, A, B, C)
    rotate = rotateKJ(swap, radians)
    [iA, iB, iC] = invertABC(A, B, C)
    back = swapABC(rotate, iA, iB, iC)
    return back

def max_value_projection(filename, pseudocolor=True):
    D = np.load(filename, allow_pickle=True)
    img = D["img"]
    labels = D["labels"]
    slicing = scraper.positive_slicing(labels)
    simg = scraper.slice3(img, slicing)
    [I, J, K] = simg.shape
    m = min(J, K)
    timg = simg
    if I < m:
        stride = int(m / I)
        timg = simg[:, ::stride, ::stride]
    return RotationProjection3d(timg, pseudocolor)

def extruded_labels(filename):
    D = np.load(filename, allow_pickle=True)
    #img = D["img"]
    labels = D["labels"]
    slicing = scraper.positive_slicing(labels)
    simg = scraper.slice3(labels, slicing)
    [I, J, K] = simg.shape
    m = min(J, K)
    timg = simg
    if I < m:
        stride = int(m / I)
        timg = simg[:, ::stride, ::stride]
    return RotationProjection3d(timg, extruded=True, pseudocolor=False)

def extrude0(labels_array):
    "extrude values along axis 0"
    extruded = labels_array[0].copy()
    for labelsi in labels_array:
        nz = (labelsi > 0)
        extruded = np.choose(nz, [extruded, labelsi])
        #volume[i] = extruded
    return extruded

class RotationProjection3d:
    
    def __init__(self, arr3d, pseudocolor=False, extruded=False):
        self.pseudocolor = pseudocolor
        self.extruded = extruded
        self.arr3d = arr3d
        # larger array for rotation...
        (I, J, K) = arr3d.shape
        N = math.ceil(np.sqrt(I*I + J*J + K*K))
        buffer = self.buffer = np.zeros((N, N, N), dtype=arr3d.dtype)
        Istart = round(0.5 * (N-I))
        Jstart = round(0.5 * (N-J))
        Kstart = round(0.5 * (N-K))
        buffer[Istart:Istart+I, Jstart:Jstart+J, Kstart:Kstart+K] = arr3d
        
    def rotate(self, theta, phi):
        R1 = rotateKJ(self.buffer, theta)
        R2 = rotateABC(R1, phi, 2, 0, 1)
        return R2     
    
    async def gizmo(self):
        limit = np.pi
        self.theta_slider = Slider(
            title="theta", 
            value=0, 
            minimum=-limit, 
            maximum=+limit, 
            step=0.02, 
            on_change=self.draw_image)
        self.phi_slider = Slider(
            title="theta", 
            value=0, 
            minimum=-limit, 
            maximum=+limit, 
            step=0.02, 
            on_change=self.draw_image)
        self.image = Image(height=600, width=600)
        dash = Stack([self.theta_slider, self.phi_slider, self.image])
        await dash.link()
        self.draw_image()
        
    def draw_image(self, *ignored):
        theta = self.theta_slider.value
        phi = self.phi_slider.value
        rotated = self.rotate(theta, phi)
        if self.extruded:
            projected = extrude0(rotated)
        else:
            # default max value projection
            projected = rotated.max(axis=0)
        #M = projected.max()
        #scale = 255.0 / M
        #scaled = (projected * scale).astype(np.ubyte)
        if self.extruded:
            scaled = scraper.colorize_array(projected)
        if self.pseudocolor:
            p256 = scraper.scale256(projected)
            scaled = p256
            scaled = scraper.pseudo_colorize(p256)
        #print("scaled", scaled.shape, scaled.min(), scaled.max())
        self.image.change_array(scaled)

