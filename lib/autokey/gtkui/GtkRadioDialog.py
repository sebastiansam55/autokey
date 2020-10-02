import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

import sys

class GtkRadioDialog(Gtk.Window):
	def __init__(self, title, choices):
		Gtk.Window.__init__(self, title=title)
		self.set_default_size(200,100)

		self.radioBox = Gtk.Box(spacing=6)
		self.radioBox.set_orientation(Gtk.Orientation.VERTICAL)

		firstRadioButton = Gtk.RadioButton.new_with_label_from_widget(None, choices[0])
		self.radioBox.pack_start(firstRadioButton, True, True, 0)
		if len(choices)>=2:
			for item in choices[1:]:
				rad = Gtk.RadioButton.new_with_label_from_widget(firstRadioButton, item)
				self.radioBox.pack_start(rad, True, True, 0)

		self.buttonBox = Gtk.Box(spacing=6)
		self.optionLabel = Gtk.Label()
		self.optionLabel.set_text("Choose a value")
		self.vbox = Gtk.Box(spacing=6)
		self.vbox.set_orientation(Gtk.Orientation.VERTICAL)
		self.vbox.pack_start(self.optionLabel, True, True, 0)
		self.vbox.pack_start(self.radioBox, True, True, 0)
		self.vbox.pack_start(self.buttonBox, True, True, 0)
		self.add(self.vbox)

		self.ok = Gtk.Button(label="ok")
		self.ok.connect("clicked", self.on_ok)
		self.cancel = Gtk.Button(label="cancel")
		self.cancel.connect("clicked", self.on_cancel)
		self.buttonBox.pack_start(self.ok, True, True, 0)
		self.buttonBox.pack_start(self.cancel, True, True, 0)

	def on_cancel(self, widget):
		Gtk.main_quit()

	def on_ok(self, widget):
		for item in self.radioBox:
			if item.get_active():
				print(item.get_label())
				Gtk.main_quit()

title = sys.argv[1]

win = GtkRadioDialog(sys.argv[1], sys.argv[2:])
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()

