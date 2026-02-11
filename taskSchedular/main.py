from scheduler.task import Task
from scheduler.scheduler import TaskScheduler

taskMain = TaskScheduler()
sentinal = bool(True)

while sentinal:
    print("1. Insert Task")
    print("2. Get Next Task")
    print("3. Print All Tasks")
    print("4. Current Task")
    print("5. Exit")

    choice = int(input("Enter your choice: "))

    if choice == 1:
        name = input("Enter task name: ")
        notes = input("Enter task notes: ")

        while True:
            priorityInput = (input("Enter task priority (lower number = higher priority): "))
            try:
                priority = int(priorityInput)
                break
            except ValueError:
                print("Invalid priority. Please enter a valid integer.\n")
                continue
        


        task = Task(priority=priority, name=name, notes=notes)
        taskMain.insertTask(task)
        print(f"Task '{name}' added.\n")

    elif choice == 2:
        taskMain.nextTask()

    elif choice == 3:
        print("All Tasks:")
        taskMain.printTasks()
        print()

    elif choice == 4:
        taskMain.currentTask()
        print()

    elif choice == 5:
        sentinal = False
        print("Exiting...")

    else:
        print("Invalid choice. Please try again.\n")