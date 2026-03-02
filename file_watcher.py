import time
import logging
import json
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class FileSystemWatcher(FileSystemEventHandler):
    def __init__(self, vault_path):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.done = self.vault_path / 'Done'
        self.logger = logging.getLogger('FileSystemWatcher')

    def on_created(self, event):
        """Triggered when a new file is created in the watched directory"""
        if event.is_directory:
            return

        # Wait a moment to ensure file is fully written
        time.sleep(0.5)

        source = Path(event.src_path)
        # Skip temporary files
        if source.suffix.startswith('.tmp'):
            return

        self.logger.info(f'New file detected: {source.name}')

        # Create action file in Needs_Action folder
        self.create_action_file(source)

    def create_action_file(self, file_path):
        """Create a markdown file in Needs_Action describing the dropped file"""
        metadata = {
            'type': 'file_drop',
            'original_name': file_path.name,
            'size': file_path.stat().st_size,
            'created': file_path.stat().st_ctime,
            'status': 'pending',
            'priority': 'medium'
        }

        # Create markdown content
        content = f"""---
{json.dumps(metadata, indent=2)}
---

# File Drop Detected

## File Information
- **Name**: {file_path.name}
- **Size**: {self.format_size(file_path.stat().st_size)}
- **Type**: {file_path.suffix}
- **Location**: {file_path.parent}

## Suggested Actions
- [ ] Analyze file content
- [ ] Categorize appropriately
- [ ] Process according to file type
- [ ] Move to appropriate destination
- [ ] Update Dashboard with results

## Processing Notes
- File detected at: {time.strftime('%Y-%m-%d %H:%M:%S')}
- Processing priority: {metadata['priority']}
"""

        # Create markdown file
        action_file = self.needs_action / f'FILE_{file_path.name}.md'
        action_file.write_text(content)

        self.logger.info(f'Created action file: {action_file.name}')

    def format_size(self, size_bytes):
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"

def start_watcher(vault_path):
    """Start the file system watcher"""
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        handlers=[
                            logging.FileHandler('file_watcher.log'),
                            logging.StreamHandler()
                        ])

    event_handler = FileSystemWatcher(vault_path)
    observer = Observer()
    observer.schedule(event_handler, path=str(Path(vault_path) / 'Inbox'), recursive=False)

    observer.start()
    logging.info('File System Watcher started')

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    # Use Silver-Tier vault path
    VAULT_PATH = r"C:\Users\goku\MyWebsiteProjects\hackathon-0\Silver-Tier\AI_Silver_Employee_Vault"
    start_watcher(VAULT_PATH)