import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio, GLib

class DexterOrganizerApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='org.example.DexterOrganizer')
        self.builder = None

    def do_activate(self, app):
        self.builder = Gtk.Builder.new_from_file('dexter.ui')
        window = self.builder.get_object('main_window')
        window.set_application(app)

        self.stack = self.builder.get_object('main_stack')

        # Conectar botones del menú
        self.builder.get_object('about_button').connect('clicked', self.on_about_clicked)
        self.builder.get_object('preferences_button').connect('clicked', self.on_preferences_clicked)

        window.present()

    def on_about_clicked(self, button):
        self.stack.set_visible_child_name("about")

    def on_preferences_clicked(self, button):
        self.stack.set_visible_child_name("preferences")


app = DexterOrganizerApp()
app.run()
