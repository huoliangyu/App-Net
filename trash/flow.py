class Flow:
    def __init__(self, id,   ip,  port,  gateway,  flowNumber,  flowClass,  priority,  filterHandle):
        self.id = id
        self.ip = ip
        self.port = port
        self.gateway = gateway
        self.flowNumber = flowNumber
        self.flowClass = flowClass
        self.priority = priority
        self.filterHandle = filterHandle
