# menuTitle: Tracker


"""
Preview tracking in Space Center, and then click button to apply in the font.
Components (transformed or otherwise) are handled gracefully, 
but double-check the wildly transformed ones for 1-off errors.
	
Ryan Bugden
"""


from fontTools.misc.fixedTools import otRound
import ezui
from mojo.UI import CurrentSpaceCenter, OpenSpaceCenter, inDarkMode
from mojo.subscriber import Subscriber, registerRoboFontSubscriber, getRegisteredSubscriberEvents, registerSubscriberEvent
from mojo.extensions import getExtensionDefault, setExtensionDefault

from importlib import reload
import tools
import settings
reload(tools)
reload(settings)
EXTENSION_KEY = settings.EXTENSION_KEY
EXTENSION_DEFAULTS = settings.EXTENSION_DEFAULTS



def my_round(x, base=2):
    return base * round(x/base)

def color_number_formatter(attributes):
    value = attributes["value"]
    main_color = [(0, 0, 0, 1), (1, 1, 1, 1)][inDarkMode()]
    if value != my_round(value):
        color = (1, 0, 0, 1)
    else:
        color = main_color
    attributes["fillColor"] = color

def label_formatter(attributes):
    value = attributes["value"]
    color = [(0.65, 0.65, 0.65, 1), (0.35, 0.35, 0.35, 1)][inDarkMode()]
    attributes["fillColor"] = color



