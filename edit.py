import json
import re

import aqt
import aqt.browser.previewer
import aqt.editor
from anki.errors import NotFoundError
from aqt.qt import QCloseEvent, QMainWindow, Qt
from aqt.utils import restoreGeom, saveGeom, tooltip


def occlusions2mask_groups(occlusions: str):
    pattern = r"\{\{c(\d+)::image-occlusion:rect:left=([\d.]+):top=([\d.]+):width=([\d.]+):height=([\d.]+):oi=1\}\}"
    result = {}
    for item in re.finditer(pattern, occlusions):
        k, left, top, width, height = item.groups()
        if k not in result:
            result[k] = []
        result[k].append([float(left), float(top), float(width), float(height)])
    mask_groups = [result[k] for k in result]
    return mask_groups


DOMAIN_PREFIX = "foosoft.ankiconnect."

# noinspection PyAttributeOutsideInit
class Edit(aqt.editcurrent.EditCurrent):
    dialog_geometry_tag = DOMAIN_PREFIX + "edit"
    dialog_registry_tag = DOMAIN_PREFIX + "Edit"
    dialog_search_tag = DOMAIN_PREFIX + "edit.history"

    def __init__(self, temp_note_id, origin_note_id):
        QMainWindow.__init__(self, None, Qt.WindowType.Window)
        self.note_id = temp_note_id
        self.origin_note_id = origin_note_id
        self.note = aqt.mw.col.get_note(temp_note_id)
        self.form = aqt.forms.editcurrent.Ui_Dialog()
        self.form.setupUi(self)
        self.setWindowTitle("Edit")
        self.setMinimumWidth(250)
        self.setMinimumHeight(400)
        restoreGeom(self, self.dialog_geometry_tag)

        self.form.buttonBox.setVisible(False)   # hides the Close button bar
        self.editor = aqt.editor.Editor(aqt.mw, self.form.fieldsArea, self)

        self.show()
        self.bring_to_foreground()
        self.show_note(self.note)

    def cleanup(self):
        self.editor.cleanup()
        saveGeom(self, self.dialog_geometry_tag)
        aqt.dialogs.markClosed(self.dialog_registry_tag)
        # get updated note masks
        note = aqt.mw.col.get_note(self.note_id)
        model = note.note_type()
        mask_groups = []
        fields = {}
        for info in model['flds']:
            order = info['ord']
            name = info['name']
            fields[name] = note.fields[order]
            if not mask_groups:
                mask_groups = occlusions2mask_groups(note.fields[order])
        aqt.mw.col.remove_notes([self.note_id])
        # update original note
        note = aqt.mw.col.get_note(self.origin_note_id)
        model = note.note_type()
        fields = {}
        for idx, info in enumerate(model['flds']):
            if info['name'] == "Masks":
                note.fields[info['ord']] = json.dumps(mask_groups, ensure_ascii=False)
                break
        (creator, instance) = aqt.dialogs._dialogs['Browser']
        if instance is None:
            return
        instance.table.clear_selection()
        aqt.mw.col.update_note(note)
        instance.table.select_single_card(note.cards()[0].id)

    def closeEvent(self, evt: QCloseEvent) -> None:
        self.editor.call_after_note_saved(self.cleanup)
    
    def bring_to_foreground(self):
        aqt.mw.app.processEvents()
        self.activateWindow()
        self.raise_()

    def show_note(self, note):
        cards = note.cards()
        self.editor.set_note(note)
        self.editor.card = cards[0] if cards else None

    def reload_notes_after_user_action_elsewhere(self):
        try:
            self.note.load()
        except NotFoundError:
            self.cleanup()
            return
        self.show_note(self.note)
