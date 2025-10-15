# menuTitle: Tracker

"""
Preview tracking in Space Center, and then click button to apply in the font.
Components (transformed or otherwise) should be handled gracefully, 
but double-check the wildly transformed ones for 1-off errors.
	
Ryan Bugden
Initial: 2024.11.01
Current: 2025.09.18
"""

import ezui
from mojo.UI import CurrentSpaceCenter, OpenSpaceCenter
from mojo.subscriber import Subscriber, registerRoboFontSubscriber
import math


# SETTINGS!
# Avoid changing zero-width glyphs
IGNORE_ZERO_WIDTH_GLYPHS = True
# If spacing will result in a negative width, limit it to zero, allow negative widths, or avoid respacing that glyph altogether
FUTURE_NEGATIVE_WIDTHS = "limit to zero"  # "limit to zero", "allow negatives", or "don’t change"


class Tracker(Subscriber, ezui.WindowController):

    def build(self):
        self.csc = CurrentSpaceCenter()
        if not self.csc:
            self.csc = OpenSpaceCenter(CurrentFont())
        self.lv = self.csc.glyphLineView
        self.tracking = self.csc.getTracking()
        
        content = """
        ---X--- [__]        @trackingSlider
        (Apply)             @applyButton
        """
        descriptionData = dict(
            trackingSlider=dict(
                width=500,
                valueType="integer",
                minValue=-100, 
                maxValue=100,
                tickMarks=101,
                stopOnTickMarks=True,
                value=self.tracking,
                valueIncrement=2,
                continuous=True, 
                sizeStyle='regular'
            ),
            applyButton=dict(
                width='fill'
            ),
        )
        self.w = ezui.EZPanel(
            title='Tracker',
            content=content,
            descriptionData=descriptionData,
            controller=self,
            size="auto"
        )
        self.w.getNSWindow().setTitlebarAppearsTransparent_(True)
        self.w.setDefaultButton(self.w.getItem("applyButton"))

    def started(self):
        self.w.open()
        
    def destroy(self):
        self.csc.setTracking(0)
        self.w.close()
        
    def track_glyph_sides(self, g, side_value):
        # Move contours, anchors, guidelines, image
        stuff_to_move = list(g.contours) + list(g.anchors) + list(g.guidelines) + ([g.image] if g.image else [])
        for element in stuff_to_move:
            if element:
                element.moveBy((side_value, 0))
            
        # Now handle components that have a transformation.
        for comp in g.components:
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
            # Correct the position of the components
            comp.moveBy((horz_adjust, 0))
            comp.moveBy((0, vert_adjust))

        g.width += side_value * 2
    		
    def apply_tracking(self, tracking_value):
        f = self.csc.font.asFontParts()
        half = int(tracking_value/2)
        for layer in f.layers:
            for g in layer:
                if g.width == 0 and IGNORE_ZERO_WIDTH_GLYPHS:
                    continue
                if -half * 2 > g.width and FUTURE_NEGATIVE_WIDTHS != "allow negatives":
                    if FUTURE_NEGATIVE_WIDTHS == "limit to zero":
                        half = int(-g.width/2)
                    elif FUTURE_NEGATIVE_WIDTHS == "don’t change":
                        continue
                self.track_glyph_sides(g, half)
        
    def spaceCenterDidKeyUp(self, info):
        self.update_sliders()
        
    def spaceCenterDidChangeText(self, info):
        self.update_sliders()
        
    def update_sliders(self):
        self.csc = CurrentSpaceCenter()
        self.w.getItem('trackingSlider').set(self.csc.getTracking())
        
    def trackingSliderCallback(self, sender):
        self.csc = CurrentSpaceCenter()
        self.tracking = int(sender.get() / 2) * 2
        self.csc.setTracking(self.tracking)
        # self.w.getItem("trackingSlider").set(self.tracking)
        
    def applyButtonCallback(self, sender):
        self.tracking = self.w.getItem("trackingSlider").get()
        tracking_value = int(self.tracking) 
        self.apply_tracking(tracking_value)
        self.csc.setTracking(0)
        # self.csc.refreshGlyphLineView()
        # self.csc.updateGlyphLineView()
        self.csc.glyphLineView.refresh()
        print(f"Applied tracking of {tracking_value}.")


if CurrentFont():
    registerRoboFontSubscriber(Tracker)
