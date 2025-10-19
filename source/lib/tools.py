import math
from fontTools.misc.fixedTools import otRound
from mojo.roboFont import RFont



def track_glyph(glyph, side_value, glyph_set=None):
    glyph_set = [glyph.name] if glyph_set is None else glyph_set
    with glyph.holdChanges():
        # Move contours, anchors, guidelines, image
        stuff_to_move = list(glyph.contours) + list(glyph.anchors) + list(glyph.guidelines) + ([glyph.image] if glyph.image else [])
        for element in stuff_to_move:
            if element:
                element.moveBy((side_value, 0))
        # Now handle components that have a transformation.
        for comp in glyph.components:
            if comp.baseGlyph in glyph_set:
                # Fancy math for correcting component positioning based on their transformation
                a, b, c, d, tx, ty = comp.transformation
                angle = math.atan2(b, a)
                scale_x = math.hypot(a, b)
                scale_y = math.hypot(c, d)
                cos_angle = math.cos(angle)
                sin_angle = math.sin(angle)
                # Compute horizontal adjustment
                horz_adjust = side_value * ((1 - cos_angle) + (1 - scale_x) * cos_angle)
                # Compute vertical adjustment
                vert_adjust = -side_value * sin_angle * (scale_x / scale_y)
            # Skip component correction if its base glyph is not being tracked.
            else:
                horz_adjust = side_value
                vert_adjust = 0
            # Correct the position of the components
            comp.moveBy((horz_adjust, vert_adjust))
        glyph.width += side_value * 2
        
def track_font(font, value, glyph_set=None, all_layers=True, ignore_zero_width=True, future_negative_width="allow negatives", report=False):
    half = otRound(value/2)
    layers = font.layers if all_layers else [font.defaultLayer]
    ignored_glyphs = {}
    clamped_glyphs = {}
    changed_glyphs = {}
    with font.holdChanges():
        for layer in layers:
            glyph_set = layer.keys() if glyph_set is None else glyph_set
            for g in layer:
                if g.name not in glyph_set:
                    continue
                if g.width == 0 and ignore_zero_width:
                    ignored_glyphs.setdefault(layer.name, []).append(g.name)
                    continue
                if -half * 2 > g.width and future_negative_width != "allow negatives":
                    if future_negative_width == "limit to zero":
                        half = otRound(-g.width/2)
                        clamped_glyphs.setdefault(layer.name, []).append(g.name)
                    elif future_negative_width == "don’t change":
                        ignored_glyphs.setdefault(layer.name, []).append(g.name)
                        continue
                track_glyph(g, half, glyph_set)
                changed_glyphs.setdefault(layer.name, []).append(g.name)

        print("Tracker Report:")
        print("\n*********************\nTracker Report:\n*********************")
        emoji = "⬅️➡️"
        if half < 0:
            emoji = "➡️⬅️"
        print(f"{emoji} Applied tracking of {half*2}.")
        if changed_glyphs:
            print("Changed glyphs:")
            for layer, glyphs in changed_glyphs.items():
                print(f"\t{layer}")
                print(f"\t\t{glyphs}")
        if clamped_glyphs:
            print("Glyphs limited to zero:")
            for layer, glyphs in clamped_glyphs.items():
                print(f"\t{layer}")
                print(f"\t\t{glyphs}")
        if ignored_glyphs:
            print("Deliberately ignored glyphs:")
            for layer, glyphs in ignored_glyphs.items():
                print(f"\t{layer}")
                print(f"\t\t{glyphs}")

# Tee up the main function for addition into RFont object
def track(self, value, glyph_set=None, all_layers=True, ignore_zero_width=True, future_negative_width="allow negatives", report=False):
    track_font(self, value, glyph_set, all_layers, ignore_zero_width, future_negative_width, report)



# Add to RFont object
RFont.track = track


