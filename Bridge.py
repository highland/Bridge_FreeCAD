# -*- coding: utf-8 -*-
"""
Created on Sat Sep 18 19:34:35 2021

@author: Mark Thomas
"""

from math import tan, pi, atan, sin, cos, fabs
import FreeCAD as App
from FreeCAD import Base, Part
from PySide2.QtCore import Qt
from PySide2.QtWidgets import *

doc = App.newDocument()


# class Gui(QDialog):
#     def __init__(self):
#         super(Gui, self).__init__()
#         self.setWindowTitle('Bridge Design')
#         self.setGeometry(100,100,300,400)
#         self.formGroupBox = QGroupBox('Input Data')
#         self.segments_per_arch = QLineEdit()

#     def create_input_form(self):
#         self._form_group_box = QGroupBox("Input Data")
#         layout = QFormLayout()
#         layout.addRow(QLabel("Number of bridge segments :"), QLineEdit())
#         layout.addRow(QLabel("Post Length (mm) :"), QLineEdit())
#         layout.addRow(QLabel("Post Width (mm) :"), QLineEdit())
#         layout.addRow(QLabel("Rebate : "), QLineEdit())
#         self._form_group_box.setLayout(layout)
# All Data in mm for lengths and ° for angles
def get_starting_data():
    # a segment is between 2 cross timbers
    segments_per_arch = int(input('Number of bridge segments : '))
    if segments_per_arch == 0:  # use defaults
        segments_per_arch = 6
        deck_width = 7
        post_length = 1800
        post_width = 75
        slot_depth = 9
    else:
        deck_width = int(input('Number of posts across : '))
        post_length = int(input('Post Length (mm) : '))
        post_width = int(input('Post Width (mm) : '))
        # rebate is the depth of a slot in long timber to locate cross timber
        slot_depth = int(input('Rebate : '))
    # Calculate quantities for bridge.
    arch_radius, radians_per_segment = _calculate_geometry(
        post_length, post_width, slot_depth)
    end_angle = segments_per_arch * radians_per_segment / 2
    if end_angle >= pi / 2:
        print('OVERARCHED')
        quit()
    span = 2 * arch_radius * sin(end_angle)
    height = arch_radius * (1 - cos(end_angle))
    longs = (deck_width * segments_per_arch) / 2
    ends = 2
    cross_pieces = (segments_per_arch - 1) / 2
    uprights = (segments_per_arch + 1)
    posts_required = longs + ends + cross_pieces + uprights
    print(
        f'    Radius : {arch_radius / 1000:.3f} m\n'
        f'    Segment Angle : {radians_per_segment * 180 / pi:.3f}°\n'
        f'    Span : {span / 1000:.3f} m\n'
        f'    Soffit height : {height / 1000:.3f} m\n'
        f'    {posts_required:.1f} posts needed\n'
    )
    return post_length, post_width, segments_per_arch, \
           deck_width, slot_depth, radians_per_segment, arch_radius, span


def _calculate_geometry(stob_length, stob_width, rebate):
    """ calculate internal radius (to base of cross-member) and segment angle (in radians)"""
    # assume angle to start with
    segment_angle_radians = 18 * pi / 180
    angle_tolerance = 0.000_005  # 1 second of arc in radians
    error = float("inf")
    while error > angle_tolerance:
        half_post = stob_length / 2
        extra = stob_width * (1 + 1 / cos(segment_angle_radians)) - rebate
        internal_radius = (half_post ** 2 - extra ** 2) / (2 * extra)
        newangle = atan(half_post / internal_radius)
        error = fabs(segment_angle_radians - newangle)
        segment_angle_radians = newangle
    return (internal_radius - stob_width), segment_angle_radians


# Redefinitions for readability
Point = Base.Vector

density = 510  # kg/m3 for mass of piece


def points_to_part(points, extrude_length):
    nextPoints = points[1:]
    nextPoints.append(points[0])
    pairs = zip(points, nextPoints)
    lines = [Part.LineSegment(a, b) for a, b in pairs]
    shape = Part.Shape(lines)
    wire = Part.Wire(shape.Edges)
    face = Part.Face(wire)
    part = face.extrude(Point(0, extrude_length, 0))
    return part


def make_deck_piece():
    fillet = tan(segment_angle) * stob_width
    top_half = stob_length / 2
    bottom_half = top_half - fillet
    rebate_width = stob_width / 2
    points = [
        Point(-top_half, 0, stob_width + radius),
        Point(-rebate_width, 0, stob_width + radius),
        Point(-rebate_width, 0, stob_width + radius - rebate),
        Point(rebate_width, 0, stob_width + radius - rebate),
        Point(rebate_width, 0, stob_width + radius),
        Point(top_half, 0, stob_width + radius),
        Point(bottom_half, 0, radius),
        Point(-bottom_half, 0, radius),
    ]
    part = points_to_part(points, stob_width)
    shift = Point(0, (stob_length / 4 - stob_width / 2), 0)  # shift to centre
    part.Placement.move(shift)
    return part


def make_end_deck_piece():
    fillet = tan(segment_angle) * stob_width
    top_half = stob_length / 2
    bottom_half = top_half - fillet
    rebate_width = stob_width
    points = [
        Point(-top_half, 0, stob_width + radius),
        Point(-rebate_width, 0, stob_width + radius),
        Point(-rebate_width, 0, stob_width + radius - rebate),
        Point(0, 0, stob_width + radius - rebate),
        Point(0, 0, radius),
        Point(-bottom_half, 0, radius),
    ]
    part = points_to_part(points, stob_width)
    shift = Point(0, (stob_length / 2 - stob_width / 2), 0)  # shift to centre
    part.Placement.move(shift)
    return part


