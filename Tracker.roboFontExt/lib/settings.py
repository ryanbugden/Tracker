import ezui
from mojo.extensions import getExtensionDefault, setExtensionDefault
from mojo.events import postEvent



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



class TrackerSettingsWindowController(ezui.WindowController):

    def build(self, parent):
        content = """
        * TwoColumnForm            @form
        
        > : Glyphs:
        > ( ) Selected Glyphs      @glyphsSelection
        > (X) All Glyphs

        > : Layers:
        > ( ) Default Layer        @layersSelection
        > (X) All Layers

        > : Zero-Width Glyphs:
        > [X] Ignore               @ignoreZeroWidth

        > : Future Negatives:
        > (X) Limit to Zero        @prospectiveNegativeWidths
        > ( ) Allow
        > ( ) Don’t Change
        
        > ---
        
        > (Reset Defaults)         @resetDefaultsButton
        """
        title_column_width = 130
        item_column_width = 150
        descriptionData = dict(
            form=dict(
                titleColumnWidth=title_column_width,
                itemColumnWidth=item_column_width
            ),
            resetDefaultsButton=dict(
                width='fill'
            )

        )
        self.w = ezui.EZPopover(
            content=content,
            descriptionData=descriptionData,
            parent=parent,
            parentAlignment='bottom',
            behavior="transient",
            controller=self
        )
        prefs = getExtensionDefault(EXTENSION_KEY, fallback=EXTENSION_DEFAULTS)
        try:
            self.w.setItemValues(prefs)
        except KeyError as e:
            print(f"Tracker Settings error: {e}")
        
    def started(self):
        self.w.open()
        
    def contentCallback(self, sender):
        self.update_extension_settings()
        
    def resetDefaultsButtonCallback(self, sender):
        self.w.setItemValues(EXTENSION_DEFAULTS)
        self.update_extension_settings()
        
    def update_extension_settings(self):
        setExtensionDefault(EXTENSION_KEY, self.w.getItemValues())
        postEvent(f"{EXTENSION_KEY}.trackerSettingsDidChange")
        

