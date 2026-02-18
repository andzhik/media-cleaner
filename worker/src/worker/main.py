from .processor import JobProcessor

if __name__ == "__main__":
    print("Worker started")
    processor = JobProcessor()
    processor.process_jobs()

