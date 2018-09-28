import textreport_ui_support as support

def setupSupport():
    """Replace the globals in textreport_ui_support with globals from this module
    so that ui_support can be freely regenerated."""

    support.closeWindow = closeWindowCb
    support.init = onInit


def onInit(top, gui, *args, **kwargs):
    # global w, top_level, root
    support.w = gui
    support.top_level = top
    support.root = top
    prepareTextReport()


# TODO: Turn this into a base class for other windows
class TextReport():
    """An adapter for textreport_ui_support to make the names more understandable."""

    def frame(self):
        return support.top_level

    def controls(self):
        return support.w

    def controlVars(self):
        return support

    def create(self, root, *args, **kwargs):
        """Return an exisiting window or create a new window."""

        import textreport_ui
        try:
            # return an existing window if it was already created
            if support.top_level is not None:
                return (self.frame(), self.controls())
        except: pass

        # create a new window
        (frame, controls) = textreport_ui.create_Report(root, *args, **kwargs)
        frame.protocol("WM_DELETE_WINDOW", closeWindowCb)

        return (frame, controls)


def prepareTextReport():
    pass


def closeWindowCb():
    support.destroy_window()