def make_cross_piece():
    # TODO using parta = partb.cut(partc) cut out joint at ends
    half_width = stob_width / 2
    side_height = stob_width - tan(segment_angle) * half_width
    length = stob_length / 2
    base = radius + stob_width - rebate
    points = [
        Point(0, 0, stob_width + base),
        Point(-half_width, 0, side_height + base),
        Point(-half_width, 0, base),
        Point(half_width, 0, base),
        Point(half_width, 0, side_height + base),
    ]
    return points_to_part(points, length)


def make_end_cross_piece():
    side_height = stob_width - tan(segment_angle) * stob_width
    base = radius + stob_width - rebate
    points = [
        Point(0, 0, stob_width + base),
        Point(0, 0, base),
        Point(-stob_width, 0, base),
        Point(-stob_width, 0, side_height + base),
    ]
    return points_to_part(points, stob_length)


def make_assemblies():
    # two types - even number of deck pieces
    def _make_even_assembly(deck_piece, cross_piece):
        base = cross_piece.copy()
        current_piece = deck_piece.copy()
        stob_count = (stobs_across_deck + 1) // 2
        current_piece.Placement.move(-(stob_count // 2 - 1 / 2) * deflection)  # start at one side
        for _ in range(stob_count):
            base = base.fuse(current_piece)
            current_piece = current_piece.copy()
            current_piece.Placement.move(deflection)
        return base
    # - even number of deck pieces
    def _make_odd_assembly(deck_piece, cross_piece):
        base = cross_piece.copy()
        current_piece = deck_piece.copy()
        stob_count = (stobs_across_deck) // 2
        current_piece.Placement.move(-(stob_count // 2) * deflection)  # start at one side
        for _ in range(stob_count):
            base = base.fuse(current_piece)
            current_piece = current_piece.copy()
            current_piece.Placement.move(deflection)
        return base
    deck_piece = make_deck_piece()
    cross_piece = make_cross_piece()
    deflection = Point(0, 2 * stob_width, 0)
    assembly1 = _make_even_assembly(deck_piece, cross_piece)
    if stobs_across_deck % 2 == 0:
        assembly2 = assembly1.copy()
        assembly2.rotate(Point(0, 0, 0), Point(0, 0, 1), 180)
    else:
        assembly2 = _make_odd_assembly(deck_piece, cross_piece)
    return assembly1, assembly2


def make_end_assemblies():
    cross_piece = make_end_cross_piece()
    deck_piece = make_end_deck_piece()
    deflection = Point(0, 2 * stob_width, 0)
    base1 = cross_piece.copy()
    current_piece = deck_piece.copy()
    stob_count = (stobs_across_deck + 1) // 2
    current_piece.Placement.move(-(stob_count // 2 - 1 / 2) * deflection)  # start at one side
    for _ in range(stob_count):
        base1 = base1.fuse(current_piece)
        current_piece = current_piece.copy()
        current_piece.Placement.move(deflection)
    base1.Placement.move(Point(0, -stob_length / 4, 0))
    base2 = base1.copy()
    base2.rotate(Point(0, stob_length/4, 0), Point(0, 0, 1), 180)
    return base1, base2

def assemble_bridge():
    angle = segment_angle * 180 / pi
    assembly_0, assembly_1 = make_assemblies()
    assembly_0L = assembly_0.copy()
    assembly_0L.rotate(Point(0, 0, 0), Point(0, 1,0), -angle * 2)
    bridge = assembly_0.fuse(assembly_0L)
    assembly_0R = assembly_0.copy()
    assembly_0R.rotate(Point(0, 0, 0), Point(0, 1,0), angle * 2)
    bridge = bridge.fuse(assembly_0R)
    assembly_1L = assembly_1.copy()
    assembly_1L.rotate(Point(0, 0, 0), Point(0, 1,0), -angle)
    bridge = bridge.fuse(assembly_1L)
    assembly_1LL = assembly_1L.copy()
    assembly_1LL.rotate(Point(0, 0, 0), Point(0, 1,0), -angle*2)
    bridge = bridge.fuse(assembly_1LL)
    assembly_1R = assembly_1.copy()
    assembly_1R.rotate(Point(0, 0, 0), Point(0, 1,0), angle)
    bridge = bridge.fuse(assembly_1R)
    assembly_1RR = assembly_1R.copy()
    assembly_1RR.rotate(Point(0, 0, 0), Point(0, 1,0), angle*2)
    bridge = bridge.fuse(assembly_1RR)
    right_end, left_end = make_end_assemblies()
    left_end.rotate(Point(0, 0, 0), Point(0, 1, 0), -angle * 4)
    bridge = bridge.fuse(left_end)
    right_end.rotate(Point(0, 0, 0), Point(0, 1, 0), angle * 4)
    bridge = bridge.fuse(right_end)
    return bridge

(stob_length, stob_width, segment_count, stobs_across_deck,
 rebate, segment_angle, radius, between_abutments) = get_starting_data()

bridge = assemble_bridge()
Part.show(bridge, 'Bridge')

# assembly_1, assembly_2 = make_assemblies()
# Part.show(assembly_1, "Assembly 1")
# Part.show(assembly_2, "Assembly 2")
# assembly_3, assembly_4 = make_end_assemblies()
# Part.show(assembly_3, "Assembly 3")
# Part.show(assembly_4, "Assembly 4")

