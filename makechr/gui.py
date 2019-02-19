import wx

if int(wx.version().split('.')[0]) < 4:
  raise RuntimeError('makechr gui requires wxpPython version 4.0 or greater')

import collections
import os
from PIL import Image
import StringIO
import sys
import tempfile

import app
import binary_file_writer
import color_cycler
import errors
import image_processor
import eight_by_sixteen_processor
import makechr
import memory_importer
import pixel_art_renderer
import pkg_resources
import ppu_memory
import rom_builder
import view_renderer
import file_modify_watcher
from constants import *


APP_WIDTH = 1024
APP_HEIGHT = 704
APP_TITLE = 'Makechr'


MousePos = collections.namedtuple('MousePos',
                                  ['clear', 'y', 'x', 'size', 'meta'])


class ComponentView(object):
  """A component of NES graphics, drawable to a bitmap.

  Wraps a bitmap, which displays a single component of NES graphics. Handles
  both drawing the bitmap, and processing mouseover events.
  """
  def __init__(self, parent, pos, size):
    self.width = size[0]
    self.height = size[1]
    self.bitmap = wx.Bitmap(self.width, self.height)
    self.ctrl = wx.StaticBitmap(parent, wx.ID_ANY, self.bitmap, pos=pos,
                                size=size)
    self.manager = None
    self._drawCommands = []
    self.StartMouseListener()

  def clear(self):
    empty = wx.Bitmap(self.width, self.height)
    self.load(empty)

  def load(self, bitmap):
    self.bitmap = bitmap
    wx.CallAfter(self.ctrl.SetBitmap, self.bitmap)

  def StartMouseListener(self):
    self.ctrl.Bind(wx.EVT_ENTER_WINDOW, lambda e:self.OnMouseEvent('enter', e))
    self.ctrl.Bind(wx.EVT_MOTION,       lambda e:self.OnMouseEvent('move', e))
    self.ctrl.Bind(wx.EVT_LEAVE_WINDOW, lambda e:self.OnMouseEvent('leave', e))

  def SetManager(self, manager):
    self.manager = manager

  def OnMouseEvent(self, type, e):
    y = x = clear = None
    if type == 'leave' or type == 'move':
      clear = True
    if type == 'enter' or type == 'move':
      y = e.GetY()
      x = e.GetX()
    self.emitMouse(clear, y, x)

  def drawBox(self, clear, y, x, size, color):
    self._drawCommands.append([clear, y, x, size, color])

  def drawExecute(self):
    is_clear = False
    if len(self._drawCommands) == 0:
      return
    dc = wx.ClientDC(self.ctrl)
    for clear, y, x, size, color in self._drawCommands:
      if clear and not is_clear:
        dc.DrawBitmap(self.bitmap, 0, 0, True)
        is_clear = True
      if y is None or x is None or size is None:
        continue
      dc.SetPen(wx.Pen(color, style=wx.SOLID))
      dc.SetBrush(wx.Brush(color, wx.TRANSPARENT))
      dc.DrawRectangle(x * size, y * size, size, size)
    self._drawCommands = []

  def emitMouse(self, clear, y, x):
    raise NotImplementedError()


class TileBasedComponentView(ComponentView):
  """A component that works with tiles."""

  def emitMouse(self, clear, y, x):
    if self.manager:
      y = y / 8 if y else None
      x = x / 8 if x else None
      self.manager.MouseEvent(MousePos(clear, y, x, 8, None))


class InputImageComponentView(TileBasedComponentView):
  """A component showing the input image."""

  def emitMouse(self, clear, y, x):
    if self.manager:
      y = y / 8 if y else None
      x = x / 8 if x else None
      self.manager.MouseEvent(MousePos(clear, y, x, 8, 'input'))


class BlockBasedComponentView(ComponentView):
  """A component that works with blocks."""

  def emitMouse(self, clear, y, x):
    if self.manager:
      y = y / 16 if y else None
      x = x / 16 if x else None
      self.manager.MouseEvent(MousePos(clear, y, x, 16, None))

  def drawBox(self, clear, y, x, size, color):
    if y is None or x is None or size is None:
      new_y = new_x = new_size = None
    else:
      new_size = 16
      new_y = (y * size) / new_size
      new_x = (x * size) / new_size
    ComponentView.drawBox(self, clear, new_y, new_x, new_size, color)


