
class SVGNode(dict):

    def __init__(self, name, **kvargs):
        self.name = name
        self.attrs = kvargs
        self.children = []

    def append(self, what):
        self.children.append(what)
        return self

    def __str__(self):
        return "<%s %s>%s</%s>" % (
            self.name,
            " ".join(["%s=\"%s\"" % (k, self.attrs[k]) for k in self.attrs]),
            "".join([str(e) for e in self.children]),
            self.name
        )
