"""
Screen-edge posture border, a purely visual alert.

show() paints a thick colored ring around every screen; hide() removes it. Each
is a frameless, transparent, click-through NSWindow, fully decoupled from
Notification Center and audio.

Uses AppKit so the windows share the main-thread run loop that already drives
motion callbacks: no second event loop, no cross-thread marshaling. All AppKit
objects must be touched on the main thread; the monitor guarantees that.
"""

import objc
from AppKit import (
    NSApplication,
    NSApplicationActivationPolicyAccessory,
    NSBackingStoreBuffered,
    NSBezierPath,
    NSColor,
    NSScreen,
    NSScreenSaverWindowLevel,
    NSView,
    NSWindow,
    NSWindowCollectionBehaviorCanJoinAllSpaces,
    NSWindowCollectionBehaviorFullScreenAuxiliary,
    NSWindowCollectionBehaviorStationary,
    NSWindowStyleMaskBorderless,
)
from Foundation import NSInsetRect, NSMakeRect

from config import BORDER_COLOR, BORDER_THICKNESS


class _BorderView(NSView):
    """Paints a hollow rectangle at the window edge; center stays clear."""

    def initWithFrame_thickness_color_(self, frame, thickness, color):
        self = objc.super(_BorderView, self).initWithFrame_(frame)
        if self is None:
            return None
        self._thickness = thickness
        self._color = color
        return self

    def drawRect_(self, _dirty):
        # Inset by half the line width so the stroke isn't clipped at the edge.
        bounds = self.bounds()
        path = NSBezierPath.bezierPathWithRect_(
            NSInsetRect(bounds, self._thickness / 2.0, self._thickness / 2.0)
        )
        path.setLineWidth_(self._thickness)
        self._color.set()
        path.stroke()


class PostureBorder:
    """Colored edge border on all screens; show()/hide() are idempotent."""

    def __init__(self, thickness=BORDER_THICKNESS, color=BORDER_COLOR):
        """Register as an accessory app (no Dock icon, never steals focus).

        Windows are built lazily on first show() so screen geometry is current.
        """
        self._thickness = thickness
        red, green, blue, alpha = color
        self._color = NSColor.colorWithCalibratedRed_green_blue_alpha_(
            red, green, blue, alpha
        )
        self._windows = []
        self._visible = False
        # Accessory app: windows on screen with no Dock icon, no focus steal.
        NSApplication.sharedApplication().setActivationPolicy_(
            NSApplicationActivationPolicyAccessory
        )

    def _build_windows(self):
        """One frameless, transparent, click-through window per screen."""
        for screen in NSScreen.screens():
            frame = screen.frame()
            window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
                frame, NSWindowStyleMaskBorderless, NSBackingStoreBuffered, False
            )
            window.setOpaque_(False)
            window.setBackgroundColor_(NSColor.clearColor())
            window.setIgnoresMouseEvents_(True)  # clicks pass through
            window.setLevel_(NSScreenSaverWindowLevel)  # above fullscreen apps
            window.setCollectionBehavior_(
                NSWindowCollectionBehaviorCanJoinAllSpaces
                | NSWindowCollectionBehaviorStationary
                | NSWindowCollectionBehaviorFullScreenAuxiliary
            )
            size = frame.size
            view = _BorderView.alloc().initWithFrame_thickness_color_(
                NSMakeRect(0, 0, size.width, size.height), self._thickness, self._color
            )
            window.setContentView_(view)
            self._windows.append(window)

    def show(self):
        """Show the border on every screen (no-op if already visible)."""
        if self._visible:
            return
        if not self._windows:
            self._build_windows()
        for window in self._windows:
            window.orderFrontRegardless()
        self._visible = True

    def hide(self):
        """Hide the border (no-op if already hidden)."""
        if not self._visible:
            return
        for window in self._windows:
            window.orderOut_(None)
        self._visible = False

    def close(self):
        """Tear down all windows on monitor shutdown."""
        self.hide()
        for window in self._windows:
            window.close()
        self._windows = []


def main():
    """Manual test: flash the border ~3s then drop it. Run via AirpodsPosture.app."""
    from Foundation import NSDate, NSDefaultRunLoopMode, NSRunLoop

    border = PostureBorder()

    def pump(seconds):
        deadline = NSDate.dateWithTimeIntervalSinceNow_(seconds)
        while NSDate.date().compare_(deadline) < 0:
            NSRunLoop.currentRunLoop().runMode_beforeDate_(
                NSDefaultRunLoopMode, NSDate.dateWithTimeIntervalSinceNow_(0.1)
            )

    print("border ON — should see a red ring on every screen")
    border.show()
    pump(3)
    print("border OFF")
    border.hide()
    pump(1)
    border.close()


if __name__ == "__main__":
    main()