class ReuseBasedComponentView(ComponentView):
  """A component that represents tile reuse."""

  def emitMouse(self, clear, y, x):
    if self.manager:
      y = y / 8 if y else None
      x = x / 8 if x else None
      self.manager.MouseEvent(MousePos(clear, y, x, 8, 'reuse'))


class ChrBasedComponentView(ComponentView):
  """A component that works with chr."""

  def emitMouse(self, clear, y, x):
    if self.manager:
      y = y / 17 if y else None
      x = x / 17 if x else None
      self.manager.ChrMouseEvent(MousePos(clear, y, x, 17, None))


class Cursor(object):
  """Dumb object that represents a cursor with position, size, and color."""

  def __init__(self):
    self.y = None
    self.x = None
    self.size = None
    self.cycler = color_cycler.ColorCycler()
    self.enabled = False

  def nextColor(self):
    self.cycler.next()

  def getColor(self):
    return self.cycler.get_color()

  def set(self, y, x, size):
    self.y = y
    self.x = x
    self.size = size


class DrawCursorManager(object):
  """Manager that routes mouse movement events and draw commands.

  The manager holds references to the cursor, and a list of components.
  Mediates mouse movement, telling each component how to draw the current
  cursor. Also handles cursor animation.
  """
  def __init__(self, parent):
    self.cursor = None
    self.components = []
    self.cursorTimer = None
    self.tileSet = False
    self.reusableCursor = Cursor()
    self.parent = parent
    self.processor = None
    self.CreateCursorTimer()

  def setProcessor(self, processor):
    self.processor = processor

  def addCursor(self, cursor):
    self.cursor = cursor
    # Alias the cycler, so that cursor and reusableCursor share the same one.
    self.reusableCursor.cycler = self.cursor.cycler

  def addComponent(self, component):
    self.components.append(component)
    component.SetManager(self)

  def getChrTilePosition(self):
    nt = self.processor.ppu_memory().get_page(0).nametable
    if self.cursor.y is None or self.cursor.x is None:
      return (None, None)
    try:
      tile = nt[self.cursor.y][self.cursor.x]
    except IndexError:
      # Sometimes, x == size of array.
      return (None, None)
    chr_y = tile / 16
    chr_x = tile % 16
    return chr_y, chr_x

  def CreateCursorTimer(self):
    self.cursorTimer = wx.Timer(self.parent, wx.ID_ANY)
    self.cursorTimer.Start(30)
    self.parent.Bind(wx.EVT_TIMER, self.OnCursorTimer, self.cursorTimer)

  def OnCursorTimer(self, e):
    if not self.cursor.enabled:
      return
    self.cursor.nextColor()
    self.OnCursor(False)

  def MouseEvent(self, pos):
    if not self.cursor.enabled:
      return
    self.tileSet = None
    clear, y, x, size, meta = (pos.clear, pos.y, pos.x, pos.size, pos.meta)
    if clear:
      self.cursor.set(None, None, None)
    if y is not None and x is not None and size is not None:
      self.cursor.set(y, x, size)
    if meta == 'reuse':
      nt = self.processor.ppu_memory().get_page(0).nametable
      try:
        self.tileSet = nt[self.cursor.y][self.cursor.x]
      except TypeError:
        self.tileSet = None
    if meta == 'input':
      e = self.processor.err().find(y, x)
      if e:
        self.parent.ShowMessage('{0} {1}'.format(type(e).__name__, e), 6)
      else:
        self.parent.ShowMessage('', 1)
    self.OnCursor(clear)

  def ChrMouseEvent(self, pos):
    if not self.cursor.enabled:
      return
    clear, y, x, size, meta = (pos.clear, pos.y, pos.x, pos.size, pos.meta)
    if x is None or y is None:
      self.parent.UpdateNumTileMsg(None, None)
      return
    self.tileSet = y * 16 + x
    try:
      elems = self.parent.nt_inverter[self.tileSet]
    except (AttributeError, KeyError):
      elems = None
    if elems:
      (y,x) = elems[0]
      self.cursor.set(y, x, 8)
    self.parent.UpdateNumTileMsg(None, self.tileSet)
    self.OnCursor(clear)

  def OnCursor(self, clear):
    if self.tileSet:
      self.DrawCursorToComponents(clear, self.cursor)
      try:
        elems = self.parent.nt_inverter[self.tileSet]
      except (AttributeError, KeyError):
        elems = None
      if elems and len(elems) <= TILE_REUSE_LIMIT:
        for y,x in elems:
          self.reusableCursor.set(y, x, 8)
          self.DrawCursorToComponents(False, self.reusableCursor)
    else:
      self.DrawCursorToComponents(clear, self.cursor)
    for comp in self.components:
      comp.drawExecute()

  def DrawCursorToComponents(self, clear, cursor):
    color = cursor.getColor()
    for comp in self.components:
      if isinstance(comp, ChrBasedComponentView):
        (chr_y, chr_x) = self.getChrTilePosition()
        chr_size = 17
        if chr_y is not None and chr_x is not None:
          comp.drawBox(clear, chr_y, chr_x, chr_size, color)
      else:
        comp.drawBox(clear, cursor.y, cursor.x, cursor.size, color)