class Tracker(Subscriber, ezui.WindowController):

    def build(self):
        self.csc = CurrentSpaceCenter()
        if not self.csc:
            self.csc = OpenSpaceCenter(CurrentFont())
        self.lv = self.csc.glyphLineView
        self.tracking = self.csc.getTracking()
        
        content = """
        ---X---                  @trackingSlider

        *HorizontalStack
        > (*)                    @settingsButton
        > All Glyphs             @infoLabel
        > 0%                     @percentageLabel
        > [__]                   @trackingTextField
        > (Apply)                @applyButton
        """
        descriptionData = dict(
            trackingSlider=dict(
                width='fill',
                # valueType="integer",
                minValue=-300, 
                maxValue=300,
                tickMarks=3,
                # stopOnTickMarks=True,
                value=self.tracking,
                # valueIncrement=2,
                continuous=True, 
                sizeStyle='regular'
            ),
            trackingTextField=dict(
                valueType="integer",
                stringFormatter=color_number_formatter,
                value=self.tracking,
                valueIncrement=2,
                continuous=True,
                # valueWidth=50,
                width=50,
                gravity='trailing',
            ),
            infoLabel=dict(
                stringFormatter=label_formatter,
            ),
            percentageLabel=dict(
                gravity='trailing',
                stringFormatter=label_formatter,
            ),
            applyButton=dict(
                width=100,
                gravity='trailing'
            ),
        )
        window_height=101
        self.w = ezui.EZPanel(
            title='Tracker',
            content=content,
            descriptionData=descriptionData,
            controller=self,
            size=(500, 'auto'),
            minSize=(100, window_height),
            maxSize=(1000, window_height),
        )
        self.w.getNSWindow().setTitlebarAppearsTransparent_(True)
        self.w.setDefaultButton(self.w.getItem("applyButton"))
        self.update_info_label()
        self.update_percentage_label()

    def started(self):
        self.w.open()
        
    def destroy(self):
        self.reset_space_center()
        self.w.close()

    def reset_space_center(self):
        self.csc.setTracking(0)
        self.csc.refreshGlyphLineView()
        
    def spaceCenterDidKeyUp(self, info):
        self.update_slider_from_sc()
        
    def spaceCenterDidChangeText(self, info):
        self.update_slider_from_sc()

    def roboFontAppearanceChanged(self, info):
        # Update gray value of labels
        self.update_info_label()
        self.update_percentage_label()

    def settingsButtonCallback(self, sender):
        settings.TrackerSettingsWindowController(sender)
        
    def trackingSliderCallback(self, sender):
        self.csc = CurrentSpaceCenter()
        self.tracking = otRound(sender.get() / 2) * 2
        self.w.getItem('trackingTextField').set(self.tracking)
        self.update_percentage_label()
        self.w.getItem("applyButton").enable(True)
        self.preview_tracking()

    def trackingTextFieldCallback(self, sender):
        # Update slider from text field
        self.w.getItem('trackingSlider').set(sender.get())
        value = sender.get()
        if value == my_round(value):
            self.w.getItem("applyButton").enable(True)
            self.tracking = otRound(sender.get() / 2) * 2
            self.preview_tracking()
        else:
            self.w.getItem("applyButton").enable(False)
        self.update_percentage_label()
        
    def applyButtonCallback(self, sender):
        # Set up settings
        f = self.csc.font.asFontParts()
        settings = getExtensionDefault(EXTENSION_KEY, EXTENSION_DEFAULTS)
        # Apply tracking to font
        f.track(
            value = otRound(self.w.getItem("trackingTextField").get()), 
            glyph_set = [f.selectedGlyphNames, None][settings["glyphsSelection"]],
            all_layers = settings["layersSelection"], 
            ignore_zero_width = settings["ignoreZeroWidth"], 
            future_negative_width = ["limit to zero", "allow negatives", "don’t change"][settings["prospectiveNegativeWidths"]],
            report=True
            )
        self.reset_space_center()
        self.update_slider_from_sc()

    def update_slider_from_sc(self):
        self.csc = CurrentSpaceCenter()
        self.w.getItem('trackingSlider').set(self.csc.getTracking())
        self.trackingSliderCallback(self.w.getItem('trackingSlider'))
        
    def update_info_label(self):        
        settings = getExtensionDefault(EXTENSION_KEY, EXTENSION_DEFAULTS)
        self.w.getItem("infoLabel").set(["Selected Glyphs", "All Glyphs"][settings["glyphsSelection"]])

    def update_percentage_label(self):        
        f = self.csc.font.asFontParts()
        value = self.w.getItem("trackingTextField").get()
        percentage = value / f.info.unitsPerEm * 100
        if percentage == int(value / f.info.unitsPerEm * 100):
            label_text = f"{int(percentage)}%"
        else:
            label_text = f"{round(percentage, 2)}%"
        self.w.getItem("percentageLabel").set(label_text)

    def preview_tracking(self):
        # Get settings
        f = self.csc.font.asFontParts()
        settings = getExtensionDefault(EXTENSION_KEY, EXTENSION_DEFAULTS)
        glyph_set = [f.selectedGlyphNames, None][settings["glyphsSelection"]]
        all_layers = settings["layersSelection"]
        ignore_zero_width = settings["ignoreZeroWidth"]
        future_negative_width = ["limit to zero", "allow negatives", "don’t change"][settings["prospectiveNegativeWidths"]]

        # Check that we're in a relevant layer. Otherwise, don't change the Space Center preview.
        if all_layers == True or self.csc.getLayerName() == f.defaultLayer.name:
            # If we're tracking the whole font, just do a simple tracking change.
            if glyph_set is None and ignore_zero_width == False and future_negative_width == "allow negatives":
                self.csc.setTracking(self.tracking)
            else:
                # Establish actual glyph set and filter out some glyphs, given settings
                glyph_set = f.keys() if glyph_set is None else glyph_set
                layer = f.getLayer(self.csc.getLayerName())
                filtered_glyph_set = set()
                for g_name in glyph_set:
                    if ignore_zero_width and layer[g_name].width == 0:
                        continue
                    if future_negative_width == "don’t change" and layer[g_name].width < -self.tracking:
                        continue
                    filtered_glyph_set.add(g_name)

                # Glyph specific spacing preview
                self.reset_space_center()
                grs = self.csc.glyphRecords
                side_value = otRound(self.tracking/2)
                for i, gr in enumerate(grs):
                    if gr.glyph.name not in filtered_glyph_set:
                        continue
                    if future_negative_width == "limit to zero" and gr.glyph.width < -self.tracking:
                        side_value = -gr.glyph.width/2  # otRound(-g.width/2) 
                    gr.xAdvance += side_value
                    if i > 0: 
                        p = grs[i-1]
                        p.xAdvance += side_value
                self.csc.refreshGlyphLineView()

    def trackerSettingsDidChange(self, info):
        self.reset_space_center()
        self.update_info_label()
        self.preview_tracking()



if CurrentFont():
    registerRoboFontSubscriber(Tracker)
    # Register a subscriber event for when Tracker settings change
    event_name = f"{EXTENSION_KEY}.trackerSettingsDidChange"
    if event_name not in getRegisteredSubscriberEvents():
        registerSubscriberEvent(
            subscriberEventName=event_name,
            methodName="trackerSettingsDidChange",
            lowLevelEventNames=[event_name],
            dispatcher="roboFont",
            documentation="Sent when Tracker extension settings have changed.",
            delay=None
        )
