"""
A fake notification banner we draw with AppKit.

A real Notification Center banner kills the AirPods motion stream, so we
recreate the look (frosted top-right panel) with a plain window instead. Cost:
it won't show up in Notification Center history.

Like alert_border.py: touch all AppKit objects on the main thread. The daemon's
motion callbacks run on the main queue, so show()/hide() are called from there.
"""

from AppKit import (
    NSApplication,
    NSApplicationActivationPolicyAccessory,
    NSBackingStoreBuffered,
    NSColor,
    NSFont,
    NSFloatingWindowLevel,
    NSScreen,
    NSTextField,
    NSVisualEffectBlendingModeBehindWindow,
    NSVisualEffectMaterialHUDWindow,
    NSVisualEffectStateActive,
    NSVisualEffectView,
    NSWindow,
    NSWindowCollectionBehaviorCanJoinAllSpaces,
    NSWindowCollectionBehaviorFullScreenAuxiliary,
    NSWindowCollectionBehaviorStationary,
    NSWindowStyleMaskBorderless,
)
import objc
from Foundation import NSMakeRect, NSObject

from config import BANNER_WIDTH, BANNER_HEIGHT, BANNER_MARGIN, BANNER_DURATION_S


def _label(frame, size, bold, color):
    """Non-interactive text label, transparent background."""
    field = NSTextField.alloc().initWithFrame_(frame)
    field.setBezeled_(False)
    field.setDrawsBackground_(False)
    field.setEditable_(False)
    field.setSelectable_(False)
    font = NSFont.boldSystemFontOfSize_(size) if bold else NSFont.systemFontOfSize_(size)
    field.setFont_(font)
    field.setTextColor_(color)
    return field


class PostureBanner(NSObject):
    """Top-right banner; show()/hide() are idempotent.

    NSObject subclass so it can be an NSTimer target for auto-dismiss.
    """

    def init(self):
        self = objc.super(PostureBanner, self).init()
        if self is None:
            return None
        self._window = None
        self._icon = None
        self._title = None
        self._message = None
        self._visible = False
        self._timer = None
        # Accessory app: no Dock icon, never steals focus.
        NSApplication.sharedApplication().setActivationPolicy_(
            NSApplicationActivationPolicyAccessory
        )
        return self

    def _build_window(self):
        """Frosted click-through panel: icon + title + message."""
        w, h, pad = BANNER_WIDTH, BANNER_HEIGHT, 16
        window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(0, 0, w, h), NSWindowStyleMaskBorderless, NSBackingStoreBuffered, False
        )
        window.setOpaque_(False)
        window.setBackgroundColor_(NSColor.clearColor())
        window.setIgnoresMouseEvents_(True)          # clicks pass through
        window.setLevel_(NSFloatingWindowLevel)       # above normal
        window.setCollectionBehavior_(
            NSWindowCollectionBehaviorCanJoinAllSpaces
            | NSWindowCollectionBehaviorStationary
            | NSWindowCollectionBehaviorFullScreenAuxiliary
        )

        blur = NSVisualEffectView.alloc().initWithFrame_(NSMakeRect(0, 0, w, h))
        blur.setMaterial_(NSVisualEffectMaterialHUDWindow)
        blur.setBlendingMode_(NSVisualEffectBlendingModeBehindWindow)
        blur.setState_(NSVisualEffectStateActive)
        blur.setWantsLayer_(True)
        blur.layer().setCornerRadius_(16.0)
        blur.layer().setMasksToBounds_(True)

        white = NSColor.labelColor()
        self._icon = _label(NSMakeRect(pad, h / 2 - 22, 44, 44), 32, False, white)
        self._title = _label(NSMakeRect(pad + 52, h - 40, w - pad - 64, 22), 15, True, white)
        self._message = _label(NSMakeRect(pad + 52, 12, w - pad - 64, 40), 13, False,
                               NSColor.secondaryLabelColor())
        self._message.cell().setWraps_(True)
        for field in (self._icon, self._title, self._message):
            blur.addSubview_(field)

        window.setContentView_(blur)
        self._window = window

    def _position(self):
        """Top-right of the main screen, below the menu bar."""
        vis = NSScreen.mainScreen().visibleFrame()
        x = vis.origin.x + vis.size.width - BANNER_WIDTH - BANNER_MARGIN
        y = vis.origin.y + vis.size.height - BANNER_HEIGHT - BANNER_MARGIN
        self._window.setFrameOrigin_((x, y))

    def show_(self, info):
        """Show a banner. info is (title, message, emoji). Auto-dismisses."""
        title, message, emoji = info
        if self._window is None:
            self._build_window()
        self._icon.setStringValue_(emoji)
        self._title.setStringValue_(title)
        self._message.setStringValue_(message)
        self._position()
        self._window.orderFrontRegardless()
        self._visible = True
        self._arm_autohide()

    def _arm_autohide(self):
        """(Re)start the auto-dismiss timer."""
        from Foundation import NSTimer, NSRunLoop, NSDefaultRunLoopMode
        if self._timer is not None:
            self._timer.invalidate()
        self._timer = NSTimer.timerWithTimeInterval_target_selector_userInfo_repeats_(
            BANNER_DURATION_S, self, b"hide", None, False
        )
        NSRunLoop.currentRunLoop().addTimer_forMode_(self._timer, NSDefaultRunLoopMode)

    def hide(self):
        """Hide the banner (no-op if already hidden)."""
        if not self._visible:
            return
        if self._timer is not None:
            self._timer.invalidate()
            self._timer = None
        self._window.orderOut_(None)
        self._visible = False

    def close(self):
        """Tear down on daemon shutdown."""
        self.hide()
        if self._window is not None:
            self._window.close()
            self._window = None


def main():
    """Manual test: pop the banner, pump the run loop, exit. Run via AirpodsPosture.app."""
    from Foundation import NSDate, NSDefaultRunLoopMode, NSRunLoop

    banner = PostureBanner.alloc().init()

    def pump(seconds):
        deadline = NSDate.dateWithTimeIntervalSinceNow_(seconds)
        while NSDate.date().compare_(deadline) < 0:
            NSRunLoop.currentRunLoop().runMode_beforeDate_(
                NSDefaultRunLoopMode, NSDate.dateWithTimeIntervalSinceNow_(0.1)
            )

    print("banner ON — top-right, should look like a macOS notification")
    banner.show_(("Posture Check", "Your head's leaning forward — ease your chin back!", "🦒"))
    pump(BANNER_DURATION_S + 1)
    print("banner should have auto-dismissed")
    banner.close()


if __name__ == "__main__":
    main()
