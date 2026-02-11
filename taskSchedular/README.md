# Task Scheduler

# A Python-based task scheduling system that allows user to create, manage, and organize tasks.

# Features:

#  - Create tasks with assigned priorities
#  - Automatically schedules tasks using a min-heap
#  - Always retrives the heighest priority task first

# How It Works:

# The scheduler uses a **minimum heap priority queue** to maintain tasks in sorted order based on priority.
# - Lower priority number = higher scheduling priority
# - Insertion: `O(log n)`
# - Removal (extract-min): `O(log n)`
# - Peek highest-priority task: `O(1)`

# This ensures efficiency even as the number of tasks grow.