"""Native GTK interface. All I/O runs off the GTK main thread."""
import os
import threading
import time
from pathlib import Path
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk, Pango

from . import __version__
from .devices import (DeviceError, descendants, device_number, select_devices,
                      snapshot)
from .engine import PreparedImage, write_image
from .streams import Cancelled
from .udisks import UDisks
from .i18n import tr


STYLE = b"""
#distroflash { background-color: @theme_bg_color; }
#distroflash .brand {
    background-color: #102b40; color: #f4fafb;
    border-radius: 14px; padding: 20px;
}
#distroflash .brand-title { font-size: 24pt; font-weight: 700; }
#distroflash .brand-copy { color: #d3e7ed; }
#distroflash .stage {
    background-color: @theme_base_color;
    border: 1px solid alpha(@theme_fg_color, 0.18);
    border-radius: 10px; padding: 16px;
}
#distroflash .stage-title { font-size: 12pt; font-weight: 600; }
#distroflash .step {
    background-color: #102b40; color: #ffffff;
    border-radius: 16px; min-width: 30px; min-height: 30px;
    font-weight: 700;
}
#distroflash .hint { color: mix(@theme_text_color, @theme_base_color, 0.2); }
#distroflash button { min-height: 30px; padding: 5px 14px; border-radius: 6px; }
#distroflash combobox button { min-height: 32px; }
#distroflash button:focus, #distroflash combobox:focus {
    outline: 2px solid @theme_selected_bg_color; outline-offset: 2px;
}
#distroflash button.suggested-action:not(:disabled) {
    background-image: none; background-color: #087f78;
    color: #ffffff; border-color: #087f78; text-shadow: none;
}
#distroflash button.suggested-action:hover:not(:disabled) { background-color: #066b65; }
#distroflash button.suggested-action:active:not(:disabled) { background-color: #055952; }
#distroflash progressbar trough { min-height: 8px; border-radius: 4px; }
#distroflash progressbar progress {
    min-height: 8px; background-image: none; background-color: #087f78;
    border-color: #087f78; border-radius: 4px;
}
"""


def capacity(size):
    return f"{size / 1024**3:.1f} GiB"


