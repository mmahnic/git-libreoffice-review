import mainwin
import mainwin_ui
import socket
import traceback


if __name__ == '__main__':
    try:
        mainwin.setupUiMainSupport()
        mainwin_ui.vp_start_gui()
    except Exception as e:
        try:
            f = open( r"{}/grd-{}.out".format(os.getenv("TEMP", "C:/"), socket.gethostname()), "w" )
            f.write( "Error: {}".format( e ) )
            traceback.print_exc(file=f)
            f.close()
        except: pass
        raise e

