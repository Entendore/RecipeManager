import sys, json, os, uuid, math
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton, QFormLayout,
    QComboBox, QSpinBox, QScrollArea, QMessageBox, QFileDialog,
    QStackedWidget, QFrame, QGridLayout, QGroupBox, QTabWidget,
    QSplitter, QCheckBox, QDialog, QSizePolicy, QTextBrowser
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor, QPen, QLinearGradient

# ─── Constants & Data ────────────────────────────────────────────────────────
DATA_FILE = "recipes.json"
CATEGORIES = ["Breakfast","Lunch","Dinner","Dessert","Snack","Appetizer","Soup","Salad","Beverage","Other"]
UNITS = ["cup","tablespoon","teaspoon","ounce","pound","gram","kilogram","ml","liter","piece","clove","slice","can","package","pinch","dash","to taste",""]
DIFFICULTIES = ["Easy","Medium","Hard"]
CATEGORY_COLORS = {
    "Breakfast":("#FF9A56","#FF6B35"),"Lunch":("#56C596","#2E8B57"),"Dinner":("#5B86E5","#36D1DC"),
    "Dessert":("#E84393","#FD79A8"),"Snack":("#FDCB6E","#F39C12"),"Appetizer":("#A29BFE","#6C5CE7"),
    "Soup":("#FF7675","#D63031"),"Salad":("#55EFC4","#00B894"),"Beverage":("#74B9FF","#0984E3"),
    "Other":("#B2BEC3","#636E72"),
}
SAMPLE_RECIPES = [
    {"name":"Classic Pancakes","category":"Breakfast","ingredients":[{"name":"all-purpose flour","quantity":"1.5","unit":"cup"},{"name":"sugar","quantity":"2","unit":"tablespoon"},{"name":"baking powder","quantity":"2","unit":"teaspoon"},{"name":"egg","quantity":"1","unit":"piece"},{"name":"milk","quantity":"1.25","unit":"cup"},{"name":"butter, melted","quantity":"3","unit":"tablespoon"},{"name":"vanilla extract","quantity":"1","unit":"teaspoon"}],"instructions":["Whisk flour, sugar, baking powder, and salt.","Add egg, milk, butter, and vanilla. Mix until just combined.","Heat pan over medium heat, grease with butter.","Pour 1/4 cup batter per pancake. Flip when bubbles form.","Cook 1-2 min until golden. Serve with syrup."],"prep_time":10,"cook_time":15,"servings":4,"difficulty":"Easy","notes":"Rest batter 5 min for fluffier results.","image_path":"","tags":["quick","kid-friendly"],"favorite":True},
    {"name":"Tomato Basil Soup","category":"Soup","ingredients":[{"name":"crushed tomatoes","quantity":"28","unit":"ounce"},{"name":"onion","quantity":"1","unit":"piece"},{"name":"garlic","quantity":"4","unit":"clove"},{"name":"broth","quantity":"2","unit":"cup"},{"name":"basil","quantity":"0.5","unit":"cup"},{"name":"cream","quantity":"0.25","unit":"cup"},{"name":"olive oil","quantity":"2","unit":"tablespoon"}],"instructions":["Sauté onion in olive oil until soft.","Add garlic, cook 1 min.","Add tomatoes and broth. Simmer 15 min.","Blend with basil until smooth.","Stir in cream, season, and serve."],"prep_time":10,"cook_time":25,"servings":4,"difficulty":"Easy","notes":"Freezes well.","image_path":"","tags":["vegetarian","winter"],"favorite":False},
    {"name":"Garlic Shrimp Pasta","category":"Dinner","ingredients":[{"name":"linguine","quantity":"12","unit":"ounce"},{"name":"shrimp","quantity":"1","unit":"pound"},{"name":"butter","quantity":"4","unit":"tablespoon"},{"name":"garlic","quantity":"6","unit":"clove"},{"name":"white wine","quantity":"0.5","unit":"cup"},{"name":"lemon juice","quantity":"2","unit":"tablespoon"},{"name":"parmesan","quantity":"0.5","unit":"cup"}],"instructions":["Cook pasta al dente. Reserve water.","Cook shrimp in 2 tbsp butter. Remove.","Add rest of butter and garlic, cook 1 min.","Deglaze with wine and lemon.","Toss pasta, shrimp, and sauce. Top with parmesan."],"prep_time":15,"cook_time":20,"servings":4,"difficulty":"Medium","notes":"","image_path":"","tags":["seafood","pasta"],"favorite":True},
]

# ─── Data Model ──────────────────────────────────────────────────────────────
class Recipe:
    def __init__(self, name="", category="Other"):
        self.id=str(uuid.uuid4());self.name=name;self.category=category;self.ingredients=[];self.instructions=[]
        self.prep_time=0;self.cook_time=0;self.servings=4;self.difficulty="Easy"
        self.notes="";self.image_path="";self.tags=[];self.favorite=False;self.created_at=datetime.now().isoformat()
    def to_dict(self): return {k:v for k,v in self.__dict__.items()}
    @classmethod
    def from_dict(cls, d):
        r=cls()
        for k,v in d.items(): setattr(r,k,v)
        return r

class RecipeStore:
    def __init__(self, path=DATA_FILE):
        self.path=path; self.recipes=[]; self._load()
    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path,"r",encoding="utf-8") as f: self.recipes=[Recipe.from_dict(d) for d in json.load(f)]
            except: self.recipes=[]
        else: self._seed()
    def _seed(self):
        for d in SAMPLE_RECIPES:
            r=Recipe()
            for k,v in d.items(): setattr(r,k,v)
            r.id=str(uuid.uuid4()); self.recipes.append(r)
        self.save()
    def save(self):
        with open(self.path,"w",encoding="utf-8") as f: json.dump([r.to_dict() for r in self.recipes], f, indent=2, ensure_ascii=False)
    def add(self, r): self.recipes.append(r); self.save()
    def update(self, r):
        for i,rr in enumerate(self.recipes):
            if rr.id==r.id: self.recipes[i]=r; break
        self.save()
    def delete(self, rid): self.recipes=[r for r in self.recipes if r.id!=rid]; self.save()
    def search(self, q="", cat="All", fav=False):
        res=self.recipes
        if fav: res=[r for r in res if r.favorite]
        if cat!="All": res=[r for r in res if r.category==cat]
        if q:
            ql=q.lower()
            res=[r for r in res if ql in r.name.lower() or ql in r.category.lower() or any(ql in i.get("name","").lower() for i in r.ingredients) or any(ql in t.lower() for t in r.tags)]
        return res

