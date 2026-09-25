import os
import shutil
import hou

try:
    from PySide6 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui

TEXTURE_EXTENSIONS = {
    ".rat", ".tx", ".exr", ".png", ".jpg", 
    ".jpeg", ".tif", ".tiff", ".tga", ".hdr", 
    ".dds", ".bmp", ".psd"
}

GEOMETRY_EXTENSIONS = {
    ".fbx", ".obj", ".abc", ".usd", ".usda", ".usdc", ".ply"
}

LOOKDEV_EXTENSIONS = {
    ".cube", ".look", ".3dl", ".mtlx"
}

MISC_EXTENSIONS = {
    ".ttf", ".otf", ".wav", ".mp3", ".csv", ".json", ".py", ".h"
}

EXCLUDE_CACHE_EXTS = {
    ".bgeo", ".sc", ".gz", ".vdb", ".nvdb", ".sim", ".simdata", ".pc"
}


def resolve_material_container_name(node):
    curr = node
    highest_mat_node = None
    
    while curr and curr != hou.root():
        type_name = curr.type().name().lower()
        cat_name = curr.type().category().name().lower()

        is_rs_mat = "redshift" in type_name and ("material" in type_name or "vopnet" in type_name)
        is_std_mat = "material" in type_name or "builder" in type_name or "matnet" in type_name
        is_mat_cat = cat_name in ("shop", "vopnet")

        if is_rs_mat or is_std_mat or is_mat_cat:
            highest_mat_node = curr.name()
            
        parent = curr.parent()
        if parent and parent != hou.root():
            p_type = parent.type().name().lower()
            if "redshift" in p_type or "material" in p_type or "builder" in p_type:
                highest_mat_node = parent.name()

        curr = curr.parent()

    return highest_mat_node


class CollectBoxDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(CollectBoxDialog, self).__init__(parent or hou.qt.mainWindow())
        self.setWindowTitle("CollectBox")
        self.setMinimumWidth(620)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Window)

        self.build_ui()
        self.apply_dark_style()
        self.init_paths()

    def build_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setSpacing(9)
        main_layout.setContentsMargins(14, 12, 14, 12)

        # ---------------- 1. Target Directory ----------------
        dir_group = QtWidgets.QGroupBox("Destination")
        dir_layout = QtWidgets.QHBoxLayout(dir_group)
        dir_layout.setSpacing(6)

        self.txt_path = QtWidgets.QLineEdit()
        self.txt_path.setPlaceholderText("Select Destination Directory...")
        self.btn_browse = QtWidgets.QPushButton("Browse")
        self.btn_browse.setFixedWidth(75)
        self.btn_browse.clicked.connect(self.browse_target_directory)

        dir_layout.addWidget(self.txt_path)
        dir_layout.addWidget(self.btn_browse)
        main_layout.addWidget(dir_group)

        # ---------------- 2. Collection Filters ----------------
        filter_group = QtWidgets.QGroupBox("Asset Categories")
        filter_layout = QtWidgets.QVBoxLayout(filter_group)
        filter_layout.setSpacing(6)

        self.chk_tex = QtWidgets.QCheckBox("Textures (Organized by Material Name)")
        self.chk_tex.setChecked(True)

        self.chk_geo = QtWidgets.QCheckBox("Geometries (.fbx, .obj, .abc, .usd, etc.)")
        self.chk_geo.setChecked(True)

        self.chk_look = QtWidgets.QCheckBox("LookDev & LUTs (.cube, .mtlx, etc.)")
        self.chk_look.setChecked(True)

        self.chk_misc = QtWidgets.QCheckBox("Misc Assets (Fonts, Audio, Scripts)")
        self.chk_misc.setChecked(False)

        self.chk_copy_hip = QtWidgets.QCheckBox("Save Clean HIP File to Target Root")
        self.chk_copy_hip.setChecked(True)

        self.chk_open_hip = QtWidgets.QCheckBox("Open Collected HIP after export")
        self.chk_open_hip.setChecked(False)

        filter_layout.addWidget(self.chk_tex)
        filter_layout.addWidget(self.chk_geo)
        filter_layout.addWidget(self.chk_look)
        filter_layout.addWidget(self.chk_misc)
        filter_layout.addWidget(self.chk_copy_hip)
        filter_layout.addWidget(self.chk_open_hip)
        main_layout.addWidget(filter_group)

        # ---------------- 3. Console Output (16px) ----------------
        self.txt_log = QtWidgets.QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setMinimumHeight(200)
        main_layout.addWidget(self.txt_log)

        # ---------------- 4. Action Button ----------------
        self.btn_collect = QtWidgets.QPushButton("Collect Assets")
        self.btn_collect.setStyleSheet("font-weight: bold; font-size: 13px; padding: 7px 0px; background-color: #3b5998;")
        self.btn_collect.clicked.connect(self.run_collection)
        main_layout.addWidget(self.btn_collect)

        # ---------------- 5. Footer ----------------
        footer = QtWidgets.QHBoxLayout()
        footer.setContentsMargins(2, 4, 2, 2)

        lbl_copy = QtWidgets.QLabel("©2026 by Saeid Yaghani. All rights reserved.")
        lbl_copy.setStyleSheet("color: #a5a5a5; font-size: 12.5px; font-weight: 500;")

        lbl_link = QtWidgets.QLabel('<a href="https://www.instagram.com/saeidyaghani" style="color: #4da6ff; text-decoration: none; font-size: 12.5px; font-weight: bold;">https://www.instagram.com/saeidyaghani</a>')
        lbl_link.setOpenExternalLinks(True)

        footer.addWidget(lbl_copy)
        footer.addStretch()
        footer.addWidget(lbl_link)
        main_layout.addLayout(footer)

    def apply_dark_style(self):
        self.setStyleSheet("""
            QDialog { background-color: #242424; color: #ddd; font-family: 'Segoe UI', sans-serif; font-size: 12px; }
            QGroupBox { border: 1px solid #383838; border-radius: 4px; margin-top: 10px; padding-top: 10px; font-weight: bold; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; color: #aaa; }
            QLineEdit { background-color: #1a1a1a; border: 1px solid #3a3a3a; border-radius: 3px; padding: 4px; color: #eee; font-size: 13px; }
            QTextEdit { 
                background-color: #141414; 
                border: 1px solid #363636; 
                border-radius: 4px; 
                font-family: 'Consolas', 'Cascadia Code', 'Courier New', monospace; 
                font-size: 16px; 
                font-weight: 500;
                line-height: 1.5;
                padding: 10px;
                color: #e6e6e6; 
            }
            QPushButton { background-color: #383838; border: 1px solid #484848; border-radius: 3px; padding: 4px 10px; color: #eee; }
            QPushButton:hover { background-color: #484848; border-color: #585858; }
            QPushButton:pressed { background-color: #2a2a2a; }
            QCheckBox { spacing: 6px; }
        """)

    def init_paths(self):
        hip_dir = hou.hscriptExpandString("$HIP")
        hip_name = hou.hipFile.basename()
        project_stem = os.path.splitext(hip_name)[0]
        
        if not project_stem or project_stem.startswith("untitled"):
            folder_name = "project_collected"
        else:
            folder_name = f"{project_stem}_collected"

        default_dir = os.path.join(hip_dir, folder_name)
        self.txt_path.setText(default_dir)

    def log(self, text):
        self.txt_log.append(text)
        QtWidgets.QApplication.processEvents()

    def browse_target_directory(self):
        sel_dir = hou.ui.selectFile(
            start_directory=self.txt_path.text(),
            title="Select Target Folder for Collection",
            file_type=hou.fileType.Directory
        )
        if sel_dir:
            expanded = hou.text.expandString(sel_dir).rstrip("/\\")
            self.txt_path.setText(expanded)

    def run_collection(self):
        if hou.hipFile.isNewFile():
            hou.ui.displayMessage("Please save the .hip file first.", severity=hou.severityType.Warning)
            return

        base_collect_dir = self.txt_path.text().strip()
        if not base_collect_dir:
            hou.ui.displayMessage("Target directory is empty.", severity=hou.severityType.Warning)
            return

        base_collect_dir = hou.text.expandString(base_collect_dir).rstrip("/\\")
        os.makedirs(base_collect_dir, exist_ok=True)

        original_hip_path = hou.hipFile.path()
        original_hip_name = os.path.basename(original_hip_path)
        dest_hip_path = os.path.join(base_collect_dir, original_hip_name)

        self.txt_log.clear()
        self.log(f"== Starting Collection to: {base_collect_dir} ==")

        allowed_exts = set()
        if self.chk_tex.isChecked():
            allowed_exts |= TEXTURE_EXTENSIONS
        if self.chk_geo.isChecked():
            allowed_exts |= GEOMETRY_EXTENSIONS
        if self.chk_look.isChecked():
            allowed_exts |= LOOKDEV_EXTENSIONS
        if self.chk_misc.isChecked():
            allowed_exts |= MISC_EXTENSIONS

        collected_stats = {"Textures": 0, "Geometries": 0, "LookDev": 0, "Misc": 0, "Skipped": 0}
        repath_cache = []

        self.btn_collect.setEnabled(False)
        self.btn_collect.setText("Collecting...")
        QtWidgets.QApplication.processEvents()

        with hou.InterruptableOperation("Collecting Assets...", open_interrupt_dialog=True):
            for parm, raw_path in hou.fileReferences():
                if parm is None or not raw_path:
                    continue

                if parm.isLocked() or parm.isTimeDependent():
                    continue

                expanded_path = hou.text.expandString(raw_path)
                clean_path = expanded_path.split("?")[0].strip()
                lower_clean = clean_path.lower()

                if any(lower_clean.endswith(ext) for ext in EXCLUDE_CACHE_EXTS) or ".bgeo." in lower_clean:
                    continue

                _, ext = os.path.splitext(lower_clean)
                if ext not in allowed_exts:
                    continue

                if not os.path.isfile(clean_path):
                    collected_stats["Skipped"] += 1
                    self.log(f"[Missing] {clean_path}")
                    continue

                node = parm.node()
                filename = os.path.basename(clean_path)

                if ext in TEXTURE_EXTENSIONS:
                    mat_folder = resolve_material_container_name(node) or "textures_misc"
                    sub_dir = os.path.join(base_collect_dir, "tex", mat_folder)
                    rel_prefix = f"$HIP/tex/{mat_folder}"
                    cat_key = "Textures"
                elif ext in GEOMETRY_EXTENSIONS:
                    sub_dir = os.path.join(base_collect_dir, "geo")
                    rel_prefix = "$HIP/geo"
                    cat_key = "Geometries"
                elif ext in LOOKDEV_EXTENSIONS:
                    sub_dir = os.path.join(base_collect_dir, "lut")
                    rel_prefix = "$HIP/lut"
                    cat_key = "LookDev"
                else:
                    sub_dir = os.path.join(base_collect_dir, "misc")
                    rel_prefix = "$HIP/misc"
                    cat_key = "Misc"

                os.makedirs(sub_dir, exist_ok=True)
                dest_file_path = os.path.join(sub_dir, filename)

                try:
                    if not os.path.exists(dest_file_path) or os.path.getsize(dest_file_path) != os.path.getsize(clean_path):
                        shutil.copy2(clean_path, dest_file_path)

                    new_parm_value = f"{rel_prefix}/{filename}".replace("\\", "/")
                    
                    if not parm.node().isInsideLockedHDA():
                        repath_cache.append((parm, raw_path, new_parm_value))

                    collected_stats[cat_key] += 1
                    self.log(f"[Copied] {filename} -> {cat_key}")

                except Exception as e:
                    self.log(f"[Error] {clean_path}: {e}")

            if self.chk_copy_hip.isChecked():
                try:
                    for parm, orig_val, new_val in repath_cache:
                        parm.set(new_val)

                    hou.hipFile.save(dest_hip_path)
                    self.log(f"[Saved HIP] {dest_hip_path}")

                    if self.chk_open_hip.isChecked():
                        hou.hipFile.open(dest_hip_path, suppress_save_prompt=True)
                    else:
                        for parm, orig_val, new_val in repath_cache:
                            parm.set(orig_val)
                        hou.hipFile.setName(original_hip_path)

                except Exception as e:
                    self.log(f"[HIP Save Error] {e}")

        self.btn_collect.setEnabled(True)
        self.btn_collect.setText("Collect Assets")

        summary = ", ".join([f"{k}: {v}" for k, v in collected_stats.items()])
        self.log(f"\n== Complete! ({summary}) ==")


def launch_collectbox():
    global collectbox_window
    try:
        collectbox_window.close()
        collectbox_window.deleteLater()
    except:
        pass
    collectbox_window = CollectBoxDialog()
    collectbox_window.show()