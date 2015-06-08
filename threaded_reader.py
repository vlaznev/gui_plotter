from Queue import Queue
import threading

class ThreadedReader:
	def __init__(self, file, startImmediately=True):
		self.queue = Queue()
		self.file = file
		self.thread = None
		if startImmediately:
			self.start()

	def next(self):
		return None if self.queue.empty() else self.queue.get()

	def thread_loop(self):
		for line in self.file:
			self.queue.put(line)

	def start(self):
		self.thread = threading.Thread(target = self.thread_loop)
		self.thread.daemon = True
		self.thread.start()
