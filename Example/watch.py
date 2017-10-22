from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class FileModifiedHandler(FileSystemEventHandler):

    def __init__(self, path, file_name, callback):
        self.file_name = file_name
        self.callback = callback

        # set observer to watch for changes in the directory
        self.observer = Observer()
        self.observer.schedule(self, path, recursive=False)
        self.observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.observer.stop()
        
        self.observer.join()

    def on_modified(self, event): 
        # only act on the change that we're looking for
        if not event.is_directory and event.src_path.endswith(self.file_name):
            # self.observer.stop() # stop watching
            self.callback() # call callback


if __name__ == '__main__':
    def update():
        print "FILE WAS MODIFIED"

    print "Waiting for file change..."
    FileModifiedHandler('./JSON', 'inputJSON.json', update)