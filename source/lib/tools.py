import math
from fontTools.misc.fixedTools import otRound
from mojo.roboFont import RFont


def get_sync_metrics_state(font):
    lib_key = "com.typemytype.robofont.syncGlyphLayers"
    if lib_key in font.lib:
        settings = font.lib[lib_key]
        if "metrics" in settings:
            return settings
    return None

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
    half = value/2
    layers = font.layers if all_layers else [font.defaultLayer]
    ignored_glyphs = {}
    clamped_glyphs = {}
    changed_glyphs = {}
    # Save sync metrics state and restore afterward
    sync_metrics = get_sync_metrics_state(font)
    if sync_metrics:
        temp_state = sync_metrics.split()
        temp_state.remove("metrics")
        temp_state = " ".join(temp_state)
        font.lib["com.typemytype.robofont.syncGlyphLayers"] = temp_state
        print(f"Tracker: Temporarily suspending sync metrics state: {sync_metrics} --> {temp_state} ")
    with font.holdChanges():
        for layer in layers:
            layer_glyph_names = layer.keys() if glyph_set is None else glyph_set
            effective_glyph_set = set()
            for g_name in layer_glyph_names:
                if g_name not in layer:
                    continue
                g = layer[g_name]
                if g.width == 0 and ignore_zero_width:
                    ignored_glyphs.setdefault(layer.name, []).append(g_name)
                    continue
                if -half * 2 > g.width and future_negative_width == "don’t change":
                    ignored_glyphs.setdefault(layer.name, []).append(g_name)
                    continue
                effective_glyph_set.add(g_name)
            for g in layer:
                if g.name not in effective_glyph_set:
                    continue
                glyph_half = half
                if -glyph_half * 2 > g.width and future_negative_width == "limit to zero":
                    glyph_half = -g.width/2
                    clamped_glyphs.setdefault(layer.name, []).append(g.name)
                track_glyph(g, glyph_half, effective_glyph_set)
                changed_glyphs.setdefault(layer.name, []).append(g.name)
                
    # Restore sync metrics
    if sync_metrics: 
        print(f"Tracker: Restoring sync metrics state: {temp_state} --> {sync_metrics}")
        font.lib["com.typemytype.robofont.syncGlyphLayers"] = sync_metrics

    if report:
        print("Tracker Report:")
        print("\n*********************\nTracker Report:\n*********************")
        emoji = "⬅️➡️"
        if half < 0:
            emoji = "➡️⬅️"
        print(f"{emoji} Applied tracking of {half*2}.")
        if half != otRound(half):
            print("⚠️ Note: It was not an even number, so you might end up with floating-point sidebearings.")
        if changed_glyphs:
            print("\n🔺 Changed glyphs:")
            for layer, glyphs in changed_glyphs.items():
                print(f"\t📑 {layer}")
                print(f"\t\t{glyphs}")
        if clamped_glyphs:
            print("\n🫸 Glyphs limited to zero:")
            for layer, glyphs in clamped_glyphs.items():
                print(f"\t📑 {layer}")
                print(f"\t\t{glyphs}")
        if ignored_glyphs:
            print("\n👋 Deliberately ignored glyphs:")
            for layer, glyphs in ignored_glyphs.items():
                print(f"\t📑 {layer}")
                print(f"\t\t{glyphs}")

# Tee up the main function for addition into RFont object
def track(self, value, glyph_set=None, all_layers=True, ignore_zero_width=True, future_negative_width="allow negatives", report=False):
    track_font(self, value, glyph_set, all_layers, ignore_zero_width, future_negative_width, report)



# Add to RFont object
RFont.track = track