# ─── Cooking Timer ───────────────────────────────────────────────────────────
class CookingTimer(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⏱ Cooking Timer")
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint | Qt.WindowCloseButtonHint)
        self.setFixedSize(280, 180)
        self.seconds_left = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        
        lay = QVBoxLayout(self)
        self.time_lbl = QLabel("00:00")
        self.time_lbl.setObjectName("timerDisplay")
        self.time_lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.time_lbl)
        
        ctrl = QHBoxLayout()
        self.mins = QSpinBox(); self.mins.setRange(0, 999); self.mins.setSuffix(" min"); self.mins.setValue(5)
        self.start_btn = QPushButton("Start"); self.start_btn.setObjectName("saveBtn")
        self.start_btn.clicked.connect(self.start)
        self.pause_btn = QPushButton("Pause"); self.pause_btn.setObjectName("cancelBtn")
        self.pause_btn.clicked.connect(self.pause)
        self.reset_btn = QPushButton("Reset"); self.reset_btn.clicked.connect(self.reset)
        ctrl.addWidget(self.mins); ctrl.addWidget(self.start_btn); ctrl.addWidget(self.pause_btn); ctrl.addWidget(self.reset_btn)
        lay.addLayout(ctrl)

    def start(self):
        if self.seconds_left == 0: self.seconds_left = self.mins.value() * 60
        self.timer.start(1000); self.update_display()

    def pause(self): self.timer.stop()

    def reset(self): self.timer.stop(); self.seconds_left=0; self.update_display()

    def tick(self):
        self.seconds_left -= 1
        self.update_display()
        if self.seconds_left <= 0:
            self.timer.stop()
            QMessageBox.information(self, "Timer!", "⏰ Time is up!")

    def update_display(self):
        m, s = divmod(max(0, self.seconds_left), 60)
        self.time_lbl.setText(f"{m:02d}:{s:02d}")

# ─── Editor Components ───────────────────────────────────────────────────────
class IngredientEditRow(QWidget):
    remove_clicked = Signal(object); changed = Signal()
    def __init__(self, name="", qty="", unit=""):
        super().__init__(); self.setFixedHeight(36)
        lay = QHBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(4)
        self.name_e = QLineEdit(name); self.name_e.setPlaceholderText("Ingredient")
        self.qty_e = QLineEdit(qty); self.qty_e.setPlaceholderText("Qty"); self.qty_e.setFixedWidth(60)
        self.unit_e = QComboBox(); self.unit_e.addItems(UNITS); self.unit_e.setCurrentText(unit); self.unit_e.setEditable(True); self.unit_e.setFixedWidth(110)
        btn = QPushButton("✕"); btn.setObjectName("removeRowBtn"); btn.setFixedSize(24,24)
        btn.clicked.connect(lambda: self.remove_clicked.emit(self))
        lay.addWidget(self.name_e, 1); lay.addWidget(self.qty_e); lay.addWidget(self.unit_e); lay.addWidget(btn)
        for w in [self.name_e, self.qty_e]: w.textChanged.connect(self.changed.emit)
        self.unit_e.currentTextChanged.connect(self.changed.emit)

    def data(self): return {"name":self.name_e.text().strip(),"quantity":self.qty_e.text().strip(),"unit":self.unit_e.currentText().strip()}
    def scale_qty(self, ratio):
        try: self.qty_e.setText(str(round(float(self.qty_e.text())*ratio, 3)).rstrip('0').rstrip('.'))
        except: pass

class InstructionEditRow(QWidget):
    remove_clicked = Signal(object); changed = Signal()
    def __init__(self, text="", num=1):
        super().__init__(); self.setFixedHeight(68)
        lay = QHBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(4)
        self.num_l = QLabel(f"{num}."); self.num_l.setFixedWidth(24); self.num_l.setAlignment(Qt.AlignCenter|Qt.AlignTop)
        self.num_l.setStyleSheet("font-weight:bold;color:#2d8cf0;padding-top:4px;")
        self.text_e = QTextEdit(text); self.text_e.setPlaceholderText("Step...")
        btn = QPushButton("✕"); btn.setObjectName("removeRowBtn"); btn.setFixedSize(24,24)
        btn.clicked.connect(lambda: self.remove_clicked.emit(self))
        lay.addWidget(self.num_l); lay.addWidget(self.text_e, 1); lay.addWidget(btn)
        self.text_e.textChanged.connect(self.changed.emit)
    def text(self): return self.text_e.toPlainText().strip()
    def set_num(self, n): self.num_l.setText(f"{n}.")