class MakechrGui(wx.Frame):
  """MakechrGui main application."""

  def __init__(self, *args, **kwargs):
    super(MakechrGui, self).__init__(*args, **kwargs)
    self.processor = image_processor.ImageProcessor()
    self.renderer = view_renderer.ViewRenderer(scale=1)
    self.inputImagePath = None
    self.cursor = None
    self.manager = None
    self.watcher = file_modify_watcher.FileModifyWatcher()
    self.messageTimer = None
    self.Create()
    self.Bind(wx.EVT_CLOSE, self._close_handler)

  def Create(self):
    self.panel = wx.Panel(self, -1)
    self.CreateApp()
    self.CreateMenu()
    self.CreateImages()
    self.CreateOptions()
    self.CreateLabels()
    self.CreateReloadTimer()
    self.CreateCursorManager()
    self.CreateMessageTimer()

  def CreateApp(self):
    # On OSX, there's no menubar. Otherwise, add padding.
    height_padding = 0 if sys.platform == 'darwin' else 32
    self.SetSize((APP_WIDTH, APP_HEIGHT + height_padding))
    self.SetTitle(APP_TITLE)
    self.SetPosition((200, 30))
    # Set the application icon.
    res = pkg_resources.resource_stream('makechr', 'res/icon.png')
    bitmap = self.PilImgToBitmap(Image.open(res))
    icon = wx.Icon()
    icon.CopyFromBitmap(bitmap)
    self.SetIcon(icon)

  def CreateMenu(self):
    menubar = wx.MenuBar()
    # File
    fileMenu = wx.Menu()
    self.openItem = fileMenu.Append(wx.ID_ANY, '&Open')
    self.saveItem = fileMenu.Append(wx.ID_ANY, '&Save')
    self.quitItem = fileMenu.Append(wx.ID_EXIT, 'Quit', 'Quit application')
    self.Bind(wx.EVT_MENU, self.OnOpen, self.openItem)
    self.Bind(wx.EVT_MENU, self.OnSave, self.saveItem)
    self.Bind(wx.EVT_MENU, self.OnQuit, self.quitItem)
    self.saveItem.Enable(False)
    menubar.Append(fileMenu, '&File')
    # Tools
    toolsMenu = wx.Menu()
    self.importItem = toolsMenu.Append(wx.ID_ANY, '&Import RAM')
    self.exportItem = toolsMenu.Append(wx.ID_ANY, '&Export Binaries')
    self.compileItem = toolsMenu.Append(wx.ID_ANY, '&Compile to ROM')
    self.Bind(wx.EVT_MENU, self.OnImportRam, self.importItem)
    self.Bind(wx.EVT_MENU, self.OnExportBinaries, self.exportItem)
    self.Bind(wx.EVT_MENU, self.OnCompileRom, self.compileItem)
    self.exportItem.Enable(False)
    self.compileItem.Enable(False)
    menubar.Append(toolsMenu, '&Tools')
    self.SetMenuBar(menubar)

  def CreateImages(self):
    if hasattr(makechr, 'makechr'):
      version = makechr.makechr.__version__
    else:
      version = makechr.__version__

    # Message.
    msg = 'Makechr %s' % version
    self.messageComp = wx.StaticText(self.panel, wx.ID_ANY, label=msg,
                                     pos=(0x20,0x288))

    # Component views.
    self.inputComp = InputImageComponentView(self.panel,
                                             pos=(0x20,0x30), size=(0x100,0xf0))
    self.ntComp = TileBasedComponentView(self.panel,
                                         pos=(0x170,0x30), size=(0x100,0xf0))
    self.colorsComp = BlockBasedComponentView(self.panel,
                                              pos=(0x170,0x140),
                                              size=(0x100,0xf0))
    self.reuseComp = ReuseBasedComponentView(self.panel,
                                            pos=(0x290,0x30), size=(0x100,0xf0))
    self.chrComp = ChrBasedComponentView(self.panel,
                                         pos=(0x290,0x140), size=(0x10f,0x10f))

    # Palette.
    img = wx.Image(104, 32)
    self.paletteCtrl = wx.StaticBitmap(self.panel, wx.ID_ANY,
                                       wx.Bitmap(img),
                                       pos=(0x170,0x250), size=(0x68, 0x20))
    # System colors.
    img = wx.Image(252, 72)
    self.sysColorCtrl = wx.StaticBitmap(self.panel, wx.ID_ANY,
                                        wx.Bitmap(img),
                                        pos=(0x20,0x160), size=(0xfc,0x48))
    self.SetBitmapResource(self.sysColorCtrl, 'res/systemcolors.png')

    # Key for reuse.
    img = wx.Image(42, 144)
    self.rKeyCtrl = wx.StaticBitmap(self.panel, wx.ID_ANY,
                                    wx.Bitmap(img),
                                    pos=(0x3a0,0x30), size=(42,144))
    self.SetBitmapResource(self.rKeyCtrl, 'res/reuse-key.png')

  def CreateOptions(self):
    # Buttons.
    self.gridCheckBox = wx.CheckBox(self.panel, wx.ID_ANY, 'Grid',
                                    pos=(0x20,0x128))
    self.Bind(wx.EVT_CHECKBOX, self.OnGridCheckboxClicked, self.gridCheckBox)

    # Locked tiles.
    self.lockedTilesCheckBox = wx.CheckBox(self.panel, wx.ID_ANY,
                                           'Locked tiles',
                                           pos=(0x20,0x1d4))
    self.Bind(wx.EVT_CHECKBOX, self.OnLockedTilesCheckboxClicked,
              self.lockedTilesCheckBox)
    # Sprite mode.
    self.spriteModeCheckBox = wx.CheckBox(self.panel, wx.ID_ANY, 'Sprite mode',
                                          pos=(0x20,0x1e8))
    self.Bind(wx.EVT_CHECKBOX, self.OnSpriteModeCheckboxClicked,
              self.spriteModeCheckBox)
    # Allow sprite overflow.
    self.allowSpriteOverflowCheckBox = wx.CheckBox(self.panel, wx.ID_ANY,
                                                   'Allow sprite overflow',
                                                   pos=(0x30,0x1fc))
    self.Bind(wx.EVT_CHECKBOX, self.OnAllowSpriteOverflowCheckboxClicked,
              self.allowSpriteOverflowCheckBox)
    self.allowSpriteOverflowCheckBox.Enable(False)
    # Traversal
    self.traversalChoices = ['horizontal', 'vertical', 'block', '8x16']
    traversal_vals = [e.title() + ' traversal' for e in self.traversalChoices]
    self.traversalComboBox = wx.ComboBox(self.panel, wx.ID_ANY,
                                         traversal_vals[0],
                                         pos=(0x20,0x210),
                                         size=(0x100,0x1a),
                                         choices=traversal_vals,
                                         style=wx.CB_READONLY)
    self.Bind(wx.EVT_COMBOBOX, self.OnTraversalComboBoxChosen,
              self.traversalComboBox)
    # Allow chr overflow.
    self.allowChrOverflowCheckBox = wx.CheckBox(self.panel, wx.ID_ANY,
                                                'Allow chr overflow',
                                                pos=(0x20,0x22c))
    self.Bind(wx.EVT_CHECKBOX, self.OnAllowChrOverflowCheckboxClicked,
              self.allowChrOverflowCheckBox)

  def CreateMessageTimer(self):
    self.messageTimer = wx.Timer(self, wx.ID_ANY)
    self.Bind(wx.EVT_TIMER, self.OnMessageTimer, self.messageTimer)

  def OnMessageTimer(self, e):
    self.messageTimer.Stop()
    self.messageComp.SetLabel('')

  def ShowMessage(self, msg, seconds):
    self.messageComp.SetLabel(msg)
    self.messageTimer.Start(seconds * 1000)

  def CreateLabels(self):
    wx.StaticText(self.panel, wx.ID_ANY, label='Pixel art', pos=(0x20, 0x1c))
    wx.StaticText(self.panel, wx.ID_ANY, label='System colors',
                  pos=(0x20, 0x14c))
    wx.StaticText(self.panel, wx.ID_ANY, label='Options',
                  pos=(0x20, 0x1c0))
    wx.StaticText(self.panel, wx.ID_ANY, label='Nametable', pos=(0x170, 0x1c))
    wx.StaticText(self.panel, wx.ID_ANY, label='CHR', pos=(0x290, 0x12c))
    wx.StaticText(self.panel, wx.ID_ANY, label='Attribute', pos=(0x170, 0x12c))
    wx.StaticText(self.panel, wx.ID_ANY, label='Reuse', pos=(0x290, 0x1c))
    wx.StaticText(self.panel, wx.ID_ANY, label='Palette', pos=(0x170, 0x23c))
    wx.StaticText(self.panel, wx.ID_ANY, label='Key', pos=(0x3a0, 0x1c))
    self.numTileCtrl = wx.StaticText(self.panel, wx.ID_ANY,
                                     label='',
                                     pos=(0x290, 0x258))
    self.UpdateNumTileMsg(0, None)

  def SetBitmapResource(self, control, rel):
    try:
      img = Image.open(pkg_resources.resource_stream('makechr', rel))
      wx.CallAfter(control.SetBitmap, self.PilImgToBitmap(img))
    except IOError:
      pass

  def UpdateNumTileMsg(self, num, curr):
    if num is None:
      num = self.num_tiles
    else:
      self.num_tiles = num
    if curr is None:
      msg = 'Number of tiles: %d  Hex: $%02x' % (num, num)
    else:
      msg = ('Number of tiles: %d  Hex: $%02x  Curr: $%02x' % (num, num, curr))
    self.numTileCtrl.SetLabel(msg)

  def CreateCursorManager(self):
    self.cursor = Cursor()
    self.manager = DrawCursorManager(self)
    #self.manager.setProcessor(self.processor)
    self.manager.addCursor(self.cursor)
    self.manager.addComponent(self.inputComp)
    self.manager.addComponent(self.ntComp)
    self.manager.addComponent(self.reuseComp)
    self.manager.addComponent(self.colorsComp)
    self.manager.addComponent(self.chrComp)

  def CreateReloadTimer(self):
    self.reloadTimer = wx.Timer(self, wx.ID_ANY)
    self.Bind(wx.EVT_TIMER, self.OnReloadTimer, self.reloadTimer)

  def IdentifyFileKind(self, path):
    golden = '(VALIANT)'
    fp = open(path, 'rb')
    bytes = fp.read(len(golden))
    fp.close()
    if bytes == golden:
      return 'valiant'
    return 'image'

  def LoadImage(self):
    if self.inputImagePath is None:
      return
    kind = self.IdentifyFileKind(self.inputImagePath)
    if kind == 'image':
      self.ReassignImage()
      self.ProcessMakechr()
      self.CreateViews()
      self.OnImageLoaded()
      # TODO: Unwatch when something else is opened.
      self.watcher.watch(self.inputImagePath, self.OnModify)
      self.ShowMessage('Loaded "%s"' % self.inputImagePath, 4.0)
    elif kind == 'valiant':
      self.LoadValiant()
      self.ReassignImage()
      self.CreateViews()
      self.OnImageLoaded()

  def OnImageLoaded(self):
    self.cursor.enabled = True
    self.saveItem.Enable(True)
    self.exportItem.Enable(True)
    self.compileItem.Enable(True)

  def LoadImportedRam(self):
    path = self.inputImagePath
    importer = memory_importer.MemoryImporter()
    mem = importer.read_ram(path)
    renderer = pixel_art_renderer.PixelArtRenderer()
    img = renderer.render(mem)
    outfile = tempfile.mkstemp(suffix='.png')[1]
    img.save(outfile)
    self.inputImagePath = outfile
    self.processor._err = errors.ErrorCollector()
    self.processor._ppu_memory = mem
    self.ReassignImage()
    self.CreateViews()
    self.OnImageLoaded()
    self.ShowMessage('Imported RAM from "%s"' % path, 4.0)

  def LoadValiant(self):
    path = self.inputImagePath
    importer = memory_importer.MemoryImporter()
    mem = importer.read_valiant(path)
    renderer = pixel_art_renderer.PixelArtRenderer()
    img = renderer.render(mem)
    outfile = tempfile.mkstemp(suffix='.png')[1]
    img.save(outfile)
    self.inputImagePath = outfile
    self.processor._err = errors.ErrorCollector()
    self.processor._ppu_memory = mem
    self.ShowMessage('Opened "%s"' % path, 4.0)

  def ReassignImage(self):
    if not self.inputImagePath:
      return
    if self.gridCheckBox.GetValue():
      renderer = self.renderer
      input = Image.open(self.inputImagePath)
      view = renderer.create_grid_view(None, input)
      bitmap = self.PilImgToBitmap(view)
    else:
      img = wx.Image(self.inputImagePath, wx.BITMAP_TYPE_ANY)
      bitmap = wx.Bitmap(img)
    self.inputComp.load(bitmap)

  def ProcessMakechr(self):
    config = self.BuildConfigFromOptions()
    # TODO: It might be inefficient to reconstruct every time.
    if config.traversal != '8x16':
      self.processor = image_processor.ImageProcessor()
      self.manager.setProcessor(self.processor)
    else:
      self.processor = eight_by_sixteen_processor.EightBySixteenProcessor()
      self.manager.setProcessor(self.processor)
    input = Image.open(self.inputImagePath)
    self.processor.process_image(input, None, None, None, config.traversal,
                                 config.is_sprite, config.is_locked_tiles,
                                 None, config.allow_overflow)

  def CreateViews(self):
    config = self.BuildConfigFromOptions()
    renderer = self.renderer
    if self.processor.err().has():
      self.ClearViews()
      # Errors.
      input = Image.open(self.inputImagePath)
      view = renderer.create_error_view(None, input, self.processor.err().get(),
                                        has_grid=False)
      self.inputComp.load(self.PilImgToBitmap(view))
      return
    self.nt_inverter = self.processor.ppu_memory().build_nt_inverter()
    # Colorization.
    view = renderer.create_colorization_view(None, self.processor.ppu_memory(),
                                             config.is_sprite)
    self.colorsComp.load(self.PilImgToBitmap(view))
    # Nametable.
    view = renderer.create_nametable_view(None, self.processor.ppu_memory())
    self.ntComp.load(self.PilImgToBitmap(view))
    # Reuse.
    view = renderer.create_reuse_view(None, self.processor.ppu_memory(),
                                      self.nt_inverter)
    self.reuseComp.load(self.PilImgToBitmap(view))
    # Palette.
    view = renderer.create_palette_view(None, self.processor.ppu_memory(),
                                        config.is_sprite)
    wx.CallAfter(self.paletteCtrl.SetBitmap, self.PilImgToBitmap(view))
    # Chr.
    view = renderer.create_chr_view(None, self.processor.ppu_memory())
    self.chrComp.load(self.PilImgToBitmap(view))
    # Num tiles.
    num = self.processor.ppu_memory().chr_set.size()
    self.UpdateNumTileMsg(num, None)

  def ClearViews(self):
    self.inputComp.clear()
    self.ntComp.clear()
    self.colorsComp.clear()
    self.reuseComp.clear()
    self.chrComp.clear()

  def PilImgToBitmap(self, pilImg):
    img = wx.Image(*pilImg.size)
    img.SetData(pilImg.convert('RGB').tobytes())
    img.SetAlpha(pilImg.convert('RGBA').tobytes()[3::4])
    return wx.Bitmap(img)

  def BuildConfigFromOptions(self):
    is_locked_tiles = self.lockedTilesCheckBox.GetValue()
    is_sprite = self.spriteModeCheckBox.GetValue()
    allow_s = 's' if self.allowSpriteOverflowCheckBox.GetValue() else ''
    traversal = self.traversalChoices[
      self.traversalComboBox.GetCurrentSelection()]
    allow_c = 'c' if self.allowChrOverflowCheckBox.GetValue() else ''
    config = ppu_memory.PpuMemoryConfig(
      traversal=traversal, is_sprite=is_sprite, is_locked_tiles=is_locked_tiles,
      allow_overflow=[allow_s, allow_c])
    return config

  def OnOpen(self, e):
    dlg = wx.FileDialog(self, 'Choose project or input image', '', '',
                        '*.bmp;*.png;*.gif;*.mchr', wx.FD_OPEN)
    if dlg.ShowModal() == wx.ID_OK:
      self.inputImagePath = dlg.GetPath()
    dlg.Destroy()
    if self.inputImagePath is not None:
      self.LoadImage()

  def OnSave(self, e):
    dlg = wx.FileDialog(self, 'Save project as...', '', '',
                        '*.mchr', wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
    if dlg.ShowModal() != wx.ID_OK:
      return
    path = dlg.GetPath()
    dlg.Destroy()
    if path is not None:
      config = self.BuildConfigFromOptions()
      self.processor.ppu_memory().save_valiant(path, config)
      self.ShowMessage('Saved to "%s"' % path, 4.0)

  def OnImportRam(self, e):
    dlg = wx.FileDialog(self, 'Choose memory dump', '', '',
                        '*.bin;*.mem', wx.FD_OPEN)
    if dlg.ShowModal() == wx.ID_OK:
      self.inputImagePath = dlg.GetPath()
    dlg.Destroy()
    if self.inputImagePath is not None:
      self.LoadImportedRam()

  def OnExportBinaries(self, e):
    dlg = wx.FileDialog(self, 'Save binaries as...', '', '%s.dat',
                        '', wx.FD_SAVE)
    if dlg.ShowModal() != wx.ID_OK:
      return
    path = dlg.GetPath()
    dlg.Destroy()
    if path is not None:
      if not '%s' in path:
        self.ShowMessage('ERROR: Export path must have "%s" in filename', 8.0)
        return
      config = self.BuildConfigFromOptions()
      components = self.processor.ppu_memory().save_template(path, config)
      output_set = path.replace('%s', '{' + '|'.join(components) + '}')
      self.ShowMessage('Exported binaries to "%s"' % output_set, 8.0)

  def OnCompileRom(self, e):
    dlg = wx.FileDialog(self, 'Save ROM as...', '', '', '*.nes',
                        wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
    target = None
    if dlg.ShowModal() == wx.ID_OK:
      target = dlg.GetPath()
    dlg.Destroy()
    if target is not None:
      builder = rom_builder.RomBuilder()
      # This should have a direct reference to mem
      mem = self.processor.ppu_memory()
      builder.build(mem, target)
      self.ShowMessage('Compiled ROM "%s"' % target, 4.0)

  def OnGridCheckboxClicked(self, e):
    self.ReassignImage()

  def OnLockedTilesCheckboxClicked(self, e):
    self.LoadImage()

  def OnSpriteModeCheckboxClicked(self, e):
    self.allowSpriteOverflowCheckBox.Enable(self.spriteModeCheckBox.GetValue())
    self.LoadImage()

  def OnAllowSpriteOverflowCheckboxClicked(self, e):
    self.LoadImage()

  def OnTraversalComboBoxChosen(self, e):
    self.LoadImage()

  def OnAllowChrOverflowCheckboxClicked(self, e):
    self.LoadImage()

  def ReloadFile(self):
    self.ReassignImage()
    self.ProcessMakechr()
    self.CreateViews()
    self.OnImageLoaded()

  def OnReloadTimer(self, e):
    self.reloadTimer.Stop()
    self.ReloadFile()

  def OnModify(self, e):
    wx.CallAfter(self.reloadTimer.Start, 1000)

  def OnQuit(self, e):
    self.Close()

  def _close_handler(self, e):
    try:
      self.watcher.stop()
    except:
      pass
    try:
      self.reloadTimer.Stop()
    except:
      pass
    try:
      self.messageTimer.Stop()
    except:
      pass
    try:
      self.manager.cursorTimer.Stop()
    except:
      pass
    e.Skip()


class MakechrGuiApp(wx.App):
  def OnInit(self):
    self.SetAppName('Makechr')
    mainframe = MakechrGui(None)
    self.SetTopWindow(mainframe)
    mainframe.Show(True)
    return 1


if __name__ == '__main__':
  if len(sys.argv) > 1:
    makechr.run()
    sys.exit(0)
  if hasattr(sys, "frozen"):
    sys.stderr = StringIO.StringIO()
  app = MakechrGuiApp()
  app.MainLoop()
