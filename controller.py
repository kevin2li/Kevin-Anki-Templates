# -*- coding: utf-8 -*-
# Handles the main integration with Anki
# -------------------------------------------------------
instance = None

import json
import os
import re
import time
import traceback
from pathlib import Path

import aqt
from anki.hooks import addHook, wrap
from aqt import dialogs, mw
from bs4 import BeautifulSoup

from .edit import Edit


def run():
    global instance
    instance = Controller(mw)
    instance.setupBindings(mw.reviewer, wrap)


class Controller:
    _mw = None
    def __init__(self, ankiMw):
        self._mw = ankiMw
        self.counter = 1
        self.origin_note = None
        self.temp_note = None

    def setupBindings(self, reviewer, wrapFn):
        if not reviewer:
            print('No reviewer')
            return

        # Editor
        addHook("setupEditorButtons", self.setupEditorButtons)
        addHook("setupEditorShortcuts", self.setupShortcuts)

    def setupEditorButtons(self, buttons, editor):
        """Add buttons to editor"""

        def addTkMarkup(arg):
            editor.web.eval(f"wrap('[[c{self.counter}::', ']]');")
            self.counter += 1
        editor._links['guru-cloze'] = addTkMarkup
        
        def resetCounter(arg):
            self.counter = 1
        editor._links['guru-reset-counter'] = resetCounter

        def updateImageCloze(arg):
            try:
                (creator, instance) = dialogs._dialogs['Browser']
                if instance is None:
                    return []
                t = int(time.time()*1000)
                selectedNotes = instance.selectedNotes()
                self.origin_note = selectedNotes[0]
                note = mw.col.get_note(selectedNotes[0])
                model = note.note_type()
                if model['name'] != 'Kevin Image Cloze':
                    return
                fields = {}
                for info in model['flds']:
                    order = info['ord']
                    name = info['name']
                    fields[name] = note.fields[order]
                soup = BeautifulSoup(fields['Image'], 'html.parser')
                img = soup.find('img')
                src = img.get('src')
                mask_groups = json.loads(fields['Masks'])
                occlusion_str = ""
                for k, mask_group in enumerate(mask_groups):
                    for bbox in mask_group:
                        occlusion_str += f"{{{{c{k+1}::image-occlusion:rect:left={bbox[0]}:top={bbox[1]}:width={bbox[2]}:height={bbox[3]}:oi=1}}}}<br>"
                if not occlusion_str:
                    occlusion_str = "{{c1::image-occlusion:rect:left=0:top=0:width=0.1:height=0.1:oi=1}}"
                img_path = os.path.join(mw.col.media._dir, src)
                mw.col.add_image_occlusion_note(0, img_path, occlusion_str, "", "", [])
                res = mw.col.db.list("select distinct(n.id) from notes n order by n.id desc limit 1")
                self.temp_note = res[0]
                Edit(self.temp_note, self.origin_note)
            except:
                traceback.print_exc()

        editor._links['update-image-cloze'] = updateImageCloze

        add_cloze_button = editor._addButton(
            str(Path(__file__).parent.absolute() / 'resources/horizontal-fill-blank.svg'),
            'guru-cloze',
            "Kevin Text Cloze('Ctrl+Alt+z')",
            toggleable=False,
            id='bt_add_tk'
        )
        
        reset_counter_button = editor._addButton(
            str(Path(__file__).parent.absolute() / 'resources/reset.svg'),
            'guru-reset-counter',
            "Kevin Text Cloze reset counter('Ctrl+Alt+c')",
            toggleable=False,
            id='bt_add_tk'
        )

        update_image_cloze_button = editor._addButton(
            str(Path(__file__).parent.absolute() / 'resources/modify.svg'),
            'update-image-cloze',
            "Update Kevin Image Cloze",
            toggleable=False,
            id='bt_add_tk'
        )
        return buttons + [add_cloze_button, reset_counter_button, update_image_cloze_button]

    def setupShortcuts(self, scuts:list, editor):
        def addTkMarkup():
            editor.web.eval(f"wrap('[[c{self.counter}::', ']]');")
            self.counter += 1
        def resetCounter():
            self.counter = 1
        scuts.append(('Ctrl+Alt+z', addTkMarkup))
        scuts.append(('Ctrl+Alt+c', resetCounter))
