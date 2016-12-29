import os
import watchdog.observers
import watchdog.events


class FileModifyEvent(object):
  def __init__(self, filename):
    self.filename = filename


class FileModifyEventHandler(watchdog.events.FileSystemEventHandler):
  def __init__(self, filename, callback):
    self.filename = os.path.abspath(filename)
    self.callback = callback

  def on_modified(self, event):
    target = os.path.abspath(event.src_path)
    if target == self.filename:
      self.callback(FileModifyEvent(self.filename))

  def observe_path(self):
    return os.path.dirname(os.path.abspath(self.filename))


class FileModifyWatcher(object):
  def __init__(self):
    self.observer = None

  def watch(self, filename, callback):
    self.observer = watchdog.observers.Observer()
    event_handler = FileModifyEventHandler(filename, callback)
    self.observer.schedule(event_handler, event_handler.observe_path())
    self.observer.start()

  def stop(self):
    if self.observer:
      self.observer.stop()

  def finish(self):
    if self.observer:
      self.observer.join()
