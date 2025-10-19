EXTENSION_KEY = 'com.ryanbugden.tracker.settings'
EXTENSION_DEFAULTS = {
    # Radio button
    "glyphsSelection": 1,  # selected glyphs, or all glyphs
    # Radio button
    "layersSelection": 1,  # default layer, or all layers
    # Avoid changing zero-width glyphs
    "ignoreZeroWidth": True,
    # If spacing will result in a negative width, limit it to zero, allow negative widths, or avoid respacing that glyph altogether
    "prospectiveNegativeWidths": 0, # "limit to zero", "allow negatives", or "don’t change"
}