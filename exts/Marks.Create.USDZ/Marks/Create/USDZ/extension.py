import os
import weakref
import omni.ext
import omni.ui as ui
from omni.kit.window.content_browser import get_content_window
from omni.kit.window.filepicker import FilePickerDialog
import glob
from pxr import Usd


class CommandItem(ui.AbstractItem):
    """Single item of the model"""

    def __init__(self, text):
        super().__init__()
        self.name_model = ui.SimpleStringModel(text)

class FilesModel(ui.AbstractItemModel):
    """
    Represents the list of commands registered in Kit.
    It is used to make a single level tree appear like a simple list.
    """

    def __init__(self):
        super().__init__()

        self._files_list = []
        self._collected_files = []

        self._files_list_changed()

    def _files_list_changed(self):
        """Called by subscribe_on_change"""
        self._files_list = []
        for f in self._collected_files:
            self._files_list.append(CommandItem(f))
        self._item_changed(None)

    def get_item_children(self, item):
        """Returns all the children when the widget asks it."""
        if item is not None:
            # Since we are doing a flat list, we return the children of root only.
            # If it's not root we return.
            return []

        return self._files_list

    def get_item_value_model_count(self, item):
        """The number of columns"""
        return 1

    def get_item_value_model(self, item, column_id):
        """
        Return value model.
        It's the object that tracks the specific value.
        In our case we use ui.SimpleStringModel.
        """ 
        if item and isinstance(item, CommandItem):
            return item.name_model
# Functions and vars are available to other extension as usual in python: `example.python_ext.some_public_function(x)`
def some_public_function(x: int):
    print("[Marks.Create.USDZ] some_public_function was called with x: ", x)
    return x ** x

def Get_Content_Browser():
    content_browser_ref = weakref.ref(get_content_window(), lambda ref: self.destroy())
    content_browser = content_browser_ref()
    return content_browser

def Echo_Selected():
    content_browser = Get_Content_Browser()
    res = []
    if content_browser:
        selections = content_browser.get_current_selections(pane=2)
        for sel in selections:
            if "." in sel:
                res.append(sel)
    return res

def Build_USDZ_File(usdz_file,files):
    with Usd.ZipFileWriter.CreateNew(usdz_file) as usdzWriter:
        for f in files:
            usdzWriter.AddFile(f)

# Any class derived from `omni.ext.IExt` in top level module (defined in `python.modules` of `extension.toml`) will be
# instantiated when extension gets enabled and `on_startup(ext_id)` will be called. Later when extension gets disabled
# on_shutdown() is called.
class MyExtension(omni.ext.IExt):
    # ext_id is current extension id. It can be used with extension manager to query additional information, like where
    # this extension is located on filesystem.
    def on_startup(self, ext_id):
        print("[Marks.Create.USDZ] MyExtension startup")

        def on_Set_To_Content():
            content_browser = Get_Content_Browser()
            selection = content_browser.get_current_selections(pane=1)
            if len(selection):
                path = os.path.join(selection[0],"Generated_USDZ_File.usdz").replace("\\","/")
                self.save_location.model.set_value(path)

        def on_click():
            selection = Echo_Selected()
            for s in selection:
                self._command_model._collected_files.append(s)
            self._command_model._files_list_changed()

        def on_reset():
            self._command_model._collected_files = []
            self._command_model._files_list_changed()
        def on_Create():
            Build_USDZ_File(self.save_location.model.get_value_as_string(),self._command_model._collected_files)

        self._window = ui.Window("My Window", width=800, height=600)

        with self._window.frame:
            with ui.VStack():

                with ui.ScrollingFrame(height=ui.Fraction(8),horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_OFF,vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,style_type_name_override="TreeView"):
                    self._command_model = FilesModel()
                    self.tree_view = ui.TreeView(self._command_model,root_visible=False,header_visible=False,style={"TreeView.Item": {"margin": 4}})

                on_reset()

                with ui.HStack(height=50):
                    ui.Button("Add", clicked_fn=on_click)
                    ui.Button("Reset", clicked_fn=on_reset)
                    ui.Button("Create", clicked_fn=on_Create)
                
                with ui.HStack(height=20):
                    label = ui.Label("Save Location",width=100)
                    self.save_location = ui.StringField() 
                    user_profile = os.environ["USERPROFILE"]
                    usdz_file = os.path.join(user_profile,"Documents","Generated_USDZ_File.usdz")
                    self.save_location.model.set_value(usdz_file)
                    ui.Button("Set To Content",width=150, clicked_fn=on_Set_To_Content)

    def on_shutdown(self):
        print("[Marks.Create.USDZ] MyExtension shutdown")

