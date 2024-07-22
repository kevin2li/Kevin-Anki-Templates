import glob
import json
import os
from pathlib import Path

import anki
from anki.hooks import addHook
from aqt import mw


def createOrUpdateTemplate():
    kevin_templates = []
    template_data_dir = Path(__file__).parent / "templates"
    meta_path_list = glob.glob(str(template_data_dir / "**" / "meta.json"), recursive=True)
    for path in meta_path_list:
        obj = {}
        with open(path, "r", encoding="utf-8") as f:
            meta = json.load(f)
            obj.update(meta)
        front_path = Path(path).parent / "front.html"
        back_path = Path(path).parent / "back.html"
        css_path = Path(path).parent / "style.css"
        with open(front_path, "r", encoding="utf-8") as f1,\
            open(back_path, "r", encoding="utf-8") as f2,\
            open(css_path, "r", encoding="utf-8") as f3:
            obj["Front"] = rf'{f1.read()}'
            obj["Back"]  = rf'{f2.read()}'
            obj["Css"]   = rf'{f3.read()}'
        kevin_templates.append(obj)
    for config in kevin_templates:
        model = mw.col.models.byName(config['Name'])
        if not model:
            createTemplate(config)
        else:
            updateTemplate(config)
    migrateAssets()

def createTemplate(config):
    m = mw.col.models
    model = m.new(config["Name"])
    model["flds"] = [m.newField(field) for field in config['Fields']]
    template = m.newTemplate(config["Name"])
    template["qfmt"] = config['Front']
    template["afmt"] = config['Back']
    model["css"] = config['Css']

    m.addTemplate(model, template)
    m.add(model)
    m.save(model)


def updateTemplate(config):
    m = mw.col.models
    model = mw.col.models.byName(config["Name"])
    model["tmpls"][0]["qfmt"] = config['Front']
    model["tmpls"][0]["afmt"] = config['Back']
    model["css"] = config['Css']
    mw.col.models.save(model)


def migrateAssets():
    asset_path_list = glob.glob(str(Path(__file__).parent / "assets" / "**" / "*"), recursive=True)
    mediaFolder = mw.col.media.dir()
    for asset_path in asset_path_list:
        asset_name = Path(asset_path).name
        target_path = str(Path(mediaFolder) / asset_name)
        if not os.path.exists(target_path):
            mw.col.media.add_file(asset_path)

addHook("profileLoaded", createOrUpdateTemplate)
