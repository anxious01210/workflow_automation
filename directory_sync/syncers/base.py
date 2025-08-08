class BaseSyncer:
    def __init__(self, directory): self.directory = directory
    def test_connection(self): raise NotImplementedError
    def sync(self): raise NotImplementedError  # return dict(created=.., updated=.., deactivated=.., notes="..")
