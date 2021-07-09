# -*- coding: utf-8 -*-

from mathics.builtin.base import BoxConstructError
from mathics.builtin.box.graphics import PolygonBox
from mathics.builtin.colors.color_directives import _Color

from mathics.builtin.drawing.graphics_internals import GLOBALS

class DensityPlotBox(PolygonBox):
    def init_vertex_colors(self, colors_expr):
        if not colors_expr.has_form("List", None):
            raise BoxConstructError
        # from trepan.api import debug; debug()
        if (
            colors_expr.leaves
            and colors_expr.leaves[0].has_form("List", None)
        ):
            leaves = colors_expr.leaves
        else:
            leaves = [Expression(SymbolList, *colors.leaves)]
        self.vertex_colors = []
        for leaf in leaves:
            if leaf.has_form("List", None):
                self.vertex_colors.append(leaf.leaves)
            else:
                raise BoxConstructError




    def init(self, graphics, style, item=None, options=None):
        super(PolygonBox, self).init(graphics, item, style)
        self.edge_color, self.face_color = style.get_style(_Color, face_element=True)
        if item is not None:
            if not (2 <= len(item.leaves) <= 3):
                raise BoxConstructError
            points_expr, colors_expr = item.leaves[0:2]
            self.do_init(graphics, points_expr)
            self.init_vertex_colors(colors_expr)
            # Is this right?
            for leaf in item.leaves[2:]:
                if not leaf.has_form("Rule", 2):
                    raise BoxConstructError
                name = leaf.leaves[0].get_name()
                self.process_option(name, leaf.leaves[1])
        else:
            raise BoxConstructError

# FIXME: GLOBALS is a horrible name.
GLOBALS.update(
    {
        "System`DensityPlotBox": DensityPlotBox,
    }
)
