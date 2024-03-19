#Convenience Class to store the configuration that was sent by the frontend
class Configuration:

    def __init__(self, request_json):
        self.updateEveryEvent = request_json.get('paramUpdateEveryEvent', False)
        self.updateXEvents = request_json.get('paramUpdateXEvents', False)
        self.updateXEventsValue = request_json.get('paramUpdateXEventsValue', -1)
        self.updateXSeconds = request_json.get('paramUpdateXSeconds', False)
        self.updateXSecondsValue = request_json.get('paramUpdateXSecondsValue', -1)
        self.useSpaceSaving = request_json.get('paramUseSpaceSaving', False)
        self.useLossyCounting = request_json.get('paramUseLossyCounting', False)
        self.datastructureMax = request_json.get('paramDataStructureMax', -1)
        self.mineDuplicates = request_json.get('paramMineDuplicates', False)
        self.noL2LWithL1l = request_json.get('paramNoL2LWithL1l', False)
        self.noBinaryConflicts = request_json.get('paramNoBinaryConflicts', False)
        self.connectNet = request_json.get('paramConnectNet', False)
        self.mineLongDependencies = request_json.get('paramMineLongDependencies', False)
        self.td = request_json.get('paramTd', 0.5)
        self.tl1l = request_json.get('paramTl1l', 0.5)
        self.tl2l = request_json.get('paramTl2l', 0.5)
        self.tld = request_json.get('paramTld', 0.5)
        self.tpat = request_json.get('paramTpat', 0)
        self.useExperimental = request_json.get('paramUseExperimental', False)
