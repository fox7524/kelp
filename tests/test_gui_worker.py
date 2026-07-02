import os
import shutil
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from PyQt5.QtCore import QEventLoop

from gui import OrganizerWorker
from src.organizer.utils import get_file_date_folder

def test_organizer_worker_pipeline(tmp_path):
    source = tmp_path / "source"
    dest = tmp_path / "dest"
    source.mkdir()
    dest.mkdir()
    
    # Create files
    f1 = source / "alper_gezeravci_video.mp4"
    f2 = source / "yitik_zamanin_izinde_kapak.png"
    f3 = source / "notes.txt"
    f4 = source / "notes_dup.txt"  # Duplicate of notes.txt
    
    f1.write_text("alper gezeravci contents")
    f2.write_text("yitik zamanin contents")
    f3.write_text("notes contents")
    f4.write_text("notes contents")
    
    keywords = ["alper gezeravcı", "yitik zamanın izinde"]
    
    # Initialize the worker
    worker = OrganizerWorker(
        source_dir=source,
        dest_dir=dest,
        keywords=keywords,
        action="copy",
        dry_run=False
    )
    
    # Mock the show_duplicates_signal by automatically populating worker.duplicate_selections and setting the resume event
    def mock_show_duplicates(duplicates, scan_root):
        # We want to keep notes.txt (index 0, path f3) and discard notes_dup.txt (path f4)
        # duplicates is a list of groups: [[f3, f4]]
        # We map group index 0 to f3
        worker.duplicate_selections = {0: f3}
        worker.duplicate_event.set()
        
    worker.show_duplicates_signal.connect(mock_show_duplicates)
    
    # Run the worker synchronously
    worker.run()
    
    # Verify duplicates were resolved:
    # notes_dup.txt (f4) should be moved to _duplicates_backup
    backup_file = source / "_duplicates_backup" / "notes_dup.txt"
    assert backup_file.exists()
    assert backup_file.read_text() == "notes contents"
    assert not f4.exists()
    assert f3.exists()  # notes.txt kept
    
    # Verify files were rearranged into destination folder:
    # alper_gezeravci_video.mp4 -> dest / alper gezeravcı /
    assert (dest / "alper gezeravcı" / "alper_gezeravci_video.mp4").exists()
    # yitik_zamanin_izinde_kapak.png -> dest / yitik zamanın izinde /
    assert (dest / "yitik zamanın izinde" / "yitik_zamanin_izinde_kapak.png").exists()
    # notes.txt (f3) -> dest / YYYY-MM /
    date_folder = get_file_date_folder(f3)
    assert (dest / date_folder / "notes.txt").exists()