# ─── Advanced Recipe Editor ──────────────────────────────────────────────────
class RecipeEditor(QWidget):
    saved = Signal(object)
    cancelled = Signal()

    def __init__(self, recipe=None, parent=None):
        super().__init__(parent)
        self.recipe = recipe or Recipe()
        self.is_new = recipe is None
        self.base_servings = self.recipe.servings
        self._build_ui()
        if not self.is_new: self._populate()
        else:
            for _ in range(3): self._add_ing()
            self._add_inst()
        self._update_preview()

    def _build_ui(self):
        main_lay = QHBoxLayout(self); main_lay.setContentsMargins(0,0,0,0)
        
        # Left: Tabs
        self.tabs = QTabWidget(); self.tabs.setDocumentMode(True)
        
        # Tab 1: Info
        info_w = QWidget(); info_l = QFormLayout(info_w)
        self.name_e = QLineEdit(); self.name_e.setPlaceholderText("Recipe Name")
        info_l.addRow("Name:", self.name_e)
        self.cat_e = QComboBox(); self.cat_e.addItems(CATEGORIES)
        info_l.addRow("Category:", self.cat_e)
        time_row = QHBoxLayout()
        self.prep_e = QSpinBox(); self.prep_e.setRange(0,999); self.prep_e.setSuffix(" min")
        self.cook_e = QSpinBox(); self.cook_e.setRange(0,999); self.cook_e.setSuffix(" min")
        time_row.addWidget(self.prep_e); time_row.addWidget(self.cook_e)
        info_l.addRow("Prep / Cook:", time_row)
        self.serv_e = QSpinBox(); self.serv_e.setRange(1,100)
        self.serv_e.valueChanged.connect(self._scale_ingredients)
        info_l.addRow("Servings:", self.serv_e)
        self.diff_e = QComboBox(); self.diff_e.addItems(DIFFICULTIES)
        info_l.addRow("Difficulty:", self.diff_e)
        self.tabs.addTab(info_w, "📋 Info")

        # Tab 2: Ingredients
        ing_w = QWidget(); ing_l = QVBoxLayout(ing_w)
        self.ing_container = QVBoxLayout(); self.ing_container.setSpacing(4)
        self.ing_rows = []
        ing_scroll = QScrollArea(); ing_scroll.setWidgetResizable(True)
        ing_inner = QWidget(); ing_inner.setLayout(self.ing_container)
        ing_scroll.setWidget(ing_inner)
        ing_l.addWidget(ing_scroll)
        ing_btns = QHBoxLayout()
        b_add = QPushButton("+ Add"); b_add.setObjectName("addRowBtn"); b_add.clicked.connect(lambda: self._add_ing())
        b_up = QPushButton("↑ Up"); b_up.clicked.connect(lambda: self._move_ing(-1))
        b_down = QPushButton("↓ Down"); b_down.clicked.connect(lambda: self._move_ing(1))
        ing_btns.addWidget(b_add); ing_btns.addWidget(b_up); ing_btns.addWidget(b_down)
        ing_l.addLayout(ing_btns)
        self.tabs.addTab(ing_w, "🥕 Ingredients")

        # Tab 3: Instructions
        inst_w = QWidget(); inst_l = QVBoxLayout(inst_w)
        self.inst_container = QVBoxLayout(); self.inst_container.setSpacing(4)
        self.inst_rows = []
        inst_scroll = QScrollArea(); inst_scroll.setWidgetResizable(True)
        inst_inner = QWidget(); inst_inner.setLayout(self.inst_container)
        inst_scroll.setWidget(inst_inner)
        inst_l.addWidget(inst_scroll)
        inst_btns = QHBoxLayout()
        b_add2 = QPushButton("+ Add Step"); b_add2.setObjectName("addRowBtn"); b_add2.clicked.connect(lambda: self._add_inst())
        b_up2 = QPushButton("↑ Up"); b_up2.clicked.connect(lambda: self._move_inst(-1))
        b_down2 = QPushButton("↓ Down"); b_down2.clicked.connect(lambda: self._move_inst(1))
        inst_btns.addWidget(b_add2); inst_btns.addWidget(b_up2); inst_btns.addWidget(b_down2)
        inst_l.addLayout(inst_btns)
        self.tabs.addTab(inst_w, "📝 Steps")

        # Tab 4: Extra
        ext_w = QWidget(); ext_l = QFormLayout(ext_w)
        self.tags_e = QLineEdit(); self.tags_e.setPlaceholderText("comma, separated, tags")
        ext_l.addRow("Tags:", self.tags_e)
        self.notes_e = QTextEdit(); self.notes_e.setFixedHeight(100)
        ext_l.addRow("Notes:", self.notes_e)
        img_row = QHBoxLayout()
        self.img_path = ""
        self.img_btn = QPushButton("Choose Image"); self.img_btn.setObjectName("addRowBtn")
        self.img_btn.clicked.connect(self._pick_img)
        self.img_lbl = QLabel("None"); self.img_lbl.setObjectName("imageHint")
        img_row.addWidget(self.img_btn); img_row.addWidget(self.img_lbl, 1)
        ext_l.addRow("Image:", img_row)
        self.tabs.addTab(ext_w, "⚙ Extra")

        # Right: Preview
        self.preview = QTextBrowser(); self.preview.setOpenExternalLinks(False)
        self.preview.setStyleSheet("QTextBrowser{background:#fff; border-left:1px solid #e0e0e0; padding:20px; font-size:14px;}")

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.tabs); splitter.addWidget(self.preview)
        splitter.setSizes([500, 400])
        main_lay.addWidget(splitter)

        # Bottom Buttons
        btn_lay = QHBoxLayout()
        btn_lay.addStretch()
        cancel = QPushButton("Cancel"); cancel.setObjectName("cancelBtn"); cancel.clicked.connect(self.cancelled.emit)
        save = QPushButton("💾 Save Recipe"); save.setObjectName("saveBtn"); save.clicked.connect(self._save)
        btn_lay.addWidget(cancel); btn_lay.addWidget(save)
        main_lay.addLayout(btn_lay)

        # Debounced preview update
        self._preview_timer = QTimer(); self._preview_timer.setSingleShot(True); self._preview_timer.setInterval(300)
        self._preview_timer.timeout.connect(self._update_preview)
        self.name_e.textChanged.connect(lambda: self._preview_timer.start())
        self.cat_e.currentTextChanged.connect(lambda: self._preview_timer.start())
        self.prep_e.valueChanged.connect(lambda: self._preview_timer.start())
        self.cook_e.valueChanged.connect(lambda: self._preview_timer.start())
        self.diff_e.currentTextChanged.connect(lambda: self._preview_timer.start())
        self.tags_e.textChanged.connect(lambda: self._preview_timer.start())
        self.notes_e.textChanged.connect(lambda: self._preview_timer.start())

    def _add_ing(self, n="", q="", u=""):
        r = IngredientEditRow(n,q,u); r.remove_clicked.connect(self._rm_ing); r.changed.connect(lambda: self._preview_timer.start())
        self.ing_rows.append(r); self.ing_container.addWidget(r)
    def _rm_ing(self, row):
        self.ing_rows.remove(row); self.ing_container.removeWidget(row); row.deleteLater(); self._preview_timer.start()
    def _move_ing(self, d):
        w = self.tabs.widget(1)
        if not w: return
        scroll = w.findChild(QScrollArea)
        # Find currently focused or last added - simple implementation: move last modified
        for i, r in enumerate(self.ing_rows):
            if r.name_e.hasFocus() or r.qty_e.hasFocus() or r.unit_e.hasFocus():
                ni = i + d
                if 0 <= ni < len(self.ing_rows):
                    self.ing_rows.insert(ni, self.ing_rows.pop(i))
                    self._rebuild_ing_layout(); self._preview_timer.start()
                return

    def _add_inst(self, t=""):
        r = InstructionEditRow(t, len(self.inst_rows)+1); r.remove_clicked.connect(self._rm_inst); r.changed.connect(lambda: self._preview_timer.start())
        self.inst_rows.append(r); self.inst_container.addWidget(r)
    def _rm_inst(self, row):
        self.inst_rows.remove(row); self.inst_container.removeWidget(row); row.deleteLater()
        for i,r in enumerate(self.inst_rows): r.set_num(i+1)
        self._preview_timer.start()
    def _move_inst(self, d):
        for i, r in enumerate(self.inst_rows):
            if r.text_e.hasFocus():
                ni = i + d
                if 0 <= ni < len(self.inst_rows):
                    self.inst_rows.insert(ni, self.inst_rows.pop(i))
                    for j,rr in enumerate(self.inst_rows): rr.set_num(j+1)
                    self._rebuild_inst_layout(); self._preview_timer.start()
                return

    def _rebuild_ing_layout(self):
        while self.ing_container.count(): self.ing_container.takeAt(0).widget().deleteLater()
        for r in self.ing_rows: self.ing_container.addWidget(r)
    def _rebuild_inst_layout(self):
        while self.inst_container.count(): self.inst_container.takeAt(0).widget().deleteLater()
        for r in self.inst_rows: self.inst_container.addWidget(r)

    def _scale_ingredients(self, new_serv):
        if self.base_servings == 0: self.base_servings = 1
        ratio = new_serv / self.base_servings
        if ratio != 1.0:
            for r in self.ing_rows: r.scale_qty(ratio)
            self.base_servings = new_serv
        self._preview_timer.start()

    def _pick_img(self):
        p, _ = QFileDialog.getOpenFileName(self, "Image", "", "Images (*.png *.jpg *.jpeg)")
        if p: self.img_path = p; self.img_lbl.setText(os.path.basename(p))

    def _populate(self):
        r = self.recipe; self.base_servings = r.servings
        self.name_e.setText(r.name); self.cat_e.setCurrentText(r.category)
        self.prep_e.setValue(r.prep_time); self.cook_e.setValue(r.cook_time)
        self.serv_e.setValue(r.servings); self.diff_e.setCurrentText(r.difficulty)
        self.tags_e.setText(", ".join(r.tags)); self.notes_e.setPlainText(r.notes)
        if r.image_path: self.img_path = r.image_path; self.img_lbl.setText(os.path.basename(r.image_path))
        for i in r.ingredients: self._add_ing(i.get("name",""), i.get("quantity",""), i.get("unit",""))
        for s in r.instructions: self._add_inst(s)

    def _update_preview(self):
        name = self.name_e.text().strip() or "Untitled Recipe"
        cat = self.cat_e.currentText()
        c1, c2 = CATEGORY_COLORS.get(cat, CATEGORY_COLORS["Other"])
        ings = "".join(f"<li><b>{i.data()['name']}</b> — {i.data()['quantity']} {i.data()['unit']}</li>" for i in self.ing_rows if i.data()['name'])
        steps = "".join(f"<li>{r.text()}</li>" for r in self.inst_rows if r.text())
        tags = ", ".join(t.strip() for t in self.tags_e.text().split(",") if t.strip())
        
        html = f"""
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; color: #333; }}
            h1 {{ color: {c1}; margin-bottom: 5px; }}
            .meta {{ color: #666; font-size: 13px; margin-bottom: 20px; }}
            h2 {{ border-bottom: 2px solid {c1}; padding-bottom: 5px; color: #2c3e50; margin-top: 25px; }}
            ul {{ padding-left: 20px; }}
            li {{ margin-bottom: 8px; }}
            .notes {{ background: #f9f9f9; padding: 10px; border-radius: 6px; font-style: italic; color: #555; }}
            .tags {{ color: #2d8cf0; font-size: 12px; }}
        </style>
        <h1>{name}</h1>
        <div class="meta">
            🍽 {cat} &nbsp;|&nbsp; ⏱ Prep: {self.prep_e.value()}m &nbsp;|&nbsp; 🔥 Cook: {self.cook_e.value()}m &nbsp;|&nbsp; 👥 Serves {self.serv_e.value()} &nbsp;|&nbsp; ⭐ {self.diff_e.currentText()}
        </div>
        {"<div class='tags'># " + tags.replace(", ", " #") + "</div>" if tags else ""}
        <h2>🥕 Ingredients</h2><ul>{ings if ings else '<li><i>None added yet</i></li>'}</ul>
        <h2>📝 Instructions</h2><ol>{steps if steps else '<li><i>None added yet</i></li>'}</ol>
        {"<h2>📒 Notes</h2><div class='notes'>"+self.notes_e.toPlainText()+"</div>" if self.notes_e.toPlainText() else ""}
        """
        self.preview.setHtml(html)

    def _save(self):
        name = self.name_e.text().strip()
        if not name: return QMessageBox.warning(self, "Error", "Name is required.")
        ings = [r.data() for r in self.ing_rows if r.data()['name']]
        steps = [r.text() for r in self.inst_rows if r.text()]
        if not ings: return QMessageBox.warning(self, "Error", "Add at least one ingredient.")
        if not steps: return QMessageBox.warning(self, "Error", "Add at least one step.")
        
        r = self.recipe
        r.name=name; r.category=self.cat_e.currentText(); r.prep_time=self.prep_e.value()
        r.cook_time=self.cook_e.value(); r.servings=self.serv_e.value(); r.difficulty=self.diff_e.currentText()
        r.ingredients=ings; r.instructions=steps
        r.tags=[t.strip() for t in self.tags_e.text().split(",") if t.strip()]
        r.notes=self.notes_e.toPlainText().strip(); r.image_path=self.img_path
        self.saved.emit(r)

    def export_html(self):
        name = self.name_e.text().strip() or "Recipe"
        path, _ = QFileDialog.getSaveFileName(self, "Export HTML", f"{name}.html", "HTML (*.html)")
        if path:
            with open(path, "w", encoding="utf-8") as f: f.write(self.preview.toHtml())
            QMessageBox.information(self, "Exported", f"Saved to {path}")

