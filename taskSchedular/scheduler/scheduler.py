import heapq
from scheduler.task import Task

class TaskScheduler:
    def __init__ (self):
        self._heap = []
    
    def insertTask (self, task: Task):
        heapq.heappush(self._heap,task)

    def nextTask (self):
        sortedTasks = sorted(self._heap)

        if self.isEmpty():
            print("No tasks available")
        else:
            heapq.heappop(self._heap)
            current = sortedTasks[0]
            print("Next Task: " , current.name , current.notes)

    def isEmpty (self) -> bool:
        return len(self._heap) == 0
    
    def printTasks (self):
        sortedTasks = sorted(self._heap)
        if self.isEmpty():
            print("No tasks available")
        for task in sortedTasks:
            print(task.name)

    def currentTask (self):
        sortedTasks = sorted(self._heap)
        if self.isEmpty():
            print("No tasks available")
        else:
            current = sortedTasks[0]
            print("Current Task: " , current.name , current.notes)