class Window(Gtk.ApplicationWindow):
    def __init__(self, application):
        super().__init__(application=application, title="DistroFlash")
        self.set_default_size(780, 740)
        self.set_name("distroflash")
        self.style = Gtk.CssProvider()
        self.style.load_from_data(STYLE)
        Gtk.StyleContext.add_provider_for_screen(
            self.get_screen(), self.style, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.connect("destroy", lambda *_: Gtk.StyleContext.remove_provider_for_screen(
            self.get_screen(), self.style))
        self.image = None
        self.devices = []
        self.busy = False
        self.cancel = threading.Event()
        self.last_report = 0
        self.indeterminate = False
        self.phase = ""
        self.phase_started = time.monotonic()
        self.connect("delete-event", self.on_close)

        header = Gtk.HeaderBar(title="DistroFlash", subtitle=tr('Linux and Windows · {0}').format(__version__))
        header.set_show_close_button(True)
        self.set_titlebar(header)
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.add(scroll)
        layout = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        layout.set_border_width(20)
        scroll.add(layout)
        logo = Path(__file__).with_name("logo.svg")
        self.set_icon_from_file(str(logo))
        brand = Gtk.Box(spacing=16)
        brand.get_style_context().add_class("brand")
        symbol = Gtk.Image.new_from_file(str(logo))
        symbol.get_accessible().set_name("DistroFlash")
        brand.pack_start(symbol, False, False, 0)
        description = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        title = Gtk.Label(xalign=0)
        title.set_text("DistroFlash")
        title.get_style_context().add_class("brand-title")
        description.pack_start(title, False, False, 0)
        tagline = self.label(tr('Create a bootable USB in three steps.'))
        tagline.set_selectable(False)
        tagline.get_style_context().add_class("brand-copy")
        description.pack_start(tagline, False, False, 0)
        brand.pack_start(description, True, True, 0)
        layout.pack_start(brand, False, False, 0)
        source, source_heading = self.stage(layout, "1", tr('Image'))
        self.choose = Gtk.Button.new_with_mnemonic(tr('Choose _image…'))
        self.choose.connect("clicked", self.choose_image)
        source_heading.pack_end(self.choose, False, False, 0)
        self.image_label = self.label(tr('Linux/Windows ISO, or IMG, RAW and BIN.'))
        self.image_label.get_style_context().add_class("hint")
        source.pack_start(self.image_label, False, False, 0)

        destination, row = self.stage(layout, "2", tr('USB/SD device'))
        self.refresh_button = Gtk.Button.new_with_mnemonic(tr('_Refresh'))
        self.refresh_button.connect("clicked", self.refresh)
        row.pack_end(self.refresh_button, False, False, 0)
        self.combo = Gtk.ComboBoxText()
        self.combo.set_hexpand(True)
        self.combo.get_accessible().set_name(tr('USB/SD device'))
        cell = self.combo.get_cells()[0]
        cell.set_property("ellipsize", Pango.EllipsizeMode.END)
        cell.set_property("max-width-chars", 44)
        self.combo.connect("changed", lambda _: self.controls())
        destination.pack_start(self.combo, False, False, 0)
        self.device_hint = self.label(tr('Internal disks and devices used by the system are excluded.'))
        self.device_hint.get_style_context().add_class("hint")
        destination.pack_start(self.device_hint, False, False, 0)
        row = Gtk.Box(spacing=8)
        self.unmount = Gtk.Button.new_with_mnemonic(tr('_Unmount partitions'))
        self.unmount.connect("clicked", self.unmount_selected)
        row.pack_start(self.unmount, False, False, 0)
        self.eject = Gtk.Button.new_with_mnemonic(tr('_Eject'))
        self.eject.connect("clicked", self.eject_selected)
        row.pack_start(self.eject, False, False, 0)
        destination.pack_start(row, False, False, 0)
        writing, _ = self.stage(layout, "3", tr('Write and verify'))
        self.status = self.label(tr('Select an image to begin.'))
        writing.pack_start(self.status, False, False, 0)
        self.bar = Gtk.ProgressBar(show_text=True)
        writing.pack_start(self.bar, False, False, 0)
        warning = self.label(tr('Writing erases the selected device. No persistence.'))
        warning.get_style_context().add_class("hint")
        writing.pack_start(warning, False, False, 0)
        row = Gtk.Box(spacing=8)
        self.stop = Gtk.Button.new_with_mnemonic(tr('_Cancel'))
        self.stop.connect("clicked", self.stop_work)
        row.pack_start(self.stop, False, False, 0)
        self.start = Gtk.Button.new_with_mnemonic(tr('_Write and verify'))
        self.start.get_style_context().add_class("suggested-action")
        self.start.connect("clicked", self.start_write)
        row.pack_end(self.start, False, False, 0)
        writing.pack_start(row, False, False, 0)
        self.controls()
        GLib.timeout_add(100, self.pulse)
        GLib.idle_add(self.refresh)

    @staticmethod
    def stage(layout, number, text):
        panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        panel.get_style_context().add_class("stage")
        heading = Gtk.Box(spacing=12)
        step = Gtk.Label(label=number)
        step.get_style_context().add_class("step")
        step.set_valign(Gtk.Align.CENTER)
        heading.pack_start(step, False, False, 0)
        title = Gtk.Label(label=text, xalign=0)
        title.get_style_context().add_class("stage-title")
        heading.pack_start(title, False, False, 0)
        panel.pack_start(heading, False, False, 0)
        layout.pack_start(panel, False, False, 0)
        return panel, heading

    @staticmethod
    def label(text):
        label = Gtk.Label(label=text, xalign=0)
        label.set_line_wrap(True)
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_max_width_chars(64)
        label.set_selectable(True)
        return label

    def selected(self):
        index = self.combo.get_active()
        return self.devices[index] if 0 <= index < len(self.devices) else None

    def controls(self):
        self.combo.set_tooltip_text(self.combo.get_active_text())
        for widget in (self.choose, self.refresh_button, self.combo):
            widget.set_sensitive(not self.busy)
        target = self.selected()
        self.unmount.set_sensitive(not self.busy and target is not None)
        self.eject.set_sensitive(not self.busy and target is not None)
        self.start.set_sensitive(not self.busy and target is not None and self.image is not None)
        self.stop.set_sensitive(self.busy and not self.cancel.is_set())

    def pulse(self):
        if self.busy and self.indeterminate:
            self.bar.pulse()
            elapsed = int(time.monotonic() - self.phase_started)
            self.bar.set_text(f"{self.phase} · {elapsed // 60:02d}:{elapsed % 60:02d}")
        return True

    def report(self, phase, done=0, total=0):
        now = time.monotonic()
        if total and done != total and now - self.last_report < 0.1:
            return
        self.last_report = now
        GLib.idle_add(self.show_progress, phase, done, total)

    def show_progress(self, phase, done, total):
        self.indeterminate = not total
        self.status.set_text(phase)
        self.bar.set_fraction(done / total if total else 0)
        if self.phase != phase:
            self.phase = phase
            self.phase_started = time.monotonic()
        elapsed = max(0.1, time.monotonic() - self.phase_started)
        self.bar.set_text(f"{done / total:.0%} · {done / elapsed / 1024**2:.1f} MiB/s" if total else phase)

    def launch(self, action, complete, message):
        self.busy = True
        self.cancel = threading.Event()
        self.show_progress(message, 0, 0)
        self.controls()

        def worker():
            result, error = None, None
            try:
                result = action()
            except Exception as exception:
                error = exception
            GLib.idle_add(finish, result, error)

        def finish(result, error):
            self.busy = False
            self.indeterminate = False
            self.bar.set_fraction(0)
            self.bar.set_text("")
            if error:
                self.status.set_text(str(error))
                if not isinstance(error, Cancelled):
                    self.error_dialog(str(error))
            else:
                complete(result)
            self.controls()

        threading.Thread(target=worker, name="distroflash-worker", daemon=False).start()

    def error_dialog(self, message):
        dialog = Gtk.MessageDialog(transient_for=self, modal=True, message_type=Gtk.MessageType.ERROR,
                                   buttons=Gtk.ButtonsType.CLOSE, text=tr('Operation not completed'))
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()

    def choose_image(self, *_):
        dialog = Gtk.FileChooserDialog(title=tr('Choose image'), transient_for=self,
                                       action=Gtk.FileChooserAction.OPEN)
        dialog.add_buttons(tr('Cancel'), Gtk.ResponseType.CANCEL, tr('Open'), Gtk.ResponseType.OK)
        image_filter = Gtk.FileFilter()
        image_filter.set_name(tr('ISO, IMG, RAW and BIN images'))
        for extension in ("iso", "img", "raw", "bin"):
            image_filter.add_pattern("*." + extension)
            image_filter.add_pattern("*." + extension.upper())
        dialog.add_filter(image_filter)
        deep_check = Gtk.CheckButton.new_with_mnemonic(tr('_Deep Windows integrity check (slower)'))
        deep_check.set_tooltip_text(tr('Fully decompress and check Windows archives before writing. Written USB files are always verified.'))
        dialog.set_extra_widget(deep_check)
        deep_check.show()
        response = dialog.run()
        filename = dialog.get_filename()
        verify_archives = deep_check.get_active()
        dialog.destroy()
        if response != Gtk.ResponseType.OK:
            return
        previous, self.image = self.image, None

        def prepare():
            if previous:
                previous.close()
            return PreparedImage(filename, UDisks(), self.cancel, self.report,
                                 deep_check=verify_archives)

        def ready(image):
            self.image = image
            kind = tr('Windows · UEFI x64 · NTFS') if image.kind == "windows" else tr('Linux / raw image')
            self.image_label.set_text(tr('{0}\n{1} · at least {2}').format(Path(filename).name, kind, capacity(image.required_bytes)))
            self.status.set_text(tr('Image ready. Select the device and unmount its partitions.'))
            self.refresh()

        self.image_label.set_text(tr('Inspecting image…'))
        self.launch(prepare, ready, tr('Preparing image…'))

    def refresh(self, *_):
        if self.busy:
            return
        previous = self.selected()

        def load():
            nodes = snapshot()
            eligible = select_devices(nodes)
            if self.image:
                excluded = {n["name"] for n in nodes if any(
                    device_number(c["maj:min"]) == self.image.original[0] for c in descendants(n))}
                eligible = [d for d in eligible if d.path not in excluded]
            return eligible

        def ready(devices):
            self.combo.remove_all()
            self.devices = devices
            for device in devices:
                self.combo.append_text(f"{device.model} · {capacity(device.size)} · {device.path} · {device.serial}")
            index = next((i for i, d in enumerate(devices) if previous and d.identity == previous.identity), 0)
            self.combo.set_active(index if devices else -1)
            self.device_hint.set_text(tr('No usable USB/SD device. Connect the media and refresh.')
                                      if not devices else tr('Check the model, capacity and path before writing.'))
            self.status.set_text(tr('Ready.') if self.image else tr('Select an image to begin.'))

        self.launch(load, ready, tr('Scanning devices…'))

    def checked_target(self, device):
        nodes = snapshot()
        if not any(d.identity == device.identity for d in select_devices(nodes)):
            raise DeviceError(tr('Device changed or unsafe.'))
        node = next(n for n in nodes if n["name"] == device.path)
        if self.image and any(device_number(c["maj:min"]) == self.image.original[0] for c in descendants(node)):
            raise DeviceError(tr('This device contains the source image.'))
        return node

    def unmount_selected(self, *_):
        device = self.selected()
        if not device:
            return

        def action():
            storage = UDisks()
            node = self.checked_target(device)
            for child in reversed(list(descendants(node))):
                if any(child.get("mountpoints") or []):
                    self.checked_target(device)
                    storage.unmount(storage.block_path(device_number(child["maj:min"])))

        self.launch(action, lambda _: self.status.set_text(tr('Partitions unmounted. You can start writing.')),
                    tr('Unmounting partitions…'))

    def eject_selected(self, *_):
        device = self.selected()
        if not device:
            return

        def action():
            node = self.checked_target(device)
            if any(any(c.get("mountpoints") or []) for c in descendants(node)):
                raise DeviceError(tr('Unmount partitions before ejecting the device.'))
            storage = UDisks()
            drive = storage.properties(storage.block_path(device.number), "Block")["Drive"]
            props = storage.properties(drive, "Drive")
            method = "PowerOff" if props.get("CanPowerOff") else "Eject" if props.get("Ejectable") else None
            if not method:
                raise DeviceError(tr('Ejection unavailable: unmounted media can be removed.'))
            storage.call(drive, "Drive", method, "(a{sv})", ({},))

        self.launch(action, lambda _: self.refresh(), tr('Ejecting…'))

    def start_write(self, *_):
        device = self.selected()
        if not device or not self.image:
            return
        dialog = Gtk.Dialog(title=tr('Confirm erasure'), transient_for=self, modal=True)
        dialog.add_buttons(tr('Cancel'), Gtk.ResponseType.CANCEL, tr('Erase and write'), Gtk.ResponseType.OK)
        dialog.set_default_response(Gtk.ResponseType.CANCEL)
        box = dialog.get_content_area()
        box.set_border_width(20)
        box.set_spacing(12)
        box.add(self.label(tr('All data on {0} will be erased.\n{1} · {2} · {3}\n\nTo confirm, type {4}:').format(device.path, device.model, capacity(device.size), device.serial, device.path)))
        entry = Gtk.Entry()
        entry.get_accessible().set_name(tr('Device path to erase'))
        entry.connect("changed", lambda e: dialog.set_response_sensitive(
            Gtk.ResponseType.OK, e.get_text() == device.path))
        box.add(entry)
        dialog.set_response_sensitive(Gtk.ResponseType.OK, False)
        dialog.show_all()
        response = dialog.run()
        dialog.destroy()
        if response != Gtk.ResponseType.OK:
            return
        self.launch(lambda: write_image(self.image, device, UDisks(), self.cancel, self.report),
                    lambda _: self.status.set_text(tr('Writing and verification complete. You can eject the device.')),
                    tr('Final device check…'))

    def stop_work(self, *_):
        self.cancel.set()
        self.status.set_text(tr('Cancellation requested. Wait for the current operation to finish…'))
        self.controls()

    def on_close(self, *_):
        if self.busy:
            self.stop_work()
            return True
        if self.image:
            image, self.image = self.image, None
            self.launch(image.close, lambda _: self.destroy(), tr('Releasing image…'))
            return True
        return False


def main():
    if os.geteuid() == 0:
        raise SystemExit(tr('Run DistroFlash as a normal user: Polkit manages permissions.'))
    application = Gtk.Application(application_id="org.syslinuxos.DistroFlash")
    application.connect("activate", lambda app: (Window(app).show_all()
                        if not app.get_windows() else app.get_windows()[0].present()))
    return application.run(None)