# ─── Shopping List ───────────────────────────────────────────────────────────
class ShoppingListView(QWidget):
    go_back = Signal()
    def __init__(self, store, parent=None):
        super().__init__(parent)
        self.store = store; self.selected_ids = set()
        self._build()
        
    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(24,20,24,20)
        
        top = QHBoxLayout()
        back = QPushButton("← Back"); back.setObjectName("backBtn"); back.clicked.connect(self.go_back.emit)
        top.addWidget(back)
        title = QLabel("🛒 Smart Shopping List"); title.setObjectName("detailTitle")
        top.addWidget(title); top.addStretch()
        lay.addLayout(top)

        # Recipe Picker
        self.picker_frame = QFrame(); self.picker_frame.setObjectName("pickerFrame")
        pl = QVBoxLayout(self.picker_frame)
        pl.addWidget(QLabel("Select recipes to combine:"))
        self.checks_layout = QGridLayout(); self.checks_layout.setSpacing(4)
        pl.addLayout(self.checks_layout)
        gen_btn = QPushButton("🛒 Generate List"); gen_btn.setObjectName("saveBtn")
        gen_btn.clicked.connect(self._generate)
        pl.addWidget(gen_btn)
        lay.addWidget(self.picker_frame)

        # Generated List
        self.list_frame = QFrame()
        ll = QVBoxLayout(self.list_frame)
        self.list_container = QVBoxLayout(); self.list_container.setSpacing(2)
        ll.addLayout(self.list_container)
        clear_btn = QPushButton("Clear List"); clear_btn.setObjectName("cancelBtn")
        clear_btn.clicked.connect(self._clear_list)
        ll.addWidget(clear_btn)
        lay.addWidget(self.list_frame, 1)

    def refresh_picks(self):
        while self.checks_layout.count(): self.checks_layout.takeAt(0).widget().deleteLater()
        cols = 3
        for i, r in enumerate(self.store.recipes):
            cb = QCheckBox(r.name)
            cb.setProperty("rid", r.id)
            if r.id in self.selected_ids: cb.setChecked(True)
            self.checks_layout.addWidget(cb, i//cols, i%cols)

    def _generate(self):
        self.selected_ids = set()
        all_ings = []
        for i in range(self.checks_layout.count()):
            cb = self.checks_layout.itemAt(i).widget()
            if isinstance(cb, QCheckBox) and cb.isChecked():
                rid = cb.property("rid")
                self.selected_ids.add(rid)
                recipe = next((r for r in self.store.recipes if r.id == rid), None)
                if recipe: all_ings.extend(recipe.ingredients)
        
        # Aggregate
        agg = {}
        for ing in all_ings:
            key = ing['name'].lower().strip()
            if not key: continue
            if key in agg:
                if agg[key]['unit'] == ing['unit']:
                    try: agg[key]['qty'] += float(ing['quantity'])
                    except: pass
                else:
                    agg[f"{key} ({ing['unit']})"] = {'name':ing['name'], 'qty':ing['quantity'], 'unit':ing['unit']}
            else:
                agg[key] = {'name':ing['name'], 'qty':ing['quantity'], 'unit':ing['unit']}
        
        self._clear_list()
        for k, v in agg.items():
            try: qty_str = str(round(v['qty'], 2)).rstrip('0').rstrip('.')
            except: qty_str = v['qty']
            txt = f"{qty_str} {v['unit']} — {v['name']}".strip()
            cb = QCheckBox(txt); cb.setChecked(False)
            self.list_container.addWidget(cb)

    def _clear_list(self):
        while self.list_container.count(): self.list_container.takeAt(0).widget().deleteLater()

# ─── Recipe Card ─────────────────────────────────────────────────────────────
class RecipeCard(QFrame):
    clicked = Signal(object); fav_toggled = Signal(object)
    def __init__(self, recipe):
        super().__init__(); self.recipe = recipe
        self.setFixedSize(235, 275); self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("QFrame{background:#fff;border:2px solid #e8e8e8;border-radius:12px;}")
        outer = QVBoxLayout(self); outer.setContentsMargins(0,0,0,0); outer.setSpacing(0)
        
        self.img_c = QFrame(); self.img_c.setFixedSize(235,125)
        il = QVBoxLayout(self.img_c); il.setContentsMargins(0,0,0,0)
        self.img_l = QLabel(); self.img_l.setFixedSize(235,125); self.img_l.setAlignment(Qt.AlignCenter)
        self._draw_img(); il.addWidget(self.img_l)
        
        self.fav_btn = QPushButton("♥" if recipe.favorite else "♡"); self.fav_btn.setFixedSize(30,30)
        self.fav_btn.setParent(self.img_c); self.fav_btn.move(198,5); self.fav_btn.raise_()
        self._style_fav(); self.fav_btn.clicked.connect(self._toggle_fav)
        outer.addWidget(self.img_c)
        
        tf = QFrame(); tl = QVBoxLayout(tf); tl.setContentsMargins(10,8,10,10); tl.setSpacing(4)
        tl.addWidget(self._lbl(recipe.category.upper(), "cardCategory"))
        nl = QLabel(recipe.name); nl.setObjectName("cardName"); nl.setWordWrap(True); nl.setMaximumHeight(42)
        tl.addWidget(nl)
        info = QHBoxLayout(); info.setSpacing(10)
        total = recipe.prep_time + recipe.cook_time
        h,m = divmod(total, 60)
        ts = f"{h}h {m}m" if h else (f"{m}m" if m else "—")
        for t in [f"⏱ {ts}", f"👥 {recipe.servings}", f"⭐ {recipe.difficulty}"]:
            info.addWidget(self._lbl(t, "cardMeta"))
        info.addStretch(); tl.addLayout(info)
        outer.addWidget(tf, 1)

    def _lbl(self, t, n): l=QLabel(t); l.setObjectName(n); return l
    def _draw_img(self):
        if self.recipe.image_path and os.path.exists(self.recipe.image_path):
            pm = QPixmap(self.recipe.image_path).scaled(235,125,Qt.KeepAspectRatioByExpanding,Qt.SmoothTransformation)
        else:
            pm = QPixmap(235,125); p = QPainter(pm)
            c1,c2 = CATEGORY_COLORS.get(self.recipe.category, CATEGORY_COLORS["Other"])
            g = QLinearGradient(0,0,235,125); g.setColorAt(0,QColor(c1)); g.setColorAt(1,QColor(c2))
            p.fillRect(0,0,235,125,g); p.setPen(QPen(QColor(255,255,255,70),2)); p.setBrush(Qt.NoBrush)
            p.drawEllipse(87,25,60,55); p.drawEllipse(97,35,40,35)
            p.setPen(QColor(255,255,255,190)); p.setFont(QFont("Arial",13,QFont.Bold))
            p.drawText(0,95,235,28,Qt.AlignCenter,self.recipe.category); p.end()
        self.img_l.setPixmap(pm)
    def _toggle_fav(self):
        self.recipe.favorite = not self.recipe.favorite
        self.fav_btn.setText("♥" if self.recipe.favorite else "♡"); self._style_fav()
        self.fav_toggled.emit(self.recipe)
    def _style_fav(self):
        if self.recipe.favorite: self.fav_btn.setStyleSheet("QPushButton{background:#FF4757;color:#fff;border:none;border-radius:15px;font-size:16px;font-weight:bold;}")
        else: self.fav_btn.setStyleSheet("QPushButton{background:rgba(0,0,0,0.35);color:rgba(255,255,255,0.8);border:none;border-radius:15px;font-size:16px;font-weight:bold;}")
    def enterEvent(self, e): self.setStyleSheet("QFrame{background:#fff;border:2px solid #2d8cf0;border-radius:12px;}"); super().enterEvent(e)
    def leaveEvent(self, e): self.setStyleSheet("QFrame{background:#fff;border:2px solid #e8e8e8;border-radius:12px;}"); super().leaveEvent(e)
    def mousePressEvent(self, e):
        if e.button()==Qt.LeftButton: self.clicked.emit(self.recipe)
        super().mousePressEvent(e)

# ─── Detail View ─────────────────────────────────────────────────────────────
class DetailView(QScrollArea):
    go_back = Signal(); edit_req = Signal(object); delete_req = Signal(object); list_req = Signal(object); timer_req = Signal()
    def __init__(self): super().__init__(); self.setWidgetResizable(True); self._c=QWidget(); self._l=QVBoxLayout(self._c); self._l.setContentsMargins(32,20,32,40); self._l.setSpacing(14); self.setWidget(self._c)
    def show_recipe(self, r):
        self._clear()
        self._l.addWidget(self._btn("←  Back to Recipes","backBtn",self.go_back.emit))
        tr = QHBoxLayout(); t=QLabel(r.name); t.setObjectName("detailTitle"); tr.addWidget(t); tr.addStretch()
        tr.addWidget(self._btn("✏️  Edit","detailActionBtn",lambda:self.edit_req.emit(r)))
        tr.addWidget(self._btn("⏱ Timer","detailActionBtn",self.timer_req.emit))
        tr.addWidget(self._btn("🛒 Add to List","detailActionBtn",self.list_req.emit))
        db=QPushButton("🗑️  Delete"); db.setObjectName("detailDeleteBtn"); db.clicked.connect(lambda:self.delete_req.emit(r)); tr.addWidget(db)
        self._l.addLayout(tr)
        mr=QHBoxLayout(); mr.setSpacing(10); total=r.prep_time+r.cook_time; h,m=divmod(total,60); ts=f"{h}h {m}m" if h else (f"{m}m" if m else "—")
        for txt in [f"🍽  {r.category}",f"⏱  Prep {r.prep_time} min",f"🔥  Cook {r.cook_time} min",f"⏰  Total {ts}",f"👥  Serves {r.servings}",f"⭐  {r.difficulty}"]:
            lb=QLabel(txt); lb.setObjectName("metaBadge"); mr.addWidget(lb)
        mr.addStretch(); self._l.addLayout(mr)
        if r.tags:
            trow=QHBoxLayout(); trow.addWidget(QLabel("Tags:"))
            for tg in r.tags: tl=QLabel(f" #{tg}"); tl.setObjectName("tagLabel"); trow.addWidget(tl)
            trow.addStretch(); self._l.addLayout(trow)
        sep=QFrame(); sep.setFrameShape(QFrame.HLine); sep.setObjectName("separator"); self._l.addWidget(sep)
        if r.image_path and os.path.exists(r.image_path):
            il=QLabel(); il.setPixmap(QPixmap(r.image_path).scaled(520,300,Qt.KeepAspectRatioByExpanding,Qt.SmoothTransformation)); il.setAlignment(Qt.AlignCenter); self._l.addWidget(il)
        ig=QGroupBox(f"Ingredients ({len(r.ingredients)})"); il2=QVBoxLayout()
        for ing in r.ingredients:
            qs=f"{ing.get('quantity','')} {ing.get('unit','')}".strip()
            il2.addWidget(self._lbl(f"•  {qs}  —  {ing.get('name','')}" if qs else f"•  {ing.get('name','')}","padding:3px 0;font-size:14px;"))
        ig.setLayout(il2); self._l.addWidget(ig)
        sg=QGroupBox(f"Instructions ({len(r.instructions)} steps)"); sl=QVBoxLayout(); sl.setSpacing(10)
        for i,step in enumerate(r.instructions,1):
            row=QWidget(); rl=QHBoxLayout(row); rl.setContentsMargins(0,0,0,0)
            nl=QLabel(str(i)); nl.setObjectName("stepNum"); nl.setFixedSize(30,30); nl.setAlignment(Qt.AlignCenter)
            tl=QLabel(step); tl.setWordWrap(True); tl.setStyleSheet("font-size:14px;padding-left:8px;")
            rl.addWidget(nl); rl.addWidget(tl,1); sl.addWidget(row)
        sg.setLayout(sl); self._l.addWidget(sg)
        if r.notes:
            ng=QGroupBox("Notes"); nl3=QVBoxLayout(); nlb=QLabel(r.notes); nlb.setWordWrap(True); nlb.setStyleSheet("font-style:italic;color:#666;"); nl3.addWidget(nlb); ng.setLayout(nl3); self._l.addWidget(ng)
        self._l.addStretch(); self.verticalScrollBar().setValue(0)
    def _btn(self, t, n, fn): b=QPushButton(t); b.setObjectName(n); b.clicked.connect(fn); return b
    def _lbl(self, t, s): l=QLabel(t); l.setWordWrap(True); l.setStyleSheet(s); return l
    def _clear(self):
        while self._l.count():
            it=self._l.takeAt(0)
            if it.widget(): it.widget().deleteLater()
            elif it.layout(): self._cl(it.layout())
    @staticmethod
    def _cl(lay):
        while lay.count():
            it=lay.takeAt(0)
            if it.widget(): it.widget().deleteLater()
            elif it.layout(): DetailView._cl(it.layout())

# ─── Main Window ─────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🍳 Recipe Book Pro")
        self.setMinimumSize(960, 660); self.resize(1200, 800)
        self.store = RecipeStore()
        self._fcat = "All"; self._ffav = False; self._pcols = -1; self._dark = False
        self.timer = CookingTimer(self)
        self._build(); self._apply_style(); self._refresh()

    def _build(self):
        cw=QWidget(); self.setCentralWidget(cw); root=QHBoxLayout(cw); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        
        self.sidebar=QFrame(); self.sidebar.setObjectName("sidebar"); self.sidebar.setFixedWidth(220)
        sl=QVBoxLayout(self.sidebar); sl.setContentsMargins(14,22,14,18); sl.setSpacing(4)
        logo=QLabel("🍳 Recipe Book"); logo.setObjectName("sidebarLogo"); logo.setAlignment(Qt.AlignCenter); sl.addWidget(logo); sl.addSpacing(10)
        
        self.btn_all=QPushButton("📋  All Recipes"); self.btn_all.setObjectName("sideNav"); self.btn_all.clicked.connect(lambda:self._sf("All",False)); sl.addWidget(self.btn_all)
        self.btn_fav=QPushButton("♥  Favorites"); self.btn_fav.setObjectName("sideNav"); self.btn_fav.clicked.connect(lambda:self._sf("All",True)); sl.addWidget(self.btn_fav)
        self.btn_shop=QPushButton("🛒  Shopping List"); self.btn_shop.setObjectName("sideNav"); self.btn_shop.clicked.connect(self._open_shop); sl.addWidget(self.btn_shop)
        
        cl=QLabel("CATEGORIES"); cl.setObjectName("sideSectionLabel"); sl.addSpacing(8); sl.addWidget(cl)
        self._cbs=[]
        for cat in CATEGORIES:
            b=QPushButton(cat); b.setObjectName("sideNav"); b.clicked.connect(lambda _, c=cat:self._sf(c,False)); sl.addWidget(b); self._cbs.append(b)
        sl.addStretch()
        
        self.dark_btn=QPushButton("🌙  Dark Mode"); self.dark_btn.setObjectName("sideNav"); self.dark_btn.clicked.connect(self._toggle_dark); sl.addWidget(self.dark_btn)
        add_btn=QPushButton("➕  New Recipe"); add_btn.setObjectName("sideAddBtn"); add_btn.clicked.connect(self._add); sl.addWidget(add_btn)
        root.addWidget(self.sidebar)

        self.stack=QStackedWidget(); root.addWidget(self.stack, 1)
        
        # Page 0: Grid
        self.gp=QWidget(); gl=QVBoxLayout(self.gp); gl.setContentsMargins(22,18,22,18); gl.setSpacing(14)
        sr=QHBoxLayout()
        self.search=QLineEdit(); self.search.setPlaceholderText("🔍  Search recipes…"); self.search.setClearButtonEnabled(True); self.search.textChanged.connect(self._refresh)
        sr.addWidget(self.search,1); self.cnt=QLabel(""); self.cnt.setObjectName("countLabel"); sr.addWidget(self.cnt)
        gl.addLayout(sr)
        self.cs=QScrollArea(); self.cs.setWidgetResizable(True); self.cc=QWidget(); self.cg=QGridLayout(self.cc); self.cg.setSpacing(16); self.cg.setAlignment(Qt.AlignTop|Qt.AlignLeft)
        self.cs.setWidget(self.cc); gl.addWidget(self.cs)
        self.stack.addWidget(self.gp)

        # Page 1: Detail
        self.detail=DetailView()
        self.detail.go_back.connect(self._show_grid); self.detail.edit_req.connect(self._edit)
        self.detail.delete_req.connect(self._delete); self.detail.list_req.connect(self._add_to_list)
        self.detail.timer_req.connect(self.timer.show)
        self.stack.addWidget(self.detail)

        # Page 2: Editor
        self.editor_page = QWidget(); ep_lay = QVBoxLayout(self.editor_page); ep_lay.setContentsMargins(0,0,0,0)
        self.stack.addWidget(self.editor_page)

        # Page 3: Shopping List
        self.shop_view = ShoppingListView(self.store)
        self.shop_view.go_back.connect(self._show_grid)
        self.stack.addWidget(self.shop_view)

    def _sf(self, c, f): self._fcat=c; self._ffav=f; self._hnav(); self._refresh(); self._show_grid()
    def _hnav(self):
        for b in self._cbs: b.setProperty("active",False)
        self.btn_all.setProperty("active",False); self.btn_fav.setProperty("active",False); self.btn_shop.setProperty("active",False)
        if self._ffav: self.btn_fav.setProperty("active",True)
        elif self._fcat=="All": self.btn_all.setProperty("active",True)
        else:
            for b in self._cbs:
                if b.text()==self._fcat: b.setProperty("active",True)
        for b in [self.btn_all,self.btn_fav,self.btn_shop]+self._cbs: b.style().unpolish(b); b.style().polish(b)

    def _refresh(self):
        while self.cg.count(): it=self.cg.takeAt(0); (it.widget() and it.widget().deleteLater())
        q=self.search.text().strip(); recs=self.store.search(q,self._fcat,self._ffav); n=len(recs)
        self.cnt.setText(f"{n} recipe{'s' if n!=1 else ''}")
        if not recs:
            el=QLabel("No recipes found.\nClick ➕ New Recipe to add one!"); el.setAlignment(Qt.AlignCenter); el.setObjectName("emptyLabel"); self.cg.addWidget(el,0,0); return
        cols=max(1,(self.cs.width()-32)//251); self._pcols=cols
        for i,r in enumerate(recs):
            c=RecipeCard(r); c.clicked.connect(self._view); c.fav_toggled.connect(self._on_fav)
            self.cg.addWidget(c,i//cols,i%cols)

    def _show_grid(self): self.stack.setCurrentIndex(0); self._refresh()
    def _view(self, r): self.detail.show_recipe(r); self.stack.setCurrentIndex(1)
    
    def _add_to_list(self, r):
        self.shop_view.selected_ids.add(r.id)
        QMessageBox.information(self, "Added", f"Added '{r.name}' to shopping list.")

    def _add(self):
        if self.editor_page.layout(): 
            while self.editor_page.layout().count(): self.editor_page.layout().takeAt(0).widget().deleteLater()
        ed = RecipeEditor(parent=self)
        ed.saved.connect(self._save_new); ed.cancelled.connect(self._show_grid)
        self.editor_page.layout().addWidget(ed)
        self.stack.setCurrentIndex(2)

    def _edit(self, r):
        if self.editor_page.layout(): 
            while self.editor_page.layout().count(): self.editor_page.layout().takeAt(0).widget().deleteLater()
        ed = RecipeEditor(recipe=r, parent=self)
        ed.saved.connect(self._save_edit); ed.cancelled.connect(self._show_grid)
        self.editor_page.layout().addWidget(ed)
        self.stack.setCurrentIndex(2)

    def _save_new(self, r): self.store.add(r); self._show_grid()
    def _save_edit(self, r): self.store.update(r); self._show_grid()
    def _delete(self, r):
        if QMessageBox.question(self,"Delete",f"Delete '{r.name}'?",QMessageBox.Yes|QMessageBox.No)==QMessageBox.Yes:
            self.store.delete(r.id); self._show_grid()
    def _on_fav(self, r): 
      self.store.update(r); 
      if self._ffav and not r.favorite: self._refresh()
    def _open_shop(self):
        self._hnav(); self.btn_shop.setProperty("active",True); self.btn_shop.style().unpolish(self.btn_shop); self.btn_shop.style().polish(self.btn_shop)
        self.shop_view.refresh_picks(); self.stack.setCurrentIndex(3)
    def resizeEvent(self, e):
        super().resizeEvent(e); cols=max(1,(self.cs.width()-32)//251)
        if cols!=self._pcols: self._refresh()

    def _toggle_dark(self):
        self._dark = not self._dark
        self.dark_btn.setText("☀️  Light Mode" if self._dark else "🌙  Dark Mode")
        self._apply_style()

    def _apply_style(self):
        bg="#1e1e1e" if self._dark else "#f5f6fa"
        side_bg="qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #1a1a2e,stop:1 #16213e)" if self._dark else "qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #2c3e50,stop:1 #1a252f)"
        txt="#e0e0e0" if self._dark else "#333"
        card_bg="#2d2d2d" if self._dark else "#fff"
        card_border="#444" if self._dark else "#e8e8e0"
        input_bg="#333" if self._dark else "#fff"
        input_border="#555" if self._dark else "#e0e0e0"
        
        self.setStyleSheet(f"""
        QMainWindow {{ background:{bg}; }}
        QWidget {{ font-family:'Segoe UI','Arial',sans-serif; color:{txt}; }}
        QFrame#sidebar {{ background:{side_bg}; }}
        QLabel#sidebarLogo {{ color:#fff; font-size:17px; font-weight:bold; padding:8px 0; }}
        QLabel#sideSectionLabel {{ color:rgba(255,255,255,0.4); font-size:11px; font-weight:bold; padding:6px 4px 2px 4px; letter-spacing:1px; }}
        QPushButton#sideNav {{ color:rgba(255,255,255,0.82); text-align:left; padding:8px 12px; border:none; border-radius:6px; font-size:13px; background:transparent; }}
        QPushButton#sideNav:hover {{ background:rgba(255,255,255,0.08); color:#fff; }}
        QPushButton#sideNav[active="true"] {{ background:rgba(255,255,255,0.14); color:#fff; font-weight:bold; }}
        QPushButton#sideAddBtn {{ background:#2d8cf0; color:#fff; border:none; padding:11px 16px; border-radius:8px; font-size:14px; font-weight:bold; }}
        QPushButton#sideAddBtn:hover {{ background:#2577d3; }}
        QLineEdit {{ background:{input_bg}; border:2px solid {input_border}; border-radius:10px; padding:10px 16px; font-size:14px; color:{txt}; }}
        QLineEdit:focus {{ border-color:#2d8cf0; }}
        QLabel#countLabel {{ color:#999; font-size:13px; }}
        QLabel#cardCategory {{ color:#999; font-size:10px; font-weight:bold; }}
        QLabel#cardName {{ color:{txt}; font-size:13px; font-weight:bold; }}
        QLabel#cardMeta {{ color:#aaa; font-size:11px; }}
        QPushButton#backBtn {{ color:#2d8cf0; font-size:14px; border:none; background:transparent; text-align:left; }}
        QPushButton#backBtn:hover {{ text-decoration:underline; }}
        QLabel#detailTitle {{ color:{txt}; font-size:24px; font-weight:bold; }}
        QLabel#metaBadge {{ background:{"#333" if self._dark else "#eef2f7"}; color:{"#ddd" if self._dark else "#555"}; padding:6px 14px; border-radius:8px; font-size:12px; }}
        QLabel#tagLabel {{ color:#2d8cf0; font-size:12px; }}
        QFrame#separator {{ color:{input_border}; }}
        QPushButton#detailActionBtn {{ background:#2d8cf0; color:#fff; border:none; padding:8px 18px; border-radius:8px; font-size:13px; font-weight:bold; }}
        QPushButton#detailActionBtn:hover {{ background:#2577d3; }}
        QPushButton#detailDeleteBtn {{ color:#FF4757; border:2px solid #FF4757; padding:8px 18px; border-radius:8px; font-size:13px; font-weight:bold; background:transparent; }}
        QPushButton#detailDeleteBtn:hover {{ background:#FF4757; color:#fff; }}
        QLabel#stepNum {{ background:#2d8cf0; color:#fff; border-radius:15px; font-weight:bold; font-size:13px; }}
        QGroupBox {{ font-weight:bold; font-size:14px; color:{txt}; border:1px solid {input_border}; border-radius:8px; margin-top:14px; padding-top:20px; }}
        QGroupBox::title {{ subcontrol-origin:margin; left:14px; padding:0 6px; }}
        QComboBox {{ background:{input_bg}; border:2px solid {input_border}; border-radius:6px; padding:6px 10px; color:{txt}; }}
        QComboBox:focus {{ border-color:#2d8cf0; }}
        QComboBox::drop-down {{ border:none; width:24px; }}
        QComboBox QAbstractItemView {{ background:{input_bg}; color:{txt}; selection-background-color:#2d8cf0; }}
        QSpinBox {{ background:{input_bg}; border:2px solid {input_border}; border-radius:6px; padding:6px 10px; color:{txt}; }}
        QSpinBox:focus {{ border-color:#2d8cf0; }}
        QTextEdit {{ background:{input_bg}; border:2px solid {input_border}; border-radius:6px; padding:6px; color:{txt}; }}
        QTextEdit:focus {{ border-color:#2d8cf0; }}
        QPushButton#addRowBtn {{ color:#2d8cf0; border:2px dashed #2d8cf0; background:transparent; padding:8px; border-radius:8px; font-size:13px; }}
        QPushButton#addRowBtn:hover {{ background:rgba(45,140,240,0.1); }}
        QPushButton#removeRowBtn {{ color:#cc0000; border:1px solid {input_border}; background:{"#3a2020" if self._dark else "#fafafa"}; border-radius:4px; font-size:14px; font-weight:bold; }}
        QPushButton#removeRowBtn:hover {{ background:#ffe0e0; color:#cc0000; }}
        QPushButton#cancelBtn {{ color:{txt}; border:2px solid {input_border}; background:{"#333" if self._dark else "#fff"}; padding:9px 24px; border-radius:8px; font-size:13px; }}
        QPushButton#cancelBtn:hover {{ background:{"#444" if self._dark else "#f5f5f5"}; }}
        QPushButton#saveBtn {{ background:#2d8cf0; color:#fff; border:none; padding:9px 28px; border-radius:8px; font-size:13px; font-weight:bold; }}
        QPushButton#saveBtn:hover {{ background:#2577d3; }}
        QLabel#imageHint {{ color:#999; font-size:12px; }}
        QLabel#timerDisplay {{ font-size:48px; font-weight:bold; color:#2d8cf0; padding:20px; }}
        QScrollArea {{ border:none; background:transparent; }}
        QScrollBar:vertical {{ background:transparent; width:8px; }}
        QScrollBar::handle:vertical {{ background:#ccc; border-radius:4px; min-height:30px; }}
        QScrollBar::handle:vertical:hover {{ background:#aaa; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
        QLabel#emptyLabel {{ color:#bbb; font-size:16px; padding:60px; }}
        QTabWidget::pane {{ border:1px solid {input_border}; background:{bg}; border-radius:4px; }}
        QTabBar::tab {{ background:{"#333" if self._dark else "#f0f0f0"}; color:{txt}; padding:8px 16px; border-top-left-radius:4px; border-top-right-radius:4px; margin-right:2px; }}
        QTabBar::tab:selected {{ background:{bg}; color:#2d8cf0; font-weight:bold; }}
        QFrame#pickerFrame {{ background:{"#2a2a2a" if self._dark else "#fff"}; border:1px solid {input_border}; border-radius:8px; padding:16px; }}
        QTextBrowser {{ background:{"#2a2a2a" if self._dark else "#fff"}; color:{txt}; border:none; }}
        """)

def main():
    app=QApplication(sys.argv); app.setStyle("Fusion"); app.setFont(QFont("Segoe UI",10))
    win=MainWindow(); win.show(); sys.exit(app.exec())

if __name__=="__main__":
    main()