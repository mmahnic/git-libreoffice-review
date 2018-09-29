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
    gui.top_level = top
    prepareTextReport(gui)


def prepareTextReport(gui):
    pass


def getOrCreateTextReport(root, *args, **kwargs):
    """Return an exisiting window or create a new window."""

    import textreport_ui
    try:
        # return an existing window if it was already created
        if support.w is not None:
            gui = support.w
            return (gui.top_level, gui)
    except: pass

    # create a new window
    (frame, gui) = textreport_ui.create_Report(root, *args, **kwargs)
    frame.protocol("WM_DELETE_WINDOW", lambda: closeWindowCb(gui))

    return (frame, gui)


def closeWindowCb(gui):
    support.w = None
    support.top_level = None
    gui.top_level.destroy()
